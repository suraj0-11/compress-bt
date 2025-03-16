FROM python:3.11-slim

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

# Install pip and setuptools first
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python packages
RUN pip install --no-cache-dir \
    pyrogram==2.0.106 \
    tgcrypto==1.2.5 \
    python-dotenv==1.0.0 \
    aiofiles==23.2.1 \
    hachoir==3.2.0

# Verify installations
RUN pip list

# Copy the application
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Set environment variables
ENV PATH="/usr/local/bin:${PATH}"
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages:/app:${PYTHONPATH}"

# Test imports
RUN python3 -c "import sys; print('Python version:', sys.version)"
RUN python3 -c "import asyncio; print('Asyncio version:', asyncio.__version__ if hasattr(asyncio, '__version__') else 'built-in')"
RUN python3 -c "import tgcrypto; print('TgCrypto imported successfully')"
RUN python3 -c "import pyrogram; print('Pyrogram imported successfully')"

# Command to run the bot
CMD ["python3", "bot.py"] 