# Shell

import subprocess
from pyrogram import filters
from bot import Var

@bot.on_message(filters.command("shell") & filters.user(Var.OWNER_ID))
async def shell_handler(client, message):
    cmd = message.text.split(" ", 1)
    
    if len(cmd) == 1:
        return await message.reply("Usage: `/shell <command>`", quote=True)
    
    command = cmd[1]

    try:
        result = subprocess.getoutput(command)
        if not result:
            result = "✅ Command executed with no output."

        if len(result) > 4000:
            return await message.reply_document(
                document=("output.txt", result.encode()),
                caption="📄 Output too long — sent as file."
            )

        await message.reply(f"```\n{result}\n```", quote=True)

    except Exception as e:
        await message.reply(f"❌ Error:\n```\n{e}\n```", quote=True)

# Eval 

import re
import io
import contextlib

@bot.on_message(filters.command("eval") & filters.user(Var.OWNER_ID))
async def eval_handler(client, message):
    text = message.text

    # Extract code from triple backticks if present
    pattern = r"```(?:python)?\n([\s\S]+?)```"
    match = re.search(pattern, text)

    if match:
        code = match.group(1)
    else:
        parts = text.split(" ", 1)
        if len(parts) == 1:
            return await message.reply("Usage: `/eval <python code>` or ```python\nprint('hi')```")
        code = parts[1]

    # Prepare execution
    stdout = io.StringIO()
    local_vars = {}

    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, {"bot": bot, "client": client, "message": message}, local_vars)

        output = stdout.getvalue() or "✅ Executed with no output."

        if len(output) > 4000:
            return await message.reply_document(
                document=("eval.txt", output.encode()),
                caption="📦 Output too long — sent as file."
            )

        await message.reply(f"```\n{output}\n```")

    except Exception as e:
        await message.reply(f"❌ Error:\n```\n{e}\n```")
