# Use a Python base image from Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything except the database folder into the container
COPY /src /app/

# Expose the port that Flask app runs on (if you're using a different port, change it here)
EXPOSE 8002

# Command to run the Fast API app when the container starts
CMD ["python", "auth_server.py"]
