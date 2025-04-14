from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FoodViewSet, register_user, LoginView

router = DefaultRouter()
router.register(r'foods', FoodViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', register_user, name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]

