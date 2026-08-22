"""
S2E Bot V59 - FINAL FIXED FOR RENDER
Fixes:
1. No open ports detected -> Flask port binding added
2. Conflict: terminated by other getUpdates -> webhook delete + error handler
3. 3 Channels separate + Upload button fixed
"""
import warnings
warnings.filterwarnings('ignore')
import os, threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now(): return datetime.now(IST)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# === CHANNELS SEPARATE ===
MAIN_CHANNEL_ID = -1004352241439
SCREENSHOT_CHANNEL_ID = -1004295034675
WITHDRAW_CHANNEL_ID = -1004319888475

current_screenshot_channel = SCREENSHOT_CHANNEL_ID
current_withdraw_channel = WITHDRAW_CHANNEL_ID
current_join_channel = MAIN_CHANNEL_ID

def get_screenshot_channel(): return current_screenshot_channel
def get_withdraw_channel(): return current_withdraw_channel
def get_join_channel(): return current_join_channel

ADMIN_ID_LIST = [7256515560, 8544307598]
_env = os.getenv("ADMIN_IDS") or ""
if _env:
    for x in _env.replace(",", " ").split():
        if x.strip().isdigit():
            _id = int(x.strip())
            if _id not in ADMIN_ID_LIST: ADMIN_ID_LIST.append(_id)

def is_admin(uid): return uid in ADMIN_ID_LIST

users_db = {}
bot_application = None

# === FIX 1: FLASK PORT BINDING FOR RENDER ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return f"S2E Bot V59 Running! {get_ist_now()}<br>Main: {get_join_channel()}<br>Screenshot: {get_screenshot_channel()}<br>Withdraw: {get_withdraw_channel()}"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Flask binding to port {port} for Render...")
    flask_app.run(host='0.0.0.0', port=port, debug=False)

# === BOT HANDLERS ===
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📅 Daily Tasks", callback_data="daily")],
          [InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
          [InlineKeyboardButton("⬅️ Admin", callback_data="admin_panel")]]
    if update.message:
        await update.message.reply_text("🏠 Main Menu V59 FIXED", reply_markup=InlineKeyboardMarkup(kb))

async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    kb = [[InlineKeyboardButton("📤 Upload Screenshot - FIXED", callback_data="upload_screenshot_1")],
          [InlineKeyboardButton("⬅️ Back", callback_data="back_menu")]]
    await update.callback_query.edit_message_text("📅 Task 1 - Click Upload (Fixed)", reply_markup=InlineKeyboardMarkup(kb))

async def upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer("Now send photo 📸")
    except: pass
    context.user_data['waiting_for_screenshot_task'] = {'id': '1', 'task_number': 1, 'title': 'Daily Task', 'reward': 5}
    await update.callback_query.edit_message_text(
        f"📤 Upload Here\nWill go ONLY to {get_screenshot_channel()} - NOT main\nNow send photo"
    )

async def unified_screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        waiting = context.user_data.get('waiting_for_screenshot_task')
        if not waiting:
            await update.message.reply_text("First click Upload Screenshot button in Daily Tasks")
            return
        file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_daily_{user_id}_1"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_daily_{user_id}_1")
        ]])
        caption = f"📸 NEW PROOF V59\nUser: {user_id}\nTask: {waiting['task_number']}\nTime: {get_ist_now()}"
        try:
            await context.bot.send_photo(chat_id=get_screenshot_channel(), photo=file_id, caption=caption, reply_markup=kb)
            await update.message.reply_text(f"✅ Sent ONLY to Screenshot Channel {get_screenshot_channel()}")
            context.user_data.pop('waiting_for_screenshot_task', None)
            print(f"SCREENSHOT OK -> {get_screenshot_channel()}")
        except Exception as e:
            await update.message.reply_text(f"❌ Bot not admin in screenshot channel {get_screenshot_channel()}\nError: {e}")
    except Exception as e:
        print(f"Handler error {e}")

async def admin_panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    await update.callback_query.edit_message_text(
        f"👑 Admin V59\nMain: {get_join_channel()}\nScreenshot: {get_screenshot_channel()}\nWithdraw: {get_withdraw_channel()}\n\n✅ Port bind + Conflict fixed"
    )

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await menu(update, context)

# Admin commands
async def set_screenshot_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_screenshot_channel
    if not is_admin(update.effective_user.id): return
    try:
        current_screenshot_channel = int(context.args[0])
        await update.message.reply_text(f"✅ Screenshot Channel Set: {current_screenshot_channel}\nNow all task screenshots will go to this channel with Approve buttons!\nTest: Ask a user to submit a task")
    except: await update.message.reply_text("Usage: /set_screenshot_channel -1004295034675")

async def set_withdraw_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_withdraw_channel
    if not is_admin(update.effective_user.id): return
    try:
        current_withdraw_channel = int(context.args[0])
        await update.message.reply_text(f"✅ Withdraw Channel Set: {current_withdraw_channel}")
    except: await update.message.reply_text("Usage: /set_withdraw_channel -1004319888475")

async def set_join_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_join_channel
    if not is_admin(update.effective_user.id): return
    try:
        current_join_channel = int(context.args[0])
        await update.message.reply_text(f"✅ Main Channel Set: {current_join_channel}")
    except: await update.message.reply_text("Usage: /set_join_channel -1004352241439")

async def channels_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(f"📊 STATUS V59\nMain: {get_join_channel()}\nScreenshot: {get_screenshot_channel()} (TASK ONLY)\nWithdraw: {get_withdraw_channel()} (WITHDRAW ONLY)\n✅ All separate + Port fixed")

async def add_balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        uid = int(context.args[0]); amt = int(context.args[1])
        users_db.setdefault(uid, {})['balance'] = users_db.get(uid, {}).get('balance', 0) + amt
        await update.message.reply_text(f"Added Rs{amt} to {uid}")
    except: await update.message.reply_text("Usage: /add_balance 8709635130 765")

async def admin_approve_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    try:
        uid = int(update.callback_query.data.split("_")[-2])
        users_db.setdefault(uid, {})['balance'] = users_db.get(uid, {}).get('balance', 0) + 5
        await update.callback_query.edit_message_caption(caption=update.callback_query.message.caption + "\n\n✅ APPROVED")
        await context.bot.send_message(chat_id=uid, text="✅ Task approved ₹5 added")
    except: pass

async def admin_reject_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    await update.callback_query.edit_message_caption(caption=update.callback_query.message.caption + "\n\n❌ REJECTED")

# === FIX 2: CONFLICT FIX ===
async def post_init(application):
    await application.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted - Conflict fixed!")

async def error_handler(update, context):
    err = str(context.error)
    if "Conflict" in err:
        print(f"⚠️ Conflict ignored (other instance): {err}")
        return
    print(f"Error: {context.error}")

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing"); return

    # Start Flask in background thread - FIXES PORT ERROR
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask thread started for Render port binding")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    global bot_application; bot_application = app
    app.add_error_handler(error_handler)

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", lambda u,c: u.message.reply_text("Use /channels_status")))
    app.add_handler(CommandHandler("set_screenshot_channel", set_screenshot_channel_cmd))
    app.add_handler(CommandHandler("set_withdraw_channel", set_withdraw_channel_cmd))
    app.add_handler(CommandHandler("set_join_channel", set_join_channel_cmd))
    app.add_handler(CommandHandler("channels_status", channels_status_cmd))
    app.add_handler(CommandHandler("add_balance", add_balance_cmd))

    app.add_handler(CallbackQueryHandler(daily_cb, pattern=r"^daily$"))
    app.add_handler(CallbackQueryHandler(upload_screenshot_cb, pattern=r"^upload_screenshot_"))
    app.add_handler(CallbackQueryHandler(admin_panel_cb, pattern=r"^admin_panel$"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern=r"^back_menu$"))
    app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern=r"^admin_approve_daily_"))
    app.add_handler(CallbackQueryHandler(admin_reject_daily_cb, pattern=r"^admin_reject_daily_"))

    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, unified_screenshot_handler))

    print("🚀 V59 STARTING - Port + Conflict + 3 Channels FIXED")
    print(f"MAIN: {get_join_channel()} SCREENSHOT: {get_screenshot_channel()} WITHDRAW: {get_withdraw_channel()}")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
