import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import shutil
import math
import re
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Bot configuration
class Config:
    API_ID = 3281305
    API_HASH = "a9e62ec83fe3c22379e3e19195c8b3f6"
    BOT_TOKEN = "6519805517:AAFiX-NMkszvdThiwIplnFLHgDB78J_LbQw"
    AUTH_USERS = [6147004598, 6052965703, 6953453057]
    TEMP_FOLDER = "downloads"
    PRESET = "veryfast"  # Default preset
    CRF = "28"  # Default CRF value for x264
    AUDIO_CODEC = "libopus"  # Default audio codec
    CODEC = "libx264"  # Default video codec
    MAX_QUEUE_SIZE = 5  # Maximum files in queue per user
    QUALITY = "846x480"  # Default quality
    
    # Valid presets and CRF values for different codecs
    VALID_PRESETS = {
        "libx264": ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
        "libx265": ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
        "av1": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]
    }
    
    DEFAULT_CRF = {
        "libx264": "28",
        "libx265": "27",
        "av1": "45"
    }

    @classmethod
    def get_valid_presets(cls, codec):
        return cls.VALID_PRESETS.get(codec, cls.VALID_PRESETS["libx264"])

    @classmethod
    def is_valid_preset(cls, codec, preset):
        return preset in cls.get_valid_presets(codec)

    @classmethod
    def get_default_crf(cls, codec):
        return cls.DEFAULT_CRF.get(codec, "28")

# Queue system
class QueueSystem:
    def __init__(self):
        self.user_queues: Dict[int, List[Tuple[Message, str]]] = defaultdict(list)
        self.processing: Dict[int, bool] = defaultdict(bool)
        self.lock = asyncio.Lock()

    async def add_to_queue(self, user_id: int, message: Message, file_name: str) -> Tuple[bool, int]:
        async with self.lock:
            if len(self.user_queues[user_id]) >= Config.MAX_QUEUE_SIZE:
                return False, len(self.user_queues[user_id])
            self.user_queues[user_id].append((message, file_name))
            return True, len(self.user_queues[user_id])

    async def process_queue(self, user_id: int):
        if self.processing[user_id]:
            return
        
        self.processing[user_id] = True
        try:
            while self.user_queues[user_id]:
                message, file_name = self.user_queues[user_id][0]
                await process_file(message, file_name)
                async with self.lock:
                    self.user_queues[user_id].pop(0)
        finally:
            self.processing[user_id] = False

    async def get_queue_status(self, user_id: int) -> str:
        queue = self.user_queues[user_id]
        if not queue:
            return "No files in queue"
        
        status = "🎯 Queue Status:\n\n"
        for i, (_, file_name) in enumerate(queue, 1):
            status += f"{i}. {file_name}\n"
        return status

# Initialize bot and queue
app = Client("compression_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
queue_system = QueueSystem()

# Create temp folder if not exists
if not os.path.exists(Config.TEMP_FOLDER):
    os.makedirs(Config.TEMP_FOLDER)

# Helper function to format size
def format_size(size):
    units = ['B', 'KB', 'MB', 'GB']
    size_bytes = float(size)
    unit_index = 0
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1
    return f"{size_bytes:.2f} {units[unit_index]}"

# Progress bar function
def create_progress_bar(current, total):
    length = 20
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    percent = round(current * 100 / total, 1)
    return f"[{bar}] {percent}%"

# Time formatter
def time_formatter(seconds: float) -> str:
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return ((str(days) + "d, ") if days else "") + \
           ((str(hours) + "h, ") if hours else "") + \
           ((str(minutes) + "m, ") if minutes else "") + \
           ((str(seconds) + "s") if seconds else "")

# Progress callback for download and upload
async def progress_callback(current, total, message, start_time, action):
    now = time.time()
    diff = now - start_time
    
    if diff < 1:
        return
    
    speed = current / diff
    progress_bar = create_progress_bar(current, total)
    percentage = round(current * 100 / total, 1)
    current_mb = round(current / 1024 / 1024, 2)
    total_mb = round(total / 1024 / 1024, 2)
    
    if speed > 0:
        eta = (total - current) / speed
    else:
        eta = 0
    
    eta = time_formatter(eta)
    speed = f"{round(speed / 1024 / 1024, 2)} MB/s"
    
    text = f"{action}\n\n" \
           f"{progress_bar}\n" \
           f"💫 **Progress**: {percentage}%\n" \
           f"💾 **Size**: {current_mb}/{total_mb} MB\n" \
           f"⚡ **Speed**: {speed}\n" \
           f"⏰ **ETA**: {eta}"
    
    try:
        await message.edit_text(text)
    except:
        pass

# Encoding progress monitor
async def monitor_encoding_progress(progress_file, message, input_size):
    start_time = time.time()
    while True:
        if not os.path.exists(progress_file):
            break
            
        with open(progress_file, 'r') as file:
            lines = file.readlines()
            
        progress_info = {}
        for line in lines:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                progress_info[key] = value
                
        if 'out_time_ms' in progress_info:
            time_in_ms = int(progress_info['out_time_ms'])
            if 'duration' in progress_info:
                duration_ms = float(progress_info['duration']) * 1000000
                progress = min(time_in_ms / duration_ms, 1)
                await progress_callback(
                    time_in_ms,
                    duration_ms,
                    message,
                    start_time,
                    "🔄 Encoding Video"
                )
                
        await asyncio.sleep(3)

# Compression function
async def compress_video(input_file, output_file, message, codec):
    progress_file = f"{Config.TEMP_FOLDER}/progress.txt"
    error_file = f"{Config.TEMP_FOLDER}/error.txt"
    
    # Change output extension to mkv to support all codecs and subtitles
    output_file = output_file.rsplit('.', 1)[0] + '.mkv'
    
    # Base command with input file
    cmd = [
        "ffmpeg", "-hide_banner",
        "-i", input_file,
        "-map", "0",  # Map all streams
        "-metadata", "title=CompressBotTG",  # Add metadata
    ]
    
    # Add video codec specific settings
    if codec == "libx264":
        cmd.extend([
            "-c:v", codec,
            "-preset", Config.PRESET,
            "-crf", Config.CRF,
            "-pix_fmt", "yuv420p",
        ])
    elif codec == "libx265":
        cmd.extend([
            "-c:v", codec,
            "-preset", Config.PRESET,
            "-crf", Config.CRF,
            "-pix_fmt", "yuv420p",
            "-x265-params", "no-info=1",
            "-tag:v", "hvc1",  # For better compatibility
        ])
    elif codec == "av1":
        cmd.extend([
            "-c:v", "libsvtav1",
            "-preset", Config.PRESET,
            "-crf", Config.CRF,
            "-pix_fmt", "yuv420p",
        ])
    
    # Add quality settings if specified
    if Config.QUALITY:
        cmd.extend(["-s", Config.QUALITY])
    
    # Add audio settings
    cmd.extend([
        "-c:a", "libopus",
        "-ac", "1",  # Mono audio
        "-vbr", "2",  # Variable bitrate mode
    ])
    
    # Add subtitle settings
    cmd.extend([
        "-c:s", "copy",  # Copy subtitles
    ])
    
    # Add output settings
    cmd.extend([
        "-max_muxing_queue_size", "1024",
        "-progress", progress_file,
        output_file,
        "-y"
    ])
    
    # Create process with pipe for stderr
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Wait for the process to complete and get output
    stdout, stderr = await process.communicate()
    
    # Check if output file exists and has size
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return True, output_file
    else:
        # Log the error
        error_msg = stderr.decode() if stderr else "Unknown error"
        await message.reply_text(
            f"❌ Encoding failed!\n\n"
            f"Command: {' '.join(cmd)}\n\n"
            f"Error: {error_msg}"
        )
        return False, None

# Process file function
async def process_file(message: Message, file_name: str = None):
    download_path = None
    output_path = None
    progress_file = None
    
    try:
        # Get file info
        file_name = file_name or (message.document.file_name if message.document else "video.mp4")
        download_path = os.path.join(Config.TEMP_FOLDER, f"input_{file_name}")
        output_path = os.path.join(Config.TEMP_FOLDER, f"compressed_{file_name}")
        progress_file = f"{Config.TEMP_FOLDER}/progress.txt"
        
        # Download file
        status_msg = await message.reply_text(
            f"⚙️ Processing File\n\n"
            f"🎥 File: {file_name}\n"
            f"🛠 Codec: {Config.CODEC}\n"
            f"📊 CRF: {Config.CRF}\n"
            f"⚡ Preset: {Config.PRESET}\n"
            f"📐 Resolution: {Config.QUALITY}\n"
            f"🔊 Audio: {Config.AUDIO_CODEC}"
        )
        
        start_time = time.time()
        
        # Download with progress
        await message.download(
            file_name=download_path,
            progress=progress_callback,
            progress_args=(status_msg, start_time, "📥 Downloading")
        )
        
        # Verify downloaded file
        if not os.path.exists(download_path) or os.path.getsize(download_path) == 0:
            raise Exception("Download failed or file is empty")
        
        # Get original file size
        original_size = os.path.getsize(download_path)
        
        # Start encoding
        await status_msg.edit_text("🎬 Starting encoding process...")
        
        # Create tasks for encoding and progress monitoring
        encoding_process = asyncio.create_task(
            compress_video(download_path, output_path, status_msg, Config.CODEC)
        )
        progress_monitor = asyncio.create_task(
            monitor_encoding_progress(progress_file, status_msg, original_size)
        )
        
        # Wait for encoding to complete
        success, final_output_path = await encoding_process
        await progress_monitor
        
        if success and os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0:
            compressed_size = os.path.getsize(final_output_path)
            
            # Verify compressed file size
            if compressed_size == 0:
                raise Exception("Compressed file is empty")
            
            # Upload the compressed file
            start_time = time.time()
            await status_msg.edit_text("📤 Starting upload...")
            
            await message.reply_document(
                final_output_path,
                progress=progress_callback,
                progress_args=(status_msg, start_time, "📤 Uploading"),
                caption=(
                    f"📊 Compression Stats:\n\n"
                    f"Original size: {format_size(original_size)}\n"
                    f"Compressed size: {format_size(compressed_size)}\n"
                    f"Codec: {Config.CODEC}\n"
                    f"CRF: {Config.CRF}\n"
                    f"Preset: {Config.PRESET}\n"
                    f"Resolution: {Config.QUALITY}\n"
                    f"Compression ratio: {(1 - (compressed_size / original_size)) * 100:.1f}%"
                )
            )
            
            await status_msg.edit_text("✅ Process Completed Successfully!")
        else:
            await status_msg.edit_text("❌ Compression failed! Check logs for details.")
            
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)  # Print to console for debugging
        if 'status_msg' in locals():
            await status_msg.edit_text(f"❌ {error_msg}")
        else:
            await message.reply_text(f"❌ {error_msg}")
        
    finally:
        # Cleanup
        for path in [download_path, output_path, progress_file]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

# Command handlers
@app.on_message(filters.command("start"))
async def start_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        await message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    
    await message.reply_text(
        "Welcome to the File Compression Bot!\n\n"
        "Just send me any file and I'll compress it automatically.\n\n"
        "Available commands:\n"
        "/codec - Set compression codec (libx264/libx265)\n"
        "/quality - Set output resolution (e.g., /quality 1280x720)\n"
        "/crf - Set CRF value (e.g., /crf 28)\n"
        "/preset - Set encoding preset (e.g., /preset veryfast)\n"
        "/queue - Show current queue status\n"
        "/help - Show help message"
    )

@app.on_message(filters.command("help"))
async def help_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        return
    
    valid_presets = Config.get_valid_presets(Config.CODEC)
    help_text = (
        "**Available Commands:**\n\n"
        "Just send files to compress them automatically\n"
        "/codec [codec] - Set codec (libx264/libx265)\n"
        "/quality [width]x[height] - Set resolution (e.g., 1280x720)\n"
        "/crf [value] - Set CRF value (0-51, lower is better quality)\n"
        f"/preset [value] - Set preset ({', '.join(valid_presets)})\n"
        "/queue - Show current queue status\n\n"
        "Current Settings:\n"
        f"Preset: {Config.PRESET}\n"
        f"CRF: {Config.CRF}\n"
        f"Quality: {Config.QUALITY or 'Original'}\n"
        f"Audio Codec: {Config.AUDIO_CODEC}\n"
        f"Video Codec: {Config.CODEC}"
    )
    await message.reply_text(help_text)

@app.on_message(filters.command("codec"))
async def codec_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        return
    
    try:
        codec = message.text.split()[1].lower()
        if codec not in ["libx264", "libx265", "av1"]:
            await message.reply_text("Invalid codec. Use libx264, libx265, or av1")
            return
        
        # Update codec and set appropriate CRF
        Config.CODEC = codec
        Config.CRF = Config.get_default_crf(codec)
        
        # For AV1, change preset to numerical value if not already
        if codec == "av1" and not Config.PRESET.isdigit():
            Config.PRESET = "6"  # Default AV1 preset
        
        await message.reply_text(
            f"Codec set to {codec}\n"
            f"CRF automatically adjusted to {Config.CRF}\n"
            f"Current preset: {Config.PRESET}"
        )
    except IndexError:
        await message.reply_text("Please specify a codec: /codec [libx264/libx265/av1]")

@app.on_message(filters.command("quality"))
async def quality_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        return
    
    try:
        quality = message.text.split()[1].lower()
        if not re.match(r'^\d+x\d+$', quality):
            await message.reply_text("Invalid format. Use width x height (e.g., 1280x720)")
            return
        
        Config.QUALITY = quality
        await message.reply_text(f"Quality set to {quality}")
    except IndexError:
        await message.reply_text("Please specify quality: /quality [width]x[height]")

@app.on_message(filters.command("crf"))
async def crf_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        return
    
    try:
        crf = message.text.split()[1]
        if not crf.isdigit() or not (0 <= int(crf) <= 51):
            await message.reply_text("CRF value must be between 0 and 51")
            return
        
        Config.CRF = crf
        await message.reply_text(f"CRF value set to {crf}")
    except IndexError:
        await message.reply_text("Please specify CRF value: /crf [0-51]")

@app.on_message(filters.command("preset"))
async def preset_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        return
    
    try:
        preset = message.text.split()[1].lower()
        if not Config.is_valid_preset(Config.CODEC, preset):
            valid_presets = Config.get_valid_presets(Config.CODEC)
            await message.reply_text(f"Invalid preset. Valid presets for {Config.CODEC}: {', '.join(valid_presets)}")
            return
        
        Config.PRESET = preset
        await message.reply_text(f"Preset set to {preset}")
    except IndexError:
        valid_presets = Config.get_valid_presets(Config.CODEC)
        await message.reply_text(f"Please specify preset: /preset [{', '.join(valid_presets)}]")

@app.on_message(filters.command("queue"))
async def queue_command(client, message):
    if message.from_user.id not in Config.AUTH_USERS:
        return
    
    status = await queue_system.get_queue_status(message.from_user.id)
    await message.reply_text(status)

# Handle incoming files
@app.on_message(filters.document | filters.video)
async def handle_file(client, message: Message):
    if message.from_user.id not in Config.AUTH_USERS:
        await message.reply_text("You are not authorized to use this bot.")
        return
    
    file_name = message.document.file_name if message.document else "video.mp4"
    
    # Add to queue
    added, queue_position = await queue_system.add_to_queue(message.from_user.id, message, file_name)
    
    if not added:
        await message.reply_text(
            f"⚠️ Queue is full (max {Config.MAX_QUEUE_SIZE} files).\n"
            "Please wait for current files to complete."
        )
        return
    
    await message.reply_text(
        f"✅ File added to queue\n"
        f"📝 Position: {queue_position}\n"
        f"📁 File: {file_name}"
    )
    
    # Start processing queue
    asyncio.create_task(queue_system.process_queue(message.from_user.id))

# Start the bot
app.run() 