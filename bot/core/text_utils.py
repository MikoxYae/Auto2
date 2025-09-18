from calendar import month_name
from datetime import datetime
from random import choice
from asyncio import sleep as asleep
from aiohttp import ClientSession
from anitopy import parse

from bot import Var, bot
from .database import db
from .ffencoder import ffargs
from .func_utils import handle_logs
from .reporter import rep

# Caption format for dedicated channels (without synopsis)
DEDICATED_CAPTION_FORMAT = """
<b>{title}</b>
<b>──────────────────────────────</b>
<b>➤ Season - {season}</b>
<b>➤ Episode - {ep_no}</b>
<b>➤ Quality: Multi [Sub]</b>
<b>──────────────────────────────</b>
"""

# Caption format for main channel (with synopsis in blockquote)
MAIN_CAPTION_FORMAT = """
<b>{title}</b>
<b>──────────────────────────────</b>
<b>➤ Season - {season}</b>
<b>➤ Episode - {ep_no}</b>
<b>➤ Quality: Multi [Sub]</b>
<b>────────────────────────────</b>
<blockquote><b>‣ Synopsis : {synopsis}

📖 Tap to expand/collapse</b></blockquote>
"""

GENRES_EMOJI = {"Action": "👊", "Adventure": choice(['🪂', '🧗‍♀']), "Comedy": "🤣", "Drama": " 🎭", "Ecchi": choice(['💋', '🥵']), "Fantasy": choice(['🧞', '🧞‍♂', '🧞‍♀','🌗']), "Hentai": "🔞", "Horror": "☠", "Mahou Shoujo": "☯", "Mecha": "🤖", "Music": "🎸", "Mystery": "🔮", "Psychological": "♟", "Romance": "💞", "Sci-Fi": "🛸", "Slice of Life": choice(['☘','🍁']), "Sports": "⚽️", "Supernatural": "🫧", "Thriller": "🔥"}

ANIME_GRAPHQL_QUERY = """
query ($id: Int, $search: String, $seasonYear: Int) {
  Media(id: $id, type: ANIME, format_not_in: [MOVIE, MUSIC, MANGA, NOVEL, ONE_SHOT], search: $search, seasonYear: $seasonYear) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    chapters
    volumes
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    meanScore
    popularity
    trending
    favourites
    studios {
      nodes {
         name
         siteUrl
      }
    }
    isAdult
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      edges {
        node {
          airingAt
          timeUntilAiring
          episode
        }
      }
    }
    externalLinks {
      url
      site
    }
    siteUrl
  }
}
"""

class AniLister:
    def __init__(self, anime_name: str, year: int) -> None:
        self.__api = "https://graphql.anilist.co"
        self.__ani_name = anime_name
        self.__ani_year = year
        self.__vars = {'search' : self.__ani_name, 'seasonYear': self.__ani_year}
    
    def __update_vars(self, year=True) -> None:
        if year:
            self.__ani_year -= 1
            self.__vars['seasonYear'] = self.__ani_year
        else:
            self.__vars = {'search' : self.__ani_name}
    
    async def post_data(self):
        async with ClientSession() as sess:
            async with sess.post(self.__api, json={'query': ANIME_GRAPHQL_QUERY, 'variables': self.__vars}) as resp:
                return (resp.status, await resp.json(), resp.headers)
        
    async def get_anidata(self):
        res_code, resp_json, res_heads = await self.post_data()
        while res_code == 404 and self.__ani_year > 2020:
            self.__update_vars()
            await rep.report(f"AniList Query Name: {self.__ani_name}, Retrying with {self.__ani_year}", "warning", log=False)
            res_code, resp_json, res_heads = await self.post_data()
        
        if res_code == 404:
            self.__update_vars(year=False)
            res_code, resp_json, res_heads = await self.post_data()
        
        if res_code == 200:
            return resp_json.get('data', {}).get('Media', {}) or {}
        elif res_code == 429:
            f_timer = int(res_heads['Retry-After'])
            await rep.report(f"AniList API FloodWait: {res_code}, Sleeping for {f_timer} !!", "error")
            await asleep(f_timer)
            return await self.get_anidata()
        elif res_code in [500, 501, 502]:
            await rep.report(f"AniList Server API Error: {res_code}, Waiting 5s to Try Again !!", "error")
            await asleep(5)
            return await self.get_anidata()
        else:
            await rep.report(f"AniList API Error: {res_code}", "error", log=False)
            return {}
    
class TextEditor:
    def __init__(self, name):
        self.__name = name
        self.adata = {}
        self.pdata = parse(name)

    async def load_anilist(self):
        cache_names = []
        for option in [(False, False), (False, True), (True, False), (True, True)]:
            ani_name = await self.parse_name(*option)
            if ani_name in cache_names:
                continue
            cache_names.append(ani_name)
            self.adata = await AniLister(ani_name, datetime.now().year).get_anidata()
            if self.adata:
                break

    @handle_logs
    async def get_id(self):
        if (ani_id := self.adata.get('id')) and str(ani_id).isdigit():
            return ani_id
            
    @handle_logs
    async def parse_name(self, no_s=False, no_y=False):
        anime_name = self.pdata.get("anime_title")
        anime_season = self.pdata.get("anime_season")
        anime_year = self.pdata.get("anime_year")
        if anime_name:
            pname = anime_name
            if not no_s and self.pdata.get("episode_number") and anime_season:
                pname += f" {anime_season}"
            if not no_y and anime_year:
                pname += f" {anime_year}"
            return pname
        return anime_name
        
    @handle_logs
    async def get_poster(self):
        try:
            # Get all custom banners
            all_banners = await db.get_all_custom_banners()
            
            # Check if any custom banner name matches this torrent
            for banner in all_banners:
                banner_name = banner['anime_name']
                
                # Check if banner name is in torrent name OR torrent name is in banner name
                if (banner_name.lower() in self.__name.lower()) or (self.__name.lower() in banner_name.lower()):
                    await rep.report(f"✅ Using custom banner for: {banner_name}", "info")
                    return banner['banner_file_id']
            
            # Fallback to AniList poster
            if anime_id := await self.get_id():
                await rep.report(f"🎨 Using AniList poster for: {self.__name}", "info")
                return f"https://img.anili.st/media/{anime_id}"
            
            # Default fallback
            return "https://telegra.ph/file/112ec08e59e73b6189a20.jpg"
            
        except Exception as e:
            await rep.report(f"❌ Error getting poster: {str(e)}", "error")
            # Return default on error
            if anime_id := await self.get_id():
                return f"https://img.anili.st/media/{anime_id}"
            return "https://telegra.ph/file/112ec08e59e73b6189a20.jpg"
        
    @handle_logs
    async def get_upname(self, qual=""):
        """Generate filename in format: S01Ep01 - Episode Title [480p][@TeamWarlords].mkv"""
        
        # Get season and episode numbers
        anime_season = self.pdata.get("anime_season", "01")
        if isinstance(anime_season, list):
            season_num = str(anime_season[-1]).zfill(2)
        else:
            season_num = str(anime_season).zfill(2) if anime_season else "01"
        
        episode_num = str(self.pdata.get("episode_number", "01")).zfill(2)
        
        # Try to get episode title from AniList data
        episode_title = "Unknown Episode"
        
        # Check if we have episode data from AniList
        if self.adata and 'airingSchedule' in self.adata:
            try:
                # Look for the specific episode in airing schedule
                current_ep = int(episode_num)
                for edge in self.adata['airingSchedule']['edges']:
                    if edge['node']['episode'] == current_ep:
                        # For now, we'll use a generic title since AniList doesn't provide episode titles
                        episode_title = f"Episode {current_ep}"
                        break
            except:
                pass
        
        # If no specific episode title found, use torrent name parsing
        if episode_title == "Unknown Episode":
            # Try to extract episode title from torrent name
            torrent_name = self.__name
            
            # Remove common patterns to get episode title
            import re
            
            # Remove resolution, groups, year, etc.
            clean_name = re.sub(r'\[.*?\]', '', torrent_name)  # Remove [groups], [1080p], etc.
            clean_name = re.sub(r'\(.*?\)', '', clean_name)    # Remove (year), etc.
            clean_name = re.sub(r'20\d{2}', '', clean_name)    # Remove years
            clean_name = re.sub(r'S\d+', '', clean_name, flags=re.IGNORECASE)  # Remove season
            clean_name = re.sub(r'EP?\d+', '', clean_name, flags=re.IGNORECASE)  # Remove episode
            clean_name = re.sub(r'Episode\s*\d+', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'第\d+話', '', clean_name)     # Remove Japanese episode
            clean_name = re.sub(r'\d+p', '', clean_name, flags=re.IGNORECASE)  # Remove quality
            clean_name = re.sub(r'(HEVC|H\.?264|H\.?265|x264|x265)', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'(1080|720|480)', '', clean_name)
            clean_name = re.sub(r'-\s*$', '', clean_name)      # Remove trailing dash
            clean_name = clean_name.strip(' -')
            
            # Split by common separators and take meaningful part
            parts = re.split(r'[-–—]', clean_name)
            if len(parts) > 1:
                episode_title = parts[-1].strip()
            else:
                episode_title = clean_name or f"Episode {episode_num}"
        
        # Clean episode title
        episode_title = episode_title.strip()
        if not episode_title or episode_title.lower() in ['unknown episode', 'episode']:
            episode_title = f"Episode {episode_num}"
        
        # Format brand name (remove @ if already present)
        brand = Var.BRAND_UNAME.strip('@')
        
        # Generate filename: S01Ep01 - Episode Title [480p][@TeamWarlords].mkv
        filename = f"S{season_num}Ep{episode_num} - {episode_title} [{qual}p][{brand}].mkv"
        
        # Clean filename (remove invalid characters)
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', ' ', filename)  # Replace multiple spaces with single space
        
        return filename

    @handle_logs
    async def get_caption(self, is_main_channel=False):
        """Get caption for posts - different format for main channel vs dedicated channels"""
        titles = self.adata.get("title", {})
        title = titles.get('english') or titles.get('romaji') or titles.get('native') or "Unknown Anime"
        
        # Get season and episode from parsed data
        season = self.pdata.get("anime_season", "01")
        if isinstance(season, list):
            season = str(season[-1]).zfill(2)
        else:
            season = str(season).zfill(2) if season else "01"
        
        episode = str(self.pdata.get("episode_number", "01")).zfill(2)
        
        if is_main_channel:
            # Main channel format with synopsis and expand indicator
            synopsis = self.adata.get("description", "No synopsis available.")
            if synopsis and len(synopsis) > 800:
                synopsis = synopsis[:800] + "..."
            
            return MAIN_CAPTION_FORMAT.format(
                title=title,
                season=season,
                ep_no=episode,
                synopsis=synopsis
            )
        else:
            # Dedicated channel format without synopsis
            return DEDICATED_CAPTION_FORMAT.format(
                title=title,
                season=season,
                ep_no=episode
            )
