#!/usr/bin/env python3
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging
import json
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
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"
SAVED_USERS_FILE = "saved_users.json"

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
    except:
        pass

def load_banned():
    try:
        if os.path.exists(BANNED_FILE):
            with open(BANNED_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()

def save_banned(banned):
    try:
        with open(BANNED_FILE, 'w') as f:
            json.dump(list(banned), f)
    except:
        pass

def load_saved_users():
    """Load all saved user IDs from groups"""
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
# SAVE USER ID AUTOMATICALLY
# ============================================================
async def save_user_id(user_id, username, first_name, chat_id, chat_title):
    """Save user ID to database"""
    saved_users = load_saved_users()
    
    if str(user_id) not in saved_users:
        saved_users[str(user_id)] = {
            "id": user_id,
            "username": username,
            "name": first_name,
            "groups": []
        }
    
    # Add group if not exists
    group_info = {"chat_id": chat_id, "chat_title": chat_title, "last_seen": datetime.now().isoformat()}
    existing_group = None
    for i, g in enumerate(saved_users[str(user_id)]["groups"]):
        if g["chat_id"] == chat_id:
            existing_group = i
            break
    
    if existing_group is not None:
        saved_users[str(user_id)]["groups"][existing_group]["last_seen"] = datetime.now().isoformat()
    else:
        saved_users[str(user_id)]["groups"].append(group_info)
    
    # Update username if changed
    if username:
        saved_users[str(user_id)]["username"] = username
    saved_users[str(user_id)]["name"] = first_name
    
    save_saved_users(saved_users)

# ============================================================
# MESSAGE HANDLER - AUTO SAVE USER ID
# ============================================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto save user ID when they send message"""
    if not update.message:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    if not user or not chat:
        return
    
    # Skip if user is bot
    if user.is_bot:
        return
    
    # Save user ID
    await save_user_id(
        user_id=user.id,
        username=user.username or "NoUsername",
        first_name=user.first_name or "User",
        chat_id=chat.id,
        chat_title=chat.title or "Private Chat"
    )
    
    # Log for owner
    logger.info(f"Saved user: {user.id} (@{user.username}) in {chat.title}")

# ============================================================
# /banall COMMAND - BAN ALL SAVED USERS
# ============================================================
async def banall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Only owner can use this command
    if user_id != OWNER_ID:
        await update.message.reply_text(
            format_with_emojis("❌ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝! 𝐎𝐧𝐥𝐲 𝐨𝐰𝐧𝐞𝐫 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬."),
            parse_mode="HTML"
        )
        return
    
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    
    # Check if bot is admin
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
            format_with_emojis(f"❌ 𝐄𝐫𝐫𝐨𝐫: {str(e)}"),
            parse_mode="HTML"
        )
        return
    
    # Load saved users
    saved_users = load_saved_users()
    
    if not saved_users:
        await update.message.reply_text(
            format_with_emojis("📭 𝐍𝐨 𝐮𝐬𝐞𝐫𝐬 𝐬𝐚𝐯𝐞𝐝 𝐲𝐞𝐭! 𝐖𝐚𝐢𝐭 𝐟𝐨𝐫 𝐬𝐨𝐦𝐞𝐨𝐧𝐞 𝐭𝐨 𝐬𝐞𝐧𝐝 𝐚 𝐦𝐞𝐬𝐬𝐚𝐠𝐞."),
            parse_mode="HTML"
        )
        return
    
    # Get current group members (to ban)
    try:
        members = []
        async for member in context.bot.get_chat_members(chat_id):
            if member.user.id != context.bot.id and not member.user.is_bot:
                members.append(member.user.id)
    except:
        members = []
    
    # Filter: only ban users who are saved AND in current group
    saved_ids = set(saved_users.keys())
    to_ban = [uid for uid in members if str(uid) in saved_ids]
    
    if not to_ban:
        await update.message.reply_text(
            format_with_emojis("📭 𝐍𝐨 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬 𝐟𝐨𝐮𝐧𝐝 𝐢𝐧 𝐭𝐡𝐢𝐬 𝐠𝐫𝐨𝐮𝐩!"),
            parse_mode="HTML"
        )
        return
    
    status_msg = await update.message.reply_text(
        format_with_emojis(f"""🔥 𝐁𝐀𝐍𝐍𝐈𝐍𝐆 𝐀𝐋𝐋 𝐒𝐀𝐕𝐄𝐃 𝐔𝐒𝐄𝐑𝐒

👥 𝐓𝐨𝐭𝐚𝐥 𝐭𝐨 𝐛𝐚𝐧: {stylish(str(len(to_ban)))}
📊 𝐆𝐫𝐨𝐮𝐩: {stylish(chat.title)}
⚡ 𝐒𝐭𝐚𝐭𝐮𝐬: {stylish('In Progress...')}"""),
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
            logger.error(f"Failed to ban {uid}: {e}")
        
        # Show progress every 10 bans
        if (i + 1) % 5 == 0 or (i + 1) == len(to_ban):
            progress = int((i + 1) / len(to_ban) * 100)
            elapsed = (datetime.now() - start_time).seconds
            await status_msg.edit_text(
                format_with_emojis(f"""🔥 𝐁𝐀𝐍𝐍𝐈𝐍𝐆 𝐀𝐋𝐋 𝐒𝐀𝐕𝐄𝐃 𝐔𝐒𝐄𝐑𝐒

👥 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {stylish(str(banned_count))}/{stylish(str(len(to_ban)))} ({stylish(str(progress))}%)
✅ 𝐁𝐚𝐧𝐧𝐞𝐝: {stylish(str(banned_count))}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {stylish(str(failed_count))}
⏱️ 𝐓𝐢𝐦𝐞: {stylish(str(elapsed))}𝐬"""),
                parse_mode="HTML"
            )
        
        await asyncio.sleep(0.05)
    
    elapsed = (datetime.now() - start_time).seconds
    final_msg = f"""✅ 𝐁𝐀𝐍 𝐀𝐋𝐋 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃!

📊 𝐆𝐫𝐨𝐮𝐩: {stylish(chat.title)}
👥 𝐓𝐨𝐭𝐚𝐥 𝐁𝐚𝐧𝐧𝐞𝐝: {stylish(str(banned_count))}
❌ 𝐅𝐚𝐢𝐥𝐞𝐝: {stylish(str(failed_count))}
⏱️ 𝐓𝐢𝐦𝐞: {stylish(str(elapsed))}𝐬

⚡ 𝐀𝐥𝐥 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬 𝐡𝐚𝐯𝐞 𝐛𝐞𝐞𝐧 𝐛𝐚𝐧𝐧𝐞𝐝!"""
    
    await status_msg.edit_text(format_with_emojis(final_msg), parse_mode="HTML")

# ============================================================
# /savedusers COMMAND - Show all saved users
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
            format_with_emojis("📭 𝐍𝐨 𝐮𝐬𝐞𝐫𝐬 𝐬𝐚𝐯𝐞𝐝 𝐲𝐞𝐭."),
            parse_mode="HTML"
        )
        return
    
    msg = "👥 𝐒𝐀𝐕𝐄𝐃 𝐔𝐒𝐄𝐑𝐒\n━━━━━━━━━━━━━━━━━━\n"
    for uid, data in list(saved_users.items())[:50]:
        username = data.get("username", "N/A")
        name = data.get("name", "Unknown")
        groups = len(data.get("groups", []))
        msg += f"🆔 {uid} | @{username} | {name} | {groups} groups\n"
    
    if len(saved_users) > 50:
        msg += f"\n... 𝐚𝐧𝐝 {len(saved_users) - 50} 𝐦𝐨𝐫𝐞"
    
    msg += f"\n📊 𝐓𝐨𝐭𝐚𝐥: {len(saved_users)}"
    
    await update.message.reply_text(
        format_with_emojis(msg),
        parse_mode="HTML"
    )

# ============================================================
# /clearsaved COMMAND - Clear all saved users
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
        format_with_emojis("✅ 𝐀𝐥𝐥 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬 𝐡𝐚𝐯𝐞 𝐛𝐞𝐞𝐧 𝐜𝐥𝐞𝐚𝐫𝐞𝐝!"),
        parse_mode="HTML"
    )

# ============================================================
# /start COMMAND
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    msg = """🔥 𝐁𝐀𝐍 𝐀𝐋𝐋 𝐁𝐎𝐓

📌 𝐇𝐨𝐰 𝐢𝐭 𝐰𝐨𝐫𝐤𝐬:
1️⃣ 𝐁𝐨𝐭 𝐚𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜𝐚𝐥𝐥𝐲 𝐬𝐚𝐯𝐞𝐬 𝐞𝐯𝐞𝐫𝐲 𝐮𝐬𝐞𝐫 𝐰𝐡𝐨 𝐬𝐞𝐧𝐝𝐬 𝐚 𝐦𝐞𝐬𝐬𝐚𝐠𝐞
2️⃣ 𝐔𝐬𝐞 /𝐛𝐚𝐧𝐚𝐥𝐥 𝐭𝐨 𝐛𝐚𝐧 𝐀𝐋𝐋 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬

👑 𝐎𝐰𝐧𝐞𝐫 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬:
/𝐛𝐚𝐧𝐚𝐥𝐥 - 𝐁𝐚𝐧 𝐚𝐥𝐥 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬
/𝐬𝐚𝐯𝐞𝐝𝐮𝐬𝐞𝐫𝐬 - 𝐕𝐢𝐞𝐰 𝐚𝐥𝐥 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬
/𝐜𝐥𝐞𝐚𝐫𝐬𝐚𝐯𝐞𝐝 - 𝐂𝐥𝐞𝐚𝐫 𝐬𝐚𝐯𝐞𝐝 𝐮𝐬𝐞𝐫𝐬

⚠️ 𝐁𝐨𝐭 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐚𝐝𝐦𝐢𝐧 𝐰𝐢𝐭𝐡 𝐛𝐚𝐧 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧!"""
    
    await update.message.reply_text(
        format_with_emojis(msg),
        parse_mode="HTML"
    )

# ============================================================
# MAIN
# ============================================================
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("banall", banall))
    application.add_handler(CommandHandler("savedusers", savedusers))
    application.add_handler(CommandHandler("clearsaved", clearsaved))
    
    # Message handler - auto save user IDs
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    
    logger.info("Ban All Bot Started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
