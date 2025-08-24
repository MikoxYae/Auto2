from pyrogram.filters import command, private
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatAction

from bot import bot, Var, admin
from bot.core.database import db
from bot.core.func_utils import new_task, sendMessage, editMessage

@bot.on_message(command('ban') & private & admin)
@new_task
async def add_banuser(client, message):        
    pro = await message.reply("⏳ <i>Pʀᴏᴄᴇssɪɴɢ ʀᴇǫᴜᴇsᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()
    banusers = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not banusers:
        return await editMessage(pro,
            "<b>❗ Yᴏᴜ ᴍᴜsᴛ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ IDs ᴛᴏ ʙᴀɴ.</b>\n\n"
            "<b>📌 Usᴀɢᴇ:</b>\n"
            "<code>/ban [user_id]</code> — Ban one or more users by ID\n\n"
            "<b>Example:</b>\n"
            "<code>/ban 1234567890 9876543210</code>",
            reply_markup
        )

    report, success_count = "", 0
    admin_ids = await db.get_all_admins()
    
    for uid in banusers:
        try:
            uid_int = int(uid)
        except:
            report += f"⚠️ Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code>\n"
            continue

        # Prevent banning admins and owner
        if uid_int in admin_ids or uid_int == Var.OWNER_ID:
            report += f"⛔ Sᴋɪᴘᴘᴇᴅ ᴀᴅᴍɪɴ/ᴏᴡɴᴇʀ ID: <code>{uid_int}</code>\n"
            continue

        if uid_int in banuser_ids:
            report += f"⚠️ Aʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ: <code>{uid_int}</code>\n"
            continue

        # Validate Telegram ID length (typically 9-10 digits)
        if len(str(uid_int)) >= 9:
            await db.add_ban_user(uid_int)
            report += f"✅ Bᴀɴɴᴇᴅ: <code>{uid_int}</code>\n"
            success_count += 1
        else:
            report += f"⚠️ Invalid Telegram ID length: <code>{uid_int}</code>\n"

    if success_count:
        await editMessage(pro, f"<b>✅ Bᴀɴɴᴇᴅ Usᴇʀs Uᴘᴅᴀᴛᴇᴅ:</b>\n\n{report}", reply_markup)
    else:
        await editMessage(pro, f"<b>❌ Nᴏ ᴜsᴇʀs ᴡᴇʀᴇ ʙᴀɴɴᴇᴅ.</b>\n\n{report}", reply_markup)

@bot.on_message(command('unban') & private & admin)
@new_task
async def delete_banuser(client, message):        
    pro = await message.reply("⏳ <i>Pʀᴏᴄᴇssɪɴɢ ʀᴇǫᴜᴇsᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()
    banusers = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]])

    if not banusers:
        return await editMessage(pro,
            "<b>❗ Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ IDs ᴛᴏ ᴜɴʙᴀɴ.</b>\n\n"
            "<b>📌 Usage:</b>\n"
            "<code>/unban [user_id]</code> — Unban specific user(s)\n"
            "<code>/unban all</code> — Remove all banned users",
            reply_markup
        )

    if len(banusers) == 1 and banusers[0].lower() == "all":
        if not banuser_ids:
            return await editMessage(pro, "<b>✅ Nᴏ ᴜsᴇʀs ɪɴ ᴛʜᴇ ʙᴀɴ ʟɪsᴛ.</b>", reply_markup)
        
        for uid in banuser_ids:
            await db.del_ban_user(uid)
        listed = "\n".join([f"✅ Uɴʙᴀɴɴᴇᴅ: <code>{uid}</code>" for uid in banuser_ids])
        return await editMessage(pro, f"<b>🚫 Cʟᴇᴀʀᴇᴅ Bᴀɴ Lɪsᴛ:</b>\n\n{listed}", reply_markup)

    report = ""
    for uid in banusers:
        try:
            uid_int = int(uid)
        except:
            report += f"⚠️ Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code>\n"
            continue

        if uid_int in banuser_ids:
            await db.del_ban_user(uid_int)
            report += f"✅ Uɴʙᴀɴɴᴇᴅ: <code>{uid_int}</code>\n"
        else:
            report += f"⚠️ Nᴏᴛ ɪɴ ʙᴀɴ ʟɪsᴛ: <code>{uid_int}</code>\n"

    await editMessage(pro, f"<b>🚫 Uɴʙᴀɴ Rᴇᴘᴏʀᴛ:</b>\n\n{report}", reply_markup)

@bot.on_message(command('banlist') & private & admin)
@new_task
async def get_banuser_list(client, message):        
    pro = await message.reply("⏳ <i>Fᴇᴛᴄʜɪɴɢ Bᴀɴ Lɪsᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()

    if not banuser_ids:
        return await editMessage(pro, "<b>✅ Nᴏ ᴜsᴇʀs ɪɴ ᴛʜᴇ ʙᴀɴ ʟɪsᴛ.</b>", 
                               InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]]))

    result = "<b>🚫 Bᴀɴɴᴇᴅ Usᴇʀs:</b>\n\n"
    for uid in banuser_ids:
        await message.reply_chat_action(ChatAction.TYPING)
        try:
            user = await client.get_users(uid)
            user_link = f'<a href="tg://user?id={uid}">{user.first_name}</a>'
            result += f"• {user_link} — <code>{uid}</code>\n"
        except:
            result += f"• <code>{uid}</code> — <i>Could not fetch name</i>\n"

    await editMessage(pro, result, 
                     InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close")]]))
