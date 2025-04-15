from django.urls import path
from .views import RegisterView, LoginView, CartView
from .views import get_all_foods

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('foods/', get_all_foods, name='get_all_foods'),
    path('cart/', CartView.as_view()),  

]




# urlpatterns = [
#     path('auth/register/', RegisterView.as_view()),
#     path('auth/login/', LoginView.as_view()),
#     path('foods/', get_all_foods),
   
# ]
