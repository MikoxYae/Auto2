from asyncio import gather, create_task, sleep as asleep, Event
from asyncio.subprocess import PIPE
from os import path as ospath, system
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove
from traceback import format_exc
from base64 import urlsafe_b64encode
from time import time
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, bot_loop, Var, ani_cache, ffQueue, ffLock, ff_queued
from .tordownload import TorDownloader
from .database import db
from .func_utils import getfeed, encode, editMessage, sendMessage, convertBytes
from .text_utils import TextEditor
from .ffencoder import FFEncoder
from .tguploader import TgUploader
from .reporter import rep

btn_formatter = {
    'Hdrip': '𝗛𝗗𝗥𝗶𝗽',
    '1080': '𝟭𝟬𝟴𝟬𝗽', 
    '720': '𝟳𝟮𝟬𝗽',
    '480': '𝟰𝟴𝟬𝗽'
 }

async def fetch_animes():
    await rep.report("Fetch Animes Started !!", "info")
    while True:
        await asleep(60)
        if ani_cache['fetch_animes']:
            for link in Var.RSS_ITEMS:
                if (info := await getfeed(link, 0)):
                    bot_loop.create_task(get_animes(info.title, info.link))

async def get_animes(name, torrent, force=False):
    try:
        aniInfo = TextEditor(name)
        await aniInfo.load_anilist()
        ani_id, ep_no = aniInfo.adata.get('id'), aniInfo.pdata.get("episode_number")
        if ani_id not in ani_cache['ongoing']:
            ani_cache['ongoing'].add(ani_id)
        elif not force:
            return
        if not force and ani_id in ani_cache['completed']:
            return
        if force or (not (ani_data := await db.getAnime(ani_id)) \
            or (ani_data and not (qual_data := ani_data.get(ep_no))) \
            or (ani_data and qual_data and not all(qual for qual in qual_data.values()))):
            
            if "[Batch]" in name:
                await rep.report(f"Torrent Skipped!\n\n{name}", "warning")
                return
            
            await rep.report(f"New Anime Torrent Found!\n\n{name}", "info")
            
            # Check if anime has dedicated channel
            channel_details = await db.find_channel_by_anime_title(name)
            
            if channel_details:
                # Get poster
                poster_url = await aniInfo.get_poster()
                
                # Post to dedicated channel
                if poster_url:
                    post_msg = await bot.send_photo(
                        channel_details['channel_id'],
                        photo=poster_url,
                        caption=await aniInfo.get_caption()
                    )
                else:
                    # Send as message if no poster available
                    post_msg = await bot.send_message(
                        channel_details['channel_id'],
                        text=await aniInfo.get_caption()
                    )
                
                # Send sticker to dedicated channel
                await bot.send_sticker(
                    channel_details['channel_id'],
                    sticker="CAACAgUAAxkBAAEOyQtoXB1SxAZqiP0wK7NbBBxxHwUG7gAC4BMAAp6PIFcLAAGEEdQGq4s2BA"
                )
                
                # Post summary to main channel with join button
                await post_main_channel_summary(name, aniInfo, channel_details)
                
                await asleep(1.5)
                stat_msg = await sendMessage(channel_details['channel_id'], f"<b>ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀɴɪᴍᴇ</b>")
            else:
                # Original behavior - post to main channel
                poster_url = await aniInfo.get_poster()
                
                if poster_url:
                    post_msg = await bot.send_photo(
                        Var.MAIN_CHANNEL,
                        photo=poster_url,
                        caption=await aniInfo.get_caption()
                    )
                else:
                    # Send as message if no poster available
                    post_msg = await bot.send_message(
                        Var.MAIN_CHANNEL,
                        text=await aniInfo.get_caption()
                    )
                
                # Send sticker after the post
                await bot.send_sticker(
                    Var.MAIN_CHANNEL,
                    sticker="CAACAgUAAxkBAAEOyQtoXB1SxAZqiP0wK7NbBBxxHwUG7gAC4BMAAp6PIFcLAAGEEdQGq4s2BA"
                )
                
                await asleep(1.5)
                stat_msg = await sendMessage(Var.MAIN_CHANNEL, f"<b>ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀɴɪᴍᴇ</b>")
            
            dl = await TorDownloader("./downloads").download(torrent, name)
            if not dl or not ospath.exists(dl):
                await rep.report(f"<b> ғɪʟᴇ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ, ᴛʀʏ ᴀɢᴀɪɴ</b>", "error")
                await stat_msg.delete()
                return

            post_id = post_msg.id
            ffEvent = Event()
            ff_queued[post_id] = ffEvent
            if ffLock.locked():
                await editMessage(stat_msg, f"<b>ϙᴜᴇᴜᴇᴅ ᴛᴏ ᴇɴᴄᴏᴅᴇ...</b>")
                await rep.report("<b>ᴀᴅᴅᴇᴅ ᴛᴀsᴋ ᴛᴏ ϙᴜᴇᴜᴇ....</b>", "info")
            await ffQueue.put(post_id)
            await ffEvent.wait()
            
            await ffLock.acquire()
            btns = []
            for qual in Var.QUALS:
                filename = await aniInfo.get_upname(qual)
                await editMessage(stat_msg, f"‣ <b>ᴀɴɪᴍᴇ ɴᴀᴍᴇ :</b><b>{name}</b>\n\n<b>ʀᴇᴀᴅʏ ᴛᴏ ᴇɴᴄᴏᴅᴇ.....</b>") # Ready to Encode...
                
                await asleep(1.5)
                await rep.report("<b>sᴛᴀʀᴛɪɴɢ ᴇɴᴄᴏᴅᴇ...</b>", "info")
                try:
                    out_path = await FFEncoder(stat_msg, dl, filename, qual).start_encode()
                except Exception as e:
                    await rep.report(f"<b>ᴇʀʀᴏʀ: {e}, ᴄᴀɴᴄᴇʟʟᴇᴅ, ʀᴇᴛʀʏ ᴀɢᴀɪɴ !</b>", "error")
                    await stat_msg.delete()
                    ffLock.release()
                    return
                await rep.report("<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴄᴏᴍᴘʀᴇssᴇᴅ ɴᴏᴡ ɢᴏɪɴɢ ᴛᴏ ᴜᴘʟᴏᴀᴅ.... </b>", "info")
                
                await editMessage(stat_msg, f"<b>ʀᴇᴀᴅʏ ᴛᴏ ᴜᴘʟᴏᴀᴅ...</b>")
                await asleep(1.5)
                try:
                    msg = await TgUploader(stat_msg).upload(out_path, qual)
                except Exception as e:
                    await rep.report(f"<b>ᴇʀʀᴏʀ: {e}, ᴄᴀɴᴄᴇʟʟᴇᴅ, ʀᴇᴛʀʏ ᴀɢᴀɪɴ !</b>", "error")
                    await stat_msg.delete()
                    ffLock.release()
                    return
                await rep.report("<b>sᴜᴄᴄᴇsғᴜʟʟʏ ᴜᴘʟᴏᴀᴅᴇᴅ ғɪʟᴇ ɪɴᴛᴏ ᴛɢ...</b>", "info")
                
                msg_id = msg.id
                link = f"https://telegram.me/{(await bot.get_me()).username}?start={await encode('get-'+str(msg_id * abs(Var.FILE_STORE)))}"
                
                if post_msg:
                    if len(btns) != 0 and len(btns[-1]) == 1:
                        btns[-1].insert(1, InlineKeyboardButton(f"{btn_formatter[qual]} - {convertBytes(msg.document.file_size)}", url=link))
                    else:
                        btns.append([InlineKeyboardButton(f"{btn_formatter[qual]} - {convertBytes(msg.document.file_size)}", url=link)])
                    await editMessage(post_msg, post_msg.caption.html if post_msg.caption else "", InlineKeyboardMarkup(btns))
                    
                await db.saveAnime(ani_id, ep_no, qual, post_id)
                bot_loop.create_task(extra_utils(msg_id, out_path))
            ffLock.release()
            
            await stat_msg.delete()
            await aioremove(dl)
        ani_cache['completed'].add(ani_id)
    except Exception as error:
        await rep.report(format_exc(), "error")

async def post_main_channel_summary(name, aniInfo, channel_details):
    """Post summary to main channel with join button"""
    try:
        # Extract episode info from name
        episode_info = extract_episode_info(name)
        
        # Get clean anime title from aniInfo instead of raw filename
        titles = aniInfo.adata.get("title", {})
        clean_title = titles.get('english') or titles.get('romaji') or titles.get('native') or "Unknown Anime"
        
        # Create summary caption with clean title
        caption = f"<b>{clean_title}</b>\n"
        caption += f"<b>──────────────────────────────</b>\n"
        caption += f"<b>➤ Season - {episode_info['season']}</b>\n"
        caption += f"<b>➤ Episode - {episode_info['episode']}</b>\n"
        caption += f"<b>➤ Quality: {episode_info['quality']}</b>\n"
        caption += f"<b>────────────────────────────</b>"
        
        # Create join button
        keyboard = None
        if channel_details.get('invite_link'):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴊᴏɪɴ ɴᴏᴡ ᴛᴏ ᴡᴀᴛᴄʜ", url=channel_details['invite_link'])]
            ])
        
        # Get poster
        poster_url = await aniInfo.get_poster()
        
        # Send summary to main channel
        if poster_url:
            await bot.send_photo(
                chat_id=Var.MAIN_CHANNEL,
                photo=poster_url,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                chat_id=Var.MAIN_CHANNEL,
                text=caption,
                reply_markup=keyboard
            )
        
        await rep.report(f"✅ Posted summary to main channel: {clean_title}", "info")
        
    except Exception as e:
        await rep.report(f"❌ Failed to post summary to main channel: {str(e)}", "error")

def extract_episode_info(anime_title):
    """Extract episode, season and quality info from anime title"""
    import re
    
    info = {
        'season': '01',
        'episode': '01',
        'quality': 'Multi [Sub]',
        'codec': 'H.264'
    }
    
    # Extract season
    season_match = re.search(r'[Ss](\d+)', anime_title)
    if season_match:
        info['season'] = season_match.group(1).zfill(2)
    
    # Extract episode
    episode_patterns = [
        r'[Ee](\d+)',
        r'Episode[\s\-]*(\d+)',
        r'Ep[\s\-]*(\d+)',
        r'\s(\d+)\s',
        r'-\s*(\d+)\s*-'
    ]
    
    for pattern in episode_patterns:
        episode_match = re.search(pattern, anime_title)
        if episode_match:
            info['episode'] = episode_match.group(1).zfill(2)
            break
    
    # Extract quality
    if '1080p' in anime_title.upper():
        info['quality'] = '1080p [Sub]'
    elif '720p' in anime_title.upper():
        info['quality'] = '720p [Sub]'
    elif '480p' in anime_title.upper():
        info['quality'] = '480p [Sub]'
    elif 'HEVC' in anime_title.upper():
        info['quality'] = 'HEVC [Sub]'
        info['codec'] = 'H.265'
    
    return info

async def extra_utils(msg_id, out_path):
    msg = await bot.get_messages(Var.FILE_STORE, message_ids=msg_id)

    if Var.BACKUP_CHANNEL != 0:
        for chat_id in Var.BACKUP_CHANNEL.split():
            await msg.copy(int(chat_id))
            
    # MediaInfo, ScreenShots, Sample Video ( Add-ons Features )
