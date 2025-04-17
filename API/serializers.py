from rest_framework import serializers
from .models import Food, CartItem
from .models import Order, OrderItem


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    food = FoodSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'food', 'quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    food = FoodSerializer()

    class Meta:
        model = OrderItem
        fields = ['food', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'items', 'total', 'status', 'created_at']


     
       