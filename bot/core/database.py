from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import re
import time
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

    async def present_user(self, user_id):
        """Check if user exists in database"""
        try:
            if self.db is None:
                await self.connect()
            user = await self.db.users.find_one({"user_id": user_id})
            return bool(user)
        except Exception as e:
            await rep.report(f"Error checking user presence: {str(e)}", "error")
            return False

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
        """Remove pending connection for user"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.pending_connections.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing pending connection: {str(e)}", "error")
            return False

    def clean_name_for_matching(self, name):
        """Clean anime name for better matching"""
        import re
        # Remove common anime release tags
        patterns_to_remove = [
            r'\[.*?\]',  # Remove anything in brackets
            r'\(.*?\)',  # Remove anything in parentheses  
            r'- \d+',    # Remove episode numbers
            r'S\d+',     # Remove season numbers
            r'1080p|720p|480p|HEVC|x264|x265',  # Remove quality tags
            r'SubsPlease|Erai-raws|HorribleSubs',  # Remove group tags
        ]
        
        cleaned = name
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()

    async def get_del_timer(self):
        """Get auto-delete timer"""
        try:
            if self.db is None:
                await self.connect()
            settings = await self.db.settings.find_one({"key": "del_timer"})
            return int(settings.get("value", 600)) if settings else 600
        except Exception as e:
            await rep.report(f"Error getting delete timer: {str(e)}", "error")
            return 600

    async def set_del_timer(self, timer):
        """Set auto-delete timer"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.settings.update_one(
                {"key": "del_timer"},
                {"$set": {"key": "del_timer", "value": timer}},
                upsert=True
            )
        except Exception as e:
            await rep.report(f"Error setting delete timer: {str(e)}", "error")

    # CUSTOM BANNERS MANAGEMENT
    async def add_custom_banner(self, anime_name, banner_file_id):
        """Add custom banner for anime"""
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

    async def remove_custom_banner(self, anime_name):
        """Remove custom banner for anime"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.custom_banners.delete_one({"anime_name": anime_name})
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing custom banner: {str(e)}", "error")
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
                    'anime_name': banner["anime_name"],
                    'banner_file_id': banner["banner_file_id"],
                    'date_added': banner.get("date_added", "Unknown")
                })
            return banners
        except Exception as e:
            await rep.report(f"Error getting all custom banners: {str(e)}", "error")
            return []

    # FORCE SUBSCRIPTION METHODS
    async def add_channel(self, channel_id):
        """Add force subscription channel"""
        try:
            if self.db is None:
                await self.connect()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            channel_data = {
                "channel_id": channel_id,
                "mode": "off",  # Default mode is off
                "date_added": current_time
            }
            await self.db.force_sub_channels.update_one(
                {"channel_id": channel_id},
                {"$set": channel_data},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error adding force sub channel: {str(e)}", "error")
            return False

    async def rem_channel(self, channel_id):
        """Remove force subscription channel"""
        try:
            if self.db is None:
                await self.connect()
            result = await self.db.force_sub_channels.delete_one({"channel_id": channel_id})
            # Also remove any join requests for this channel
            await self.db.join_request_channels.delete_many({"channel_id": channel_id})
            # Remove invite links data
            await self.db.force_sub_channels.update_one(
                {"channel_id": channel_id},
                {"$unset": {"invite_link": "", "link_expire_date": ""}}
            )
            return result.deleted_count > 0
        except Exception as e:
            await rep.report(f"Error removing force sub channel: {str(e)}", "error")
            return False

    async def show_channels(self):
        """Get all force subscription channels"""
        try:
            if self.db is None:
                await self.connect()
            cursor = self.db.force_sub_channels.find({})
            channels = []
            async for channel in cursor:
                channels.append(channel["channel_id"])
            return channels
        except Exception as e:
            await rep.report(f"Error getting force sub channels: {str(e)}", "error")
            return []

    async def set_channel_mode(self, channel_id, mode):
        """Set channel mode (on/off for request mode)"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.force_sub_channels.update_one(
                {"channel_id": channel_id},
                {"$set": {"mode": mode}},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error setting channel mode: {str(e)}", "error")
            return False

    async def get_channel_mode(self, channel_id):
        """Get channel mode"""
        try:
            if self.db is None:
                await self.connect()
            channel = await self.db.force_sub_channels.find_one({"channel_id": channel_id})
            return channel.get("mode", "off") if channel else "off"
        except Exception as e:
            await rep.report(f"Error getting channel mode: {str(e)}", "error")
            return "off"

    async def reqChannel_exist(self, channel_id):
        """Check if channel exists in force sub list"""
        try:
            if self.db is None:
                await self.connect()
            channel_ids = await self.show_channels()
            return int(channel_id) in channel_ids
        except Exception as e:
            await rep.report(f"Error checking if channel exists: {str(e)}", "error")
            return False

    # FORCE SUBSCRIPTION REQUEST MODE METHODS
    async def store_invite_link(self, channel_id, invite_link, expire_date=None):
        """Store invite link for a channel"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.force_sub_channels.update_one(
                {"channel_id": channel_id},
                {"$set": {
                    "invite_link": invite_link,
                    "link_expire_date": expire_date,
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error storing invite link: {str(e)}", "error")
            return False

    async def get_invite_link(self, channel_id):
        """Get stored invite link for a channel"""
        try:
            if self.db is None:
                await self.connect()
            data = await self.db.force_sub_channels.find_one({"channel_id": channel_id})
            if data and data.get('invite_link'):
                # Check if link has expired
                if data.get('link_expire_date'):
                    if int(time.time()) >= data['link_expire_date']:
                        return None
                return data['invite_link']
            return None
        except Exception as e:
            await rep.report(f"Error getting invite link: {str(e)}", "error")
            return None

    async def req_user(self, channel_id, user_id):
        """Add user to join request list"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.join_request_channels.update_one(
                {"channel_id": int(channel_id)},
                {"$addToSet": {"user_ids": int(user_id)}},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error adding user to request list: {str(e)}", "error")
            return False

    async def del_req_user(self, channel_id, user_id):
        """Remove user from join request list"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.join_request_channels.update_one(
                {"channel_id": int(channel_id)},
                {"$pull": {"user_ids": int(user_id)}}
            )
            return True
        except Exception as e:
            await rep.report(f"Error removing user from request list: {str(e)}", "error")
            return False

    async def req_user_exist(self, channel_id, user_id):
        """Check if user exists in join request list"""
        try:
            if self.db is None:
                await self.connect()
            found = await self.db.join_request_channels.find_one({
                "channel_id": int(channel_id),
                "user_ids": int(user_id)
            })
            return bool(found)
        except Exception as e:
            await rep.report(f"Error checking request list: {str(e)}", "error")
            return False

    # TOKEN MANAGEMENT METHODS
    async def store_token(self, user_id, token, expire_seconds):
        """Store verification token with expiry"""
        try:
            if self.db is None:
                await self.connect()
            expire_time = time.time() + expire_seconds
            await self.db.tokens.update_one(
                {"user_id": user_id},
                {"$set": {
                    "token": token,
                    "expire_time": expire_time,
                    "created_time": time.time()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error storing token: {str(e)}", "error")
            return False

    async def is_token_valid(self, token):
        """Check if token exists and is not expired"""
        try:
            if self.db is None:
                await self.connect()
            current_time = time.time()
            token_data = await self.db.tokens.find_one({
                "token": token,
                "expire_time": {"$gt": current_time}
            })
            return bool(token_data)
        except Exception as e:
            await rep.report(f"Error validating token: {str(e)}", "error")
            return False

    async def remove_token(self, token):
        """Remove token after successful verification"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.tokens.delete_one({"token": token})
            return True
        except Exception as e:
            await rep.report(f"Error removing token: {str(e)}", "error")
            return False

    async def get_user_token(self, user_id):
        """Get user's current valid token"""
        try:
            if self.db is None:
                await self.connect()
            current_time = time.time()
            token_data = await self.db.tokens.find_one({
                "user_id": user_id,
                "expire_time": {"$gt": current_time}
            })
            if token_data:
                return token_data.get("token")
            return None
        except Exception as e:
            await rep.report(f"Error getting user token: {str(e)}", "error")
            return None

    # VERIFICATION STATUS METHODS
    async def get_verify_status(self, user_id):
        """Get user verification status"""
        try:
            if self.db is None:
                await self.connect()
            user = await self.db.users.find_one({"user_id": user_id})
            if user and "verify_status" in user:
                return user["verify_status"]
            return {
                'is_verified': False,
                'verified_time': 0,
                'verify_token': "",
                'link': ""
            }
        except Exception as e:
            await rep.report(f"Error getting verify status: {str(e)}", "error")
            return {
                'is_verified': False,
                'verified_time': 0,
                'verify_token': "",
                'link': ""
            }

    async def update_verify_status(self, user_id, verify_token="", is_verified=False, verified_time=0, link=""):
        """Update user verification status"""
        try:
            if self.db is None:
                await self.connect()
            verify_status = {
                'verify_token': verify_token,
                'is_verified': is_verified,
                'verified_time': verified_time,
                'link': link
            }
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"verify_status": verify_status}},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error updating verify status: {str(e)}", "error")
            return False

    async def get_verify_count(self, user_id):
        """Get user verification count"""
        try:
            if self.db is None:
                await self.connect()
            user = await self.db.verify_counts.find_one({"user_id": user_id})
            if user:
                return user.get("verify_count", 0)
            return 0
        except Exception as e:
            await rep.report(f"Error getting verify count: {str(e)}", "error")
            return 0

    async def set_verify_count(self, user_id, count):
        """Set user verification count"""
        try:
            if self.db is None:
                await self.connect()
            await self.db.verify_counts.update_one(
                {"user_id": user_id},
                {"$set": {"verify_count": count}},
                upsert=True
            )
            return True
        except Exception as e:
            await rep.report(f"Error setting verify count: {str(e)}", "error")
            return False

# Create database instance
db = Database()
