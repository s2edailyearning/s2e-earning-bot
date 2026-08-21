
import os
import json
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===== CONFIG =====
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# HARDCODED CHANNEL IDs - YOUR 3 CHANNELS - NO COMMAND NEEDED!
DEFAULT_SCREENSHOT_CHANNEL = -1004428587527  # TASK Screenshots
DEFAULT_WITHDRAW_CHANNEL = -1004319888475   # S2E Withdrawal
DEFAULT_JOIN_CHANNEL = -1004352241439       # S2E Member details

# Load from env if exists, else use hardcoded
SCREENSHOT_CHANNEL = int(os.environ.get("SCREENSHOT_CHANNEL", str(DEFAULT_SCREENSHOT_CHANNEL)))
WITHDRAW_CHANNEL = int(os.environ.get("WITHDRAW_CHANNEL", str(DEFAULT_WITHDRAW_CHANNEL)))
JOIN_CHANNEL = int(os.environ.get("JOIN_CHANNEL", str(DEFAULT_JOIN_CHANNEL)))

ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "7256515560").split(",") if x.strip().isdigit()]

CONFIG_FILE = "channels_config.json"

# Save config
def save_config():
    data = {
        "screenshot": SCREENSHOT_CHANNEL,
        "withdraw": WITHDRAW_CHANNEL,
        "join": JOIN_CHANNEL
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except: pass

def load_config():
    global SCREENSHOT_CHANNEL, WITHDRAW_CHANNEL, JOIN_CHANNEL
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                SCREENSHOT_CHANNEL = data.get("screenshot", SCREENSHOT_CHANNEL)
                WITHDRAW_CHANNEL = data.get("withdraw", WITHDRAW_CHANNEL)
                JOIN_CHANNEL = data.get("join", JOIN_CHANNEL)
    except: pass
    # If env says use default, ensure hardcoded
    if SCREENSHOT_CHANNEL == 0:
        SCREENSHOT_CHANNEL = DEFAULT_SCREENSHOT_CHANNEL
    if WITHDRAW_CHANNEL == 0:
        WITHDRAW_CHANNEL = DEFAULT_WITHDRAW_CHANNEL
    if JOIN_CHANNEL == 0:
        JOIN_CHANNEL = DEFAULT_JOIN_CHANNEL

load_config()
save_config()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask for Render keepalive
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "S2E Bot V30 Live - Channels Hardcoded!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# Helpers
def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📋 Pending Daily (0)", callback_data="pending"),
             InlineKeyboardButton("💰 Withdraw (0)", callback_data="withdraw")],
            [InlineKeyboardButton("⏰ Today's Tasks", callback_data="tasks"),
             InlineKeyboardButton("🏦 Promo Campaigns", callback_data="promo")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats"),
             InlineKeyboardButton("🚫 Banned List", callback_data="banned")],
            [InlineKeyboardButton("📋 Menu", callback_data="menu")]
        ]
        await update.message.reply_text(
            f"S2E Admin Panel V30\n\n"
            f"✅ Screenshot: {SCREENSHOT_CHANNEL}\n"
            f"✅ Withdraw: {WITHDRAW_CHANNEL}\n"
            f"✅ Join Log: {JOIN_CHANNEL}\n\n"
            f"Channels auto-set! Use /channels_status to verify",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # Auto log to join channel if configured
        try:
            if JOIN_CHANNEL:
                await context.bot.send_message(
                    JOIN_CHANNEL,
                    f"🟢 Bot Started V30\nAdmin: {user_id}\nScreenshot: {SCREENSHOT_CHANNEL}"
                )
        except Exception as e:
            logger.error(f"Join channel log failed: {e}")
    else:
        await update.message.reply_text("Welcome to S2E Daily Earning Bot! Use /tasks")

async def set_screenshot_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global SCREENSHOT_CHANNEL
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(f"Current: {SCREENSHOT_CHANNEL}\nUsage: /set_screenshot_channel -100xxx")
        return
    try:
        SCREENSHOT_CHANNEL = int(context.args[0])
        save_config()
        await update.message.reply_text(f"✅ Screenshot channel set: {SCREENSHOT_CHANNEL}")
        # Test send
        try:
            await context.bot.send_message(SCREENSHOT_CHANNEL, "✅ Screenshot Channel Connected - V30")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Set but cannot post, check admin: {e}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def set_withdraw_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WITHDRAW_CHANNEL
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(f"Current: {WITHDRAW_CHANNEL}")
        return
    try:
        WITHDRAW_CHANNEL = int(context.args[0])
        save_config()
        await update.message.reply_text(f"✅ Withdraw channel set: {WITHDRAW_CHANNEL}")
        try:
            await context.bot.send_message(WITHDRAW_CHANNEL, "✅ Withdraw Channel Connected - V30")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Set but cannot post: {e}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def set_join_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global JOIN_CHANNEL
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(f"Current: {JOIN_CHANNEL}")
        return
    try:
        JOIN_CHANNEL = int(context.args[0])
        save_config()
        await update.message.reply_text(f"✅ Join channel set: {JOIN_CHANNEL}")
        try:
            await context.bot.send_message(JOIN_CHANNEL, "✅ Member Log Channel Connected - V30")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Set but cannot post: {e}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def channels_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = (
        f"📡 *Channels Status V30*\n\n"
        f"📸 Screenshot: `{SCREENSHOT_CHANNEL}`\n"
        f"{'✅' if SCREENSHOT_CHANNEL else '❌'} {'Set' if SCREENSHOT_CHANNEL else 'Not Set'}\n\n"
        f"💸 Withdraw: `{WITHDRAW_CHANNEL}`\n"
        f"{'✅' if WITHDRAW_CHANNEL else '❌'} {'Set' if WITHDRAW_CHANNEL else 'Not Set'}\n\n"
        f"👥 Join Log: `{JOIN_CHANNEL}`\n"
        f"{'✅' if JOIN_CHANNEL else '❌'} {'Set' if JOIN_CHANNEL else 'Not Set'}\n\n"
        f"_Hardcoded V30 - No need to set manually_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    # Test all
    for name, cid in [("Screenshot", SCREENSHOT_CHANNEL), ("Withdraw", WITHDRAW_CHANNEL), ("Join", JOIN_CHANNEL)]:
        try:
            if cid:
                await context.bot.send_message(cid, f"✅ Test from /channels_status - {name} OK V30")
        except Exception as e:
            await update.message.reply_text(f"❌ {name} failed: {e}")

# Main bot
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return
    
    # Start Flask in thread (for Render)
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_screenshot_channel", set_screenshot_channel))
    application.add_handler(CommandHandler("set_withdraw_channel", set_withdraw_channel))
    application.add_handler(CommandHandler("set_join_channel", set_join_channel))
    application.add_handler(CommandHandler("channels_status", channels_status))
    
    logger.info(f"Bot V30 Starting with channels: {SCREENSHOT_CHANNEL}, {WITHDRAW_CHANNEL}, {JOIN_CHANNEL}")
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
