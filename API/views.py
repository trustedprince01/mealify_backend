from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Food
from .serializers import FoodSerializer


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




