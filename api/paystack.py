# api/paystack.py
import requests
import json
import uuid
import os
from django.conf import settings

# Use the secret key from settings
PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
# Use the frontend URL from settings or default to localhost
FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')

def generate_reference():
    """Generate a unique transaction reference"""
    return str(uuid.uuid4())

def initialize_payment(amount, email, reference=None):
    """Initialize a payment with Paystack"""
    if reference is None:
        reference = generate_reference()
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    # Convert amount to kobo (Paystack uses the smallest currency unit)
    amount_in_kobo = int(float(amount) * 100)
    
    data = {
        "email": email,
        "amount": amount_in_kobo,
        "reference": reference,
        "callback_url": f"{FRONTEND_URL}/payment/verify"  # Dynamic callback URL
    }
    
    print(f"Initializing payment with data: {data}")
    print(f"Using secret key: {PAYSTACK_SECRET_KEY[:5]}...")
    print(f"Using callback_url: {data['callback_url']}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()
        
        print(f"Paystack response: {response_data}")
        
        if response.status_code == 200 and response_data.get('status'):
            return {
                'status': True,
                'data': response_data.get('data'),
                'reference': reference
            }
        return {
            'status': False,
            'message': response_data.get('message', 'Payment initialization failed')
        }
    except Exception as e:
        print(f"Error initializing payment: {str(e)}")
        return {
            'status': False, 
            'message': str(e)
        }

def verify_payment(reference):
    """Verify a payment using the reference"""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'status': response_data.get('status'),
                'data': response_data.get('data'),
                'message': response_data.get('message')
            }
        return {
            'status': False,
            'message': response_data.get('message', 'Payment verification failed')
        }
    except Exception as e:
        return {
            'status': False,
            'message': str(e)
        }