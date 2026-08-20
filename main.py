import os
import re
import threading
from datetime import datetime, date
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@S2E_Daily_Earning")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/S2E_Daily_Earning")

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "S2E Daily Earning Bot Live! 🚀"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

NAME, GENDER, DOB, UPI, PINCODE, PROFESSION = range(6)

# --- In-Memory DB (Permanent kosam Google Sheet ki connect cheyachu) ---
users_db = {}
referrals_db = {}  # referrer_id -> count
tasks_db = {}      # user_id -> completed tasks count
daily_done = {}    # user_id -> last daily date string

def calculate_age(dob_date):
    today = date.today()
    return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

def get_balance(uid): return referrals_db.get(uid, 0) * 10 + tasks_db.get(uid, 0) * 5
def get_tasks(uid): return referrals_db.get(uid, 0) + tasks_db.get(uid, 0)

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ])

# --- Menu Button Handlers ---
async def my_ref_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    ref_count = referrals_db.get(uid, 0)
    bal = get_balance(uid)
    await query.message.reply_text(
        f"👥 My Referrals\n\n"
        f"Total Joined: {ref_count}\n"
        f"Tasks from Referrals: {ref_count}\n"
        f"Earning: ₹{ref_count*10}\n\n"
        f"🔗 Your Link (Click cheste auto Start vastundi):\nhttps://t.me/S2E_Daily_Earning_bot?start={uid}\n\n"
        f"Share cheyi - prathi friend join + register ayithe ₹10!",
        reply_markup=main_menu_keyboard()
    )

async def wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    bal = get_balance(uid)
    tasks = get_tasks(uid)
    await query.message.reply_text(
        f"💰 Wallet\n\n"
        f"Balance: ₹{bal}\n"
        f"Tasks Completed: {tasks}/15\n"
        f"Status: {'🔓 Eligible for Withdraw' if bal>=200 and tasks>=15 else '🔒 Locked'}\n\n"
        f"Withdraw Conditions:\n"
        f"• Minimum ₹200 {'✅' if bal>=200 else f'❌ (Need ₹{200-bal} more)'}\n"
        f"• 15 Tasks {'✅' if tasks>=15 else f'❌ ({tasks}/15)'}",
        reply_markup=main_menu_keyboard()
    )

async def daily_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    today_str = str(date.today())
    last_done = daily_done.get(uid)
    
    if last_done == today_str:
        await query.message.reply_text(
            f"📅 Daily Task\n\n✅ Already completed today!\n\nTasks Completed: {get_tasks(uid)}/15\nCome back tomorrow for next task!",
            reply_markup=main_menu_keyboard()
        )
        return

    # Complete daily task
    daily_done[uid] = today_str
    tasks_db[uid] = tasks_db.get(uid, 0) + 1
    
    await query.message.reply_text(
        f"📅 Daily Task Completed! ✅\n\n"
        f"+ ₹5 Added!\n"
        f"Tasks: {get_tasks(uid)}/15\n"
        f"Balance: ₹{get_balance(uid)}\n\n"
        f"Tomorrow malli ra - daily ₹5!",
        reply_markup=main_menu_keyboard()
    )

async def withdraw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    bal = get_balance(uid)
    tasks = get_tasks(uid)
    upi = users_db.get(uid, {}).get('upi', 'Not Set')

    # --- CONDITION CHECK ---
    if bal < 200 or tasks < 15:
        msg = f"💸 Withdraw - Not Eligible ❌\n\n"
        msg += f"Your Status:\n"
        msg += f"💰 Balance: ₹{bal} / ₹200 {'✅' if bal>=200 else f'❌ Need ₹{200-bal} more'}\n"
        msg += f"📋 Tasks: {tasks} / 15 {'✅' if tasks>=15 else f'❌ Need {15-tasks} more'}\n\n"
        
        if bal < 200:
            msg += f"👉 Balance kosam: Referrals cheyi (₹10 per friend) + Daily Task (₹5 per day)\n"
        if tasks < 15:
            msg += f"👉 Tasks kosam: Roju Daily Task click cheyi + Friends ni join cheyinchu\n\n"
        msg += f"Conditions complete ayyaka Withdraw unlock avutundi!"
        
        await query.message.reply_text(msg, reply_markup=main_menu_keyboard())
        return

    # Eligible - show confirmation
    keyboard = [
        [InlineKeyboardButton(f"✅ Confirm Withdraw ₹{bal} to {upi}", callback_data=f"confirm_withdraw_{bal}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="wallet")]
    ]
    await query.message.reply_text(
        f"💸 Withdraw Eligible! ✅\n\n"
        f"Balance: ₹{bal}\n"
        f"Tasks: {tasks}/15 ✅\n"
        f"UPI: {upi}\n\n"
        f"Withdraw chesthava? 24hrs lo payment vastundi!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_withdraw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    bal = get_balance(uid)
    upi = users_db.get(uid, {}).get('upi', '')
    
    # Reset balance after withdraw request (or keep pending)
    # For demo, we set to 0 and log
    referrals_db[uid] = 0
    tasks_db[uid] = 0
    
    await query.message.reply_text(
        f"✅ Withdraw Request Submitted!\n\n"
        f"Amount: ₹{bal}\n"
        f"UPI: {upi}\n"
        f"Status: Pending ⏳\n\n"
        f"24 hours lo payment chestham! Keep earning!",
        reply_markup=main_menu_keyboard()
    )
    # Here you can send notification to admin channel
    # await context.bot.send_message(chat_id=ADMIN_ID, text=f"New Withdraw: User {uid} Amount {bal} UPI {upi}")

# --- Start with Auto Referral Handling ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # Referral tracking - link click cheste auto /start?start=ID vastundi - typing avasaram ledu!
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != uid and uid not in users_db:
                referrals_db[referrer_id] = referrals_db.get(referrer_id, 0) + 1
                # Notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 New Referral Joined! +₹10\nTotal: {referrals_db[referrer_id]} referrals"
                    )
                except: pass
        except: pass

    if uid in users_db and users_db[uid].get("registered"):
        bal = get_balance(uid)
        await update.message.reply_text(
            f"Welcome back {users_db[uid]['name']} ✅\n\n"
            f"💰 Balance: ₹{bal}\n"
            f"📋 Tasks: {get_tasks(uid)}/15\n"
            f"🔗 Referral: https://t.me/S2E_Daily_Earning_bot?start={uid}\n\n"
            f"Link click cheste friend ki auto /start vastundi - typing avasaram ledu!",
            reply_markup=main_menu_keyboard()
        )
        return

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
    ]
    await update.message.reply_text(
        f"Welcome to S2E Daily Earning! 🚀\n\n"
        f"Your ID: {uid}\n"
        f"💸 Earn up to ₹500 daily!\n\n"
        f"Steps:\n1. Join Channel\n2. Register (18+)\n3. Refer & Do Daily Tasks\n4. Withdraw @ ₹200 + 15 Tasks\n\n"
        f"Referral Link click cheste neeke direct Start button vastundi!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=uid)
        if member.status in ['left', 'kicked']:
            raise Exception("Not joined")
    except:
        await query.message.reply_text("❌ You haven't joined yet! Join Channel first.")
        return ConversationHandler.END

    if uid in users_db and users_db[uid].get("registered"):
        await query.message.reply_text("✅ Already Registered!", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    users_db[uid] = {}
    await query.message.reply_text("✅ Verification Done! Registration (18+ only) 📝\n\n1️⃣ Full Name:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Valid name enter cheyi:")
        return NAME
    users_db[uid]['name'] = name
    kb = [["Male", "Female", "Other"]]
    await update.message.reply_text(f"Hi {name}! 2️⃣ Gender:", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = update.message.text.strip()
    if g not in ["Male", "Female", "Other"]:
        await update.message.reply_text("Button nundi select cheyi:")
        return GENDER
    users_db[uid]['gender'] = g
    await update.message.reply_text("3️⃣ DOB (DD-MM-YYYY) - 18+ required:", reply_markup=ReplyKeyboardRemove())
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text.strip()
    try:
        dob_date = datetime.strptime(txt, "%d-%m-%Y").date()
        age = calculate_age(dob_date)
        if age < 18:
            await update.message.reply_text(f"❌ Age {age} - 18+ only! Malli DOB enter cheyi:")
            return DOB
    except:
        await update.message.reply_text("Format DD-MM-YYYY like 15-08-2000:")
        return DOB
    users_db[uid]['dob'] = txt
    users_db[uid]['age'] = age
    await update.message.reply_text(f"✅ Age {age} verified\n\n4️⃣ UPI ID (e.g., name@phonepe):")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upi = update.message.text.strip()
    if "@" not in upi:
        await update.message.reply_text("Valid UPI - e.g., 98765@ybl:")
        return UPI
    users_db[uid]['upi'] = upi
    await update.message.reply_text("5️⃣ Pincode (6 digits):")
    return PINCODE

async def get_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pin = update.message.text.strip()
    if not re.match(r"^\d{6}$", pin):
        await update.message.reply_text("6 digit pincode:")
        return PINCODE
    users_db[uid]['pincode'] = pin
    kb = [["Student", "Employee", "Self-Employed", "Business"], ["Freelancer", "Other"]]
    await update.message.reply_text("6️⃣ Profession:", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]['profession'] = update.message.text.strip()
    users_db[uid]['registered'] = True
    bal = get_balance(uid)
    await update.message.reply_text(
        f"🎉 Registration Done {users_db[uid]['name']}!\n\n"
        f"UPI: {users_db[uid]['upi']}\nBalance: ₹{bal}\nTasks: {get_tasks(uid)}/15\n\n"
        f"Link: https://t.me/S2E_Daily_Earning_bot?start={uid}\nShare cheyi!",
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text("Menu:", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("S2E Menu:", reply_markup=main_menu_keyboard())

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_joined_callback, pattern="^check_joined$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)],
            PINCODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pincode)],
            PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_profession)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True, per_chat=True, per_message=False
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(my_ref_callback, pattern="^my_ref$"))
    app.add_handler(CallbackQueryHandler(wallet_callback, pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(daily_callback, pattern="^daily$"))
    app.add_handler(CallbackQueryHandler(withdraw_callback, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(confirm_withdraw_callback, pattern="^confirm_withdraw_"))
    app.add_handler(conv)
    print("Bot started! ✅ Withdraw system + Auto Start Ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
