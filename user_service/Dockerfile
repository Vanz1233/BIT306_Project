FROM python:3.13.1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the project code
COPY . .

# Note: We don't put the CMD here. We will orchestrate that in the docker-compose file!