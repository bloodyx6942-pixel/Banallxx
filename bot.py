#!/usr/bin/env python3
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import os
import asyncio
from datetime import datetime
from flask import Flask
import threading

# ============================================================
# FLASK APP (Render Health Check)
# ============================================================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "✅ Mass Ban Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.environ.get("OWNER_ID", 8586849798))

# ============================================================
# STYLISH CHARACTERS
# ============================================================
STYLISH = {
    'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
    'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
    'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
    'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
    'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟',
    'g': '𝐠', 'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥',
    'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
    's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱',
    'y': '𝐲', 'z': '𝐳',
    '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
    '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
}

def stylish(text):
    return ''.join(STYLISH.get(c, c) for c in text)

# ============================================================
# PREMIUM EMOJIS
# ============================================================
PREMIUM_EMOJIS = {
    "fire": {"id": "6147524086768604985", "fallback": "🔥"},
    "crown": {"id": "6147565374289220368", "fallback": "👑"},
    "cross": {"id": "6273840152980755328", "fallback": "❌"},
    "check": {"id": "6274007313107915274", "fallback": "✔️"},
    "warning": {"id": "5852873584912896283", "fallback": "⚠️"},
    "lightning": {"id": "5971944878815317190", "fallback": "⚡"},
    "flex": {"id": "6147464060305676048", "fallback": "😎"},
    "stars": {"id": "6235403472741603087", "fallback": "⭐"},
    "shield": {"id": "5449449325434266744", "fallback": "🛡️"},
    "lock": {"id": "5465443379917629504", "fallback": "🔓"},
}

def get_emoji_html(name):
    if name in PREMIUM_EMOJIS:
        data = PREMIUM_EMOJIS[name]
        return f'<tg-emoji emoji-id="{data["id"]}">{data["fallback"]}</tg-emoji>'
    return ""

def e(name):
    return get_emoji_html(name)

def get_random_emojis(count=2):
    names = list(PREMIUM_EMOJIS.keys())
    if not names:
        return ["", ""]
    import random
    selected = random.sample(names, min(count, len(names)))
    return [e(name) for name in selected]

def format_with_emojis(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():
            left, right = get_random_emojis(2)
            styled_line = stylish(line)
            result.append(f"{left} {styled_line} {right}")
        else:
            result.append(line)
    return '\n'.join(result)

# ============================================================
# MASS BAN FUNCTION
# ============================================================
async def mass_ban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text(
            format_with_emojis("𝐎𝐧𝐥𝐲 𝐨𝐰𝐧𝐞𝐫 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬 𝐜𝐨𝐦𝐦𝐚𝐧𝐝!"),
            parse_mode="HTML"
        )
        return
    
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                format_with_emojis("𝐁𝐨𝐭 𝐢𝐬 𝐧𝐨𝐭 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧 𝐢𝐧 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩!"),
                parse_mode="HTML"
            )
            return
        
        if not bot_member.can_restrict_members:
            await update.message.reply_text(
                format_with_emojis("𝐁𝐨𝐭 𝐝𝐨𝐞𝐬𝐧'𝐭 𝐡𝐚𝐯𝐞 𝐛𝐚𝐧 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧!"),
                parse_mode="HTML"
            )
            return
    except Exception as e:
        await update.message.reply_text(
            format_with_emojis(f"𝐄𝐫𝐫𝐨𝐫: {str(e)}"),
            parse_mode="HTML"
        )
        return
    
    status_msg = await update.message.reply_text(
        format_with_emojis("🔥 𝐌𝐀𝐒𝐒 𝐁𝐀𝐍 𝐒𝐓𝐀𝐑𝐓𝐄𝐃..."),
        parse_mode="HTML"
    )
    
    try:
        members = []
        async for member in context.bot.get_chat_members(chat_id):
            if member.user.id != context.bot.id and not member.user.is_bot:
                members.append(member.user.id)
        
        total_members = len(members)
        
        if total_members == 0:
            await status_msg.edit_text(
                format_with_emojis("❌ 𝐍𝐨 𝐦𝐞𝐦𝐛𝐞𝐫𝐬 𝐟𝐨𝐮𝐧𝐝!"),
                parse_mode="HTML"
            )
            return
        
        banned_count = 0
        failed_count = 0
        start_time = datetime.now()
        
        for i, member_id in enumerate(members):
            try:
                await context.bot.ban_chat_member(chat_id, member_id)
                banned_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to ban {member_id}: {e}")
            
            if (i + 1) % 10 == 0 or (i + 1) == total_members:
                progress = int((i + 1) / total_members * 100)
                elapsed = (datetime.now() - start_time).seconds
                await status_msg.edit_text(
                    format_with_emojis(f"""🔥 𝐌𝐀𝐒𝐒 𝐁𝐀𝐍 𝐈𝐍 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒

📊 𝐆𝐫𝐨𝐮𝐩: {stylish(chat.title)}
👥 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {stylish(str(banned_count))}/{stylish(str(total_members))} ({stylish(str(progress))}%)
✅ 𝐁𝐚𝐧𝐧𝐞𝐝: {stylish(str(banned_count))}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {stylish(str(failed_count))}
⏱️ 𝐄𝐥𝐚𝐩𝐬𝐞𝐝: {stylish(str(elapsed))}𝐬"""),
                    parse_mode="HTML"
                )
            
            await asyncio.sleep(0.05)
        
        elapsed = (datetime.now() - start_time).seconds
        final_msg = f"""✅ 𝐌𝐀𝐒𝐒 𝐁𝐀𝐍 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃

📊 𝐆𝐫𝐨𝐮𝐩: {stylish(chat.title)}
👥 𝐓𝐨𝐭𝐚𝐥: {stylish(str(total_members))}
✅ 𝐁𝐚𝐧𝐧𝐞𝐝: {stylish(str(banned_count))}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {stylish(str(failed_count))}
⏱️ 𝐓𝐢𝐦𝐞: {stylish(str(elapsed))}𝐬"""
        
        await status_msg.edit_text(format_with_emojis(final_msg), parse_mode="HTML")
        
    except Exception as e:
        await status_msg.edit_text(
            format_with_emojis(f"❌ 𝐄𝐫𝐫𝐨𝐫: {str(e)}"),
            parse_mode="HTML"
        )

# ============================================================
# /massban COMMAND
# ============================================================
async def massban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mass_ban_group(update, context)

# ============================================================
# /start COMMAND
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    if chat_type in ['group', 'supergroup']:
        msg = """🔥 𝐌𝐀𝐒𝐒 𝐁𝐀𝐍 𝐁𝐎𝐓

𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:
/𝐦𝐚𝐬𝐬𝐛𝐚𝐧 - 𝐁𝐚𝐧 𝐚𝐥𝐥 𝐦𝐞𝐦𝐛𝐞𝐫𝐬

⚠️ 𝐎𝐧𝐥𝐲 𝐨𝐰𝐧𝐞𝐫 𝐜𝐚𝐧 𝐮𝐬𝐞!
⚠️ 𝐁𝐨𝐭 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐚𝐝𝐦𝐢𝐧!"""
        await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")
        return
    
    msg = """🔥 𝐌𝐀𝐒𝐒 𝐁𝐀𝐍 𝐁𝐎𝐓

𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:
/𝐦𝐚𝐬𝐬𝐛𝐚𝐧 - 𝐁𝐚𝐧 𝐚𝐥𝐥 𝐦𝐞𝐦𝐛𝐞𝐫𝐬

⚠️ 𝐎𝐧𝐥𝐲 𝐨𝐰𝐧𝐞𝐫 𝐜𝐚𝐧 𝐮𝐬𝐞!"""
    
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============================================================
# MAIN
# ============================================================
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("massban", massban))
    
    logger.info("Mass Ban Bot Started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()