from django.urls import path
from .views import RegisterView, LoginView, CartView
from .views import get_all_foods
from . import views
from .views import update_or_delete_cart_item

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    
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
    
    # Payment endpoints
    path('payment/initialize/', views.initialize_transaction, name='initialize_payment'),
    path('payment/verify/', views.verify_transaction, name='verify_payment'),
    path('order/checkout/', views.place_order_with_payment, name='checkout'),

    # Dashboard endpoints
    path('dashboard/stats/', views.get_dashboard_stats, name='dashboard_stats'),
]




  