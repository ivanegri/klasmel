FROM python:3.9-slim

WORKDIR /app

# Copy requirements from the v2_flask directory
COPY v2_flask/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p data

# Copy the entire project
COPY . .

EXPOSE 5000

# Run the Flask application
CMD ["python", "v2_flask/app.py"]
