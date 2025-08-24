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
