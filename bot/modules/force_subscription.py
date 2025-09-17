from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, admin
from bot.core.database import db
from bot.core.func_utils import sendMessage, new_task

@bot.on_message(filters.command('fsubstats') & filters.private & admin)
@new_task
async def force_sub_stats(client, message):
    """Get force subscription statistics"""
    temp = await message.reply("📊 <b>ɢᴀᴛʜᴇʀɪɴɢ sᴛᴀᴛɪsᴛɪᴄs...</b>", quote=True)
    
    try:
        channels = await db.show_channels()
        total_channels = len(channels)
        
        if total_channels == 0:
            return await temp.edit("📊 <b>ɴᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ.</b>")
        
        normal_mode = 0
        request_mode = 0
        channel_info = []
        
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                
                if mode == "on":
                    request_mode += 1
                    mode_text = "🟢 ʀᴇǫᴜᴇsᴛ"
                else:
                    normal_mode += 1
                    mode_text = "🔴 ɴᴏʀᴍᴀʟ"
                
                # Get member count
                try:
                    member_count = await client.get_chat_members_count(ch_id)
                except:
                    member_count = "ᴜɴᴋɴᴏᴡɴ"
                
                channel_info.append(f"• <b>{chat.title}</b>\n  ├ ᴍᴏᴅᴇ: {mode_text}\n  └ ᴍᴇᴍʙᴇʀs: {member_count}")
                
            except Exception as e:
                channel_info.append(f"• <code>{ch_id}</code> - <i>ᴇʀʀᴏʀ: {str(e)[:30]}...</i>")
        
        stats_text = f"""📊 <b>ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ sᴛᴀᴛɪsᴛɪᴄs</b>

📈 <b>ᴏᴠᴇʀᴠɪᴇᴡ:</b>
├ <b>ᴛᴏᴛᴀʟ ᴄʜᴀɴɴᴇʟs:</b> {total_channels}
├ <b>ɴᴏʀᴍᴀʟ ᴍᴏᴅᴇ:</b> {normal_mode}
└ <b>ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ:</b> {request_mode}

📋 <b>ᴄʜᴀɴɴᴇʟ ᴅᴇᴛᴀɪʟs:</b>
{chr(10).join(channel_info)}"""

        await temp.edit(
            stats_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await temp.edit(f"❌ <b>ᴇʀʀᴏʀ ɢᴇᴛᴛɪɴɢ sᴛᴀᴛɪsᴛɪᴄs:</b>\n<code>{str(e)}</code>")

@bot.on_message(filters.command('clearlogs') & filters.private & admin)
@new_task
async def clear_join_request_logs(client, message):
    """Clear all join request logs"""
    temp = await message.reply("🧹 <b>ᴄʟᴇᴀʀɪɴɢ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ʟᴏɢs...</b>", quote=True)
    
    try:
        # Clear all join request logs
        if hasattr(db.db, 'join_requests'):
            result = await db.db.join_requests.delete_many({})
            deleted_count = result.deleted_count
        else:
            deleted_count = 0
        
        await temp.edit(f"✅ <b>ᴄʟᴇᴀʀᴇᴅ {deleted_count} ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ʟᴏɢs.</b>")
        
    except Exception as e:
        await temp.edit(f"❌ <b>ᴇʀʀᴏʀ ᴄʟᴇᴀʀɪɴɢ ʟᴏɢs:</b>\n<code>{str(e)}</code>")

@bot.on_message(filters.command('fsub_help') & filters.private & admin)
@new_task
async def force_sub_help(client, message):
    """Show force subscription help"""
    help_text = """
🔰 <b>ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʜᴇʟᴘ</b>

📋 <b>ᴄʜᴀɴɴᴇʟ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ:</b>
• <code>/addchnl [channel_id]</code> - ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ
• <code>/delchnl [channel_id/all]</code> - ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ
• <code>/listchnl</code> - ʟɪsᴛ ᴀʟʟ ᴄʜᴀɴɴᴇʟs

⚙️ <b>ᴍᴏᴅᴇ ᴄᴏɴᴛʀᴏʟ:</b>
• <code>/fsub_mode</code> - ᴛᴏɢɢʟᴇ ᴄʜᴀɴɴᴇʟ ᴍᴏᴅᴇs

📊 <b>sᴛᴀᴛɪsᴛɪᴄs:</b>
• <code>/fsubstats</code> - ᴠɪᴇᴡ ᴅᴇᴛᴀɪʟᴇᴅ sᴛᴀᴛs
• <code>/clearlogs</code> - ᴄʟᴇᴀʀ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ʟᴏɢs

🔍 <b>ᴍᴏᴅᴇs ᴇxᴘʟᴀɪɴᴇᴅ:</b>
🔴 <b>ɴᴏʀᴍᴀʟ ᴍᴏᴅᴇ:</b> ᴜsᴇʀs ᴊᴏɪɴ ᴅɪʀᴇᴄᴛʟʏ
🟢 <b>ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ:</b> ᴜsᴇʀs sᴇɴᴅ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛs (ᴍᴀɴᴜᴀʟ ᴀᴘᴘʀᴏᴠᴀʟ)

💡 <b>ᴛɪᴘs:</b>
• ᴍᴀᴋᴇ sᴜʀᴇ ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs
• ᴜsᴇ ʀᴇǫᴜᴇsᴛ ᴍᴏᴅᴇ ғᴏʀ ᴘʀɪᴠᴀᴛᴇ/ᴘʀᴇᴍɪᴜᴍ ᴄʜᴀɴɴᴇʟs
• ʀᴇɢᴜʟᴀʀʟʏ ᴄʜᴇᴄᴋ sᴛᴀᴛɪsᴛɪᴄs ᴛᴏ ᴍᴏɴɪᴛᴏʀ ᴘᴇʀғᴏʀᴍᴀɴᴄᴇ
"""
    
    await message.reply(
        help_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    )
