# Telegram File Compression Bot

A Telegram bot that compresses files using various codecs (libx264, libx265, and AV1) with libopus audio codec.

## Features

- Supports multiple video codecs:
  - libx264 (H.264)
  - libx265 (H.265/HEVC)
  - AV1 (libsvtav1)
- Uses libopus for audio compression
- Authorized users only
- Progress tracking
- File size comparison
- Supports all file types
- Easy deployment to Koyeb

## Requirements

- Python 3.8+
- FFmpeg with libx264, libx265, and libsvtav1 support
- Required Python packages (see requirements.txt)

## Setup

1. Install FFmpeg with required codecs:
```bash
sudo apt update
sudo apt install ffmpeg
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python3 bot.py
```

## Deployment to Koyeb

1. Fork this repository
2. Create a new Koyeb account if you don't have one
3. Create a new app in Koyeb and connect it to your forked repository
4. The bot will automatically start running

## Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/codec [codec]` - Set compression codec (libx264/libx265/av1)
- Send any file to compress it

## Configuration

The bot is pre-configured with:
- Default preset: medium
- Default CRF: 28
- Audio codec: libopus
- Audio bitrate: 40k

## Note

Make sure to have enough storage space available for processing files. 