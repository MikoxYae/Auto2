from pyrogram.filters import command, private, reply
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, admin
from bot.core.database import db
from bot.core.func_utils import sendMessage, new_task

@bot.on_message(command('setbanner') & private & admin & reply)
@new_task
async def set_custom_banner(client, message):
    """Set custom banner for anime"""
    # Get anime name from command
    text = message.text.strip()
    anime_name = text.replace('/setbanner', '').strip()
    
    if not anime_name:
        return await sendMessage(message, 
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/setbanner [anime_name]</code>\n"
            "<i>(Reply to a photo)</i>\n\n"
            "<b>Example:</b>\n"
            "<code>/setbanner Rascal Does Not Dream of Bunny Girl Senpai</code>"
        )
    
    # Check if replying to photo
    replied_msg = message.reply_to_message
    if not replied_msg or not replied_msg.photo:
        return await sendMessage(message,
            "<b>❌ Please reply to a photo!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/setbanner [anime_name]</code>\n"
            "<i>(Reply to a photo)</i>"
        )
    
    try:
        # Get photo file_id
        photo_file_id = replied_msg.photo.file_id
        
        # Save to database
        await db.add_custom_banner(anime_name, photo_file_id)
        
        # Send confirmation with preview
        await sendMessage(message,
            f"✅ <b>Custom Banner Set Successfully!</b>\n\n"
            f"📺 <b>Anime:</b> {anime_name}\n"
            f"🖼️ <b>Banner ID:</b> <code>{photo_file_id}</code>\n\n"
            f"ℹ️ <b>This banner will be used for all future posts of this anime!</b>"
        )
        
        # Send preview of the banner
        await client.send_photo(
            message.chat.id,
            photo=photo_file_id,
            caption=f"🖼️ <b>Banner Preview for:</b>\n<code>{anime_name}</code>"
        )
        
    except Exception as e:
        await sendMessage(message,
            f"❌ <b>Error setting banner:</b>\n"
            f"<code>{str(e)}</code>"
        )

@bot.on_message(command('removebanner') & private & admin)
@new_task
async def remove_custom_banner(client, message):
    """Remove custom banner for anime"""
    # Get anime name from command
    text = message.text.strip()
    anime_name = text.replace('/removebanner', '').strip()
    
    if not anime_name:
        return await sendMessage(message,
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/removebanner [anime_name]</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/removebanner Rascal Does Not Dream of Bunny Girl Senpai</code>"
        )
    
    try:
        # Remove from database
        success = await db.remove_custom_banner(anime_name)
        
        if success:
            await sendMessage(message,
                f"✅ <b>Custom Banner Removed!</b>\n\n"
                f"📺 <b>Anime:</b> {anime_name}\n\n"
                f"ℹ️ <b>Future posts will use AniList default banner.</b>"
            )
        else:
            await sendMessage(message,
                f"❌ <b>No custom banner found for:</b>\n"
                f"<code>{anime_name}</code>\n\n"
                f"<b>Use:</b> <code>/listbanners</code> to see all custom banners."
            )
            
    except Exception as e:
        await sendMessage(message,
            f"❌ <b>Error removing banner:</b>\n"
            f"<code>{str(e)}</code>"
        )

@bot.on_message(command('listbanners') & private & admin)
@new_task
async def list_custom_banners(client, message):
    """List all custom banners"""
    try:
        banners = await db.get_all_custom_banners()
        
        if not banners:
            return await sendMessage(message,
                "<b>📋 No custom banners set yet.</b>\n\n"
                "<b>Use:</b> <code>/setbanner [anime_name]</code> to add custom banners."
            )
        
        result = "<b>🎨 Custom Anime Banners:</b>\n\n"
        for banner in banners:
            result += f"🎬 <b>{banner['anime_name']}</b>\n"
            result += f"├ <b>Banner ID:</b> <code>{banner['banner_file_id']}</code>\n"
            result += f"└ <b>Added:</b> {banner.get('date_added', 'Unknown')}\n\n"
        
        await sendMessage(message, result)
        
    except Exception as e:
        await sendMessage(message,
            f"❌ <b>Error fetching banners:</b>\n"
            f"<code>{str(e)}</code>"
        )

@bot.on_message(command('viewbanner') & private & admin)
@new_task
async def view_custom_banner(client, message):
    """View specific anime banner"""
    # Get anime name from command
    text = message.text.strip()
    anime_name = text.replace('/viewbanner', '').strip()
    
    if not anime_name:
        return await sendMessage(message,
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/viewbanner [anime_name]</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/viewbanner Rascal Does Not Dream of Bunny Girl Senpai</code>"
        )
    
    try:
        # Get banner from database
        banner_file_id = await db.get_custom_banner(anime_name)
        
        if banner_file_id:
            # Send the banner
            await client.send_photo(
                message.chat.id,
                photo=banner_file_id,
                caption=f"🎨 <b>Custom Banner for:</b>\n<code>{anime_name}</code>\n\n"
                       f"🆔 <b>File ID:</b> <code>{banner_file_id}</code>"
            )
        else:
            await sendMessage(message,
                f"❌ <b>No custom banner found for:</b>\n"
                f"<code>{anime_name}</code>\n\n"
                f"<b>Available Commands:</b>\n"
                f"• <code>/setbanner {anime_name}</code> - Set banner\n"
                f"• <code>/listbanners</code> - View all banners"
            )
            
    except Exception as e:
        await sendMessage(message,
            f"❌ <b>Error viewing banner:</b>\n"
            f"<code>{str(e)}</code>"
        )

@bot.on_message(command('updatebanner') & private & admin & reply)
@new_task
async def update_custom_banner(client, message):
    """Update existing custom banner"""
    # Get anime name from command
    text = message.text.strip()
    anime_name = text.replace('/updatebanner', '').strip()
    
    if not anime_name:
        return await sendMessage(message,
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/updatebanner [anime_name]</code>\n"
            "<i>(Reply to a photo)</i>\n\n"
            "<b>Example:</b>\n"
            "<code>/updatebanner Rascal Does Not Dream of Bunny Girl Senpai</code>"
        )
    
    # Check if replying to photo
    replied_msg = message.reply_to_message
    if not replied_msg or not replied_msg.photo:
        return await sendMessage(message,
            "<b>❌ Please reply to a photo!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/updatebanner [anime_name]</code>\n"
            "<i>(Reply to a photo)</i>"
        )
    
    try:
        # Check if banner exists
        existing_banner = await db.get_custom_banner(anime_name)
        if not existing_banner:
            return await sendMessage(message,
                f"❌ <b>No existing banner found for:</b>\n"
                f"<code>{anime_name}</code>\n\n"
                f"<b>Use:</b> <code>/setbanner {anime_name}</code> to create new banner."
            )
        
        # Get new photo file_id
        new_photo_file_id = replied_msg.photo.file_id
        
        # Update in database
        await db.add_custom_banner(anime_name, new_photo_file_id)  # This overwrites existing
        
        # Send confirmation
        await sendMessage(message,
            f"✅ <b>Banner Updated Successfully!</b>\n\n"
            f"📺 <b>Anime:</b> {anime_name}\n"
            f"🔄 <b>Old Banner:</b> <code>{existing_banner}</code>\n"
            f"🆕 <b>New Banner:</b> <code>{new_photo_file_id}</code>\n\n"
            f"ℹ️ <b>Updated banner will be used for future posts!</b>"
        )
        
        # Send preview of new banner
        await client.send_photo(
            message.chat.id,
            photo=new_photo_file_id,
            caption=f"🔄 <b>Updated Banner Preview for:</b>\n<code>{anime_name}</code>"
        )
        
    except Exception as e:
        await sendMessage(message,
            f"❌ <b>Error updating banner:</b>\n"
            f"<code>{str(e)}</code>"
        )
