# Use a lightweight Python base image
FROM python:3.9-slim
# Set working directory
WORKDIR /app
# Copy only necessary files
COPY src/ .
# Install dependencies
RUN pip install --no-cache-dir flask requests
# Run the node
CMD ["python", "node.py"]