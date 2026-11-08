import os
import time
import math
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked
import yt_dlp

# === BOT CREDENTIALS ===
API_ID = 25131184
API_HASH = "33a9391cdc79df295c4e326440e58a8c"
BOT_TOKEN = "8342749669:AAHxEkD6KdWSH_QwERwp6_-ByER5quhLCh0"

# === ADMIN CONFIGURATION ===
ADMIN_ID = 7567720140

app = Client("public_social_downloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# === USER DATABASE (TXT FILE FOR RAILWAY) ===
USERS_FILE = "users_db.txt"

def load_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(int(line.strip()) for line in f if line.strip().isdigit())

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

# === HELPER FUNCTIONS ===
def format_bytes(size):
    power = 2**10
    n = 0
    dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{str(round(size, 2))} {dic_powerN[n]}B"

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

# === PROGRESS BAR ===
async def progress_bar(current, total, message, start_time):
    now = time.time()
    diff = now - start_time
    if diff < 2 or (round(diff % 3.0) != 0 and current != total):
        return
    percentage = current * 100 / total
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0
    progress_str = "[{0}{1}]".format(
        ''.join(["⬢" for i in range(math.floor(percentage / 10))]),
        ''.join(["⬡" for i in range(10 - math.floor(percentage / 10))])
    )
    text = (f"🚀 **Uploading to Telegram...**\n\n"
            f"{progress_str} **{round(percentage, 2)}%**\n"
            f"⚡ **Speed:** {format_bytes(speed)}/s\n"
            f"⏳ **ETA:** {format_time(eta)}\n"
            f"💾 **Size:** {format_bytes(current)} / {format_bytes(total)}")
    try:
        await message.edit_text(text)
    except:
        pass

# === START COMMAND ===
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    save_user(message.from_user.id)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{client.me.username}?startgroup=true")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/INTELLIGENCE_BEE1"),
         InlineKeyboardButton("📢 Updates", url="https://t.me/INTELLIGENCE_BEE1")]
    ])
    await message.reply_text(
        f"👋 **Hello {message.from_user.first_name}, Welcome to Ultimate Downloader!**\n\n"
        "🌐 I can download videos and audio from **TikTok, Facebook, Instagram, Twitter/X, YouTube, Pinterest** and 1000+ other sites.\n\n"
        "📥 **How to use:**\n"
        "Just send me the link of the video you want to download!",
        reply_markup=buttons
    )

# === ADMIN COMMANDS ===
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_cmd(client, message):
    users = load_users()
    await message.reply_text(f"📊 **Bot Statistics:**\n\n👥 Total Users: `{len(users)}`")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Please reply to a message to broadcast it.")
    
    users = load_users()
    await message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    success, failed = 0, 0
    for user_id in users:
        try:
            await message.reply_to_message.copy(user_id)
            success += 1
            await asyncio.sleep(0.1) # Anti-Flood
        except UserIsBlocked:
            failed += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user_id)
            success += 1
        except:
            failed += 1

    await message.reply_text(f"✅ **Broadcast Completed!**\n\n🎯 Success: `{success}`\n🚫 Failed/Blocked: `{failed}`")

# === CORE DOWNLOADER ===
@app.on_message(filters.text & filters.private & ~filters.command(["start", "stats", "broadcast"]))
async def download_media(client, message):
    save_user(message.from_user.id)
    url = message.text.strip()
    
    if not url.startswith("http"):
        return await message.reply_text("❌ Please send a valid URL (http/https).")

    status_msg = await message.reply_text("🔍 **Analyzing Link...**")

    # yt-dlp Options for Max Quality (No Watermark for TikTok)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True
    }

    try:
        await status_msg.edit_text("⬇️ **Downloading Media to Server...**")
        
        # Run yt-dlp in a background thread to prevent blocking other users
        def extract_and_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        info = await asyncio.to_thread(extract_and_download)
        
        file_path = f"downloads/{info['id']}.mp4"
        title = info.get('title', 'Social Media Video')
        uploader = info.get('uploader', info.get('extractor_key', 'Unknown'))
        
        caption = (f"🎬 **{title[:50]}...**\n"
                   f"👤 **Source:** {uploader}\n\n"
                   f"🤖 @{client.me.username}")

        # Inline Button for sharing
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 Share Bot", switch_inline_query=" is the best downloader bot!")
        ]])

        await status_msg.edit_text("📤 **Uploading to Telegram...**")
        start_time = time.time()
        
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=caption,
            supports_streaming=True,
            reply_markup=reply_markup,
            progress=progress_bar,
            progress_args=(status_msg, start_time)
        )
            
        await status_msg.delete()
        
        # Auto Clean-up
        if os.path.exists(file_path): 
            os.remove(file_path)

    except Exception as e:
        error_text = str(e)
        if "Unsupported URL" in error_text:
            err_msg = "❌ This website is not supported."
        elif "Private video" in error_text or "Video is private" in error_text:
            err_msg = "❌ This account or video is private. I cannot access it."
        else:
            err_msg = f"❌ **Download Failed:**\n\n`{error_text[:200]}`"
            
        await status_msg.edit_text(err_msg)

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    print("🚀 Ultimate Public Social Downloader is Online!")
    app.run()
