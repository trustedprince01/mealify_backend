from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Food, CartItem, Order, OrderItem, Payment, DeliveryAddress

# Register the custom User model
admin.site.register(User, UserAdmin)

# Register other models
admin.site.register(Food)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(DeliveryAddress)
