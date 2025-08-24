from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
from bot.core.reporter import rep

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            from bot import Var
            self.client = AsyncIOMotorClient(Var.MONGO_URI)
            self.db = self.client.anime_bot
            # Test connection
            await self.db.command("ping")
            await rep.report("MongoDB connected successfully", "info")
            return True
        except Exception as e:
            await rep.report(f"MongoDB connection error: {str(e)}", "error")
            return False

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()

    # USER MANAGEMENT
    async def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Add or update user"""
        try:
            if self.db is None:
                await self.connect()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "date_joined": current_time,
                "is_banned": False
            }
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
        except Exception as e:
            await rep.report(f"Error adding user: {str(e)}", "error")

    async def is_banned(self, user_id):
        """Check if user is banned"""
        try:
            if self.db is None:
                await self.connect()
            user = await self.db.users.find_one({"user_id": user_id})
            return user.get("is_banned", False) if user else False
        except Exception as e:
            await rep.report(f"Error checking ban status: {str(e)}", "error")
            return False

    async def add_ban_user(self, user_id):
        """Ban user"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": True}},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error banning user: {str(e)}", "error")
            return False

    async def del_ban_user(self, user_id):
        """Unban user"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": False}}
            )
            return True
        except Exception as e:
            await rep.report(f"Error unbanning user: {str(e)}", "error")
            return False

    async def get_ban_users(self):
        """Get all banned users"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.users.find({"is_banned": True})
            banned_users = []
            async for user in cursor:
                banned_users.append(user["user_id"])
            return banned_users
        except Exception as e:
            await rep.report(f"Error getting banned users: {str(e)}", "error")
            return []

    async def del_user(self, user_id):
        """Delete user"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.users.delete_one({"user_id": user_id})
            return True
        except Exception as e:
            await rep.report(f"Error deleting user: {str(e)}", "error")
            return False

    async def full_userbase(self):
        """Get all users"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.users.find({})
            users = []
            async for user in cursor:
                users.append(user["user_id"])
            return users
        except Exception as e:
            await rep.report(f"Error getting userbase: {str(e)}", "error")
            return []

    # ADMIN MANAGEMENT
    async def add_admin(self, user_id):
        """Add admin"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.admins.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error adding admin: {str(e)}", "error")
            return False

    async def del_admin(self, user_id):
        """Remove admin"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.admins.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing admin: {str(e)}", "error")
            return False

    async def get_all_admins(self):
        """Get all admins"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.admins.find({})
            admins = []
            async for admin in cursor:
                admins.append(admin["user_id"])
            return admins
        except Exception as e:
            await rep.report(f"Error getting admins: {str(e)}", "error")
            return []

    async def is_admin(self, user_id):
        """Check if user is admin"""
        try:
            if self.db is None:
                await self.connect()
            admin = await self.db.admins.find_one({"user_id": user_id})
            return admin is not None
        except Exception as e:
            await rep.report(f"Error checking admin status: {str(e)}", "error")
            return False

    # ANIME DATA MANAGEMENT
    async def saveAnime(self, anime_id, episode_number, quality, post_id):
        """Save anime episode data"""
        try:
            if self.db is None:
                await self.connect()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            anime_data = {
                "anime_id": anime_id,
                "episode_number": episode_number,
                "quality": quality,
                "post_id": post_id,
                "date_added": current_time
            }
            await self.db.anime_data.update_one(
                {"anime_id": anime_id, "episode_number": episode_number, "quality": quality},
                {"$set": anime_data},
                upsert=True
            )
        except Exception as e:
            await rep.report(f"Error saving anime: {str(e)}", "error")

    async def getAnime(self, anime_id):
        """Get anime data"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.anime_data.find({"anime_id": anime_id})
            anime_data = {}
            async for record in cursor:
                episode = record["episode_number"]
                quality = record["quality"]
                post_id = record["post_id"]
                
                if episode not in anime_data:
                    anime_data[episode] = {}
                anime_data[episode][quality] = post_id
            
            return anime_data if anime_data else None
        except Exception as e:
            await rep.report(f"Error getting anime: {str(e)}", "error")
            return None

    async def reboot(self):
        """Clear anime cache/data"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.anime_data.delete_many({})
        except Exception as e:
            await rep.report(f"Error rebooting: {str(e)}", "error")

    # ANIME CHANNELS MANAGEMENT
    async def add_anime_channel(self, anime_name, channel_id, channel_title, invite_link=None):
        """Add anime channel mapping"""
        try:
            if self.db is None:
                await self.connect()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            channel_data = {
                "anime_name": anime_name,
                "channel_id": channel_id,
                "channel_title": channel_title,
                "invite_link": invite_link,
                "date_added": current_time
            }
            await self.db.anime_channels.update_one(
                {"anime_name": anime_name},
                {"$set": channel_data},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error adding anime channel: {str(e)}", "error")
            return False

    async def find_channel_by_anime_title(self, torrent_name):
        """Find channel by matching anime title"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.anime_channels.find({})
            
            clean_torrent = self.clean_name_for_matching(torrent_name)
            
            async for channel in cursor:
                anime_name = channel["anime_name"]
                clean_anime = self.clean_name_for_matching(anime_name)
                
                if clean_anime.lower() in clean_torrent.lower() or clean_torrent.lower() in clean_anime.lower():
                    return {
                        'anime_name': anime_name,
                        'channel_id': channel["channel_id"],
                        'channel_title': channel["channel_title"],
                        'invite_link': channel.get("invite_link")
                    }
            
            return None
        except Exception as e:
            await rep.report(f"Error finding channel: {str(e)}", "error")
            return None

    async def get_all_anime_channels(self):
        """Get all anime channel mappings"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.anime_channels.find({}).sort("date_added", -1)
            
            mappings = []
            async for channel in cursor:
                mappings.append({
                    'anime_name': channel["anime_name"],
                    'channel_id': channel["channel_id"],
                    'channel_title': channel["channel_title"],
                    'invite_link': channel.get("invite_link")
                })
            
            return mappings
        except Exception as e:
            await rep.report(f"Error getting anime channels: {str(e)}", "error")
            return []

    async def remove_anime_channel(self, anime_name):
        """Remove anime channel mapping"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.anime_channels.delete_one({"anime_name": {"$regex": f"^{re.escape(anime_name)}$", "$options": "i"}})
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing anime channel: {str(e)}", "error")
            return False

    # PENDING CONNECTIONS
    async def add_pending_connection(self, user_id, anime_name, invite_link):
        """Add pending channel connection"""
        try:
            if self.db is None:
                await self.connect()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection_data = {
                "user_id": user_id,
                "anime_name": anime_name,
                "invite_link": invite_link,
                "timestamp": current_time
            }
            await self.db.pending_connections.update_one(
                {"user_id": user_id},
                {"$set": connection_data},
                upsert=True
            )
        except Exception as e:
            await rep.report(f"Error adding pending connection: {str(e)}", "error")

    async def get_pending_connection(self, user_id):
        """Get pending connection for user"""
        try:
            if self.db is None:
                await self.connect()
            connection = await self.db.pending_connections.find_one({"user_id": user_id})
            
            if connection:
                return {'anime_name': connection["anime_name"], 'invite_link': connection["invite_link"]}
            return None
        except Exception as e:
            await rep.report(f"Error getting pending connection: {str(e)}", "error")
            return None

    async def remove_pending_connection(self, user_id):
        """Remove pending connection"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.pending_connections.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing pending connection: {str(e)}", "error")
            return False

    # CUSTOM BANNERS MANAGEMENT
    async def add_custom_banner(self, anime_name, banner_file_id):
        """Add custom banner"""
        try:
            if self.db is None:
                await self.connect()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            banner_data = {
                "anime_name": anime_name,
                "banner_file_id": banner_file_id,
                "date_added": current_time
            }
            await self.db.custom_banners.update_one(
                {"anime_name": anime_name},
                {"$set": banner_data},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error adding custom banner: {str(e)}", "error")
            return False

    async def get_custom_banner(self, anime_name):
        """Get custom banner for anime"""
        try:
            if self.db is None:
                await self.connect()
            banner = await self.db.custom_banners.find_one({"anime_name": anime_name})
            return banner["banner_file_id"] if banner else None
        except Exception as e:
            await rep.report(f"Error getting custom banner: {str(e)}", "error")
            return None

    async def get_all_custom_banners(self):
        """Get all custom banners"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.custom_banners.find({})
            banners = []
            async for banner in cursor:
                banners.append({
                    "anime_name": banner["anime_name"],
                    "banner_file_id": banner["banner_file_id"],
                    "date_added": banner.get("date_added", "Unknown")
                })
            return banners
        except Exception as e:
            await rep.report(f"Error getting all banners: {str(e)}", "error")
            return []

    async def remove_custom_banner(self, anime_name):
        """Remove custom banner"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.custom_banners.delete_one({"anime_name": anime_name})
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing banner: {str(e)}", "error")
            return False

    # SETTINGS MANAGEMENT
    async def set_del_timer(self, duration):
        """Set auto-delete timer"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.settings.update_one(
                {"key": "del_timer"},
                {"$set": {"key": "del_timer", "value": str(duration)}},
                upsert=True
            )
        except Exception as e:
            await rep.report(f"Error setting delete timer: {str(e)}", "error")

    async def get_del_timer(self):
        """Get auto-delete timer"""
        try:
            if self.db is None:
                await self.connect()
            setting = await self.db.settings.find_one({"key": "del_timer"})
            return int(setting["value"]) if setting else 600  # Default 10 minutes
        except Exception as e:
            await rep.report(f"Error getting delete timer: {str(e)}", "error")
            return 600

    # HELPER METHODS
    def clean_name_for_matching(self, name):
        """Clean name for matching"""
        # Remove common patterns
        name = re.sub(r'\[.*?\]', '', name)  # Remove brackets
        name = re.sub(r'\(.*?\)', '', name)  # Remove parentheses
        name = re.sub(r'[_\-\.]', ' ', name)  # Replace separators with spaces
        name = re.sub(r'\s+', ' ', name)  # Multiple spaces to single
        return name.strip()

# Create database instance
db = Database()
