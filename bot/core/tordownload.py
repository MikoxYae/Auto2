from os import path as ospath, listdir
from aiofiles import open as aiopen
from aiofiles.os import path as aiopath, remove as aioremove, mkdir

from aiohttp import ClientSession
from torrentp import TorrentDownloader
from bot import LOGS
from bot.core.func_utils import handle_logs

class TorDownloader:
    def __init__(self, path="."):
        self.__downdir = path
        self.__torpath = "torrents/"
    
    @handle_logs
    async def download(self, torrent, name=None):
        if torrent.startswith("magnet:"):
            # Get list of files before download
            files_before = set(listdir(self.__downdir)) if ospath.exists(self.__downdir) else set()
            
            torp = TorrentDownloader(torrent, self.__downdir)
            await torp.start_download()
            
            # Get list of files after download
            files_after = set(listdir(self.__downdir)) if ospath.exists(self.__downdir) else set()
            
            # Find the new file(s) that were downloaded
            new_files = files_after - files_before
            if new_files:
                # Get the largest file (usually the video file)
                largest_file = max(new_files, key=lambda f: ospath.getsize(ospath.join(self.__downdir, f)))
                return ospath.join(self.__downdir, largest_file)
            
            # Fallback: return the name parameter if provided
            return ospath.join(self.__downdir, name) if name else None
            
        elif torfile := await self.get_torfile(torrent):
            # Get list of files before download
            files_before = set(listdir(self.__downdir)) if ospath.exists(self.__downdir) else set()
            
            torp = TorrentDownloader(torfile, self.__downdir)
            await torp.start_download()
            await aioremove(torfile)
            
            # Get list of files after download
            files_after = set(listdir(self.__downdir)) if ospath.exists(self.__downdir) else set()
            
            # Find the new file(s) that were downloaded
            new_files = files_after - files_before
            if new_files:
                # Get the largest file (usually the video file)
                largest_file = max(new_files, key=lambda f: ospath.getsize(ospath.join(self.__downdir, f)))
                return ospath.join(self.__downdir, largest_file)
            
            return None

    @handle_logs
    async def get_torfile(self, url):
        if not await aiopath.isdir(self.__torpath):
            await mkdir(self.__torpath)
        
        tor_name = url.split('/')[-1]
        des_dir = ospath.join(self.__torpath, tor_name)
        
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiopen(des_dir, 'wb') as file:
                        async for chunk in response.content.iter_any():
                            await file.write(chunk)
                    return des_dir
        return None
