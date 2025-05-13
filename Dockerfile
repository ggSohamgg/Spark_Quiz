# Use the official Python slim image to keep the image size small
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files
COPY . .

# Expose the port Fly.io will use (default is 8080)
EXPOSE 8080

# Command to run the Flask app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
