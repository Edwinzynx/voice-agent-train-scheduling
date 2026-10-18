# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app
ENV APP_ENV=production PYTHONUNBUFFERED=1

# Copy the requirements file into the container
COPY backend/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Keep local credentials, databases, and frontend tooling out of the backend image.
COPY backend /app/backend
COPY eval /app/eval
WORKDIR /app/backend

# Expose port 8000 for the FastAPI server
EXPOSE 8000

# Run run.py when the container launches
CMD ["python", "run.py"]
