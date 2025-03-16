FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1-mesa-glx \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg installation
RUN ffmpeg -version

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install each package individually with explicit versions
RUN pip install --no-cache-dir pyrogram==2.0.106 && \
    pip install --no-cache-dir tgcrypto==1.2.5 && \
    pip install --no-cache-dir python-dotenv==1.0.0 && \
    pip install --no-cache-dir aiofiles==23.2.1 && \
    pip install --no-cache-dir hachoir==3.2.0 && \
    pip install --no-cache-dir asyncio==3.4.3

# Verify installations
RUN pip list

# Copy the application
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Set environment variable for FFmpeg path
ENV PATH="/usr/bin:${PATH}"
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Run test script
RUN python3 test_imports.py

# Command to run the application
CMD ["sh", "-c", "python3 test_imports.py && python3 bot.py"] 