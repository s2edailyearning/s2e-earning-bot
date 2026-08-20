import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ENV ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Example: @S2EDailyEarning or -100xxxxxxxxxx
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/S2E_Daily_Earning_Channel")

DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)

# --- Data handling ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

def get_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "id": uid,
            "referrals": [],
            "active_referrals": 0,
            "wallet": 0,
            "task_completed": False,
            "referred_by": None
        }
        save_data(data)
    return data["users"][uid]

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    bot_username = (await context.bot.get_me()).username

    # Referral handling
    referrer_id = None
    if context.args and len(context.args) > 0:
        referrer_id = context.args[0].strip()
    
    current_user = get_user(user_id)

    # If new referral
    if referrer_id and referrer_id != user_id and current_user["referred_by"] is None:
        if referrer_id in data["users"]:
            referrer = data["users"][referrer_id]
            if user_id not in referrer["referrals"]:
                referrer["referrals"].append(user_id)
                current_user["referred_by"] = referrer_id
                save_data(data)
                try:
                    await context.bot.send_message(
                        chat_id=int(referrer_id),
                        text=f"🎉 New Referral Joined!\n\nUser {user.first_name} joined using your link.\nThey need to complete the task to become active."
                    )
                except:
                    pass

    # Welcome Message - 100% ENGLISH
    welcome_text = f"""🚀 Welcome to S2E Daily Earning!

Your ID: {user_id}
Channel: S2E Daily Earning

Referral System:
• When 5 members join using your link and complete tasks, your wallet will be unlocked
• ₹10 per Active Referral

Your Referral Link:
https://t.me/{bot_username}?start={user_id}

Join the channel and click 'Check Joined' to verify!
"""

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")],
        [
            InlineKeyboardButton("👥 My Referrals", callback_data="my_referrals"),
            InlineKeyboardButton("💰 Wallet", callback_data="wallet")
        ],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily_task")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# --- Callback Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user = get_user(user_id)
    bot_username = (await context.bot.get_me()).username

    if query.data == "check_joined":
        try:
            # Check if user joined channel
            if not CHANNEL_ID:
                await query.message.reply_text("⚠️ Channel not configured. Please contact admin.")
                return

            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=int(user_id))
            if member.status in ["member", "administrator", "creator"]:
                # Mark task completed
                if not user["task_completed"]:
                    user["task_completed"] = True
                    # Reward referrer
                    if user["referred_by"]:
                        ref_id = user["referred_by"]
                        if ref_id in data["users"]:
                            ref_user = data["users"][ref_id]
                            ref_user["active_referrals"] += 1
                            ref_user["wallet"] += 10
                            save_data(data)
                            try:
                                await context.bot.send_message(
                                    chat_id=int(ref_id),
                                    text=f"✅ Your referral {query.from_user.first_name} completed the task!\n💰 You earned ₹10! Total Active: {ref_user['active_referrals']}"
                                )
                            except:
                                pass
                    save_data(data)

                await query.message.reply_text(
                    "✅ Verification Successful!\n\nYou have joined the channel. Your task is completed!\n\nNow share your referral link to earn more."
                )
            else:
                await query.message.reply_text(
                    "❌ You have not joined the channel yet!\n\nPlease join the channel first and then click 'Check Joined'.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)]])
                )
        except Exception as e:
            logging.error(f"Check joined error: {e}")
            await query.message.reply_text(
                f"⚠️ Could not verify. Make sure the bot is admin in the channel.\n\nChannel: {CHANNEL_LINK}\n\nAfter joining, click Check Joined again.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)]])
            )

    elif query.data == "my_referrals":
        total = len(user["referrals"])
        active = user["active_referrals"]
        text = f"""👥 My Referrals

Total Referrals: {total}
Active Referrals: {active}
Pending: {total - active}

Your Referral Link:
https://t.me/{bot_username}?start={user_id}

Share this link and earn ₹10 per active user!
You need 5 active referrals to unlock wallet.
"""
        await query.message.reply_text(text)

    elif query.data == "wallet":
        active = user["active_referrals"]
        balance = user["wallet"]
        if active >= 5:
            status = "✅ Unlocked"
        else:
            status = f"🔒 Locked (Need {5 - active} more active referrals)"

        text = f"""💰 Wallet

Balance: ₹{balance}
Status: {status}

Active Referrals: {active}/5

Minimum withdrawal: ₹50
Earn ₹10 for each active referral.

Your Referral Link:
https://t.me/{bot_username}?start={user_id}
"""
        await query.message.reply_text(text)

    elif query.data == "daily_task":
        text = f"""📅 Daily Task

✅ Task 1: Join our channel - Completed if you verified
⏳ Task 2: Refer 5 friends - {user['active_referrals']}/5

Complete daily tasks to keep your account active!

Your Link:
https://t.me/{bot_username}?start={user_id}
"""
        await query.message.reply_text(text)

# --- Main ---
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in Environment Variables!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot started! English version LIVE...")
    app.run_polling()
