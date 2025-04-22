# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG=True
ENV SECRET_KEY=temporary-key-for-build-only
ENV PYTHONPATH=/app
ENV CORS_ALLOW_ALL_ORIGINS=True

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create the simplest settings.py fix
RUN echo '#!/bin/bash\nsed -i "s/CORS_ALLOWED_ORIGINS = \\[/CORS_ALLOWED_ORIGINS = \\[\\n    \\"https:\\/\\/mealify-foods.up.railway.app\\",/g" mealify_backend/settings.py' > fix_settings.sh
RUN cat fix_settings.sh
RUN chmod +x fix_settings.sh
RUN ./fix_settings.sh

# Debug - show directory listing
RUN echo "Directory listing:" && ls -la
RUN echo "API directory:" && ls -la api || echo "api directory not found"

# Create necessary files for the User model if they don't exist
RUN mkdir -p api
RUN touch api/__init__.py

# Create basic API files
RUN echo 'from django.contrib.auth.models import AbstractUser\nfrom django.db import models\n\nclass User(AbstractUser):\n    is_vendor = models.BooleanField(default=False)\n    is_customer = models.BooleanField(default=False)\n    is_staff_user = models.BooleanField(default=False)' > api/models.py
RUN echo 'from django.contrib import admin\nfrom .models import User\n\nadmin.site.register(User)' > api/admin.py
RUN echo 'from django.urls import path\nfrom . import views\n\nurlpatterns = [\n    # Add your URL patterns here\n    path("health/", views.health, name="health"),\n]' > api/urls.py
RUN echo 'from django.http import JsonResponse\n\ndef health(request):\n    return JsonResponse({"status": "ok"})' > api/views.py

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8000

# Start command
CMD python manage.py migrate && python manage.py collectstatic --noinput && gunicorn mealify_backend.wsgi --log-file -