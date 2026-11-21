# Small, official Python base image
FROM python:3.11-slim

# Sensible Python defaults for containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app ./app

# Copy Streamlit frontend
copy ./streamlit_app.py ./streamlit_app.py 

# The port uvicorn will listen on
EXPOSE 8000
EXPOSE 8501

# Start the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]