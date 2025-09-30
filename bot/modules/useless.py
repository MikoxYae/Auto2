from pyrogram.filters import command, private
from pyrogram.types import Message

from bot import bot, admin, Var
from bot.core.database import db
from bot.core.func_utils import new_task, sendMessage

@bot.on_message(command('dlt_time') & private & admin)
@new_task
async def set_delete_time(client, message):
    try:
        duration = int(message.command[1])
        
        if duration < 10:
            return await sendMessage(message, "<b>Duration must be at least 10 seconds.</b>")
        
        await db.set_del_timer(duration)
        
        # Convert seconds to readable format
        if duration >= 3600:
            time_str = f"{duration // 3600}h {(duration % 3600) // 60}m {duration % 60}s"
        elif duration >= 60:
            time_str = f"{duration // 60}m {duration % 60}s"
        else:
            time_str = f"{duration}s"
        
        await sendMessage(message, f"<b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ <blockquote>{duration} sᴇᴄᴏɴᴅs ({time_str}).</blockquote></b>")

    except (IndexError, ValueError):
        await sendMessage(message, "<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b>\n\n<b>Usage:</b> <code>/dlt_time [duration]</code>\n\n<b>Example:</b>\n<code>/dlt_time 300</code> (5 minutes)\n<code>/dlt_time 1800</code> (30 minutes)")
    except Exception as e:
        await sendMessage(message, f"<b>Error setting delete timer:</b> <code>{str(e)}</code>")

@bot.on_message(command('check_dlt_time') & private & admin)
@new_task
async def check_delete_time(client, message):
    try:
        duration = await db.get_del_timer()
        
        # Convert seconds to readable format
        if duration >= 3600:
            time_str = f"{duration // 3600}h {(duration % 3600) // 60}m {duration % 60}s"
        elif duration >= 60:
            time_str = f"{duration // 60}m {duration % 60}s"
        else:
            time_str = f"{duration}s"
        
        await sendMessage(message, f"<b><blockquote>Cᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ɪs sᴇᴛ ᴛᴏ {duration} sᴇᴄᴏɴᴅs ({time_str}).</blockquote></b>")
    
    except Exception as e:
        await sendMessage(message, f"<b>Error retrieving delete timer:</b> <code>{str(e)}</code>")

@bot.on_message(command('help') & private & admin)
@new_task
async def help_command(client, message):
    user_id = message.from_user.id
    
    if user_id == Var.OWNER_ID:
        help_text = """
<b>🔧 Owner Commands:</b>
• /restart - Restart the bot
• /add_admin [user_id] - Add admin
• /deladmin [user_id] or /deladmin all - Remove admin(s)
• /admins - View all admins
• /ban [user_id] - Ban user(s)
• /unban [user_id] or /unban all - Unban user(s)
• /banlist - View banned users
• /broadcast - Broadcast message to all users
• /pbroadcast - Broadcast and pin message
• /dbroadcast [duration] - Broadcast with auto-delete
• /users - Check total users
• /log - Get bot logs
• /addlink [rss_url] - Add RSS feed
• /addtask [rss_url] [index] - Add specific task
• /rtask [rss_url] [index] - Retry specific task
• /reboot - Clear anime cache
• /pause - Pause anime fetching
• /resume - Resume anime fetching
• /dlt_time [seconds] - Set auto-delete timer
• /check_dlt_time - Check current delete timer

<b>📊 Admin Commands:</b>
• /users - Check total users
• /log - Get bot logs
• /ban [user_id] - Ban user(s)
• /unban [user_id] or /unban all - Unban user(s)
• /banlist - View banned users
• /pause - Pause anime fetching
• /resume - Resume anime fetching
• /addlink [rss_url] - Add RSS feed
• /addtask [rss_url] [index] - Add specific task
• /rtask [rss_url] [index] - Retry specific task
• /reboot - Clear anime cache
• /dlt_time [seconds] - Set auto-delete timer
• /check_dlt_time - Check current delete timer
        """
    else:
        help_text = """
<b>📊 Admin Commands:</b>
• /users - Check total users
• /log - Get bot logs
• /ban [user_id] - Ban user(s)
• /unban [user_id] or /unban all - Unban user(s)
• /banlist - View banned users
• /pause - Pause anime fetching
• /resume - Resume anime fetching
• /addlink [rss_url] - Add RSS feed
• /addtask [rss_url] [index] - Add specific task
• /rtask [rss_url] [index] - Retry specific task
• /reboot - Clear anime cache
• /dlt_time [seconds] - Set auto-delete timer
• /check_dlt_time - Check current delete timer
        """
    
    await sendMessage(message, help_text)

import psutil
import shutil
import platform
import subprocess
from datetime import datetime, timedelta
from pyrogram import filters

BOOT_TIME = datetime.fromtimestamp(psutil.boot_time())

def format_bytes(size):
    # Convert bytes to human-readable format
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

@bot.on_message(filters.command("stats") & filters.user(Var.OWNER_ID))
async def stats_handler(client, message):
    # Disk usage
    disk = shutil.disk_usage("/")
    disk_total = format_bytes(disk.total)
    disk_used = format_bytes(disk.used)
    disk_free = format_bytes(disk.free)
    disk_percent = (disk.used / disk.total) * 100

    # Memory
    mem = psutil.virtual_memory()
    mem_total = format_bytes(mem.total)
    mem_used = format_bytes(mem.used)
    mem_free = format_bytes(mem.available)
    mem_percent = mem.percent
    swap = format_bytes(psutil.swap_memory().used)

    # CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_load = ", ".join(f"{x:.2f}" for x in psutil.getloadavg())
    cpu_cores = psutil.cpu_count(logical=False)

    # Network
    net = psutil.net_io_counters()
    net_total = format_bytes(net.bytes_sent + net.bytes_recv)

    # System info
    os_name = platform.system()
    kernel = platform.release()
    python_ver = platform.python_version()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    uptime = datetime.now() - BOOT_TIME
    uptime_str = f"{uptime.days*24 + uptime.seconds//3600}h {uptime.seconds//60%60}m"

    # Software Versions
    ffmpeg_version = subprocess.getoutput("ffmpeg -version").split('\n')[0].split()[2] or "Unknown"
    pyrogram_version = subprocess.getoutput("pip show pyrogram | grep Version").split()[-1] or "Unknown"

    text = f"""
<pre>
=================================================
                SYSTEM DASHBOARD               
=================================================
[DISK]
| Total      : {disk_total}
| Used       : {disk_used}  ({disk_percent:.1f}%)
| Free       : {disk_free}

[MEMORY]
| RAM Total  : {mem_total}
| RAM Used   : {mem_used}  ({mem_percent:.1f}%)
| RAM Free   : {mem_free}
| Swap Used  : {swap}

[CPU]
| Cores      : {cpu_cores}
| Usage      : {cpu_usage}%
| Load Avg   : {cpu_load}

[NETWORK]
| Data Total : {net_total}

[SYSTEM]
| OS         : {os_name}
| Kernel     : {kernel}
| Python     : {python_ver}
| Time       : {now}
| Uptime     : {uptime_str}

[SOFT VERSIONS]
| ffmpeg     : {ffmpeg_version}
| Pyrogram   : {pyrogram_version}
=================================================
</pre>
"""
    await message.reply(text)
