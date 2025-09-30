from os import path as ospath, mkdir, system, getenv
from logging import INFO, ERROR, FileHandler, StreamHandler, basicConfig, getLogger
from traceback import format_exc
from asyncio import Queue, Lock

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import ChatMemberUpdated
from dotenv import load_dotenv
from uvloop import install

install()
basicConfig(format="[%(asctime)s] [%(name)s | %(levelname)s] - %(message)s [%(filename)s:%(lineno)d]",
            datefmt="%m/%d/%Y, %H:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

getLogger("pyrogram").setLevel(ERROR)
LOGS = getLogger(__name__)

load_dotenv('config.env')

ani_cache = {
    'fetch_animes': True,
    'ongoing': set(),
    'completed': set()
}
ffpids_cache = list()

ffLock = Lock()
ffQueue = Queue()
ff_queued = dict()

class Var:
    API_ID, API_HASH, BOT_TOKEN = getenv("API_ID"), getenv("API_HASH"), getenv("BOT_TOKEN")
    MONGO_URI = getenv("MONGO_URI")
    
    if not BOT_TOKEN or not API_HASH or not API_ID or not MONGO_URI:
        LOGS.critical('Important Variables Missing. Fill Up and Retry..!! Exiting Now...')
        exit(1)

    RSS_ITEMS = getenv("RSS_ITEMS", "https://subsplease.org/rss/?r=1080").split()
    FSUB_CHATS = list(map(int, getenv('FSUB_CHATS', '').split())) if getenv('FSUB_CHATS') else []
    BACKUP_CHANNEL = getenv("BACKUP_CHANNEL") or ""
    MAIN_CHANNEL = int(getenv("MAIN_CHANNEL"))
    LOG_CHANNEL = int(getenv("LOG_CHANNEL") or 0)
    FILE_STORE = int(getenv("FILE_STORE"))
    
    # Owner system instead of multiple admins
    OWNER = getenv("OWNER", "Mikoyae756")  # Owner username without @
    OWNER_ID = int(getenv("OWNER_ID", "7970350353"))  # Owner id
    
    SEND_SCHEDULE = getenv("SEND_SCHEDULE", "False").lower() == "true"
    BRAND_UNAME = getenv("BRAND_UNAME", "@username")
    FFCODE_Hdri = getenv("FFCODE_Hdri") or """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 640x360 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    FFCODE_1080 = getenv("FFCODE_1080") or """ffmpeg -i '{}' -progress '{}' -preset veryfast -c:v libx264 -s 1920x1080 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    FFCODE_720 = getenv("FFCODE_720") or """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 1280x720 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    FFCODE_480 = getenv("FFCODE_480") or """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 854x480 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y"""
    QUALS = getenv("QUALS", "480 720 1080 Hdri ").split()
    
    AS_DOC = getenv("AS_DOC", "True").lower() == "true"
    THUMB = getenv("THUMB", "https://te.legra.ph/file/621c8d40f9788a1db7753.jpg")
    AUTO_DEL = getenv("AUTO_DEL", "True").lower() == "true"
    DEL_TIMER = int(getenv("DEL_TIMER", "600"))
    START_PHOTO = getenv("START_PHOTO", "https://te.legra.ph/file/120de4dbad87fb20ab862.jpg")
    START_MSG = getenv("START_MSG", "<b>Hey {first_name}</b>,\n\n    <i>I am Auto Animes Store & Automater Encoder Build with ❤️ !!</i>")
    START_BUTTONS = getenv("START_BUTTONS", "UPDATES|https://telegram.me/Matiz_Tech SUPPORT|https://t.me/+p78fp4UzfNwzYzQ5")
    
    # Added for users command
    WAIT_MSG = "<b>Please wait...</b>"
    # Added for broadcast commands
    REPLY_ERROR = "<b>Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ.</b>"

# Admin filter function
async def admin_filter(_, __, message):
    """Custom filter to check if user is admin or owner"""
    user_id = message.from_user.id
    if user_id == Var.OWNER_ID:
        return True
    from bot.core.database import db
    return await db.is_admin(user_id)

# Create the admin filter
admin = filters.create(admin_filter)

# Modified thumbnail handling
if ospath.exists("bot/thumb.jpg"):
    system("cp bot/thumb.jpg thumb.jpg")
    LOGS.info("Local thumbnail loaded from bot/thumb.jpg")
elif Var.THUMB and not ospath.exists("thumb.jpg"):
    system(f"wget -q {Var.THUMB} -O thumb.jpg")
    LOGS.info("Thumbnail downloaded from URL")

if not ospath.isdir("encode/"):
    mkdir("encode/")
if not ospath.isdir("thumbs/"):
    mkdir("thumbs/")
if not ospath.isdir("downloads/"):
    mkdir("downloads/")

try:
    bot = Client(name="AutoAniAdvance", api_id=Var.API_ID, api_hash=Var.API_HASH, bot_token=Var.BOT_TOKEN, plugins=dict(root="bot/modules"), parse_mode=ParseMode.HTML)
    bot_loop = bot.loop
    sch = AsyncIOScheduler(timezone="Asia/Kolkata", event_loop=bot_loop)
except Exception as ee:
    LOGS.error(str(ee))
    exit(1)

# Force Subscription Event Handlers
@bot.on_chat_member_updated()
async def handle_chat_members(client, chat_member_updated: ChatMemberUpdated):
    """Handle member updates for force subscription channels"""
    try:
        from bot.core.database import db
        
        chat_id = chat_member_updated.chat.id
        
        if await db.reqChannel_exist(chat_id):
            old_member = chat_member_updated.old_chat_member
            
            if not old_member:
                return
            
            if old_member.status == ChatMemberStatus.MEMBER:
                user_id = old_member.user.id
                
                if await db.req_user_exist(chat_id, user_id):
                    await db.del_req_user(chat_id, user_id)
                    LOGS.info(f"Removed user {user_id} from request list for channel {chat_id}")
    except Exception as e:
        LOGS.error(f"Error in handle_chat_members: {e}")

@bot.on_chat_join_request()
async def handle_join_request(client, chat_join_request):
    """Handle join requests for force subscription channels"""
    try:
        from bot.core.database import db
        
        chat_id = chat_join_request.chat.id
        user_id = chat_join_request.from_user.id
        
        channel_exists = await db.reqChannel_exist(chat_id)
        
        if channel_exists:
            if not await db.req_user_exist(chat_id, user_id):
                await db.req_user(chat_id, user_id)
                LOGS.info(f"Added user {user_id} to request list for channel {chat_id}")
    except Exception as e:
        LOGS.error(f"Error in handle_join_request: {e}")
