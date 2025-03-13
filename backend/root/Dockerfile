# backend/root/Dockerfile

FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Create certificate directory
RUN mkdir -p /app/cert/

# Copy SSL certificate
COPY DigiCertGlobalRootCA.crt.pem /app/cert/DigiCertGlobalRootCA.crt.pem

# Copy the rest of the application code
COPY . /app/

# Expose port
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]