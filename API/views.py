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
from rest_framework.permissions import BasePermission



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_foods(request):
    """Get all available foods"""
    try:
        foods = Food.objects.all().order_by('-created_at')  # latest first
        serializer = FoodSerializer(foods, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error fetching foods: {str(e)}")
        return Response(
            {'error': 'Could not load foods, try again later'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'token': f"Bearer {str(refresh.access_token)}",
        'refresh': str(refresh)
    }

class RegisterView(APIView):
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use"}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "User registered successfully"}, status=201)


class LoginView(APIView):
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        login_type = request.data.get("login_type", "customer")  # Default to customer if not specified

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=400)

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({"error": "Invalid email or password"}, status=400)
                
            # Validate login type against user role
            if login_type == "vendor" and not user.is_vendor:
                return Response({"error": "This account does not have vendor access"}, status=403)
                
            if login_type == "customer" and user.is_vendor and not user.is_staff_member:
                return Response({"error": "Vendor accounts should use the vendor login"}, status=403)

            tokens = get_tokens_for_user(user)
            return Response({
                "token": tokens["token"],
                "refresh": tokens["refresh"],
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_vendor": user.is_vendor,
                "first_name": user.first_name,
                "last_name": user.last_name
            }, status=200)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
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
    """Get all orders for the current user"""
    try:
        print(f"Getting orders for user: {request.user.username}")
        print(f"User role: {request.user.role}")
        print(f"Auth header: {request.headers.get('Authorization', 'No auth header')}")
        
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        print(f"Found {orders.count()} orders for this user")
        
        # Debug order details
        for order in orders:
            print(f"Order {order.id}: status={order.status}, total={order.total}, items={order.items.count()}")
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response(
            {'error': 'No orders found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"Error in user_orders: {str(e)}")
        return Response(
            {'error': 'Failed to fetch orders, try again later'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )





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
            'profile_picture': user.profile_picture or '',
        }
        return Response(profile_data)
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        return Response(
            {'error': 'Could not load profile, try again later'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

class IsVendorPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_vendor

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsVendorPermission])
def add_food(request):
    """Add a new food item (vendor only)"""
    try:
        data = request.data
        
        # Upload image to Cloudinary if provided
        image_url = None
        if 'image' in request.FILES:
            upload_result = cloudinary.uploader.upload(
                request.FILES['image'],
                folder="mealify_foods",
                transformation=[
                    {'width': 800, 'height': 600, 'crop': 'fill'},
                    {'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            image_url = upload_result['secure_url']
        else:
            return Response({'error': 'Image is required'}, status=400)

        # Create food item
        food = Food.objects.create(
            vendor=request.user,
            name=data.get('name'),
            description=data.get('description', ''),
            price=data.get('price'),
            category=data.get('category'),
            isVeg=data.get('category') == 'veg',
            image=image_url
        )

        return Response({
            'message': 'Food item added successfully',
            'food': {
                'id': food.id,
                'name': food.name,
                'price': food.price,
                'image': food.image,
                'category': food.category
            }
        }, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorPermission])
def get_vendor_foods(request):
    """Get all food items for the current vendor"""
    try:
        foods = Food.objects.filter(vendor=request.user).order_by('-created_at')
        data = [{
            'id': food.id,
            'name': food.name,
            'description': food.description,
            'price': food.price,
            'image': food.image,
            'category': food.category,
            'isVeg': food.isVeg,
            'is_available': food.is_available,
            'rating': food.rating,
            'created_at': food.created_at
        } for food in foods]
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsVendorPermission])
def update_food(request, food_id):
    """Update a food item (vendor only)"""
    try:
        food = Food.objects.get(id=food_id, vendor=request.user)
        data = request.data

        # Update image if provided
        if 'image' in request.FILES:
            upload_result = cloudinary.uploader.upload(
                request.FILES['image'],
                folder="mealify_foods",
                transformation=[
                    {'width': 800, 'height': 600, 'crop': 'fill'},
                    {'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            food.image = upload_result['secure_url']

        # Update other fields
        if 'name' in data:
            food.name = data['name']
        if 'description' in data:
            food.description = data['description']
        if 'price' in data:
            food.price = data['price']
        if 'category' in data:
            food.category = data['category']
            food.isVeg = data['category'] == 'veg'
        if 'is_available' in data:
            food.is_available = data['is_available']

        food.save()

        return Response({
            'message': 'Food item updated successfully',
            'food': {
                'id': food.id,
                'name': food.name,
                'price': food.price,
                'image': food.image,
                'category': food.category,
                'is_available': food.is_available
            }
        })
    except Food.DoesNotExist:
        return Response({'error': 'Food item not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsVendorPermission])
def delete_food(request, food_id):
    """Delete a food item (vendor only)"""
    try:
        food = Food.objects.get(id=food_id, vendor=request.user)
        food.delete()
        return Response({'message': 'Food item deleted successfully'})
    except Food.DoesNotExist:
        return Response({'error': 'Food item not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def become_vendor(request):
    """Request to become a vendor"""
    try:
        user = request.user
        if user.is_vendor:
            return Response({'error': 'User is already a vendor'}, status=400)

        data = request.data
        user.is_vendor = True
        user.store_name = data.get('store_name')
        user.store_description = data.get('store_description', '')
        user.save()

        return Response({
            'message': 'Successfully registered as vendor',
            'store_name': user.store_name
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

class StaffLoginView(APIView):
    def post(self, request):
        staff_id = request.data.get("staff_id")
        password = request.data.get("password")

        if not staff_id or not password:
            return Response({"error": "Staff ID and password are required"}, status=400)

        try:
            user = User.objects.get(staff_id=staff_id, is_staff_active=True)
        except User.DoesNotExist:
            return Response({"error": "Invalid staff ID or password"}, status=400)

        user = authenticate(username=user.username, password=password)
        if not user or not user.is_staff_member:
            return Response({"error": "Invalid staff ID or password"}, status=400)

        tokens = get_tokens_for_user(user)
        
        return Response({
            "token": tokens["token"],
            "refresh": tokens["refresh"],
            "staff_id": user.staff_id,
            "role": user.role,
            "username": user.username,
            "email": user.email
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_staff_account(request):
    """Create a new staff account (Admin only)"""
    if not request.user.role == 'admin':
        return Response({"error": "Only admin can create staff accounts"}, status=403)

    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        
        if role not in ['manager', 'staff']:
            return Response({"error": "Invalid role specified"}, status=400)

        # Generate unique staff ID
        import random
        import string
        staff_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        while User.objects.filter(staff_id=staff_id).exists():
            staff_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=role,
            staff_id=staff_id,
            is_staff_active=True
        )

        # Create staff profile
        StaffProfile.objects.create(
            user=user,
            department=data.get('department'),
            phone_number=data.get('phone_number'),
            address=data.get('address')
        )

        return Response({
            "message": "Staff account created successfully",
            "staff_id": staff_id
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_staff_list(request):
    """Get list of all staff members (Admin only)"""
    if not request.user.role == 'admin':
        return Response({"error": "Only admin can view staff list"}, status=403)

    try:
        staff_users = User.objects.filter(role__in=['admin', 'manager', 'staff'])
        data = [{
            'id': user.id,
            'email': user.email,
            'staff_id': user.staff_id,
            'role': user.role,
            'is_active': user.is_staff_active,
            'profile': {
                'department': user.staff_profile.department if hasattr(user, 'staff_profile') else None,
                'phone_number': user.staff_profile.phone_number if hasattr(user, 'staff_profile') else None,
            }
        } for user in staff_users]
        
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_staff_status(request, user_id):
    """Toggle staff account active status (Admin only)"""
    if not request.user.role == 'admin':
        return Response({"error": "Only admin can modify staff status"}, status=403)

    try:
        user = User.objects.get(id=user_id)
        if user.role == 'admin':
            return Response({"error": "Cannot modify admin status"}, status=400)

        user.is_staff_active = not user.is_staff_active
        user.save()

        return Response({
            "message": f"Staff account is now {'active' if user.is_staff_active else 'inactive'}",
            "is_active": user.is_staff_active
        })
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """Verify if the token is valid and return user info"""
    try:
        user = request.user
        return Response({
            'valid': True,
            'role': user.role,
            'username': user.username,
            'email': user.email
        })
    except Exception as e:
        return Response({'error': str(e)}, status=401)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, order_id):
    """Cancel an order (user only)"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        # Only allow cancellation of pending orders
        if order.status != 'pending':
            return Response({'error': 'Only pending orders can be cancelled'}, status=400)
        
        order.status = 'cancelled'
        order.save()
        
        return Response({'message': 'Order cancelled successfully'})
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorPermission])
def get_vendor_orders(request):
    """Get all orders for the current vendor"""
    try:
        print(f"Getting orders for vendor: {request.user.username}")
        print(f"User role: {request.user.role}")
        print(f"Is vendor: {request.user.is_vendor}")
        print(f"Auth header: {request.headers.get('Authorization', 'No auth header')}")
        
        # Get all orders that contain food items from this vendor
        vendor_foods = Food.objects.filter(vendor=request.user)
        print(f"Found {vendor_foods.count()} food items for this vendor")
        
        # Debug food items
        for food in vendor_foods:
            print(f"Food {food.id}: {food.name}, vendor={food.vendor.username if food.vendor else 'None'}")
        
        orders = Order.objects.filter(items__food__in=vendor_foods).distinct().order_by('-created_at')
        print(f"Found {orders.count()} orders for this vendor")
        
        # Debug order details
        for order in orders:
            print(f"Order {order.id}: status={order.status}, total={order.total}, items={order.items.count()}")
        
        # Serialize the orders
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in get_vendor_orders: {str(e)}")
        print(f"Exception type: {type(e)}")
        print(f"Exception args: {e.args}")
        return Response({'error': str(e)}, status=500)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsVendorPermission])
def update_order_status(request, order_id):
    """Update the status of an order (vendor only)"""
    try:
        # Get the order
        order = Order.objects.get(id=order_id)
        
        # Check if the order contains food from this vendor
        vendor_foods = Food.objects.filter(vendor=request.user)
        if not order.items.filter(food__in=vendor_foods).exists():
            return Response({'error': 'You do not have permission to update this order'}, status=403)
        
        # Get the new status
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status is required'}, status=400)
        
        # Validate the status
        valid_statuses = ['pending', 'preparing', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return Response({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}, status=400)
        
        # Update the order status
        order.status = new_status
        order.save()
        
        return Response({'message': f'Order status updated to {new_status}'})
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_orders(request):
    """Get recent orders for the current user"""
    try:
        # Get the 5 most recent orders
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)