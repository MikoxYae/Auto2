from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from json import loads as jloads
from re import findall
from math import floor
from os import path as ospath
from time import time, sleep
from traceback import format_exc
from asyncio import sleep as asleep, create_subprocess_shell
from asyncio.subprocess import PIPE
from base64 import urlsafe_b64encode, urlsafe_b64decode

from aiohttp import ClientSession
from aiofiles import open as aiopen
from aioshutil import rmtree as aiormtree
from html_telegraph_poster import TelegraphPoster
from feedparser import parse as feedparse
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton
from pyrogram.errors import MessageNotModified, FloodWait, UserNotParticipant, ReplyMarkupInvalid, MessageIdInvalid

from bot import bot, bot_loop, LOGS, Var
from .reporter import rep

def handle_logs(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            await rep.report(format_exc(), "error")
    return wrapper
    
async def sync_to_async(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    future = bot_loop.run_in_executor(ThreadPoolExecutor(max_workers=cpu_count() * 125), pfunc)
    return await future if wait else future
    
def new_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return bot_loop.create_task(func(*args, **kwargs))
    return wrapper

async def getfeed(link, index=0):
    try:
        feed = await sync_to_async(feedparse, link)
        return feed.entries[index]
    except IndexError:
        return None
    except Exception as e:
        LOGS.error(format_exc())
        return None

@handle_logs
async def aio_urldownload(link):
    async with ClientSession() as sess:
        async with sess.get(link) as data:
            image = await data.read()
    path = f"thumbs/{link.split('/')[-1]}"
    if not path.endswith((".jpg" or ".png")):
        path += ".jpg"
    async with aiopen(path, "wb") as f:
        await f.write(image)
    return path

@handle_logs
async def get_telegraph(out):
    client = TelegraphPoster(use_api=True)
    client.create_api_token("Mediainfo")
    uname = Var.BRAND_UNAME.lstrip('@')
    page = client.post(
        title="Mediainfo",
        author=uname,
        author_url=f"https://t.me/{uname}",
        text=f"""<pre>
{out}
</pre>
""",
        )
    return page.get("url")
    
async def sendMessage(chat, text, buttons=None, get_error=False, **kwargs):
    try:
        if isinstance(chat, int):
            return await bot.send_message(chat_id=chat, text=text, disable_web_page_preview=True,
                                        disable_notification=False, reply_markup=buttons, **kwargs)
        else:
            return await chat.reply(text=text, quote=True, disable_web_page_preview=True, disable_notification=False,
                                    reply_markup=buttons, **kwargs)
    except FloodWait as f:
        await rep.report(f, "warning")
        sleep(f.value * 1.2)
        return await sendMessage(chat, text, buttons, get_error, **kwargs)
    except ReplyMarkupInvalid:
        return await sendMessage(chat, text, None, get_error, **kwargs)
    except Exception as e:
        await rep.report(format_exc(), "error")
        if get_error:
            raise e
        return str(e)
        
async def editMessage(msg, text, buttons=None, get_error=False, **kwargs):
    try:
        if not msg:
            return None
        # Remove reply_markup from kwargs if it exists to avoid conflict
        kwargs.pop('reply_markup', None)
        return await msg.edit_text(text=text, disable_web_page_preview=True, 
                                        reply_markup=buttons, **kwargs)
    except FloodWait as f:
        await rep.report(f, "warning")
        sleep(f.value * 1.2)
        return await editMessage(msg, text, buttons, get_error, **kwargs)
    except ReplyMarkupInvalid:
        return await editMessage(msg, text, None, get_error, **kwargs)
    except (MessageNotModified, MessageIdInvalid):
        pass
    except Exception as e:
        await rep.report(format_exc(), "error")
        if get_error:
            raise e
        return str(e)

async def encode(string):
    return (urlsafe_b64encode(string.encode("ascii")).decode("ascii")).strip("=")

async def decode(b64_str):
    return urlsafe_b64decode((b64_str.strip("=") + "=" * (-len(b64_str.strip("=")) % 4)).encode("ascii")).decode("ascii")

# ENHANCED FORCE SUBSCRIPTION FUNCTIONS
async def is_subscribed(client, user_id):
    """Enhanced force subscription checker with request mode support"""
    from bot.core.database import db
    
    # Get all force subscription channels
    channel_ids = await db.show_channels()
    
    if not channel_ids:
        return True
    
    # Owner always has access
    if user_id == Var.OWNER_ID:
        return True
    
    # Check each channel
    for channel_id in channel_ids:
        if not await is_sub(client, user_id, channel_id):
            return False
    
    return True

async def is_sub(client, user_id, channel_id):
    """Check if user is subscribed to channel (with request mode support)"""
    from bot.core.database import db
    
    try:
        # First check if user is actually a member
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        
        # If user is member/admin/owner, they have access
        if status in {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER}:
            return True
        
        # If not a member, check if it's restricted/kicked
        if status in {ChatMemberStatus.RESTRICTED, ChatMemberStatus.BANNED}:
            return False
            
    except UserNotParticipant:
        # User is not a member, check if channel is in request mode
        mode = await db.get_channel_mode(channel_id)
        
        if mode == "on":  # Request mode is enabled
            # Check if user has sent a join request
            has_requested = await db.req_user_exist(channel_id, user_id)
            await rep.report(f"🔍 Request check - User {user_id}, Channel {channel_id}, Has requested: {has_requested}", "info")
            return has_requested
        
        # Normal mode and not a member = no access
        return False
    
    except Exception as e:
        await rep.report(f"Error in is_sub for user {user_id}, channel {channel_id}: {str(e)}", "error")
        return False
    
    # Default fallback
    return False

async def get_fsubs(uid, txtargs):
    """Generate force subscription message and buttons"""
    from bot.core.database import db
    
    txt = "<b><i>🔒 You must join our channels to access files!</i></b>\n\n"
    btns = []
    
    channel_ids = await db.show_channels()
    
    for no, chat_id in enumerate(channel_ids, start=1):
        try:
            chat = await bot.get_chat(chat_id)
            mode = await db.get_channel_mode(chat_id)
            
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
                sta = "✅ Joined"
            except UserNotParticipant:
                if mode == "on":
                    # Check if user has requested
                    has_requested = await db.req_user_exist(chat_id, uid)
                    sta = "⏳ Request Sent" if has_requested else "❌ Not Requested"
                else:
                    sta = "❌ Not Joined"
                
                # Get or create invite link
                link = await db.get_invite_link(chat_id)
                if not link:
                    try:
                        if mode == "on" and not chat.username:
                            # Create join request link for private channels in request mode
                            invite = await bot.create_chat_invite_link(
                                chat_id=chat_id,
                                creates_join_request=True
                            )
                            link = invite.invite_link
                            await db.store_invite_link(chat_id, link)
                        else:
                            # Use username or regular invite link
                            if chat.username:
                                link = f"https://t.me/{chat.username}"
                            else:
                                invite = await bot.create_chat_invite_link(chat_id)
                                link = invite.invite_link
                                await db.store_invite_link(chat_id, link)
                    except Exception as e:
                        await rep.report(f"Error creating invite link for {chat_id}: {str(e)}", "error")
                        link = f"https://t.me/c/{str(chat_id)[4:]}"
                
                # Add join button only if not already joined/requested
                if sta != "✅ Joined" and sta != "⏳ Request Sent":
                    button_text = "📝 Request to Join" if mode == "on" else "🔗 Join Channel"
                    btns.append([InlineKeyboardButton(f"{button_text} - {chat.title}", url=link)])
            
            except Exception as err:
                await rep.report(f"Error checking membership for {chat_id}: {str(err)}", "error")
                sta = "❌ Error"
            
            # Show channel status
            mode_text = "REQUEST MODE" if mode == "on" else "NORMAL MODE"
            txt += f"<b>{no}. {chat.title}</b>\n"
            txt += f"   • <b>Status:</b> <code>{sta}</code>\n"
            txt += f"   • <b>Mode:</b> <code>{mode_text}</code>\n\n"
        
        except Exception as err:
            await rep.report(f"Error processing channel {chat_id}: {str(err)}", "error")
            continue
    
    # Add refresh button
    btns.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_fsub")])
    
    # Add get files button if there are txtargs
    if len(txtargs) > 1:
        btns.append([InlineKeyboardButton('📁 Get Files', url=f'https://t.me/{(await bot.get_me()).username}?start={txtargs[1]}')])
    
    return txt, btns

# LEGACY SUPPORT (keeping old function names for compatibility)
async def is_fsubbed(uid):
    """Legacy function - redirects to new enhanced version"""
    return await is_subscribed(bot, uid)

async def mediainfo(file, get_json=False, get_duration=False):
    try:
        outformat = "HTML"
        if get_duration or get_json:
            outformat = "JSON"
        process = await create_subprocess_shell(f"mediainfo '''{file}''' --Output={outformat}", stdout=PIPE, stderr=PIPE)
        stdout, _ = await process.communicate()
        if get_duration:
            try:
                return float(jloads(stdout.decode())['media']['track'][0]['Duration'])
            except Exception:
                return 1440 # 24min
        return await get_telegraph(stdout.decode())
    except Exception as err:
        await rep.report(format_exc(), "error")
        return ""
        
async def clean_up():
    try:
        (await aiormtree(dirtree) for dirtree in ("downloads", "thumbs", "encode"))
    except Exception as e:
        LOGS.error(str(e))

def convertTime(s: int) -> str:
    m, s = divmod(int(s), 60)
    hr, m = divmod(m, 60)
    days, hr = divmod(hr, 24)
    convertedTime = (f"{int(days)}d, " if days else "") + \
          (f"{int(hr)}h, " if hr else "") + \
          (f"{int(m)}m, " if m else "") + \
          (f"{int(s)}s, " if s else "")
    return convertedTime[:-2]

def convertBytes(sz) -> str:
    if not sz: 
        return ""
    sz = int(sz)
    ind = 0
    Units = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T', 5: 'P'}
    while sz > 2**10:
        sz /= 2**10
        ind += 1
    return f"{round(sz, 2)} {Units[ind]}B"
