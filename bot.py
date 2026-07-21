#!/usr/bin/env python3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging
import json
import os
import random
import asyncio
from datetime import datetime
from flask import Flask
import threading

# ============================================================
# FLASK APP
# ============================================================
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "✅ Ban All Bot is running!", 200

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
# STORAGE
# ============================================================
SAVED_USERS_FILE = "saved_users.json"

def load_saved_users():
    try:
        if os.path.exists(SAVED_USERS_FILE):
            with open(SAVED_USERS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_saved_users(saved_users):
    try:
        with open(SAVED_USERS_FILE, 'w') as f:
            json.dump(saved_users, f)
    except:
        pass

# ============================================================
# SAVE USER ID
# ============================================================
async def save_user_id(user_id, username, first_name, chat_id, chat_title):
    saved_users = load_saved_users()
    
    if str(user_id) not in saved_users:
        saved_users[str(user_id)] = {
            "id": user_id,
            "username": username or "NoUsername",
            "name": first_name or "User",
            "groups": []
        }
    
    group_info = {"chat_id": chat_id, "chat_title": chat_title, "last_seen": datetime.now().isoformat()}
    
    # Check if group exists
    found = False
    for i, g in enumerate(saved_users[str(user_id)]["groups"]):
        if g["chat_id"] == chat_id:
            saved_users[str(user_id)]["groups"][i]["last_seen"] = datetime.now().isoformat()
            found = True
            break
    
    if not found:
        saved_users[str(user_id)]["groups"].append(group_info)
    
    save_saved_users(saved_users)

# ============================================================
# MESSAGE HANDLER
# ============================================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    if not user or not chat or user.is_bot:
        return
    
    await save_user_id(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        chat_id=chat.id,
        chat_title=chat.title or "Private"
    )

# ============================================================
# /banall COMMAND - FIXED
# ============================================================
async def banall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text(
            format_with_emojis("❌ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝!"),
            parse_mode="HTML"
        )
        return
    
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    
    # ✅ CHECK BOT ADMIN
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                format_with_emojis("❌ 𝐁𝐨𝐭 𝐢𝐬 𝐧𝐨𝐭 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧 𝐢𝐧 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩!"),
                parse_mode="HTML"
            )
            return
        
        if not bot_member.can_restrict_members:
            await update.message.reply_text(
                format_with_emojis("❌ 𝐁𝐨𝐭 𝐝𝐨𝐞𝐬𝐧'𝐭 𝐡𝐚𝐯𝐞 𝐛𝐚𝐧 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧!"),
                parse_mode="HTML"
            )
            return
    except Exception as e:
        await update.message.reply_text(
            format_with_emojis(f"❌ 𝐁𝐨𝐭 𝐚𝐝𝐦𝐢𝐧 𝐜𝐡𝐞𝐜𝐤 𝐟𝐚𝐢𝐥𝐞𝐝: {str(e)}"),
            parse_mode="HTML"
        )
        return
    
    saved_users = load_saved_users()
    
    if not saved_users:
        await update.message.reply_text(
            format_with_emojis("📭 𝐍𝐨 𝐮𝐬𝐞𝐫𝐬 𝐬𝐚𝐯𝐞𝐝 𝐲𝐞𝐭!"),
            parse_mode="HTML"
        )
        return
    
    # ✅ GET MEMBERS - TRY 2 METHODS
    members = []
    try:
        # Method 1: Async iterator (New API)
        async for member in context.bot.get_chat_members(chat_id):
            if member.user.id != context.bot.id and not member.user.is_bot:
                members.append(member.user.id)
    except Exception as e:
        logger.error(f"Method 1 failed: {e}")
        
        try:
            # Method 2: Try with limit (Old API fallback)
            # Note: In PTB v20+, get_chat_members_count might not exist
            # We'll use the first method with a different approach
            pass
        except Exception as e2:
            logger.error(f"Method 2 failed: {e2}")
    
    # ✅ IF MEMBERS LIST EMPTY - TRY DIRECT BAN ON SAVED USERS
    if not members:
        # Get saved user IDs
        saved_ids = list(saved_users.keys())
        
        if not saved_ids:
            await update.message.reply_text(
                format_with_emojis("📭 𝐍𝐨 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫 𝐈𝐃𝐬 𝐟𝐨𝐮𝐧𝐝!"),
                parse_mode="HTML"
            )
            return
        
        status_msg = await update.message.reply_text(
            format_with_emojis(f"🔥 𝐓𝐫𝐲𝐢𝐧𝐠 𝐭𝐨 𝐛𝐚𝐧 {len(saved_ids)} 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬..."),
            parse_mode="HTML"
        )
        
        banned_count = 0
        failed_count = 0
        start_time = datetime.now()
        
        for i, uid_str in enumerate(saved_ids):
            try:
                uid = int(uid_str)
                await context.bot.ban_chat_member(chat_id, uid)
                banned_count += 1
                await asyncio.sleep(0.1)  # Rate limit
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to ban {uid_str}: {e}")
            
            if (i + 1) % 5 == 0 or (i + 1) == len(saved_ids):
                progress = int((i + 1) / len(saved_ids) * 100)
                elapsed = (datetime.now() - start_time).seconds
                await status_msg.edit_text(
                    format_with_emojis(f"""🔥 𝐁𝐀𝐍𝐍𝐈𝐍𝐆...

👥 {banned_count}/{len(saved_ids)} ({progress}%)
✅ 𝐁𝐚𝐧𝐧𝐞𝐝: {banned_count}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {failed_count}
⏱️ {elapsed}𝐬"""),
                    parse_mode="HTML"
                )
            
            await asyncio.sleep(0.05)
        
        elapsed = (datetime.now() - start_time).seconds
        final_msg = f"""✅ 𝐁𝐀𝐍 𝐀𝐋𝐋 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃!

👥 𝐓𝐫𝐢𝐞𝐝: {len(saved_ids)}
✅ 𝐁𝐚𝐧𝐧𝐞𝐝: {banned_count}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {failed_count}
⏱️ 𝐓𝐢𝐦𝐞: {elapsed}𝐬

📌 𝐍𝐨𝐭𝐞: 𝐅𝐚𝐢𝐥𝐞𝐝 𝐮𝐬𝐞𝐫𝐬 𝐦𝐚𝐲 𝐧𝐨𝐭 𝐛𝐞 𝐢𝐧 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩."""
        
        await status_msg.edit_text(format_with_emojis(final_msg), parse_mode="HTML")
        return
    
    # ✅ NORMAL FLOW - BAN MATCHING USERS
    saved_ids = set(saved_users.keys())
    to_ban = [uid for uid in members if str(uid) in saved_ids]
    
    if not to_ban:
        await update.message.reply_text(
            format_with_emojis(f"""📭 𝐍𝐨 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬 𝐢𝐧 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩!

📊 𝐓𝐨𝐭𝐚𝐥 𝐒𝐚𝐯𝐞𝐝: {len(saved_ids)}
👥 𝐆𝐫𝐨𝐮𝐩 𝐌𝐞𝐦𝐛𝐞𝐫𝐬: {len(members)}
✅ 𝐌𝐚𝐭𝐜𝐡𝐢𝐧𝐠: 0

💡 𝐓𝐢𝐩: 𝐀𝐬𝐤 𝐮𝐬𝐞𝐫𝐬 𝐭𝐨 𝐬𝐞𝐧𝐝 𝐚 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐢𝐧 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩."""),
            parse_mode="HTML"
        )
        return
    
    status_msg = await update.message.reply_text(
        format_with_emojis(f"🔥 𝐁𝐀𝐍𝐍𝐈𝐍𝐆 {len(to_ban)} 𝐔𝐒𝐄𝐑𝐒..."),
        parse_mode="HTML"
    )
    
    banned_count = 0
    failed_count = 0
    start_time = datetime.now()
    
    for i, uid in enumerate(to_ban):
        try:
            await context.bot.ban_chat_member(chat_id, uid)
            banned_count += 1
        except Exception as e:
            failed_count += 1
        
        if (i + 1) % 5 == 0 or (i + 1) == len(to_ban):
            progress = int((i + 1) / len(to_ban) * 100)
            elapsed = (datetime.now() - start_time).seconds
            await status_msg.edit_text(
                format_with_emojis(f"""🔥 𝐁𝐀𝐍𝐍𝐈𝐍𝐆...

👥 {banned_count}/{len(to_ban)} ({progress}%)
✅ 𝐁𝐚𝐧𝐧𝐞𝐝: {banned_count}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {failed_count}
⏱️ {elapsed}𝐬"""),
                parse_mode="HTML"
            )
        
        await asyncio.sleep(0.05)
    
    elapsed = (datetime.now() - start_time).seconds
    final_msg = f"""✅ 𝐁𝐀𝐍 𝐀𝐋𝐋 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃!

👥 𝐁𝐚𝐧𝐧𝐞𝐝: {banned_count}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {failed_count}
⏱️ 𝐓𝐢𝐦𝐞: {elapsed}𝐬"""
    
    await status_msg.edit_text(format_with_emojis(final_msg), parse_mode="HTML")

# ============================================================
# /savedusers COMMAND
# ============================================================
async def savedusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text(
            format_with_emojis("❌ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝!"),
            parse_mode="HTML"
        )
        return
    
    saved_users = load_saved_users()
    
    if not saved_users:
        await update.message.reply_text(
            format_with_emojis("📭 𝐍𝐨 𝐮𝐬𝐞𝐫𝐬 𝐬𝐚𝐯𝐞𝐝."),
            parse_mode="HTML"
        )
        return
    
    msg = "👥 𝐒𝐀𝐕𝐄𝐃 𝐔𝐒𝐄𝐑𝐒\n━━━━━━━━━━━━━━━━━━\n"
    for uid, data in list(saved_users.items())[:50]:
        username = data.get("username", "N/A")
        name = data.get("name", "Unknown")
        groups = len(data.get("groups", []))
        msg += f"🆔 {uid} | @{username} | {name} | {groups}g\n"
    
    if len(saved_users) > 50:
        msg += f"\n... +{len(saved_users)-50} more"
    
    msg += f"\n📊 𝐓𝐨𝐭𝐚𝐥: {len(saved_users)}"
    
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============================================================
# /clearsaved COMMAND
# ============================================================
async def clearsaved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text(
            format_with_emojis("❌ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝!"),
            parse_mode="HTML"
        )
        return
    
    save_saved_users({})
    await update.message.reply_text(
        format_with_emojis("✅ 𝐂𝐥𝐞𝐚𝐫𝐞𝐝 𝐚𝐥𝐥 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬!"),
        parse_mode="HTML"
    )

# ============================================================
# /start COMMAND
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """🔥 𝐁𝐀𝐍 𝐀𝐋𝐋 𝐁𝐎𝐓

📌 𝐇𝐨𝐰 𝐢𝐭 𝐰𝐨𝐫𝐤𝐬:
1️⃣ 𝐀𝐮𝐭𝐨-𝐬𝐚𝐯𝐞𝐬 𝐞𝐯𝐞𝐫𝐲 𝐮𝐬𝐞𝐫
2️⃣ /𝐛𝐚𝐧𝐚𝐥𝐥 - 𝐁𝐚𝐧 𝐚𝐥𝐥

👑 𝐎𝐰𝐧𝐞𝐫 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:
/𝐛𝐚𝐧𝐚𝐥𝐥 - 𝐁𝐚𝐧 𝐚𝐥𝐥
/𝐬𝐚𝐯𝐞𝐝𝐮𝐬𝐞𝐫𝐬 - 𝐕𝐢𝐞𝐰
/𝐜𝐥𝐞𝐚𝐫𝐬𝐚𝐯𝐞𝐝 - 𝐂𝐥𝐞𝐚𝐫

⚠️ 𝐁𝐨𝐭 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐚𝐝𝐦𝐢𝐧!"""
    
    await update.message.reply_text(format_with_emojis(msg), parse_mode="HTML")

# ============================================================
# MAIN
# ============================================================
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("banall", banall))
    application.add_handler(CommandHandler("savedusers", savedusers))
    application.add_handler(CommandHandler("clearsaved", clearsaved))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    
    logger.info("Ban All Bot Started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
