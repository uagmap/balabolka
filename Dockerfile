#=================
# Builder stage
#=================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

COPY requirements.txt .

# Install dependencies to user space and clean up
RUN pip install --user --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt && \
    # Clean up pip cache and temp files
    rm -rf /tmp/* /root/.cache/pip

#======================
# Production stage
#======================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Safety
RUN find /root/.local -name "__pycache__" -type d -exec rm -rf {} + && \
    rm -rf /root/.cache

# Run the application
CMD ["python", "bot.py"]