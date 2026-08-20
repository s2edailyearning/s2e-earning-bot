import os
import re
import threading
from datetime import datetime, date
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

# --- Flask for Render port binding ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "S2E Daily Earning Bot Live! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# --- ENV ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@S2E_Daily_Earning")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/S2E_Daily_Earning")

# --- STATES ---
NAME, GENDER, DOB, UPI, PINCODE, PROFESSION = range(6)
users_db = {}

def calculate_age(dob_date):
    today = date.today()
    return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in users_db and users_db[user_id].get("registered"):
        await update.message.reply_text(
            f"Welcome back {users_db[user_id]['name']}! ✅\n\n"
            f"💰 Balance: ₹0\n"
            f"🔗 Referral: https://t.me/S2E_Daily_Earning_bot?start={user_id}\n\n"
            f"Use /menu"
        )
        return
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
    ]
    await update.message.reply_text(
        f"Welcome to S2E Daily Earning! 🚀\n\nYour ID: {user_id}\nChannel: S2E Daily Earning\n\nReferral System:\n• 5 members = wallet unlocked\n• ₹10 per Active Referral\n\nFirst, join the channel and verify!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['left', 'kicked']:
            raise Exception("Not joined")
    except:
        await query.message.reply_text("❌ You haven't joined yet! Please Join Channel first.")
        return ConversationHandler.END

    if user_id in users_db and users_db[user_id].get("registered"):
        await query.message.reply_text("✅ Already registered! /menu")
        return ConversationHandler.END

    users_db[user_id] = {}
    await query.message.reply_text(
        "✅ Verification Successful!\n\nYour task completed!\n\nNow complete registration (18+ only) 📝\n\n1️⃣ Enter your Full Name:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Please enter valid name:")
        return NAME
    users_db[user_id]['name'] = name
    keyboard = [["Male", "Female", "Other"]]
    await update.message.reply_text(f"Nice {name}! 👍\n\n2️⃣ Select Gender:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gender = update.message.text.strip()
    if gender not in ["Male", "Female", "Other"]:
        await update.message.reply_text("Select from buttons: Male / Female / Other")
        return GENDER
    users_db[user_id]['gender'] = gender
    await update.message.reply_text("3️⃣ Enter DOB (DD-MM-YYYY)\nEx: 15-08-2000\n*18+ only*", reply_markup=ReplyKeyboardRemove())
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    dob_text = update.message.text.strip()
    try:
        dob_date = datetime.strptime(dob_text, "%d-%m-%Y").date()
        age = calculate_age(dob_date)
        if age < 18:
            await update.message.reply_text(f"❌ You are {age} yrs. 18+ only required! Enter valid DOB again.")
            return DOB
        if age > 100:
            await update.message.reply_text("Enter valid DOB (DD-MM-YYYY):")
            return DOB
    except:
        await update.message.reply_text("❌ Invalid! Use DD-MM-YYYY\nEx: 15-08-2000")
        return DOB
    users_db[user_id]['dob'] = dob_text
    users_db[user_id]['age'] = age
    await update.message.reply_text(f"✅ Age verified: {age} yrs\n\n4️⃣ Enter UPI ID:\nEx: yourname@phonepe")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    upi = update.message.text.strip()
    if "@" not in upi:
        await update.message.reply_text("❌ Invalid UPI! Ex: name@phonepe")
        return UPI
    users_db[user_id]['upi'] = upi
    await update.message.reply_text("5️⃣ Enter Pincode (6 digits):\nEx: 517408")
    return PINCODE

async def get_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pin = update.message.text.strip()
    if not re.match(r"^\d{6}$", pin):
        await update.message.reply_text("❌ Invalid Pincode! 6 digits (Ex: 517408)")
        return PINCODE
    users_db[user_id]['pincode'] = pin
    keyboard = [["Student", "Employee", "Self-Employed", "Business"], ["Freelancer", "Other"]]
    await update.message.reply_text("6️⃣ Last step - Select Profession:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profession = update.message.text.strip()
    users_db[user_id]['profession'] = profession
    users_db[user_id]['registered'] = True
    users_db[user_id]['registered_at'] = datetime.now().isoformat()
    data = users_db[user_id]
    summary = (
        f"🎉 Registration Successful!\n\n"
        f"👤 Name: {data['name']}\n⚧ Gender: {data['gender']}\n"
        f"🎂 DOB: {data['dob']} (Age: {data['age']})\n"
        f"💳 UPI: {data['upi']}\n📍 Pincode: {data['pincode']}\n"
        f"💼 Profession: {data['profession']}\n\n"
        f"Your Referral Link:\nhttps://t.me/S2E_Daily_Earning_bot?start={user_id}\n\n"
        f"Share - ₹10 per active referral! 🚀"
    )
    await update.message.reply_text(summary, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. /start to restart.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily")]
    ]
    await update.message.reply_text("S2E Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    # Start Flask in background for Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
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
        per_user=True,
        per_chat=True,
        per_message=False,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(conv_handler)
    print("Bot started! ✅ Flask running for Render port binding")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
