import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mealify_backend.settings')
django.setup()

# Import the User model
from api.models import User

# Update the admin user
try:
    admin = User.objects.get(email='admin@mealify.com')
    admin.role = 'admin'  # Set role to admin
    admin.is_vendor = True  # Enable vendor access
    admin.save()
    
    # Print confirmation
    print(f"Admin user updated successfully:")
    print(f"- Username: {admin.username}")
    print(f"- Email: {admin.email}")
    print(f"- Role: {admin.role}")
    print(f"- Vendor access: {admin.is_vendor}")
    print(f"- Superuser: {admin.is_superuser}")
    
except User.DoesNotExist:
    print("Admin user with email 'admin@mealify.com' not found")
except Exception as e:
    print(f"Error updating admin user: {str(e)}") 