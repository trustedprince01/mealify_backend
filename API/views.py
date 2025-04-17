from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Food
from .serializers import FoodSerializer
from .models import CartItem
from .serializers import CartItemSerializer
from rest_framework.permissions import IsAuthenticated
from .models import CartItem, Food
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.decorators import permission_classes
from .models import Order, CartItem, OrderItem
from .serializers import OrderSerializer




@api_view(['GET'])
def get_all_foods(request):
    foods = Food.objects.all().order_by('-created_at')  # latest first
    serializer = FoodSerializer(foods, many=True)
    return Response(serializer.data)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'token': str(refresh.access_token),
        'refresh': str(refresh)
    }

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use"}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "User registered successfully"}, status=201)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password"}, status=400)

        user = authenticate(username=user.username, password=password)
        if not user:
            return Response({"error": "Invalid email or password"}, status=400)

        tokens = get_tokens_for_user(user)

        return Response({
            "token": tokens["token"],
            "refresh": tokens["refresh"],
            "username": user.username,
            "email": user.email
        }, status=200)
    
class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request):
        food_id = request.data.get("food_id")
        quantity = int(request.data.get("quantity", 1))

        try:
            food = Food.objects.get(id=food_id)
        except Food.DoesNotExist:
            return Response({"error": "Food not found"}, status=404)

        cart_item, created = CartItem.objects.get_or_create(user=request.user, food=food)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response({"message": "Item added to cart"}, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    serializer = CartItemSerializer(cart_items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    food_id = request.data.get('food_id')
    quantity = int(request.data.get('quantity', 1))

    try:
        food = Food.objects.get(id=food_id)
    except Food.DoesNotExist:
        return Response({'error': 'Food not found'}, status=404)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        food=food,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return Response({'message': 'Item added to cart'}, status=201)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cart_item(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        item.delete()
        return Response({'message': 'Item removed'}, status=200)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=404)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_or_delete_cart_item(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=404)

    if request.method == 'PATCH':
        quantity = request.data.get('quantity')
        if quantity is not None:
            item.quantity = quantity
            item.save()
            return Response({'message': 'Quantity updated'}, status=200)
        else:
            return Response({'error': 'Quantity is required'}, status=400)

    elif request.method == 'DELETE':
        item.delete()
        return Response({'message': 'Item removed from cart'}, status=200)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)
    
    if not cart_items.exists():
        return Response({'error': 'Cart is empty'}, status=400)

    total = sum(item.food.price * item.quantity for item in cart_items)
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        total=total,
        status='pending'
    )
    
    # Create order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            food=item.food,
            quantity=item.quantity
        )
    
    # Clear cart after order is created
    cart_items.delete()
    
    # Serialize the order and return it
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)