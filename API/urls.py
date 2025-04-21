from django.urls import path
from .views import RegisterView, LoginView, CartView, StaffLoginView
from .views import get_all_foods
from . import views
from .views import update_or_delete_cart_item

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/staff/login/', StaffLoginView.as_view(), name='staff_login'),
    path('verify-token/', views.verify_token, name='verify-token'),
    
    # Staff management endpoints
    path('staff/create/', views.create_staff_account, name='create_staff'),
    path('staff/list/', views.get_staff_list, name='staff_list'),
    path('staff/<int:user_id>/toggle-status/', views.toggle_staff_status, name='toggle_staff_status'),
    
    # User profile endpoints
    path('profile/', views.get_user_profile, name='get_user_profile'),
    path('profile/update/', views.update_user_profile, name='update_user_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/upload-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    
    # Food endpoints
    path('foods/', views.get_all_foods, name='get_all_foods'),
    
    # Cart endpoints
    path('cart/', views.get_user_cart, name='get_user_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/delete/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('cart/<int:item_id>/', update_or_delete_cart_item, name='update_or_delete_cart_item'),
    path('cart/place-order/', views.place_order, name='place_order'),
    
    # Order endpoints
    path('orders/', views.user_orders, name='user_orders'),
    path('orders/recent/', views.get_recent_orders, name='recent_orders'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Vendor order endpoints
    path('vendor/orders/', views.get_vendor_orders, name='vendor_orders'),
    path('vendor/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Payment endpoints
    path('payment/initialize/', views.initialize_transaction, name='initialize_payment'),
    path('payment/verify/', views.verify_transaction, name='verify_payment'),
    path('order/checkout/', views.place_order_with_payment, name='checkout'),

    # Dashboard endpoints
    path('dashboard/stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('vendor/dashboard/stats/', views.get_vendor_stats, name='vendor_dashboard_stats'),

    # Vendor endpoints
    path('vendor/become/', views.become_vendor, name='become_vendor'),
    path('vendor/foods/', views.get_vendor_foods, name='vendor_foods'),
    path('vendor/foods/add/', views.add_food, name='add_food'),
    path('vendor/foods/<int:food_id>/', views.update_food, name='update_food'),
    path('vendor/foods/<int:food_id>/delete/', views.delete_food, name='delete_food'),
]




  