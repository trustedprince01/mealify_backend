from django.urls import path
from .views import RegisterView, LoginView, CartView
from .views import get_all_foods
from . import views
from .views import update_or_delete_cart_item

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('foods/', get_all_foods, name='get_all_foods'),
    path('cart/', CartView.as_view()),  
    path('foods/', views.get_all_foods),
    path('cart/', views.get_user_cart),
    path('cart/add/', views.add_to_cart),
    path('cart/delete/<int:item_id>/', views.delete_cart_item),
    path('cart/<int:item_id>/', update_or_delete_cart_item),  # ✅ PATCH & DELETE
    path('cart/place-order/', views.place_order),
    path('orders/', views.user_orders),


]




  