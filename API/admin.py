from django.contrib import admin
from .models import Food

# Only register the Food model
admin.site.register(Food)
