# modules/update_handler.py
import os
import asyncio
from pyrogram import filters, Client
from asyncio.subprocess import PIPE, create_subprocess_exec
from bot import Var
from signal import SIGKILL

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
        await run_cmd("git", "config", "--global", "user.email", "ushachand962@gmail.com")
        await run_cmd("git", "config", "--global", "user.name", "incredaimaso")
        await run_cmd("git", "remote", "add", "origin", UPSTREAM_REPO)

    # Fetch latest commits
    await run_cmd("git", "fetch", "origin", UPSTREAM_BRANCH)

    # Compare local and remote
    _, local = await run_cmd("git", "rev-parse", "HEAD")
    _, remote = await run_cmd("git", "rev-parse", f"origin/{UPSTREAM_BRANCH}")

    if local.strip() == remote.strip():
        return await status.edit("✅ <b>Already Up to Date.</b>")

    # Apply updates
    await status.edit("📥 <b>Update found! Applying updates...</b>")
    success, reset_output = await run_cmd("git", "reset", "--hard", f"origin/{UPSTREAM_BRANCH}")
    if not success:
        return await status.edit(f"❌ Failed to apply updates:\n<pre>{reset_output}</pre>")

    # Get commit info and diff
    _, commit_info = await run_cmd("git", "log", "-1", "--pretty=format:%h - %s (%an)")
    _, diff = await run_cmd("git", "diff", "--stat", "HEAD~1..HEAD")

    # Save only chat/message info for post-restart edit
    import aiofiles
    async with aiofiles.open(".restartmsg", "w") as f:
        await f.write(f"{status.chat.id}\n{status.id}\n")

    # Show update info before restart
    await status.edit(
        f"✅ <b>Updated!</b>\n\n"
        f"<b>Latest Commit:</b>\n<pre>{commit_info}</pre>\n\n"
        f"<b>Changes:</b>\n<pre>{diff}</pre>\n\n♻️ <b>Restarting bot...</b>"
    )

    # Optional cleanup (FFmpeg processes etc.)
    try:
        from your_bot_cleanup_module import sch, clean_up, ffpids_cache, LOGS, kill
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
        pass

    # Restart bot
    os.execvp("python3", ["python3", "-m", "bot"])
