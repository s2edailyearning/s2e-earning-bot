"""
S2E Bot V62 FINAL - 7% CHARGE + 200/300/500/1000 + REMAINING BALANCE + 3 CHANNELS FIXED
Your original logic restored
"""
import os, threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now(): return datetime.now(IST)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === 3 CHANNELS SEPARATE - YOUR REAL IDS ===
MAIN_CHANNEL_ID = -1004352241439
SCREENSHOT_CHANNEL_ID = -1004295034675  # TASK SCREENSHOTS ONLY
WITHDRAW_CHANNEL_ID = -1004319888475    # WITHDRAW ONLY
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

users_db = {}  # {uid: {'balance': 765, 'upi': ''}}
# ORIGINAL OPTIONS YOU ASKED
WITHDRAW_OPTIONS = [200, 300, 500, 1000]
WITHDRAW_FEE_PERCENT = 7  # 7% charge

# Flask for Render
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"S2E V62 Live {get_ist_now()}<br>Screenshot:{get_screenshot_channel()} ONLY<br>Withdraw:{get_withdraw_channel()} ONLY<br>7% logic"
@flask_app.route('/health')
def health(): return "OK", 200
def run_flask():
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)

# === MENUS ===
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bal = users_db.get(uid, {}).get('balance', 765)
    kb = [
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_menu")],
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("👑 Admin", callback_data="admin_panel")],
    ]
    txt = f"🏠 S2E V62 FINAL\nBalance: ₹{bal}\n\n✅ Screenshot → {get_screenshot_channel()} ONLY\n✅ Withdraw → {get_withdraw_channel()} ONLY\n✅ 7% Charge Logic"
    if update.message: await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        try: await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        except: await context.bot.send_message(chat_id=uid, text=txt, reply_markup=InlineKeyboardMarkup(kb))

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await menu(update, context)

async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    kb = [[InlineKeyboardButton("📤 Upload Screenshot", callback_data="upload_screenshot_1")],
          [InlineKeyboardButton("⬅️ Back", callback_data="back_menu")]]
    await update.callback_query.edit_message_text("📅 Task 1 - Click Upload", reply_markup=InlineKeyboardMarkup(kb))

async def upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer("Now send photo 📸")
    except: pass
    context.user_data['waiting_for_screenshot_task'] = {'id': '1', 'task_number': 1, 'title': 'Daily Task', 'reward': 5}
    await update.callback_query.edit_message_text(f"📤 Upload Here\nWill go ONLY to Screenshot Channel {get_screenshot_channel()}\nNOT to main {get_join_channel()}\nNow send photo")

async def unified_screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    waiting = context.user_data.get('waiting_for_screenshot_task')
    if not waiting: return
    file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_daily_{uid}_1"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_daily_{uid}_1")]])
    caption = f"📸 NEW PROOF V62\nUser: {uid} (@{update.effective_user.username or 'no'})\nTask: {waiting['task_number']}\nTime: {get_ist_now().strftime('%d-%m %H:%M')} IST\nChannel: Screenshot ONLY {get_screenshot_channel()}"
    try:
        await context.bot.send_photo(chat_id=get_screenshot_channel(), photo=file_id, caption=caption, reply_markup=kb)
        await update.message.reply_text(f"✅ Sent ONLY to Screenshot Channel {get_screenshot_channel()}\nAdmin will approve soon.\n(Old main channel {get_join_channel()} ki vellaledu - FIXED)")
        context.user_data.pop('waiting_for_screenshot_task', None)
    except Exception as e:
        await update.message.reply_text(f"❌ Bot not admin in screenshot channel {get_screenshot_channel()}?\nError: {e}")

# === WITHDRAW WITH 7% CHARGE + REMAINING BALANCE - ORIGINAL LOGIC ===
async def withdraw_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    uid = update.effective_user.id
    bal = users_db.get(uid, {}).get('balance', 765)
    upi = users_db.get(uid, {}).get('upi', 'Not set')
    
    kb = []
    for amt in WITHDRAW_OPTIONS:
        if bal >= amt:
            fee = int(amt * WITHDRAW_FEE_PERCENT / 100)
            receive = amt - fee
            kb.append([InlineKeyboardButton(f"💸 ₹{amt} (Fee 7% = ₹{fee}, You get ₹{receive})", callback_data=f"wd_select_{amt}")])
    
    if not kb:
        kb.append([InlineKeyboardButton("❌ Low Balance", callback_data="back_menu")])
    
    kb.append([InlineKeyboardButton("✏️ Set/Edit UPI", callback_data="wd_edit_upi")])
    kb.append([InlineKeyboardButton("⬅️ Back", callback_data="back_menu")])
    
    text = (
        f"💸 WITHDRAW - ORIGINAL 7% LOGIC\n\n"
        f"Earnings: ₹{bal}\n"
        f"Min: ₹200\n"
        f"UPI: {upi}\n\n"
        f"Options: 200, 300, 500, 1000\n"
        f"Charge: 7% deducted\n"
        f"Example: ₹200 → Fee ₹14 → You get ₹186\n\n"
        f"Select amount:"
    )
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def wd_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    amt = int(update.callback_query.data.replace("wd_select_",""))
    uid = update.effective_user.id
    bal = users_db.get(uid, {}).get('balance', 765)
    upi = users_db.get(uid, {}).get('upi')
    if not upi:
        kb = [[InlineKeyboardButton("✏️ Set UPI First", callback_data="wd_edit_upi")], [InlineKeyboardButton("⬅️ Back", callback_data="withdraw_menu")]]
        await update.callback_query.edit_message_text(f"❌ UPI not set for ₹{amt}", reply_markup=InlineKeyboardMarkup(kb))
        return
    
    fee = int(amt * WITHDRAW_FEE_PERCENT / 100)
    receive = amt - fee
    remaining = bal - amt
    
    kb = [[InlineKeyboardButton(f"✅ Confirm ₹{amt} (Get ₹{receive})", callback_data=f"wd_confirm_{amt}")],
          [InlineKeyboardButton("⬅️ Back", callback_data="withdraw_menu")]]
    
    text = (
        f"Confirm Withdraw?\n"
        f"Amount: ₹{amt}\n"
        f"7% Charge: ₹{fee}\n"
        f"You will receive: ₹{receive}\n"
        f"Current Balance: ₹{bal}\n"
        f"Remaining Balance: ₹{remaining}\n"
        f"UPI: {upi}\n"
        f"Goes ONLY to {get_withdraw_channel()}"
    )
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def wd_edit_upi_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    context.user_data['waiting_for_upi'] = True
    await update.callback_query.edit_message_text("✏️ Send UPI ID now\nEx: 8709635130@ybl")

async def wd_edit_upi_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_upi'): return
    upi_text = update.message.text.strip()
    if "@" not in upi_text:
        await update.message.reply_text("❌ Invalid UPI")
        return
    uid = update.effective_user.id
    users_db.setdefault(uid, {})['upi'] = upi_text
    context.user_data.pop('waiting_for_upi', None)
    await update.message.reply_text(f"✅ UPI Saved: {upi_text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_menu")]]))

async def wd_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer("Processing...")
    except: pass
    amt = int(update.callback_query.data.replace("wd_confirm_",""))
    uid = update.effective_user.id
    bal = users_db.get(uid, {}).get('balance', 765)
    upi = users_db.get(uid, {}).get('upi', 'not_set')
    if bal < amt:
        await update.callback_query.edit_message_text(f"❌ Insufficient ₹{bal} < ₹{amt}")
        return
    fee = int(amt * WITHDRAW_FEE_PERCENT / 100)
    receive = amt - fee
    remaining = bal - amt
    users_db[uid]['balance'] = remaining
    
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"wd_admin_approve_{uid}_{amt}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"wd_admin_reject_{uid}_{amt}")
    ]])
    msg = (
        f"💸 NEW WITHDRAW V62 - 7% LOGIC\n"
        f"User: {uid} (@{update.effective_user.username or 'no'})\n"
        f"Amount: ₹{amt}\n"
        f"7% Fee: ₹{fee}\n"
        f"User Gets: ₹{receive}\n"
        f"Remaining Balance: ₹{remaining}\n"
        f"UPI: {upi}\n"
        f"Time: {get_ist_now().strftime('%d-%m %H:%M')} IST\n"
        f"Channel: Withdraw ONLY {get_withdraw_channel()}"
    )
    try:
        await context.bot.send_message(chat_id=get_withdraw_channel(), text=msg, reply_markup=kb)
        await update.callback_query.edit_message_text(
            f"✅ Withdraw Request Sent!\n\n"
            f"Amount: ₹{amt}\n"
            f"7% Charge: ₹{fee}\n"
            f"You will get: ₹{receive}\n"
            f"Remaining Balance: ₹{remaining}\n"
            f"UPI: {upi}\n"
            f"Sent ONLY to Withdraw Channel {get_withdraw_channel()}"
        )
    except Exception as e:
        users_db[uid]['balance'] = bal
        await update.callback_query.edit_message_text(f"❌ Bot not admin in withdraw channel {get_withdraw_channel()}? {e}")

# Admin callbacks
async def admin_approve_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    uid = int(update.callback_query.data.split("_")[-2])
    users_db.setdefault(uid, {})['balance'] = users_db.get(uid, {}).get('balance', 0) + 5
    await update.callback_query.edit_message_caption(caption=update.callback_query.message.caption + "\n\n✅ APPROVED")
    await context.bot.send_message(chat_id=uid, text="✅ Task approved ₹5 added")
async def wd_admin_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    await update.callback_query.edit_message_text(text=update.callback_query.message.text + "\n\n✅ APPROVED - Paid")
async def wd_admin_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    # Refund logic
    try:
        parts = update.callback_query.data.split("_")
        uid = int(parts[-2]); amt = int(parts[-1])
        users_db.setdefault(uid, {})['balance'] = users_db.get(uid, {}).get('balance', 0) + amt
        await context.bot.send_message(chat_id=uid, text=f"❌ Withdraw ₹{amt} rejected, ₹{amt} refunded")
    except: pass
    await update.callback_query.edit_message_text(text=update.callback_query.message.text + "\n\n❌ REJECTED & Refunded")
async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await menu(update, context)
async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text(f"Wallet: ₹{users_db.get(update.effective_user.id, {}).get('balance',765)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_menu")]]))
async def admin_panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    await update.callback_query.edit_message_text(f"Admin V62\nMain:{get_join_channel()}\nScreenshot:{get_screenshot_channel()} TASK ONLY\nWithdraw:{get_withdraw_channel()} WITHDRAW ONLY\n7% Logic")

async def set_screenshot_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_screenshot_channel
    if not is_admin(update.effective_user.id): return
    try: current_screenshot_channel = int(context.args[0]); await update.message.reply_text(f"✅ Screenshot Set: {current_screenshot_channel}")
    except: await update.message.reply_text("Usage: /set_screenshot_channel -1004295034675")
async def set_withdraw_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_withdraw_channel
    if not is_admin(update.effective_user.id): return
    try: current_withdraw_channel = int(context.args[0]); await update.message.reply_text(f"✅ Withdraw Set: {current_withdraw_channel}")
    except: await update.message.reply_text("Usage: /set_withdraw_channel -1004319888475")
async def channels_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(f"📊 V62 STATUS\nMain:{get_join_channel()}\nScreenshot:{get_screenshot_channel()} TASK ONLY ✅\nWithdraw:{get_withdraw_channel()} WITHDRAW ONLY ✅\nOptions:200,300,500,1000 + 7% charge + Remaining bal ✅")
async def add_balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try: uid = int(context.args[0]); amt = int(context.args[1]); users_db.setdefault(uid, {})['balance'] = users_db.get(uid, {}).get('balance', 0) + amt; await update.message.reply_text(f"Added Rs{amt} to {uid}")
    except: await update.message.reply_text("Usage: /add_balance 8709635130 765")

async def post_init(application):
    await application.bot.delete_webhook(drop_pending_updates=True)
async def error_handler(update, context):
    if "Conflict" in str(context.error): return

def main():
    if not BOT_TOKEN: return
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("set_screenshot_channel", set_screenshot_channel_cmd))
    app.add_handler(CommandHandler("set_withdraw_channel", set_withdraw_channel_cmd))
    app.add_handler(CommandHandler("channels_status", channels_status_cmd))
    app.add_handler(CommandHandler("add_balance", add_balance_cmd))
    app.add_handler(CallbackQueryHandler(lambda u,c: menu(u,c), pattern=r"^daily$"))
    # Overwrite daily with proper handler
    app.add_handler(CallbackQueryHandler(daily_cb, pattern=r"^daily$"), group=1)
    app.add_handler(CallbackQueryHandler(upload_screenshot_cb, pattern=r"^upload_screenshot_"))
    app.add_handler(CallbackQueryHandler(withdraw_menu_cb, pattern=r"^withdraw_menu$"))
    app.add_handler(CallbackQueryHandler(wd_select_cb, pattern=r"^wd_select_"))
    app.add_handler(CallbackQueryHandler(wd_edit_upi_cb, pattern=r"^wd_edit_upi$"))
    app.add_handler(CallbackQueryHandler(wd_confirm_cb, pattern=r"^wd_confirm_"))
    app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern=r"^admin_approve_daily_"))
    app.add_handler(CallbackQueryHandler(wd_admin_approve_cb, pattern=r"^wd_admin_approve_"))
    app.add_handler(CallbackQueryHandler(wd_admin_reject_cb, pattern=r"^wd_admin_reject_"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern=r"^back_menu$"))
    app.add_handler(CallbackQueryHandler(wallet_cb, pattern=r"^wallet$"))
    app.add_handler(CallbackQueryHandler(admin_panel_cb, pattern=r"^admin_panel$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wd_edit_upi_text_handler), group=0)
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, unified_screenshot_handler), group=1)
    print("V62 FINAL - 7% + 200/300/500/1000 + 3 Channels")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
