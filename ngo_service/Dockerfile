FROM python:3.13.1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the project code
COPY . .

# Start the NGO Service on Port 8002
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8002"]