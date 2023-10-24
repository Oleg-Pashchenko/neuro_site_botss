# Use an official Python 3.12 image as the base image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Install any dependencies (e.g., Django, if not already in your requirements.txt)
RUN pip install -r requirements.txt

# Expose the port on which the Django development server will run
EXPOSE 5000

# Start the Django development server
CMD ["python", "main.py"]
