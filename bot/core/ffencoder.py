from re import findall 
from math import floor
from time import time
from os import path as ospath
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, rename as aiorename
from shlex import split as ssplit
from asyncio import sleep as asleep, gather, create_subprocess_shell, create_task
from asyncio.subprocess import PIPE

from bot import Var, bot_loop, ffpids_cache, LOGS
from .func_utils import mediainfo, convertBytes, convertTime, sendMessage, editMessage
from .reporter import rep

ffargs = {
    "Hdri":Var.FFCODE_Hdri,
    '1080': Var.FFCODE_1080,
    '720': Var.FFCODE_720,
    '480': Var.FFCODE_480,
}

class FFEncoder:
    def __init__(self, message, path, name, qual):
        self.__proc = None
        self.is_cancelled = False
        self.message = message
        self.__name = name
        self.__qual = qual
        self.dl_path = path
        self.__total_time = None
        self.out_path = ospath.join("encode", name)
        self.__prog_file = 'prog.txt'
        self.__start_time = time()

    async def progress(self):
        self.__total_time = await mediainfo(self.dl_path, get_duration=True)
        if isinstance(self.__total_time, str) or not self.__total_time:
            self.__total_time = 1.0

        last_update_time = 0
        while not (self.__proc is None or self.is_cancelled):
            async with aiopen(self.__prog_file, 'r+') as p:
                text = await p.read()

            if text:
                # Parse ffmpeg stats
                time_done = int(t[-1]) / 1_000_000 if (t := findall("out_time_ms=(\d+)", text)) else 0
                ensize = int(s[-1]) if (s := findall(r"total_size=(\d+)", text)) else 0

                # Safety: clamp time_done
                time_done = min(time_done, self.__total_time)

                # Percent calculation
                percent = round((time_done / self.__total_time) * 100, 2)

                # ETA
                diff = time() - self.__start_time
                eta = (self.__total_time - time_done) if time_done > 0 else 0

                # Speed (average encoded bytes per second)
                speed = ensize / diff if diff > 0 else 0

                # More stable estimated final size
                tsize = (ensize / time_done * self.__total_time) if time_done > 5 else 0

                # Progress bar (25 blocks)
                bar_blocks = 25
                filled_blocks = floor((percent / 100) * bar_blocks)
                bar = "█" * filled_blocks + "▒" * (bar_blocks - filled_blocks)

                # Only update message every 5 seconds
                if time() - last_update_time >= 8:
                    last_update_time = time()
                    progress_str = f"""<b>ᴀɴɪᴍᴇ ɴᴀᴍᴇ :</b> <b>{self.__name}</b>

<blockquote>‣ <b>sᴛᴀᴛᴜs :</b> ᴇɴᴄᴏᴅɪɴɢ <code>[{bar}]</code> {percent}%</blockquote> 
<blockquote>‣ <b>sɪᴢᴇ :</b> {convertBytes(ensize)} out of ~ {convertBytes(tsize)}
‣ <b>sᴘᴇᴇᴅ :</b> {convertBytes(speed)}/s
‣ <b>ᴛɪᴍᴇ ᴛᴏᴏᴋ :</b> {convertTime(diff)}
‣ <b>ᴛɪᴍᴇ ʟᴇғᴛ :</b> {convertTime(eta)}</blockquote>
<blockquote>‣ <b>ғɪʟᴇ(s) ᴇɴᴄᴏᴅᴇᴅ:</b> <code>{Var.QUALS.index(self.__qual)} / {len(Var.QUALS)}</code></blockquote>"""

                    await editMessage(self.message, progress_str)

                if (prog := findall(r"progress=(\w+)", text)) and prog[-1] == 'end':
                    break

            await asleep(2)
    
    async def start_encode(self):
        if ospath.exists(self.__prog_file):
            await aioremove(self.__prog_file)
    
        async with aiopen(self.__prog_file, 'w+'):
            LOGS.info("Progress Temp Generated !")
            pass
        
        dl_npath, out_npath = ospath.join("encode", "ffanimeadvin.mkv"), ospath.join("encode", "ffanimeadvout.mkv")
        await aiorename(self.dl_path, dl_npath)
        
        ffcode = ffargs[self.__qual].format(dl_npath, self.__prog_file, out_npath)
        
        LOGS.info(f'FFCode: {ffcode}')
        self.__proc = await create_subprocess_shell(ffcode, stdout=PIPE, stderr=PIPE)
        proc_pid = self.__proc.pid
        ffpids_cache.append(proc_pid)
        _, return_code = await gather(create_task(self.progress()), self.__proc.wait())
        ffpids_cache.remove(proc_pid)
        
        await aiorename(dl_npath, self.dl_path)
        
        if self.is_cancelled:
            return
        
        if return_code == 0:
            if ospath.exists(out_npath):
                await aiorename(out_npath, self.out_path)
            return self.out_path
        else:
            await rep.report((await self.__proc.stderr.read()).decode().strip(), "error")
            
    async def cancel_encode(self):
        self.is_cancelled = True
        if self.__proc is not None:
            try:
                self.__proc.kill()
            except:
                pass
