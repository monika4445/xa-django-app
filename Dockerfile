# Dockerfile
FROM python:3.10-slim

WORKDIR /xa

# Install system dependencies
RUN apt-get update && apt-get install -y git libpq-dev

# Copy requirements and install them
COPY requirements.txt /xa/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire project
COPY . /xa/

# Expose the port for Gunicorn/Django
EXPOSE 8000

# Start Gunicorn, binding to 0.0.0.0:8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
