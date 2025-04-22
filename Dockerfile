# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files and run migrations during container start
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Collect static files and run migrations during container start
CMD ["gunicorn", "mealify_backend.wsgi", "--log-file", "-"]