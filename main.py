import os
from pyrogram import Client, filters
from dotenv import load_dotenv
import yt_dlp

# Load environment variables if they exist
load_dotenv()

# Variables with built-in fallbacks to prevent any 401 Unauthorized errors
API_ID = os.getenv("API_ID", "25131184")
API_HASH = os.getenv("API_HASH", "33a9391cdc79df295c4e326440e58a8c")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8342749669:AAHxEkD6KdWSH_QwERwp6_-ByER5quhLCh0")

# Initialize the Bot
app = Client(
    "mega_media_downloader",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply_text(
        "👋 **Welcome to Mega Media Downloader!**\n\n"
        "🔗 Send me any video link (YouTube, TikTok, Facebook, etc.) and I will download it in the **highest quality** available."
    )

@app.on_message(filters.text & ~filters.command("start"))
def download_media(client, message):
    url = message.text
    
    # Validate URL
    if not url.startswith("http"):
        message.reply_text("❌ Please send a valid HTTP/HTTPS video link.")
        return

    # Initial status update
    status_msg = message.reply_text("⏳ **Analyzing link...**\nPreparing to fetch the highest quality video.")

    # yt-dlp configurations for the absolute best quality video and audio combined
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True
    }

    try:
        # Update status
        status_msg.edit_text("⬇️ **Downloading...**\nPlease wait, this may take a few moments depending on the file size.")
        
        # Process the download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            title = info.get('title', 'Downloaded Video')
            
        # Update status for Telegram upload
        status_msg.edit_text("📤 **Upload in progress...**\nSending the high-quality video to Telegram.")
        
        # Send the file to the user
        client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎬 **{title}**\n\n✅ Downloaded via Mega Media Bot",
            reply_to_message_id=message.id
        )
        
        # Clean up: Delete the status message and the local file to save storage
        status_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        # Display exact error if something fails (e.g., unsupported website)
        status_msg.edit_text(f"❌ **Download Failed:**\n\n`{str(e)}`")

if __name__ == "__main__":
    # Auto-create downloads folder if it doesn't exist
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    print("🚀 Mega Media Downloader is running successfully!")
    app.run()
