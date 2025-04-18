from .paystack import initialize_payment, verify_payment
from .models import Payment, DeliveryAddress, Order, User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
import json

from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
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
import requests
from django.conf import settings
import cloudinary.uploader
from rest_framework.parsers import MultiPartParser, FormParser



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

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=400)

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





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_transaction(request):
    """Initialize a Paystack payment for an order"""
    data = request.data
    
    # Extract order details from the request
    order_id = data.get('order_id')
    email = request.user.email
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    
    # Generate a unique reference
    reference = f"order_{order.id}_{order.created_at.timestamp()}"
    
    # Initialize payment with Paystack
    response = initialize_payment(order.total, email, reference)
    
    if response['status']:
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            amount=order.total,
            reference=reference,
            status='pending'
        )
        
        return Response({
            'status': True,
            'message': 'Payment initialized',
            'data': {
                'authorization_url': response['data']['authorization_url'],
                'reference': reference,
                'payment_id': payment.id
            }
        })
    
    return Response({
        'status': False,
        'message': response['message']
    }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_transaction(request):
    """Verify a Paystack payment"""
    data = request.data
    reference = data.get('reference')
    
    if not reference:
        return Response({'error': 'Reference is required'}, status=400)
    
    try:
        payment = Payment.objects.get(reference=reference)
        order = payment.order
        
        # Ensure the order belongs to the current user
        if order.user != request.user:
            return Response({'error': 'Unauthorized'}, status=403)
        
        # Verify with Paystack
        response = verify_payment(reference)
        
        if response['status'] and response['data']['status'] == 'success':
            # Update payment status
            payment.status = 'completed'
            payment.verified = True
            payment.save()
            
            # Update order status
            order.status = 'paid'
            order.save()
            
            return Response({
                'status': True,
                'message': 'Payment verified successfully',
                'data': {
                    'order_id': order.id,
                    'payment_id': payment.id,
                    'amount': payment.amount
                }
            })
        
        return Response({
            'status': False,
            'message': 'Payment verification failed'
        })
    
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order_with_payment(request):
    try:
        print("Received payment request:", request.data)
        # Get order data from request
        order_data = request.data.get('order', {})
        payment_method = order_data.get('payment_method')
        print(f"Payment method: {payment_method}")

        # Validate items exist
        items = order_data.get('items', [])
        if not items:
            return Response({
                'status': False,
                'message': 'No items in order'
            }, status=400)

        # Calculate total cost - convert string prices to float
        total_cost = sum(float(item['price']) * int(item['quantity']) for item in items)
        print(f"Total cost: {total_cost}")

        # Create order with correct field names
        order = Order.objects.create(
            user=request.user,
            total=total_cost,  # Changed from total_amount to total
            status='pending'
        )
        print(f"Created order: {order.id}")

        # Add order items - make sure to get the Food objects
        for item in items:
            try:
                food = Food.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order,
                    food=food,
                    quantity=int(item['quantity'])
                )
            except Food.DoesNotExist:
                order.delete()
                return Response({
                    'status': False,
                    'message': f'Food item with id {item["id"]} not found'
                }, status=400)
        print("Added order items")

        # Create payment record to store payment method
        payment = Payment.objects.create(
            order=order,
            amount=total_cost,
            payment_method=payment_method,
            status='pending',
            reference=f"order_{order.id}_{order.created_at.timestamp()}"
        )
        
        if payment_method == 'card':
            try:
                # Initialize payment with Paystack
                print("Initializing Paystack payment...")
                response = requests.post(
                    'https://api.paystack.co/transaction/initialize',
                    json={
                        'email': request.user.email,
                        'amount': int(float(total_cost) * 100),  # Convert to kobo
                        'callback_url': 'http://localhost:8080/dashboard/orders',  # Redirect to orders page after payment
                        'reference': payment.reference,
                        'metadata': {
                            'order_id': order.id,
                            'user_id': request.user.id
                        }
                    },
                    headers={
                        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                        'Content-Type': 'application/json'
                    }
                )
                print("Paystack response:", response.json())

                if response.status_code == 200:
                    data = response.json()
                    if data['status']:
                        return Response({
                            'status': True,
                            'message': 'Payment initialized successfully',
                            'data': {
                                'authorization_url': data['data']['authorization_url']
                            }
                        })
                    else:
                        print("Paystack error:", data['message'])
                        order.delete()
                        return Response({
                            'status': False,
                            'message': data['message']
                        }, status=400)
                else:
                    print("Paystack error status:", response.status_code)
                    order.delete()
                    return Response({
                        'status': False,
                        'message': 'Failed to initialize payment'
                    }, status=400)
            except Exception as e:
                print("Paystack exception:", str(e))
                order.delete()
                return Response({
                    'status': False,
                    'message': str(e)
                }, status=500)
        elif payment_method == 'cash':
            # For cash payment, update both order and payment status
            order.status = 'pending'  # or 'processing' depending on your status flow
            order.save()
            
            # Update payment status
            payment.status = 'pending'
            payment.save()
            
            return Response({
                'status': True,
                'message': 'Order placed successfully',
                'data': {
                    'order_id': order.id
                }
            })
        else:
            order.delete()
            return Response({
                'status': False,
                'message': 'Invalid payment method'
            }, status=400)

    except Exception as e:
        print("Order placement exception:", str(e))
        return Response({
            'status': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    """Get dashboard statistics for the current user"""
    try:
        print("Fetching dashboard stats for user:", request.user.username)
        
        # Get all orders for the user (for total count)
        all_orders = Order.objects.filter(user=request.user)
        total_orders = all_orders.count()
        print(f"Total orders: {total_orders}")
        
        # Get only delivered orders for total spent calculation
        delivered_orders = Order.objects.filter(user=request.user, status='delivered')
        
        # Calculate total spent - handle possible None values
        total_spent = sum(order.total or 0 for order in delivered_orders)
        print(f"Total spent: {total_spent}")
        
        # For now, we'll return 0 for favorites until that feature is implemented
        favorite_count = 0
        
        stats = {
            'totalOrders': total_orders,
            'totalSpent': float(total_spent),
            'favoriteCount': favorite_count
        }
        print("Returning stats:", stats)
        
        return Response(stats)
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        return Response({
            'totalOrders': 0,
            'totalSpent': 0,
            'favoriteCount': 0
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get the current user's profile information"""
    try:
        user = request.user
        profile_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'date_joined': user.date_joined,
        }
        return Response(profile_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update the current user's profile information"""
    try:
        user = request.user
        data = request.data
        
        # Update user fields if provided
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user's password"""
    try:
        user = request.user
        data = request.data
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return Response({'error': 'Current password and new password are required'}, status=400)
        
        # Verify current password
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=400)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_picture(request):
    try:
        if 'image' not in request.FILES:
            return Response({
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES['image']
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image,
            folder="mealify_profiles",
            transformation=[
                {'width': 400, 'height': 400, 'crop': 'fill'},
                {'quality': 'auto'},
                {'fetch_format': 'auto'}
            ]
        )

        # Update user's profile picture URL
        user = request.user
        user.profile_picture = upload_result['secure_url']
        user.save()

        return Response({
            'message': 'Profile picture updated successfully',
            'profile_picture': upload_result['secure_url']
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)