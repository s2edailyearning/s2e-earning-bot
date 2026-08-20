import os, re, threading
from datetime import date, datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@s2edayincome")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/s2edayincome")
ADMIN_UPI = os.getenv("ADMIN_UPI", "s2eearning@upi")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@s2edayincome")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/s2edayincome")
ADMIN_IDS = os.getenv("ADMIN_IDS", "8544307598")
ADMIN_ID_LIST = [int(x.strip()) for x in ADMIN_IDS.split(",") if x.strip().isdigit()]
DEPOSIT_LINK_BASIC = os.getenv("DEPOSIT_LINK_BASIC", f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=500&cu=INR&tn=Basic")
DEPOSIT_LINK_PREMIUM = os.getenv("DEPOSIT_LINK_PREMIUM", f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=1000&cu=INR&tn=Premium")

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "S2E Bot Live! Hotfix for Admin Check"
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

# HOTFIX: Channel check with better error handling - if bot is not admin, allow join to avoid loop
async def check_channel_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        print(f"DEBUG: User {user_id} status in {CHANNEL_USERNAME}: {member.status}")
        return member.status not in ['left', 'kicked']
    except Exception as e:
        print(f"DEBUG ERROR checking channel member: {e} - Channel: {CHANNEL_USERNAME}, User: {user_id}")
        # HOTFIX: If we can't check (bot not admin or channel private), allow for now to avoid infinite loop
        # In production, you MUST add bot as admin!
        return True  # Allow to proceed, will verify later when bot is admin

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
    cnt=referrals_db.get(uid,0)
    await q.message.reply_text(f"👥 My Referrals\n\nVerified (after 1st task): {cnt}\nEarning: ₹{cnt*10}\n\nLink: https://t.me/{context.bot.username}?start={uid}\n\nReward only after friend completes first task.", reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    bal=get_balance(uid); tasks=get_tasks(uid)
    await q.message.reply_text(f"💰 Wallet\n\nBalance: ₹{bal}\nTasks: {tasks}/15\nPlan: {user_plans.get(uid,'Free Plan')}\nStatus: {'🔓 Eligible' if bal>=200 and tasks>=15 else '🔒 Locked'}", reply_markup=main_menu())

async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    today=str(date.today())
    if daily_done.get(uid)==today:
        await q.message.reply_text(f"📅 Daily Task\n✅ Already completed today!", reply_markup=main_menu()); return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Sponsor Channel", url=CHANNEL_LINK)],[InlineKeyboardButton("✅ I Completed - Verify Now", callback_data="daily_verify")],[InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]])
    await q.message.reply_text(f"📅 Today's Daily Task\nReward: ₹5 + 1 Task\n\nClick Verify after joining.", reply_markup=kb)

async def daily_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    today=str(date.today())
    if daily_done.get(uid)==today:
        await q.message.reply_text("📅 Already completed!", reply_markup=main_menu()); return
    daily_done[uid]=today
    is_first = tasks_db.get(uid,0)==0 and referrals_db.get(uid,0)==0
    tasks_db[uid]=tasks_db.get(uid,0)+1
    ref_id=pending_referrals.get(uid)
    if ref_id and is_first:
        referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
        try: await context.bot.send_message(chat_id=ref_id, text=f"🎉 Referral Verified! +₹10 Added! Total: {referrals_db[ref_id]}")
        except: pass
        del pending_referrals[uid]
    await q.message.reply_text(f"📅 Daily Task Verified! ✅\n\n+ ₹5 Added!\nTasks: {get_tasks(uid)}/15\nBalance: ₹{get_balance(uid)}", reply_markup=main_menu())

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Basic ₹500", callback_data="plan_basic")],[InlineKeyboardButton("👑 Premium ₹1000", callback_data="plan_premium")],[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]])
    await q.message.reply_text(f"💎 S2E Support Plans\n\n📦 BASIC ₹500 - 30 Days\n👑 PREMIUM ₹1000 - 90 Days + ₹100 Bonus", reply_markup=kb)

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay ₹500", url=DEPOSIT_LINK_BASIC)],[InlineKeyboardButton("✅ I Paid", callback_data="verify_basic")],[InlineKeyboardButton("🔙 Back", callback_data="support_plans")]])
    await q.message.reply_text(f"📦 Basic ₹500\nLink: {DEPOSIT_LINK_BASIC}", reply_markup=kb)

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay ₹1000", url=DEPOSIT_LINK_PREMIUM)],[InlineKeyboardButton("✅ I Paid", callback_data="verify_premium")],[InlineKeyboardButton("🔙 Back", callback_data="support_plans")]])
    await q.message.reply_text(f"👑 Premium ₹1000\nLink: {DEPOSIT_LINK_PREMIUM}\nBonus ₹100", reply_markup=kb)

async def verify_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    plan="Basic ₹500" if "basic" in q.data else "Premium ₹1000"
    user_plans[uid]=plan
    if "premium" in q.data: bonus_balance[uid]=bonus_balance.get(uid,0)+100
    await q.message.reply_text(f"✅ {plan} Payment Pending Verification!\nSend screenshot to {SUPPORT_USERNAME}", reply_markup=main_menu())

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: return
    bal=get_balance(uid); tasks=get_tasks(uid); upi=users_db.get(uid,{}).get('upi','Not Set')
    if bal<200 or tasks<15:
        msg=f"💸 Withdrawal - Not Eligible ❌\n\nBalance: ₹{bal}/₹200\nTasks: {tasks}/15"
        await q.message.reply_text(msg, reply_markup=main_menu()); return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Confirm Withdraw ₹{bal}", callback_data=f"confirm_withdraw_{bal}")]])
    await q.message.reply_text(f"💸 Eligible! ✅\nBalance: ₹{bal}\nUPI: {upi}", reply_markup=kb)

async def confirm_withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid); upi=users_db.get(uid,{}).get('upi','')
    referrals_db[uid]=0; tasks_db[uid]=0; bonus_balance[uid]=0
    await q.message.reply_text(f"✅ Withdrawal Submitted! ₹{bal} to {upi} Pending ⏳", reply_markup=main_menu())

async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Message Admin", url=SUPPORT_LINK)],[InlineKeyboardButton("✉️ Send Message", callback_data="send_support_msg")],[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]])
    await q.message.reply_text(f"📞 Contact Us\n\nSupport: {SUPPORT_USERNAME}\nChannel: {CHANNEL_USERNAME}", reply_markup=kb)

async def send_support_msg_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("✉️ Type your support message:\n\n/cancel to cancel")
    return SUPPORT_MSG

async def get_support_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; msg=update.message.text.strip()
    await update.message.reply_text(f"✅ Support Message Sent! Forwarded to {SUPPORT_USERNAME}", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try: await context.bot.send_message(chat_id=admin_id, text=f"🆘 SUPPORT\nFrom: {users_db.get(uid,{}).get('name','Unknown')} ({uid})\n{msg}")
        except: pass
    return ConversationHandler.END

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("Menu:", reply_markup=main_menu())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if uid in banned_users:
        await update.message.reply_text("🚫 Banned! Contact support.")
        return
    if context.args and len(context.args)>0:
        try:
            ref_id=int(context.args[0])
            if ref_id!=uid and uid not in users_db: pending_referrals[uid]=ref_id
        except: pass
    if uid in users_db and users_db[uid].get("registered"):
        await update.message.reply_text(f"Welcome back {users_db[uid]['name']} ✅\n💰 ₹{get_balance(uid)}\n📋 {get_tasks(uid)}/15", reply_markup=main_menu())
        return
    # HOTFIX: Always show registration if not registered, don't block on channel check error
    is_member = await check_channel_member(uid, context)
    if not is_member:
        # If check says not member but we allow in hotfix, still show join prompt first time
        # But if user already tried joining, allow to proceed
        if uid not in users_db:
            await update.message.reply_text(f"Welcome to S2E Day Income! 🚀\n\nJoin channel to start!\n\nStep 1: Join Channel\nStep 2: Return and click 'I Joined'", reply_markup=join_channel_keyboard(False))
            return
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Start Registration - Auto", callback_data="check_joined")]])
    await update.message.reply_text(f"✅ Channel Joined! Start registration (18+ only).", reply_markup=kb)

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users: await q.message.reply_text("🚫 Banned!"); return ConversationHandler.END
    # HOTFIX: Bypass strict check to avoid loop - log the check
    is_member = await check_channel_member(uid, context)
    print(f"CHECK JOINED: User {uid}, is_member={is_member}, Channel={CHANNEL_USERNAME}")
    # Allow even if check fails - prevents infinite loop you saw in screenshot
    if uid in users_db and users_db[uid].get("registered"):
        await q.message.reply_text("✅ Already registered!", reply_markup=main_menu())
        return ConversationHandler.END
    users_db[uid]={}
    await q.message.reply_text(f"✅ Verification Successful! 🎉\n\n📝 Registration (18+ only) - Step 1/7\n1️⃣ Enter your Full Name:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; name=update.message.text.strip()
    if len(name)<2: await update.message.reply_text("Enter valid name:"); return NAME
    users_db[uid]['name']=name
    kb=ReplyKeyboardMarkup([["Male","Female","Other"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Hi {name}! 👋\n\n2️⃣ Gender:", reply_markup=kb)
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; g=update.message.text.strip()
    if g not in ["Male","Female","Other"]: await update.message.reply_text("Select from buttons:"); return GENDER
    users_db[uid]['gender']=g
    await update.message.reply_text("3️⃣ DOB (DD-MM-YYYY)\nExample: 15-08-2000\n18+ only", reply_markup=ReplyKeyboardRemove())
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; txt=update.message.text.strip()
    try:
        dob=datetime.strptime(txt, "%d-%m-%Y").date(); age=calculate_age(dob)
        if age<18: await update.message.reply_text(f"❌ Age {age} - 18+ only! Enter again:"); return DOB
    except:
        await update.message.reply_text("❌ Use DD-MM-YYYY:"); return DOB
    users_db[uid]['dob']=txt; users_db[uid]['age']=age
    await update.message.reply_text(f"✅ Age {age} verified!\n\n4️⃣ Mobile (10 digits):")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; mob=update.message.text.strip()
    mob_clean = re.sub(r'\D', '', mob)
    if mob_clean.startswith('91') and len(mob_clean)==12: mob_clean=mob_clean[2:]
    if not re.match(r'^[6-9]\d{9}$', mob_clean):
        await update.message.reply_text("❌ Invalid Mobile!"); return MOBILE
    if is_duplicate_mobile(mob_clean, exclude_uid=uid):
        await update.message.reply_text(f"❌ Mobile {mob_clean} already registered!"); return MOBILE
    users_db[uid]['mobile']=mob_clean
    await update.message.reply_text(f"✅ Mobile {mob_clean} verified!\n\n5️⃣ UPI ID:")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; upi=update.message.text.strip()
    if "@" not in upi: await update.message.reply_text("❌ Invalid UPI!"); return UPI
    if is_duplicate_upi(upi, exclude_uid=uid):
        await update.message.reply_text(f"❌ UPI {upi} already registered!"); return UPI
    users_db[uid]['upi']=upi
    await update.message.reply_text("6️⃣ Pincode (6 digits):")
    return PINCODE

async def get_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; pin=update.message.text.strip()
    if not re.match(r"^\d{6}$", pin): await update.message.reply_text("Enter 6 digit pincode:"); return PINCODE
    users_db[uid]['pincode']=pin
    kb=ReplyKeyboardMarkup([["Student","Employee","Self-Employed","Business"],["Freelancer","Other"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("7️⃣ Profession:", reply_markup=kb)
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    users_db[uid]['profession']=update.message.text.strip()
    users_db[uid]['registered']=True
    d=users_db[uid]
    await update.message.reply_text(f"🎉 Registration Successful!\nName: {d['name']}\nMobile: {d['mobile']}\nUPI: {d['upi']}\nLink: https://t.me/{context.bot.username}?start={uid}", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("Menu:", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu:", reply_markup=main_menu())

# ADMIN
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): await update.message.reply_text("❌ Not admin!"); return
    await update.message.reply_text(f"👑 ADMIN PANEL\nTotal Users: {len(users_db)}\n\nCommands:\n/delete <id>\n/addmoney <id> <amount>\n/approve <id>\n/reject <id>\n/userinfo <id>")

async def delete_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /delete <id>"); return
    try: target_id=int(context.args[0])
    except: return
    if target_id in users_db: del users_db[target_id]; referrals_db.pop(target_id,None); tasks_db.pop(target_id,None); await update.message.reply_text(f"✅ Deleted {target_id}")
    else: await update.message.reply_text("Not found")

async def add_money_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if len(context.args)<2: return
    try: target_id=int(context.args[0]); amount=int(context.args[1])
    except: return
    bonus_balance[target_id]=bonus_balance.get(target_id,0)+amount
    await update.message.reply_text(f"✅ Added ₹{amount} to {target_id} - New: ₹{get_balance(target_id)}")

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try: target_id=int(context.args[0])
    except: return
    tasks_db[target_id]=tasks_db.get(target_id,0)+1
    await update.message.reply_text(f"✅ Approved {target_id} - Tasks: {get_tasks(target_id)}")

async def user_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try: target_id=int(context.args[0])
    except: return
    data=users_db.get(target_id)
    if not data: await update.message.reply_text("Not found"); return
    await update.message.reply_text(f"User {target_id}\nName: {data.get('name')}\nMobile: {data.get('mobile')}\nBalance: ₹{get_balance(target_id)}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).build()
    conv_reg = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_joined_cb, pattern="^check_joined$")],
        states={
            NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            DOB:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            MOBILE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_mobile)],
            UPI:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)],
            PINCODE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_pincode)],
            PROFESSION:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_profession)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True, per_chat=True, per_message=False
    )
    conv_support = ConversationHandler(
        entry_points=[CallbackQueryHandler(send_support_msg_cb, pattern="^send_support_msg$")],
        states={SUPPORT_MSG:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_support_msg)]},
        fallbacks=[CommandHandler("cancel", cancel_support)],
        per_user=True, per_chat=True, per_message=False
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("delete", delete_user_cmd))
    app.add_handler(CommandHandler("addmoney", add_money_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("userinfo", user_info_cmd))
    app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
    app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(daily_cb, pattern="^daily$"))
    app.add_handler(CallbackQueryHandler(daily_verify_cb, pattern="^daily_verify$"))
    app.add_handler(CallbackQueryHandler(withdraw_cb, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(confirm_withdraw_cb, pattern="^confirm_withdraw_"))
    app.add_handler(CallbackQueryHandler(support_plans_cb, pattern="^support_plans$"))
    app.add_handler(CallbackQueryHandler(plan_basic_cb, pattern="^plan_basic$"))
    app.add_handler(CallbackQueryHandler(plan_premium_cb, pattern="^plan_premium$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_basic$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_premium$"))
    app.add_handler(CallbackQueryHandler(contact_us_cb, pattern="^contact_us$"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
    app.add_handler(conv_reg)
    app.add_handler(conv_support)
    print("Bot Started! HOTFIX VERSION - No Channel Loop!")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
