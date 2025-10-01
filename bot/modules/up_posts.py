from json import loads as jloads
from os import path as ospath, execl
from sys import executable
from datetime import datetime

from aiohttp import ClientSession
from pyrogram.filters import command, private

from bot import Var, bot, ffQueue, admin
from bot.core.text_utils import TextEditor
from bot.core.reporter import rep
from bot.core.func_utils import new_task, sendMessage

def convert_to_12hr_format(time_24hr):
    """Convert 24-hour time to 12-hour format with AM/PM"""
    try:
        # Parse the time (format: "HH:MM")
        time_obj = datetime.strptime(time_24hr, "%H:%M")
        # Convert to 12-hour format
        time_12hr = time_obj.strftime("%I:%M %p")
        # Remove leading zero from hour
        if time_12hr.startswith("0"):
            time_12hr = time_12hr[1:]
        return time_12hr
    except:
        return time_24hr + " hrs"

async def generate_schedule_text():
    """Generate anime schedule text"""
    try:
        async with ClientSession() as ses:
            res = await ses.get("https://subsplease.org/api/?f=schedule&h=true&tz=Asia/Kolkata")
            aniContent = jloads(await res.text())["schedule"]
        
        text = "<b>𝗧𝗼𝗱𝗮𝘆 𝗔𝗻𝗶𝗺𝗲 𝗥𝗲𝗹𝗲𝗮𝘀𝗲 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲 [ɪsᴛ]</b>\n\n"
        
        for i in aniContent:
            aname = TextEditor(i["title"])
            await aname.load_anilist()
            anime_title = aname.adata.get('title', {}).get('english') or i['title']
            formatted_time = convert_to_12hr_format(i["time"])
            
            text += f'''<b>Anime Name :</b> {anime_title}\n<b>Time :</b> {formatted_time} [Approx]\n\n'''
        
        return text
    except Exception as err:
        await rep.report(f"Error generating schedule: {str(err)}", "error")
        return None

@bot.on_message(command('schedule') & private & admin)
@new_task
async def send_schedule_command(client, message):
    """Manual command to send anime schedule to main channel"""
    temp = await sendMessage(message, "<b><i>Generating schedule...</i></b>")
    
    try:
        schedule_text = await generate_schedule_text()
        
        if schedule_text:
            # Send to main channel
            schedule_msg = await bot.send_photo(
                Var.MAIN_CHANNEL,
                photo="https://graph.org/file/bd0dea0fae723c48b279c-76e285fcf95b537017.jpg",
                caption=schedule_text
            )
            await (await schedule_msg.pin()).delete()
            
            # Confirm to admin
            await temp.edit("<b>✅ Schedule posted to main channel successfully!</b>")
        else:
            await temp.edit("<b>❌ Failed to generate schedule. Check logs for details.</b>")
    
    except Exception as err:
        await rep.report(f"Error in schedule command: {str(err)}", "error")
        await temp.edit(f"<b>❌ Error posting schedule:</b>\n<code>{str(err)}</code>")

async def upcoming_animes():
    if Var.SEND_SCHEDULE:
        try:
            schedule_text = await generate_schedule_text()
            
            if schedule_text:
                # Send with photo
                TD_SCHR = await bot.send_photo(
                    Var.MAIN_CHANNEL,
                    photo="https://graph.org/file/df68848d38f173ac76acf-6fc89001af21521f2f.jpg",
                    caption=schedule_text
                )
                await (await TD_SCHR.pin()).delete()
        except Exception as err:
            await rep.report(str(err), "error")
    
    if not ffQueue.empty():
        await ffQueue.join()
    await rep.report("Auto Restarting..!!", "info")
    execl(executable, executable, "-m", "bot")

async def update_shdr(name, link):
    if TD_SCHR is not None:
        TD_lines = TD_SCHR.text.split('\n')
        for i, line in enumerate(TD_lines):
            if line.startswith(f"📌 {name}"):
                TD_lines[i+2] = f"    • Status : ✅ Uploaded\n    • Link : {link}"
        await TD_SCHR.edit("\n".join(TD_lines))
