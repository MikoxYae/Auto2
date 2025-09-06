import os
from os import environ, getenv
import logging
from logging.handlers import RotatingFileHandler

#============================================
# Bot Configuration
#============================================
API_ID = int(os.environ.get("API_ID", "27704224"))
API_HASH = os.environ.get("API_HASH", "c2e33826d757fe113bc154fcfabc987d")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7625600338:AAFaskZ9c3fcpqN6-8YF6iy12ueQkW-jhxM")

#============================================
# Database Configuration
#============================================
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Koi:aloksingh@cluster0.86wo9.mongodb.net/?retryWrites=true&w=majority")

#============================================
# Channel Configuration
#============================================
MAIN_CHANNEL = int(os.environ.get("MAIN_CHANNEL", "-1002585643417"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1003089985542"))
FILE_STORE = int(os.environ.get("FILE_STORE", "-1002392729611"))
BACKUP_CHANNEL = os.environ.get("BACKUP_CHANNEL", "0")

# Force Subscribe Channels (comma separated channel IDs)
FSUB_CHATS = list(map(int, os.environ.get('FSUB_CHATS', '').split())) if os.environ.get('FSUB_CHATS') else []

#============================================
# Owner/Admin Configuration
#============================================
OWNER = os.environ.get("OWNER", "Mikoyae756")  # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "7970350353"))  # Owner ID

#============================================
# RSS Feed Configuration
#============================================
RSS_ITEMS = os.environ.get("RSS_ITEMS", "0").split()

#============================================
# FFmpeg Encoding Configuration
#============================================
FFCODE_Hdrip = os.environ.get("FFCODE_Hdrip", """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 640x360 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y""")
FFCODE_1080 = os.environ.get("FFCODE_1080", """ffmpeg -i '{}' -progress '{}' -preset veryfast -c:v libx264 -s 1920x1080 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y""")
FFCODE_720 = os.environ.get("FFCODE_720", """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 1280x720 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y""")
FFCODE_480 = os.environ.get("FFCODE_480", """ffmpeg -i '{}' -progress '{}' -preset superfast -c:v libx264 -s 854x480 -pix_fmt yuv420p -crf 30 -c:a libopus -b:a 32k -c:s copy -map 0 -ac 2 -ab 32k -vbr 2 -level 3.1 '{}' -y""")

# Quality Settings
QUALS = os.environ.get("QUALS", "480 720 1080 Hdrip").split()

#============================================
# Bot Behavior Configuration
#============================================
AS_DOC = os.environ.get("AS_DOC", "True").lower() == "true"
AUTO_DEL = os.environ.get("AUTO_DEL", "True").lower() == "true"
DEL_TIMER = int(os.environ.get("DEL_TIMER", "600"))
SEND_SCHEDULE = os.environ.get("SEND_SCHEDULE", "False").lower() == "true"

#============================================
# Media Configuration
#============================================
THUMB = os.environ.get("THUMB", "https://te.legra.ph/file/621c8d40f9788a1db7753.jpg")
START_PHOTO = os.environ.get("START_PHOTO", "https://te.legra.ph/file/120de4dbad87fb20ab862.jpg")

#============================================
# Messages Configuration
#============================================
START_MSG = os.environ.get("START_MSG", "<b>Hey {first_name}</b>,\n\n    <i>I am Auto Animes Store & Automater Encoder Build with ❤️ !!</i>")
START_BUTTONS = os.environ.get("START_BUTTONS", "UPDATES|https://telegram.me/Matiz_Tech SUPPORT|https://t.me/+p78fp4UzfNwzYzQ5")
BRAND_UNAME = os.environ.get("BRAND_UNAME", "@username")

# Status Messages
WAIT_MSG = "<b>Please wait...</b>"
REPLY_ERROR = "<b>Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ.</b>"

#============================================
# Logging Configuration
#============================================
LOG_FILE_NAME = "log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s | %(levelname)s] - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%m/%d/%Y, %H:%M:%S %p",
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)

logging.getLogger("pyrogram").setLevel(logging.ERROR)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

#============================================
# Validation
#============================================
if not BOT_TOKEN or not API_HASH or not API_ID or not MONGO_URI:
    LOGGER(__name__).critical('Important Variables Missing. Fill Up and Retry..!! Exiting Now...')
    exit(1)
