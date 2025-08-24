import asyncio
from pyrogram.filters import command, private, user
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import bot, Var
from bot.core.database import db
from bot.core.func_utils import sendMessage, new_task

@bot.on_message(command('dbroadcast') & private & user(Var.OWNER_ID))
@new_task
async def delete_broadcast(client, message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])  # Get the duration in seconds
        except (IndexError, ValueError):
            await message.reply("<b>Pʟᴇᴀsᴇ ᴜsᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> Usᴀɢᴇ: /dbroadcast {duration}")
            return

        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast with auto-delete processing....</i>")
        for chat_id in query:
            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)  # Wait for the specified duration
                await sent_msg.delete()  # Delete the message after the duration
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴡɪᴛʜ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ Cᴏᴍᴘʟᴇᴛᴇᴅ</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("<b>Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ ᴡɪᴛʜ Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ.</b>")
        await asyncio.sleep(8)
        await msg.delete()

@bot.on_message(command('pbroadcast') & private & user(Var.OWNER_ID))
@new_task
async def send_pin_text(client, message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                # Send and pin the message
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Failed to send or pin message to {chat_id}: {e}")
                unsuccessful += 1
            total += 1

        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("<b>Reply to a message to broadcast and pin it.</b>")
        await asyncio.sleep(8)
        await msg.delete()

@bot.on_message(command('broadcast') & private & user(Var.OWNER_ID))
@new_task
async def send_text(client, message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply(Var.REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
