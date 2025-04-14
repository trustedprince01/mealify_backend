from django.urls import path
from .views import RegisterView, LoginView
from .views import get_all_foods

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
     path('foods/', get_all_foods, name='get_all_foods'),
]

