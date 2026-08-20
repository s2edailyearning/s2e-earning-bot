import os
import re
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

# --- ENV ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@S2E_Daily_Earning")  # or @S2E_Daily_Earning
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/S2E_Daily_Earning")

# --- STATES FOR REGISTRATION ---
NAME, GENDER, DOB, UPI, PINCODE, PROFESSION = range(6)

# Simple in-memory DB (Render free lo file reset avutundi - permanent kosam Google Sheet add cheyachu)
users_db = {}

def calculate_age(dob_date):
    today = date.today()
    return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # If already registered, show menu
    if user_id in users_db and users_db[user_id].get("registered"):
        await update.message.reply_text(
            f"Welcome back {users_db[user_id]['name']}! ✅\n\n"
            f"💰 Balance: ₹0\n"
            f"🔗 Your Referral: https://t.me/S2E_Daily_Earning_bot?start={user_id}\n\n"
            f"Use /menu for options"
        )
        return

    # Not registered - show join channel
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
    ]
    await update.message.reply_text(
        f"Welcome to S2E Daily Earning! 🚀\n\n"
        f"Your ID: {user_id}\n"
        f"Channel: S2E Daily Earning\n\n"
        f"Referral System:\n"
        f"• When 5 members join using your link and complete tasks, wallet unlocked\n"
        f"• ₹10 per Active Referral\n\n"
        f"First, join the channel and verify!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Check joined callback
async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['left', 'kicked']:
            raise Exception("Not joined")
    except:
        await query.message.reply_text("❌ You haven't joined yet! Please Join Channel first and then click Check Joined.")
        return

    # Joined - check if already registered
    if user_id in users_db and users_db[user_id].get("registered"):
        await query.message.reply_text("✅ Verification Successful! You are already registered. /menu")
        return

    # Start registration
    users_db[user_id] = {}
    await query.message.reply_text(
        "✅ Verification Successful!\n\n"
        "Your task is completed!\n\n"
        "Now let's complete your registration for daily earning (18+ only) 📝\n\n"
        "1️⃣ Enter your Full Name:"
    )
    context.user_data['reg_step'] = NAME
    return NAME

# Registration Steps
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Please enter valid name:")
        return NAME
    users_db[user_id]['name'] = name
    # Gender keyboard
    keyboard = [["Male", "Female", "Other"]]
    await update.message.reply_text(
        f"Nice {name}! 👍\n\n2️⃣ Select your Gender:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gender = update.message.text.strip()
    if gender not in ["Male", "Female", "Other"]:
        await update.message.reply_text("Please select from buttons: Male / Female / Other")
        return GENDER
    users_db[user_id]['gender'] = gender
    await update.message.reply_text(
        "3️⃣ Enter your Date of Birth (DD-MM-YYYY)\nExample: 15-08-2000\n\n*Age must be 18+*",
        reply_markup=ReplyKeyboardRemove()
    )
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    dob_text = update.message.text.strip()
    try:
        dob_date = datetime.strptime(dob_text, "%d-%m-%Y").date()
        age = calculate_age(dob_date)
        if age < 18:
            await update.message.reply_text(f"❌ Sorry, you are {age} years old. 18+ only required! Please enter valid DOB again or contact support.")
            return DOB
        if age > 100:
            await update.message.reply_text("Please enter valid DOB (DD-MM-YYYY):")
            return DOB
    except:
        await update.message.reply_text("❌ Invalid format! Use DD-MM-YYYY\nExample: 15-08-2000")
        return DOB
    
    users_db[user_id]['dob'] = dob_text
    users_db[user_id]['age'] = age
    await update.message.reply_text(f"✅ Age verified: {age} years\n\n4️⃣ Enter your UPI ID for payments:\nExample: yourname@phonepe / 9876543210@ybl")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    upi = update.message.text.strip()
    # Simple UPI validation: something@something
    if not re.match(r"^[\w.\-_]{2,256}@[a-zA-Z]{2,64}$", upi) and "@" not in upi:
        await update.message.reply_text("❌ Invalid UPI! Enter correct UPI ID (e.g., name@phonepe):")
        return UPI
    users_db[user_id]['upi'] = upi
    await update.message.reply_text("5️⃣ Enter your Pincode (6 digits):\nExample: 517408")
    return PINCODE

async def get_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    pin = update.message.text.strip()
    if not re.match(r"^\d{6}$", pin):
        await update.message.reply_text("❌ Invalid Pincode! Enter 6 digit pincode (e.g., 517408):")
        return PINCODE
    users_db[user_id]['pincode'] = pin
    keyboard = [["Student", "Employee", "Self-Employed", "Business"], ["Freelancer", "Other"]]
    await update.message.reply_text(
        "6️⃣ Last step - Select your Profession:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profession = update.message.text.strip()
    users_db[user_id]['profession'] = profession
    users_db[user_id]['registered'] = True
    users_db[user_id]['registered_at'] = datetime.now().isoformat()

    # Save summary
    data = users_db[user_id]
    summary = (
        f"🎉 Registration Successful!\n\n"
        f"👤 Name: {data['name']}\n"
        f"⚧ Gender: {data['gender']}\n"
        f"🎂 DOB: {data['dob']} (Age: {data['age']})\n"
        f"💳 UPI: {data['upi']}\n"
        f"📍 Pincode: {data['pincode']}\n"
        f"💼 Profession: {data['profession']}\n\n"
        f"Your Referral Link:\n"
        f"https://t.me/S2E_Daily_Earning_bot?start={user_id}\n\n"
        f"Now share your link - ₹10 per active referral! 🚀\n\n"
        f"Use /menu to see Wallet, My Referrals, Daily Task"
    )
    await update.message.reply_text(summary, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled. Type /start to restart.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily")]
    ]
    await update.message.reply_text("S2E Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Registration conversation - starts after check_joined
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
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(conv_handler)
    # Also keep your existing handlers for wallet, referrals etc. - add them here

    print("Bot started! ✅")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
