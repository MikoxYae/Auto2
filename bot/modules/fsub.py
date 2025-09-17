import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid

from bot import bot, Var, admin
from bot.core.database import db
from bot.core.func_utils import new_task, sendMessage, editMessage, get_fsubs

# Force Subscription Channel Management Commands

@bot.on_message(filters.command('addchnl') & filters.private & admin)
@new_task
async def add_force_sub_channel(client: Client, message: Message):
    """Add force subscription channel"""
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/addchnl -100xxxxxxxxxx</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/addchnl -1001234567890</code>"
        )

    try:
        chat_id = int(args[1])
    except ValueError:
        return await temp.edit("<b>❌ Invalid chat ID! Please use a valid channel ID.</b>")

    # Check if channel already exists
    all_channels = await db.show_channels()
    if chat_id in all_channels:
        return await temp.edit(f"<b>❌ Channel already exists in force-sub list:</b>\n<code>{chat_id}</code>")

    try:
        # Get chat info
        chat = await client.get_chat(chat_id)
        
        # Verify it's a channel or supergroup
        if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
            return await temp.edit("<b>❌ Only channels and supergroups are allowed!</b>")

        # Check if bot is admin
        bot_member = await client.get_chat_member(chat.id, "me")
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await temp.edit("<b>❌ Bot must be an admin in that channel!</b>")

        # Try to get/create invite link
        try:
            if chat.username:
                link = f"https://t.me/{chat.username}"
            else:
                invite = await client.create_chat_invite_link(chat.id)
                link = invite.invite_link
                await db.store_invite_link(chat_id, link)
        except Exception:
            link = f"https://t.me/c/{str(chat.id)[4:]}"

        # Add channel to database
        await db.add_channel(chat_id)
        
        return await temp.edit(
            f"<b>✅ Force-Sub Channel Added Successfully!</b>\n\n"
            f"<b>📺 Name:</b> <a href='{link}'>{chat.title}</a>\n"
            f"<b>🆔 ID:</b> <code>{chat_id}</code>\n"
            f"<b>🔧 Mode:</b> <code>OFF</code> (Default)\n\n"
            f"<i>💡 Use /fsub_mode to enable request mode</i>",
            disable_web_page_preview=True
        )

    except Exception as e:
        return await temp.edit(f"<b>❌ Failed to add channel:</b>\n<code>{chat_id}</code>\n\n<b>Error:</b> <i>{str(e)}</i>")

@bot.on_message(filters.command('delchnl') & filters.private & admin)
@new_task
async def delete_force_sub_channel(client: Client, message: Message):
    """Remove force subscription channel"""
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    args = message.text.split(maxsplit=1)
    all_channels = await db.show_channels()

    if len(args) != 2:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/delchnl [channel_id | all]</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/delchnl -1001234567890</code>\n"
            "<code>/delchnl all</code>"
        )

    # Handle "all" option
    if args[1].lower() == "all":
        if not all_channels:
            return await temp.edit("<b>❌ No force-sub channels found to remove.</b>")
        
        removed_count = 0
        for ch_id in all_channels:
            await db.rem_channel(ch_id)
            removed_count += 1
        
        return await temp.edit(f"<b>✅ All force-sub channels removed!</b>\n\n<b>📊 Removed:</b> <code>{removed_count}</code> channels")

    # Handle specific channel ID
    try:
        ch_id = int(args[1])
    except ValueError:
        return await temp.edit("<b>❌ Invalid Channel ID! Please use a valid number.</b>")

    if ch_id in all_channels:
        await db.rem_channel(ch_id)
        
        # Try to get channel name for confirmation
        try:
            chat = await client.get_chat(ch_id)
            channel_name = chat.title
        except:
            channel_name = f"Channel {ch_id}"
        
        return await temp.edit(
            f"<b>✅ Force-Sub Channel Removed!</b>\n\n"
            f"<b>📺 Channel:</b> <code>{channel_name}</code>\n"
            f"<b>🆔 ID:</b> <code>{ch_id}</code>"
        )
    else:
        return await temp.edit(
            f"<b>❌ Channel not found in force-sub list!</b>\n\n"
            f"<b>🆔 ID:</b> <code>{ch_id}</code>\n\n"
            f"<i>💡 Use /listchnl to see all channels</i>"
        )

@bot.on_message(filters.command('listchnl') & filters.private & admin)
@new_task
async def list_force_sub_channels(client: Client, message: Message):
    """List all force subscription channels"""
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    channels = await db.show_channels()

    if not channels:
        return await temp.edit(
            "<b>❌ No force-sub channels found.</b>\n\n"
            "<i>💡 Use /addchnl to add channels</i>"
        )

    result = "<b>📋 Force-Sub Channels List:</b>\n\n"
    
    for no, ch_id in enumerate(channels, start=1):
        try:
            chat = await client.get_chat(ch_id)
            mode = await db.get_channel_mode(ch_id)
            mode_emoji = "🟢" if mode == "on" else "🔴"
            mode_text = "ON" if mode == "on" else "OFF"
            
            # Get invite link
            link = await db.get_invite_link(ch_id)
            if not link:
                if chat.username:
                    link = f"https://t.me/{chat.username}"
                else:
                    link = f"https://t.me/c/{str(ch_id)[4:]}"
            
            result += f"<b>{no}. <a href='{link}'>{chat.title}</a></b>\n"
            result += f"   • <b>ID:</b> <code>{ch_id}</code>\n"
            result += f"   • <b>Mode:</b> {mode_emoji} <code>{mode_text}</code>\n"
            result += f"   • <b>Members:</b> <code>{chat.members_count or 'N/A'}</code>\n\n"
            
        except Exception as e:
            result += f"<b>{no}. ⚠️ Unavailable Channel</b>\n"
            result += f"   • <b>ID:</b> <code>{ch_id}</code>\n"
            result += f"   • <b>Error:</b> <i>{str(e)}</i>\n\n"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_channel_list")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

    await temp.edit(result, disable_web_page_preview=True, reply_markup=reply_markup)

@bot.on_message(filters.command('fsub_mode') & filters.private & admin)
@new_task
async def toggle_force_sub_mode(client: Client, message: Message):
    """Toggle force subscription mode for channels"""
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>", quote=True)
    channels = await db.show_channels()

    if not channels:
        return await temp.edit(
            "<b>❌ No force-sub channels found.</b>\n\n"
            "<i>💡 Use /addchnl to add channels first</i>"
        )

    # Create buttons for each channel
    buttons = []
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            mode = await db.get_channel_mode(ch_id)
            status_emoji = "🟢" if mode == "on" else "🔴"
            mode_text = "REQUEST" if mode == "on" else "NORMAL"
            title = f"{status_emoji} {chat.title} ({mode_text})"
            buttons.append([InlineKeyboardButton(title, callback_data=f"fsub_toggle_{ch_id}")])
        except:
            buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"fsub_toggle_{ch_id}")])

    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    await temp.edit(
        "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>\n\n"
        "<b>🟢 = REQUEST MODE:</b> <i>Users send join requests</i>\n"
        "<b>🔴 = NORMAL MODE:</b> <i>Users must join directly</i>",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

# Callback Query Handlers

@bot.on_callback_query(filters.regex("fsub_toggle_"))
async def handle_fsub_toggle(client: Client, callback_query: CallbackQuery):
    """Handle force-sub mode toggle"""
    try:
        ch_id = int(callback_query.data.split("_")[2])
        
        # Get current mode and toggle it
        current_mode = await db.get_channel_mode(ch_id)
        new_mode = "off" if current_mode == "on" else "on"
        
        # Update mode in database
        await db.set_channel_mode(ch_id, new_mode)
        
        try:
            chat = await client.get_chat(ch_id)
            chat_name = chat.title
        except:
            chat_name = f"Channel {ch_id}"
        
        mode_text = "REQUEST MODE (🟢)" if new_mode == "on" else "NORMAL MODE (🔴)"
        
        # Create back button
        buttons = [
            [InlineKeyboardButton("⚙️ Toggle Again", callback_data=f"fsub_toggle_{ch_id}")],
            [InlineKeyboardButton("‹ Back to List", callback_data="fsub_back")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
        
        await callback_query.message.edit_text(
            f"<b>✅ Force-Sub Mode Updated!</b>\n\n"
            f"<b>📺 Channel:</b> <code>{chat_name}</code>\n"
            f"<b>🆔 ID:</b> <code>{ch_id}</code>\n"
            f"<b>🔧 New Mode:</b> <code>{mode_text}</code>\n\n"
            f"<b>ℹ️ Mode Info:</b>\n"
            f"{'• <i>Users can send join requests and get immediate access</i>' if new_mode == 'on' else '• <i>Users must join the channel directly</i>'}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        await callback_query.answer(f"✅ Mode set to {'REQUEST' if new_mode == 'on' else 'NORMAL'}!")
        
    except Exception as e:
        await callback_query.answer("❌ Error toggling mode!", show_alert=True)

@bot.on_callback_query(filters.regex("fsub_back"))
async def handle_fsub_back(client: Client, callback_query: CallbackQuery):
    """Handle back to channel list"""
    try:
        channels = await db.show_channels()
        
        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status_emoji = "🟢" if mode == "on" else "🔴"
                mode_text = "REQUEST" if mode == "on" else "NORMAL"
                title = f"{status_emoji} {chat.title} ({mode_text})"
                buttons.append([InlineKeyboardButton(title, callback_data=f"fsub_toggle_{ch_id}")])
            except:
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"fsub_toggle_{ch_id}")])

        buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])

        await callback_query.message.edit_text(
            "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>\n\n"
            "<b>🟢 = REQUEST MODE:</b> <i>Users send join requests</i>\n"
            "<b>🔴 = NORMAL MODE:</b> <i>Users must join directly</i>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        await callback_query.answer("❌ Error loading channels!", show_alert=True)

@bot.on_callback_query(filters.regex("refresh_fsub"))
async def refresh_fsub_callback(client: Client, callback_query: CallbackQuery):
    """Handle refresh button for force subscription status"""
    user_id = callback_query.from_user.id
    
    try:
        # Get original start parameters if available
        txtargs = ["start"]  # Default
        
        # Generate updated force subscription message
        txt, btns = await get_fsubs(user_id, txtargs)
        
        await editMessage(
            callback_query.message,
            txt,
            InlineKeyboardMarkup(btns)
        )
        
        await callback_query.answer("✅ Status refreshed!")
        
    except Exception as e:
        await callback_query.answer("❌ Error refreshing status!", show_alert=True)

@bot.on_callback_query(filters.regex("refresh_channel_list"))
async def refresh_channel_list_callback(client: Client, callback_query: CallbackQuery):
    """Handle refresh button for channel list"""
    try:
        channels = await db.show_channels()

        if not channels:
            return await callback_query.message.edit_text(
                "<b>❌ No force-sub channels found.</b>\n\n"
                "<i>💡 Use /addchnl to add channels</i>"
            )

        result = "<b>📋 Force-Sub Channels List:</b>\n\n"
        
        for no, ch_id in enumerate(channels, start=1):
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                mode_emoji = "🟢" if mode == "on" else "🔴"
                mode_text = "ON" if mode == "on" else "OFF"
                
                # Get invite link
                link = await db.get_invite_link(ch_id)
                if not link:
                    if chat.username:
                        link = f"https://t.me/{chat.username}"
                    else:
                        link = f"https://t.me/c/{str(ch_id)[4:]}"
                
                result += f"<b>{no}. <a href='{link}'>{chat.title}</a></b>\n"
                result += f"   • <b>ID:</b> <code>{ch_id}</code>\n"
                result += f"   • <b>Mode:</b> {mode_emoji} <code>{mode_text}</code>\n"
                result += f"   • <b>Members:</b> <code>{chat.members_count or 'N/A'}</code>\n\n"
                
            except Exception as e:
                result += f"<b>{no}. ⚠️ Unavailable Channel</b>\n"
                result += f"   • <b>ID:</b> <code>{ch_id}</code>\n"
                result += f"   • <b>Error:</b> <i>{str(e)}</i>\n\n"

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_channel_list")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])

        await callback_query.message.edit_text(result, disable_web_page_preview=True, reply_markup=reply_markup)
        await callback_query.answer("✅ Channel list refreshed!")
        
    except Exception as e:
        await callback_query.answer("❌ Error refreshing list!", show_alert=True)

@bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Client, callback_query: CallbackQuery):
    """Handle close button"""
    try:
        await callback_query.message.delete()
    except:
        await callback_query.message.edit_text("<b>❌ Message closed!</b>")
