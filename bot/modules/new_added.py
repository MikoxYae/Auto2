# Created a update command fetch latest commits or updates from github repository and restart bot with applied changes
# update handler
# Self-contained Update Handler
# Credits: Xen & Incredaimaso ❤️

import os
import asyncio
from pyrogram import filters, Client
from asyncio.subprocess import PIPE, create_subprocess_exec
from config import Var  # your admin ID or list
from signal import SIGKILL
import aiofiles

UPSTREAM_REPO = os.getenv("UPSTREAM_REPO")
UPSTREAM_BRANCH = os.getenv("UPSTREAM_BRANCH", "main")


async def run_cmd(*cmd):
    proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    return proc.returncode == 0, (stdout or stderr).decode().strip()


@Client.on_message(filters.command("update") & filters.user(Var.OWNER_ID))
async def update_handler(client, message):
    if not UPSTREAM_REPO:
        return await message.reply("⚠️ <b>UPSTREAM_REPO not set in environment.</b>")

    status = await message.reply("<i>Checking for updates...</i>")

    # Ensure .git exists
    if not os.path.exists(".git"):
        await run_cmd("git", "init", "-q")
        await run_cmd("git", "config", "--global", "user.email", "bot@example.com")
        await run_cmd("git", "config", "--global", "user.name", "AnimeBot")
        await run_cmd("git", "remote", "add", "origin", UPSTREAM_REPO)

    # Fetch latest commits
    await run_cmd("git", "fetch", "origin", UPSTREAM_BRANCH)

    # Compare local and remote HEAD
    _, local = await run_cmd("git", "rev-parse", "HEAD")
    _, remote = await run_cmd("git", "rev-parse", f"origin/{UPSTREAM_BRANCH}")

    if local.strip() == remote.strip():
        return await status.edit("✅ <b>Already Up to Date.</b>")

    # Apply updates: reset hard to remote branch
    await status.edit("📥 <b>Update found! Applying updates...</b>")
    success, reset_output = await run_cmd("git", "reset", "--hard", f"origin/{UPSTREAM_BRANCH}")
    if not success:
        return await status.edit(f"❌ Failed to apply updates:\n<pre>{reset_output}</pre>")

    # Get latest commit info and diff
    _, commit_info = await run_cmd("git", "log", "-1", "--pretty=format:%h - %s (%an)")
    _, diff = await run_cmd("git", "diff", "--stat", "HEAD~1..HEAD")

    # Save for post-restart edit
    async with aiofiles.open(".restartmsg", "w") as f:
        await f.write(f"{status.chat.id}\n{status.id}\n{commit_info}\n{diff}")

    # Show update info before restart
    await status.edit(
        f"✅ <b>Uᴘᴅᴀᴛᴇᴅ:</b>\n\n"
        f"<b>Latest Commit:</b>\n<pre>{commit_info}</pre>\n\n"
        f"<b>Changes:</b>\n<pre>{diff}</pre>\n\n♻️ <b>Restarting bot...</b>"
    )

    # Optional cleanup: kill ffmpeg or tracked child processes
    try:
        from your_bot_cleanup_module import sch, clean_up, ffpids_cache, LOGS, kill  # adjust imports
        if sch.running:
            sch.shutdown(wait=False)
        await clean_up()
        if ffpids_cache:
            for pid in ffpids_cache:
                try:
                    LOGS.info(f"Killing Process ID : {pid}")
                    kill(pid, SIGKILL)
                except:
                    continue
    except:
        pass  # skip if cleanup not used

    # Restart bot
    os.execvp("python3", ["python3", "-m", "bot"])


# Post-restart editor: call this in bot startup
async def handle_restart_message(bot: Client):
    if not os.path.exists(".restartmsg"):
        return
    async with aiofiles.open(".restartmsg", "r") as f:
        data = (await f.read()).split("\n", 3)
        chat_id, msg_id, commit_info, diff = int(data[0]), int(data[1]), data[2], data[3]

    try:
        await bot.edit_message_text(
            chat_id,
            msg_id,
            f"✅ <b>Restarted With Latest Commits</b>\n\n"
            f"<b>Latest Commit:</b>\n<pre>{commit_info}</pre>\n\n"
            f"<b>Changes:</b>\n<pre>{diff}</pre>"
        )
    except Exception as e:
        print(f"Failed to edit restart message: {e}")

    os.remove(".restartmsg")
