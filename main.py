import os
import time
import math
import psutil
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# API Credentials (အသေထည့်ထားသည်)
API_ID = 25131184
API_HASH = "33a9391cdc79df295c4e326440e58a8c"
BOT_TOKEN = "8342749669:AAHxEkD6KdWSH_QwERwp6_-ByER5quhLCh0"

app = Client("ultimate_downloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Helper Functions ---
def format_bytes(size):
    power = 2**10
    n = 0
    dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{str(round(size, 2))} {dic_powerN[n]}B"

def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0: return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0: return f"{minutes}m {seconds}s"
    else: return f"{seconds}s"

# --- Live Progress Bar ---
async def progress_bar(current, total, message, start_time):
    now = time.time()
    diff = now - start_time
    if diff < 2 or (round(diff % 3.0) != 0 and current != total):
        return
    percentage = current * 100 / total
    speed = current / diff
    time_to_completion = round((total - current) / speed) if speed > 0 else 0
    progress_str = "[{0}{1}]".format(
        ''.join(["█" for i in range(math.floor(percentage / 5))]),
        ''.join(["░" for i in range(20 - math.floor(percentage / 5))])
    )
    text = (f"🚀 **Uploading to Telegram...**\n\n"
            f"{progress_str} **{round(percentage, 2)}%**\n"
            f"⚡ **Speed:** {format_bytes(speed)}/s\n"
            f"⏳ **ETA:** {format_time(time_to_completion)}\n"
            f"💾 **Size:** {format_bytes(current)} / {format_bytes(total)}")
    try:
        await message.edit_text(text)
    except:
        pass

# --- Start & Commands ---
@app.on_message(filters.command("start"))
async def start_command(client, message):
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛠 Developer", url="https://t.me/INTELLIGENCE_BEE1")]]
    )
    await message.reply_text(
        "👋 **Ultimate Social Media Downloader မှ ကြိုဆိုပါတယ်။**\n\n"
        "🌐 **Supported Sites:** Facebook, TikTok, Instagram, Twitter, YouTube အပါအဝင် Website ပေါင်း ၁၀၀၀ ကျော်။\n\n"
        "🎬 Video ဒေါင်းရန် - Link ကို တိုက်ရိုက်ပို့ပါ။\n"
        "🎵 Audio (MP3) ဒေါင်းရန် - `/audio <link>` လို့ပို့ပါ။\n"
        "🖥 Server စစ်ရန် - `/stats` ကိုနှိပ်ပါ။",
        reply_markup=buttons
    )

@app.on_message(filters.command("stats"))
async def stats_command(client, message):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    await message.reply_text(f"🖥 **Railway Server Status:**\n\n⚙️ CPU: `{cpu}%`\n🧠 RAM: `{ram}%`\n💾 Disk: `{disk}%`")

# --- Core Downloader ---
@app.on_message(filters.text & ~filters.command(["start", "stats"]))
async def download_media(client, message):
    text = message.text.strip()
    is_audio = text.startswith("/audio")
    url = text.replace("/audio", "").strip() if is_audio else text

    if not url.startswith("http"):
        return await message.reply_text("❌ ကျေးဇူးပြု၍ မှန်ကန်သော Website Link ကိုသာ ပေးပို့ပါ။")

    status_msg = await message.reply_text("🔍 **Link ကို စစ်ဆေးနေပါသည်...**")

    # yt-dlp Ultimate Configurations
    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'geo_bypass': True,  # နိုင်ငံခြားက ပိတ်ထားတာတွေကို ကျော်ဒေါင်းမယ်
        'nocheckcertificate': True,
        'writethumbnail': not is_audio, # Video ဆိုရင် Cover ပုံပါ ဆွဲမယ်
        'quiet': True,
        'no_warnings': True
    }

    if is_audio:
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}]
    else:
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        await status_msg.edit_text("⬇️ **Server ထဲသို့ အကြည်ဆုံး Quality ဖြင့် Download ဆွဲနေပါသည်...**")
        
        # Async run for blocking yt-dlp code
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
                
        info = await asyncio.to_thread(download_process)
        
        # Paths Setup
        if is_audio:
            file_path = f"downloads/{info['id']}.mp3"
        else:
            file_path = f"downloads/{info['id']}.mp4"
            
        thumb_path = f"downloads/{info['id']}.jpg" if not is_audio and os.path.exists(f"downloads/{info['id']}.jpg") else None

        title = info.get('title', 'Downloaded Media')
        uploader = info.get('uploader', info.get('extractor_key', 'Unknown Site'))
        duration = info.get('duration', 0)

        caption = (f"🎬 **{title}**\n\n"
                   f"📌 **Source:** {uploader}\n"
                   f"⏱ **Duration:** {format_time(duration)}\n\n"
                   f"🔥 **Downloaded via Ultimate Bot**")

        await status_msg.edit_text("📤 **Telegram သို့ ပြန်လည် ပေးပို့နေပါသည်...**")
        start_time = time.time()
        
        if is_audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=caption,
                title=title,
                performer=uploader,
                progress=progress_bar,
                progress_args=(status_msg, start_time)
            )
        else:
            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=caption,
                thumb=thumb_path,
                supports_streaming=True,
                progress=progress_bar,
                progress_args=(status_msg, start_time)
            )
            
        await status_msg.delete()
        
        # Cleanup
        if os.path.exists(file_path): os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)

    except Exception as e:
        await status_msg.edit_text(f"❌ **Download မအောင်မြင်ပါ:**\n\n`{str(e)[:400]}`\n\n(Private Account သို့မဟုတ် Server ပိတ်ထားသော Link ဖြစ်နိုင်ပါသည်)")

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    print("🚀 Ultimate Social Media Downloader is Online!")
    app.run()
