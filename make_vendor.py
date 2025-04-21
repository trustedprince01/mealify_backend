import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mealify_backend.settings')
django.setup()

# Import the User model
from api.models import User

# User email to make vendor
email = "email@example.com"  # CHANGE THIS to the user's email

# Update the user to be a vendor
try:
    user = User.objects.get(email=email)
    user.is_vendor = True  # Enable vendor access
    user.role = 'customer'  # Keep original role (or set to the appropriate role)
    
    # Optional: Add store information
    user.store_name = "Vendor Store Name"  # CHANGE THIS
    user.store_description = "Store description goes here"  # CHANGE THIS
    
    user.save()
    
    # Print confirmation
    print(f"User successfully made a vendor:")
    print(f"- Username: {user.username}")
    print(f"- Email: {user.email}")
    print(f"- Role: {user.role}")
    print(f"- Vendor access: {user.is_vendor}")
    print(f"- Store name: {user.store_name}")
    
except User.DoesNotExist:
    print(f"User with email '{email}' not found")
except Exception as e:
    print(f"Error updating user: {str(e)}") 