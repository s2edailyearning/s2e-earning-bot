import os, re, threading, json
from datetime import date, datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_ID", os.getenv("CHANNEL_USERNAME", "@s2edayincome"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/s2edayincome")
ADMIN_UPI = os.getenv("ADMIN_UPI", "s2eearning@upi")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@s2edayincome")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/s2edayincome")

ADMIN_ID_LIST = [7256515560, 8544307598]
_env_ids = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID") or ""
if _env_ids:
    for x in _env_ids.replace(",", " ").split():
        if x.strip().isdigit():
            _id = int(x.strip())
            if _id not in ADMIN_ID_LIST: ADMIN_ID_LIST.append(_id)

DEPOSIT_LINK_BASIC = f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=500&cu=INR&tn=Basic"
DEPOSIT_LINK_PREMIUM = f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=1000&cu=INR&tn=Premium"

# Config
WITHDRAW_OPTIONS = [200, 300, 500, 1000]
WITHDRAW_MIN = 200
WITHDRAW_MAX = 1000
PLATFORM_FEE_PERCENT = 7  # 7% - 5% service + 2% processing - LEGAL & TRANSPARENT
WITHDRAW_ONCE_PER_DAY = True

app_flask = Flask(__name__)
real_tasks_db = {}

@app_flask.route('/')
def home(): return f"S2E Ultimate - Withdraw System 200-1000 + 7% Fee | Admin: {ADMIN_ID_LIST}"

@app_flask.route('/admin/tasks', methods=['GET','POST'])
def admin_tasks_panel():
    if request.method == 'POST':
        try:
            data = request.json
            date_key = data.get('date')
            tasks = data.get('tasks', [])
            real_tasks_db[date_key] = tasks
            return jsonify({"status": "success", "message": f"Added {len(tasks)} tasks for {date_key}"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return "Use bot /admin"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

NAME, GENDER, DOB, MOBILE, UPI, PINCODE, PROFESSION, SUPPORT_MSG = range(8)

users_db = {}
referrals_db = {}
tasks_db = {}
daily_done = {}
bonus_balance = {}
banned_users = set()
pending_daily = {}
user_plans = {}
pending_plans = {}
referral_map = {}
pending_referrals = {}
referral_earnings = {}

# WITHDRAW SYSTEM - NEW
withdraw_requests = {}  # uid -> {amount, fee, net_amount, upi, status: processing/approved/rejected, date, request_date}
withdraw_done_date = {}  # uid -> date string (once per day)
withdraw_history = {}  # uid -> list of history

def is_admin(uid): return uid in ADMIN_ID_LIST
def calculate_age(d): 
    today=date.today()
    return today.year-d.year-((today.month,today.day)<(d.month,d.day))
def get_balance(uid): return referrals_db.get(uid,0)*10 + tasks_db.get(uid,0)*5 + bonus_balance.get(uid,0) + referral_earnings.get(uid,0)
def get_tasks(uid): return referrals_db.get(uid,0) + tasks_db.get(uid,0)
def check_plan_active(uid):
    plan = user_plans.get(uid)
    if not plan: return False, "No Plan", None
    if plan.get('status') != 'active': return False, f"{plan.get('plan','')} Pending", None
    expiry = plan.get('expiry')
    if expiry and date.today() > expiry: return False, f"{plan.get('plan','').upper()} Expired", expiry
    return True, f"{plan.get('plan','').upper()} till {expiry}", expiry
def is_first_day_free(uid):
    reg_date = users_db.get(uid, {}).get('reg_date')
    if not reg_date: return False
    return (date.today() - reg_date).days <= 1
def get_today_task():
    today_str = str(date.today())
    tasks = real_tasks_db.get(today_str)
    if not tasks:
        return {"title": "Join Sponsor Channel", "link": CHANNEL_LINK, "reward": 5, "company_payout": 0, "category": "default", "desc": "Join channel"}
    return tasks[0] if isinstance(tasks, list) else tasks

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

async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    cnt=referrals_db.get(uid,0)
    total_commission = referral_earnings.get(uid,0)
    ref_link = f"https://t.me/{context.bot.username}?start={uid}"
    await q.message.reply_text(f"👥 Referrals\nActive: {cnt}\nTask Bonus: ₹{cnt*10}\nPlan Commission: ₹{total_commission}\nLink: {ref_link}", reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    is_free = is_first_day_free(uid)
    wr = withdraw_requests.get(uid)
    wr_status = f"\n💸 Withdraw Status: {wr.get('status','')} - ₹{wr.get('amount',0)} (Net ₹{wr.get('net_amount',0)})" if wr else ""
    await q.message.reply_text(f"💰 Balance: ₹{get_balance(uid)}\nTasks: {get_tasks(uid)}/15\nPlan: {plan_status}{' FREE' if is_free and not is_active else ''}{wr_status}\n\n/withdrawstatus - Check withdraw", reply_markup=main_menu())

# NEW WITHDRAW SYSTEM - Your Idea
async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    is_free = is_first_day_free(uid)
    bal=get_balance(uid)
    
    # Check once per day
    today_str = str(date.today())
    if WITHDRAW_ONCE_PER_DAY and withdraw_done_date.get(uid)==today_str:
        await q.message.reply_text(f"🔒 Withdraw Once Per Day Only!\n\nYou already withdrew today: {today_str}\nTomorrow malli try cheyyi!\n\nStatus: /withdrawstatus", reply_markup=main_menu())
        return
    
    # Check pending withdraw
    if uid in withdraw_requests and withdraw_requests[uid].get('status')=='processing':
        await q.message.reply_text(f"⏳ Withdraw Already Processing!\n\nAmount: ₹{withdraw_requests[uid].get('amount')}\nStatus: Processing\nCheck: /withdrawstatus\n\nAdmin approve chesaka completed avuthundi!", reply_markup=main_menu())
        return
    
    # Balance check
    if bal < WITHDRAW_MIN:
        if is_free:
            await q.message.reply_text(f"💸 Balance Low: ₹{bal}/₹{WITHDRAW_MIN}\nFree trial lo 200 vaste withdraw! Referrals tho earning cheyyi!", reply_markup=main_menu())
        else:
            if not is_active:
                await q.message.reply_text(f"🔒 Plan needed! {plan_status}", reply_markup=main_menu())
            else:
                await q.message.reply_text(f"💸 Not Eligible: ₹{bal}/₹{WITHDRAW_MIN} (Min 200)", reply_markup=main_menu())
        return
    
    if not is_active and not is_free:
        await q.message.reply_text(f"🔒 Plan Expired/No Plan! {plan_status}\nRenew cheyyi!", reply_markup=main_menu())
        return
    
    # Build withdraw options based on balance - Your Logic
    # Example: balance 566 -> show 200,300,500 highlight, 1000 not highlight
    buttons = []
    row = []
    info_text = f"💸 Withdraw - Balance: ₹{bal}\nMin: ₹{WITHDRAW_MIN} Max: ₹{WITHDRAW_MAX} (Once per day, Multiple of 100)\n\nSelect Amount:\n"
    
    for amount in WITHDRAW_OPTIONS:
        if amount <= bal and amount <= WITHDRAW_MAX:
            # Highlighted / Enabled
            row.append(InlineKeyboardButton(f"✅ ₹{amount}", callback_data=f"wd_select_{amount}"))
            info_text += f"✅ ₹{amount} - Available\n"
        else:
            # Not highlighted / Disabled - insufficient
            info_text += f"❌ ₹{amount} - Insufficient (Need ₹{amount}, Have ₹{bal})\n"
        
        # 2 buttons per row
        if len(row)==2:
            buttons.append(row)
            row=[]
    if row: buttons.append(row)
    
    # Add info about disabled
    info_text += f"\nExample: Balance ₹566 unte 200,300,500 highlight, 1000 highlight kadu (insufficient)!\n"
    info_text += f"\nOnce per day only! UPI confirmation tarvata admin ki request velthundi!\n"
    info_text += f"\nFee: {PLATFORM_FEE_PERCENT}% Platform Fee (Legal)"
    
    buttons.append([InlineKeyboardButton("📊 Check Withdraw Status", callback_data="wd_status")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_menu")])
    
    await q.message.reply_text(info_text, reply_markup=InlineKeyboardMarkup(buttons))

async def wd_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    
    try:
        amount = int(q.data.split("_")[-1])
    except: return
    
    # Validate again
    if amount > bal:
        await q.message.reply_text(f"❌ Insufficient Balance! Need ₹{amount}, Have ₹{bal}\nSelect lower amount!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 Back to Withdraw", callback_data="withdraw")]]))
        return
    if amount < WITHDRAW_MIN or amount > WITHDRAW_MAX:
        await q.message.reply_text(f"❌ Amount must be {WITHDRAW_MIN}-{WITHDRAW_MAX} and multiple of 100!", reply_markup=main_menu())
        return
    if amount % 100 != 0:
        await q.message.reply_text(f"❌ Amount must be multiple of 100! Eg: 200,300,500,1000", reply_markup=main_menu())
        return
    
    # Calculate fee
    fee = int(amount * PLATFORM_FEE_PERCENT / 100)
    net_amount = amount - fee
    
    user_upi = users_db.get(uid,{}).get('upi','Not Set')
    
    text = (
        f"💸 Withdraw Confirmation\n\n"
        f"Amount Selected: ₹{amount}\n"
        f"Platform Fee ({PLATFORM_FEE_PERCENT}%): -₹{fee}\n"
        f"  • Service Charge: 5%\n"
        f"  • Processing + Maintenance: 2%\n"
        f"Net You Get: ₹{net_amount}\n\n"
        f"Your UPI ID: {user_upi}\n\n"
        f"Is UPI Correct?\n"
        f"✅ Correct ayithe admin ki request velthundi\n"
        f"❌ Wrong ayithe update cheyyi\n\n"
        f"Legal: Fee is platform maintenance charge, shown transparent!"
    )
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Yes, Correct - Confirm ₹{amount} (Net ₹{net_amount})", callback_data=f"wd_confirm_{amount}")],
        [InlineKeyboardButton("✏️ Wrong - Update UPI", callback_data="wd_update_upi")],
        [InlineKeyboardButton("🔙 Back", callback_data="withdraw")]
    ])
    await q.message.reply_text(text, reply_markup=kb)

async def wd_update_upi_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("✏️ Send new UPI ID:\nExample: yourname@upi\n\nType new UPI now:")

# Handle UPI update via text - simple handler in main message handler
async def handle_upi_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This will be called for any text that looks like UPI and user is in withdraw flow
    # For simplicity, we check if user recently clicked wrong UPI
    uid = update.effective_user.id
    text = update.message.text.strip()
    if "@" in text and len(text)>5 and text.count("@")==1:
        # Could be UPI update
        # Check if user has pending withdraw confirmation
        # We save new UPI
        if uid in users_db:
            old_upi = users_db[uid].get('upi','')
            users_db[uid]['upi']=text
            await update.message.reply_text(f"✅ UPI Updated!\nOld: {old_upi}\nNew: {text}\n\nNow go to Withdraw again!", reply_markup=main_menu())
            return True
    return False

async def wd_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    
    try:
        amount = int(q.data.split("_")[-1])
    except: return
    
    if amount > bal:
        await q.message.reply_text(f"❌ Insufficient! Balance ₹{bal}, Tried ₹{amount}")
        return
    
    # Check once per day again
    today_str = str(date.today())
    if withdraw_done_date.get(uid)==today_str:
        await q.message.reply_text("🔒 Already withdrew today! Once per day only!", reply_markup=main_menu())
        return
    
    fee = int(amount * PLATFORM_FEE_PERCENT / 100)
    net_amount = amount - fee
    user_upi = users_db.get(uid,{}).get('upi','')
    
    # Deduct from balance immediately (or hold)
    # For safety, deduct now and hold in processing
    # Reset earnings proportionally - simple: deduct from bonus first, then tasks, then referrals
    # For simplicity, we set balance to balance - amount (user requested amount, fee is our cut)
    # Actually user gets net_amount, but we deduct full amount from wallet
    # Implementation: reduce bonus_balance etc.
    
    # Simple deduction logic
    remaining = amount
    # Deduct from bonus
    bb = bonus_balance.get(uid,0)
    if bb >= remaining:
        bonus_balance[uid]=bb-remaining
        remaining=0
    else:
        remaining-=bb
        bonus_balance[uid]=0
    # Deduct from referral earnings
    if remaining>0:
        re = referral_earnings.get(uid,0)
        if re >= remaining:
            referral_earnings[uid]=re-remaining
            remaining=0
        else:
            remaining-=re
            referral_earnings[uid]=0
    # Deduct from tasks and referrals
    if remaining>0:
        # Deduct tasks
        tasks_val = tasks_db.get(uid,0)*5
        if tasks_val >= remaining:
            # Reduce tasks count
            tasks_to_reduce = remaining // 5
            tasks_db[uid]=max(0, tasks_db.get(uid,0)-tasks_to_reduce)
            if remaining %5 !=0:
                bonus_balance[uid]=bonus_balance.get(uid,0)-(remaining%5)
            remaining=0
        else:
            remaining-=tasks_val
            tasks_db[uid]=0
            # Deduct referrals
            ref_val = referrals_db.get(uid,0)*10
            if ref_val >= remaining:
                ref_to_reduce = remaining //10
                referrals_db[uid]=max(0, referrals_db.get(uid,0)-ref_to_reduce)
                remaining=0
            else:
                referrals_db[uid]=0
    
    # Create withdraw request - processing
    withdraw_requests[uid]={
        'amount': amount,
        'fee': fee,
        'net_amount': net_amount,
        'upi': user_upi,
        'status': 'processing',
        'date': today_str,
        'request_time': datetime.now().isoformat(),
        'fee_percent': PLATFORM_FEE_PERCENT
    }
    withdraw_done_date[uid]=today_str
    
    # Add to history
    if uid not in withdraw_history: withdraw_history[uid]=[]
    withdraw_history[uid].append(withdraw_requests[uid].copy())
    
    await q.message.reply_text(
        f"✅ Withdraw Request Submitted!\n\n"
        f"Amount: ₹{amount}\nFee ({PLATFORM_FEE_PERCENT}%): ₹{fee}\nNet: ₹{net_amount}\nUPI: {user_upi}\nStatus: ⏳ Processing\nDate: {today_str}\n\n"
        f"Admin 24hrs lo approve chestaru!\nCheck status: /withdrawstatus\n\nOnce per day - tomorrow malli withdraw cheyochu!",
        reply_markup=main_menu()
    )
    
    # Notify admin with final request
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Approve ₹{net_amount} to {user_upi}", callback_data=f"wd_admin_approve_{uid}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"wd_admin_reject_{uid}")],
                [InlineKeyboardButton("👤 User Info", callback_data=f"admin_userinfo_{uid}")]
            ])
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"💸 NEW WITHDRAW REQUEST - FINAL!\n\nUser: {users_db.get(uid,{}).get('name')} ID: {uid}\nAmount: ₹{amount}\nFee {PLATFORM_FEE_PERCENT}%: ₹{fee}\nNet to Send: ₹{net_amount}\nUPI: {user_upi} (Confirmed by user)\nDate: {today_str}\nStatus: Processing → Need Approval\n\nApprove cheste user ki 'Completed' ani vastundi!",
                reply_markup=kb
            )
        except: pass

async def wd_status_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    wr = withdraw_requests.get(uid)
    if not wr:
        history = withdraw_history.get(uid, [])
        if history:
            last = history[-1]
            await q.message.reply_text(f"📊 Last Withdraw:\nAmount: ₹{last.get('amount')} Net: ₹{last.get('net_amount')} UPI: {last.get('upi')} Status: {last.get('status')} Date: {last.get('date')}", reply_markup=main_menu())
        else:
            await q.message.reply_text("No withdraw history! /withdraw to start", reply_markup=main_menu())
        return
    
    status_text = "⏳ Processing - Admin will approve in 24hrs" if wr.get('status')=='processing' else "✅ Completed/Approved - Money sent!" if wr.get('status')=='approved' else "❌ Rejected"
    
    await q.message.reply_text(
        f"📊 Withdraw Status\n\n"
        f"Amount: ₹{wr.get('amount')}\nFee: ₹{wr.get('fee')} ({wr.get('fee_percent')}%)\nNet: ₹{wr.get('net_amount')}\nUPI: {wr.get('upi')}\nDate: {wr.get('date')}\nStatus: {status_text}\n\n"
        f"{'✅ Approved - Check UPI!' if wr.get('status')=='approved' else '⏳ Wait for admin approval...' if wr.get('status')=='processing' else 'Contact admin'}",
        reply_markup=main_menu()
    )

async def wd_admin_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    wr = withdraw_requests.get(uid)
    if not wr:
        await q.message.reply_text(f"No pending for {uid}")
        return
    wr['status']='approved'
    withdraw_requests[uid]=wr
    # Update history last entry
    if uid in withdraw_history and withdraw_history[uid]:
        withdraw_history[uid][-1]['status']='approved'
    
    await q.message.reply_text(f"✅ Approved withdraw for {uid} Net ₹{wr.get('net_amount')} to {wr.get('upi')}")
    try:
        await context.bot.send_message(chat_id=uid, text=f"🎉 Withdraw Approved! ✅\n\nAmount: ₹{wr.get('amount')}\nFee: ₹{wr.get('fee')}\nNet Received: ₹{wr.get('net_amount')}\nUPI: {wr.get('upi')}\nStatus: ✅ Completed\n\nMoney sent! Check UPI app!", reply_markup=main_menu())
    except: pass

async def wd_admin_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    wr = withdraw_requests.get(uid)
    if not wr: return
    # Refund balance
    amount = wr.get('amount')
    bonus_balance[uid]=bonus_balance.get(uid,0)+amount
    wr['status']='rejected'
    withdraw_requests.pop(uid, None)
    withdraw_done_date.pop(uid, None)
    await q.message.reply_text(f"❌ Rejected withdraw for {uid} - Refunded ₹{amount}")
    try:
        await context.bot.send_message(chat_id=uid, text=f"❌ Withdraw Rejected!\nAmount ₹{amount} refunded to wallet!\nContact admin {SUPPORT_USERNAME}", reply_markup=main_menu())
    except: pass

# Other handlers (daily, plans etc - simplified)
async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    is_free_day = is_first_day_free(uid)
    if not is_active and not is_free_day:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Plan", callback_data="plan_basic")]])
        await q.message.reply_text(f"🔒 Free trial over! Plan needed: {plan_status}", reply_markup=kb)
        return
    today=str(date.today())
    if daily_done.get(uid)==today or (uid in pending_daily):
        await q.message.reply_text(f"Already done/pending!", reply_markup=main_menu()); return
    task = get_today_task()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"📢 {task.get('title')}", url=task.get('link', CHANNEL_LINK))],[InlineKeyboardButton("✅ Verify", callback_data="daily_verify")]])
    await q.message.reply_text(f"Today Task: {task.get('title')}\nReward ₹{task.get('reward',5)}\nPlan: {plan_status}", reply_markup=kb)

async def daily_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    today=str(date.today())
    if daily_done.get(uid)==today: return
    task = get_today_task()
    pending_daily[uid]={'date': today, 'task': task}
    await q.message.reply_text(f"⏳ Task Submitted! Waiting approval ₹{task.get('reward',5)}", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_daily_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_daily_{uid}")]])
            await context.bot.send_message(chat_id=admin_id, text=f"Daily Pending {uid} Task {task.get('title')}", reply_markup=kb)
        except: pass

async def admin_approve_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    pending = pending_daily.get(uid)
    if not pending: return
    reward = pending.get('task',{}).get('reward',5)
    is_first = tasks_db.get(uid,0)==0
    daily_done[uid]=pending.get('date')
    tasks_db[uid]=tasks_db.get(uid,0)+1
    if reward!=5: bonus_balance[uid]=bonus_balance.get(uid,0)+(reward-5)
    del pending_daily[uid]
    ref_id = pending_referrals.get(uid)
    if ref_id and is_first:
        referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
        del pending_referrals[uid]
    await q.message.reply_text(f"✅ Approved {uid} +₹{reward}")
    try: await context.bot.send_message(chat_id=uid, text=f"Task Approved +₹{reward} Balance ₹{get_balance(uid)}", reply_markup=main_menu())
    except: pass

async def admin_reject_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    if uid in pending_daily: del pending_daily[uid]; await q.message.reply_text(f"Rejected {uid}")

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    is_active, plan_status, _ = check_plan_active(q.from_user.id)
    await q.message.reply_text(f"Plans:\nBasic ₹500 30 Days Normal Support\nPremium ₹1000 90 Days Premium Support + ₹100 Bonus\nYour: {plan_status}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📦 Basic ₹500", callback_data="plan_basic")],[InlineKeyboardButton("👑 Premium ₹1000", callback_data="plan_premium")]]))

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay ₹500", url=DEPOSIT_LINK_BASIC)],[InlineKeyboardButton("✅ I Paid", callback_data="verify_basic")]])
    await q.message.reply_text(f"Basic ₹500 - 30 Days\nPay: {DEPOSIT_LINK_BASIC}", reply_markup=kb)

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay ₹1000", url=DEPOSIT_LINK_PREMIUM)],[InlineKeyboardButton("✅ I Paid", callback_data="verify_premium")]])
    await q.message.reply_text(f"Premium ₹1000 - 90 Days + ₹100 Bonus\nPay: {DEPOSIT_LINK_PREMIUM}", reply_markup=kb)

async def verify_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    plan_type = "basic" if "basic" in q.data else "premium"
    pending_plans[uid]=plan_type
    user_plans[uid]={'plan': plan_type, 'status': 'pending', 'start': date.today(), 'expiry': None}
    await q.message.reply_text(f"{plan_type.upper()} Payment Pending Approval!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Approve {plan_type.upper()}", callback_data=f"admin_approve_plan_{uid}_{plan_type}")]])
            await context.bot.send_message(chat_id=admin_id, text=f"Plan Pending {uid} {plan_type} Ref {referral_map.get(uid,'None')}", reply_markup=kb)
        except: pass

async def admin_approve_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts = q.data.split("_")
    uid = int(parts[3]); plan_type = parts[4]
    today = date.today()
    expiry = today + timedelta(days=30 if plan_type=='basic' else 90)
    user_plans[uid]={'plan': plan_type, 'status': 'active', 'start': today, 'expiry': expiry}
    pending_plans.pop(uid, None)
    if plan_type=='premium': bonus_balance[uid]=bonus_balance.get(uid,0)+100
    ref_id = referral_map.get(uid)
    commission = 50 if plan_type=='basic' else 100
    if ref_id: referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+commission
    await q.message.reply_text(f"Approved {plan_type} for {uid} Exp {expiry}")

async def admin_reject_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    if uid in pending_plans: del pending_plans[uid]; user_plans.pop(uid, None); await q.message.reply_text(f"Rejected plan {uid}")

async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"Contact {SUPPORT_USERNAME}", reply_markup=main_menu())

async def send_support_msg_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("Type message:")
    return SUPPORT_MSG

async def get_support_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sent!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("Menu:", reply_markup=main_menu())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if context.args:
        try:
            ref_id=int(context.args[0])
            if ref_id!=uid and uid not in users_db:
                referral_map[uid]=ref_id
                pending_referrals[uid]=ref_id
        except: pass
    if uid in users_db and users_db[uid].get("registered"):
        is_active, plan_status, _ = check_plan_active(uid)
        await update.message.reply_text(f"Welcome {users_db[uid]['name']} ✅ Balance ₹{get_balance(uid)} Plan {plan_status}", reply_markup=main_menu())
        return
    await update.message.reply_text(f"Welcome S2E! 🎁 Day1 FREE Earn upto ₹200!\nID: {uid}", reply_markup=join_channel_keyboard(False))

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    users_db[uid]={'reg_date': date.today()}
    await q.message.reply_text("Registration 1/7 Name:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; name=update.message.text.strip()
    if len(name)<2: await update.message.reply_text("Enter valid name:"); return NAME
    users_db[uid]['name']=name
    kb=ReplyKeyboardMarkup([["Male","Female","Other"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Hi {name}! Gender:", reply_markup=kb)
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; g=update.message.text.strip()
    users_db[uid]['gender']=g
    await update.message.reply_text("DOB DD-MM-YYYY", reply_markup=ReplyKeyboardRemove())
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; txt=update.message.text.strip()
    try:
        dob=datetime.strptime(txt, "%d-%m-%Y").date(); age=calculate_age(dob)
        if age<18: await update.message.reply_text(f"Age {age} - 18+ only!"); return DOB
    except: await update.message.reply_text("Use DD-MM-YYYY:"); return DOB
    users_db[uid]['dob']=txt; users_db[uid]['age']=age
    await update.message.reply_text(f"Age {age}! Mobile:")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; mob=update.message.text.strip()
    mob_clean = re.sub(r'\D', '', mob)
    if mob_clean.startswith('91') and len(mob_clean)==12: mob_clean=mob_clean[2:]
    if not re.match(r'^[6-9]\d{9}$', mob_clean): await update.message.reply_text("Invalid Mobile!"); return MOBILE
    users_db[uid]['mobile']=mob_clean
    await update.message.reply_text(f"Mobile {mob_clean}! UPI:")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; upi=update.message.text.strip()
    if "@" not in upi: await update.message.reply_text("Invalid UPI!"); return UPI
    users_db[uid]['upi']=upi
    await update.message.reply_text("Pincode:")
    return PINCODE

async def get_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; pin=update.message.text.strip()
    if not re.match(r"^\d{6}$", pin): await update.message.reply_text("6 digit:"); return PINCODE
    users_db[uid]['pincode']=pin
    kb=ReplyKeyboardMarkup([["Student","Employee","Self-Employed","Business"],["Freelancer","Other"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Profession:", reply_markup=kb)
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    users_db[uid]['profession']=update.message.text.strip()
    users_db[uid]['registered']=True
    if 'reg_date' not in users_db[uid]: users_db[uid]['reg_date']=date.today()
    await update.message.reply_text(f"Registration Done! Link: https://t.me/{context.bot.username}?start={uid}", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text("Menu: Today free!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu:", reply_markup=main_menu())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if not is_admin(uid): return
    await update.message.reply_text(f"ADMIN PANEL\nUsers {len(users_db)}\nPending Daily {len(pending_daily)}\nPending Plans {len(pending_plans)}\nWithdraw Processing {len([w for w in withdraw_requests.values() if w.get('status')=='processing'])}\n\n/pending /pendingplans /withdrawrequests\n/approve <id> /approveplan <id> basic/premium\n/approvewithdraw <id> /rejectwithdraw <id>\n/addtask DATE | Title | Link | Reward | Payout\nFee: {PLATFORM_FEE_PERCENT}% - Legal")

async def withdrawrequests_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    processing = {k:v for k,v in withdraw_requests.items() if v.get('status')=='processing'}
    if not processing: await update.message.reply_text("No processing withdraws!"); return
    msg="Processing Withdraws:\n\n"
    for uid, wr in processing.items():
        msg+=f"{uid} | {users_db.get(uid,{}).get('name')} | ₹{wr.get('amount')} Fee ₹{wr.get('fee')} Net ₹{wr.get('net_amount')} UPI {wr.get('upi')}\n/approvewithdraw {uid} /rejectwithdraw {uid}\n\n"
    await update.message.reply_text(msg[:4000])

async def approvewithdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage: /approvewithdraw <id>"); return
    try: target_id=int(context.args[0])
    except: return
    wr = withdraw_requests.get(target_id)
    if not wr: await update.message.reply_text("No request"); return
    wr['status']='approved'
    withdraw_requests[target_id]=wr
    await update.message.reply_text(f"Approved withdraw {target_id} Net ₹{wr.get('net_amount')}")
    try: await context.bot.send_message(chat_id=target_id, text=f"Withdraw Approved! ✅ Net ₹{wr.get('net_amount')} sent to {wr.get('upi')} - Completed!", reply_markup=main_menu())
    except: pass

async def rejectwithdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try: target_id=int(context.args[0])
    except: return
    wr = withdraw_requests.get(target_id)
    if not wr: return
    amount = wr.get('amount')
    bonus_balance[target_id]=bonus_balance.get(target_id,0)+amount
    withdraw_requests.pop(target_id, None)
    withdraw_done_date.pop(target_id, None)
    await update.message.reply_text(f"Rejected {target_id} refunded ₹{amount}")

async def addtask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = " ".join(context.args) if context.args else ""
    if "|" not in text: await update.message.reply_text("Usage: /addtask DATE | Title | Link | Reward | Payout"); return
    try:
        parts = [p.strip() for p in text.split("|")]
        date_key = parts[0]
        title = parts[1] if len(parts)>1 else "Task"
        link = parts[2] if len(parts)>2 else CHANNEL_LINK
        reward = int(parts[3]) if len(parts)>3 and parts[3].isdigit() else 5
        payout = int(parts[4]) if len(parts)>4 and parts[4].isdigit() else 0
        task = {"title": title, "link": link, "reward": reward, "company_payout": payout, "category": "general", "desc": "Task"}
        if date_key not in real_tasks_db: real_tasks_db[date_key]=[]
        if isinstance(real_tasks_db[date_key], dict): real_tasks_db[date_key]=[real_tasks_db[date_key]]
        real_tasks_db[date_key].append(task)
        await update.message.reply_text(f"Added task for {date_key}: {title} Profit ₹{payout-reward}")
    except Exception as e: await update.message.reply_text(f"Error {e}")

async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    today = str(date.today())
    tasks = real_tasks_db.get(today, [])
    await update.message.reply_text(f"Tasks {today}: {json.dumps(tasks)[:4000]}")

async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not pending_daily: await update.message.reply_text("No pending daily!"); return
    msg = f"Pending Daily {len(pending_daily)}:\n\n"
    for uid, data in pending_daily.items():
        msg+=f"{uid} | {data.get('task',{}).get('title')} | /approve {uid}\n"
    await update.message.reply_text(msg[:4000])

async def pendingplans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not pending_plans: await update.message.reply_text("No pending plans!"); return
    msg = f"Pending Plans {len(pending_plans)}:\n\n"
    for uid, ptype in pending_plans.items():
        msg+=f"{uid} | {ptype.upper()} | /approveplan {uid} {ptype}\n"
    await update.message.reply_text(msg[:4000])

async def plans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not user_plans: await update.message.reply_text("No plans"); return
    msg = "Plans:\n\n"
    for uid, p in list(user_plans.items())[:20]:
        msg+=f"{uid} | {p.get('plan','').upper()} | {p.get('status')} | Exp {p.get('expiry')}\n"
    await update.message.reply_text(msg)

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try: target_id=int(context.args[0])
    except: return
    if target_id in pending_daily:
        is_first = tasks_db.get(target_id,0)==0
        reward = pending_daily[target_id].get('task',{}).get('reward',5)
        daily_done[target_id]=pending_daily[target_id].get('date')
        tasks_db[target_id]=tasks_db.get(target_id,0)+1
        if reward!=5: bonus_balance[target_id]=bonus_balance.get(target_id,0)+(reward-5)
        del pending_daily[target_id]
        ref_id = pending_referrals.get(target_id)
        if ref_id and is_first:
            referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
            del pending_referrals[target_id]
        await update.message.reply_text(f"Approved {target_id} +₹{reward}")

async def approveplan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if len(context.args)<2: return
    try: target_id=int(context.args[0]); ptype=context.args[1].lower()
    except: return
    if ptype not in ['basic','premium']: return
    today = date.today()
    expiry = today + timedelta(days=30 if ptype=='basic' else 90)
    user_plans[target_id]={'plan': ptype, 'status': 'active', 'start': today, 'expiry': expiry}
    pending_plans.pop(target_id, None)
    if ptype=='premium': bonus_balance[target_id]=bonus_balance.get(target_id,0)+100
    ref_id = referral_map.get(target_id)
    if ref_id: referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+(50 if ptype=='basic' else 100)
    await update.message.reply_text(f"Approved {ptype} for {target_id}")

async def user_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try: target_id=int(context.args[0])
    except: return
    data=users_db.get(target_id)
    if not data: await update.message.reply_text("Not found"); return
    await update.message.reply_text(f"User {target_id} {data.get('name')} Bal ₹{get_balance(target_id)} UPI {data.get('upi')} Plan {user_plans.get(target_id)}")

async def withdrawstatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    wr = withdraw_requests.get(uid)
    if not wr:
        await update.message.reply_text("No active withdraw! Use /menu -> Withdraw", reply_markup=main_menu())
        return
    status = wr.get('status')
    if status=='processing':
        await update.message.reply_text(f"⏳ Withdraw Processing!\nAmount ₹{wr.get('amount')} Fee ₹{wr.get('fee')} Net ₹{wr.get('net_amount')} UPI {wr.get('upi')}\nAdmin will approve in 24hrs!", reply_markup=main_menu())
    elif status=='approved':
        await update.message.reply_text(f"✅ Withdraw Completed!\nNet ₹{wr.get('net_amount')} sent to {wr.get('upi')}!", reply_markup=main_menu())
    else:
        await update.message.reply_text(f"Status {status}", reply_markup=main_menu())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it's UPI update during withdraw
    text = update.message.text.strip()
    uid = update.effective_user.id
    if "@" in text and uid in users_db and len(text)>5:
        # If user recently tried withdraw and UPI wrong, update it
        # Simple heuristic: if text looks like UPI and user has no pending withdraw or we allow update anytime
        if text.count("@")==1 and "." not in text.split("@")[-1] or True:
            # Allow UPI update
            if uid in users_db:
                old = users_db[uid].get('upi','')
                if text != old and "@" in text:
                    users_db[uid]['upi']=text
                    await update.message.reply_text(f"✅ UPI Updated from {old} to {text}\nNow withdraw again!", reply_markup=main_menu())
                    return

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
    app.add_handler(CommandHandler("withdrawstatus", withdrawstatus_cmd))
    app.add_handler(CommandHandler("withdrawrequests", withdrawrequests_cmd))
    app.add_handler(CommandHandler("approvewithdraw", approvewithdraw_cmd))
    app.add_handler(CommandHandler("rejectwithdraw", rejectwithdraw_cmd))
    app.add_handler(CommandHandler("addtask", addtask_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("pendingplans", pendingplans_cmd))
    app.add_handler(CommandHandler("plans", plans_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("approveplan", approveplan_cmd))
    app.add_handler(CommandHandler("userinfo", user_info_cmd))
    app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
    app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(daily_cb, pattern="^daily$"))
    app.add_handler(CallbackQueryHandler(daily_verify_cb, pattern="^daily_verify$"))
    app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern="^admin_approve_daily_"))
    app.add_handler(CallbackQueryHandler(admin_reject_daily_cb, pattern="^admin_reject_daily_"))
    app.add_handler(CallbackQueryHandler(admin_approve_plan_cb, pattern="^admin_approve_plan_"))
    app.add_handler(CallbackQueryHandler(admin_reject_plan_cb, pattern="^admin_reject_plan_"))
    app.add_handler(CallbackQueryHandler(withdraw_cb, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(wd_select_cb, pattern="^wd_select_"))
    app.add_handler(CallbackQueryHandler(wd_update_upi_cb, pattern="^wd_update_upi$"))
    app.add_handler(CallbackQueryHandler(wd_confirm_cb, pattern="^wd_confirm_"))
    app.add_handler(CallbackQueryHandler(wd_status_cb, pattern="^wd_status$"))
    app.add_handler(CallbackQueryHandler(wd_admin_approve_cb, pattern="^wd_admin_approve_"))
    app.add_handler(CallbackQueryHandler(wd_admin_reject_cb, pattern="^wd_admin_reject_"))
    app.add_handler(CallbackQueryHandler(support_plans_cb, pattern="^support_plans$"))
    app.add_handler(CallbackQueryHandler(plan_basic_cb, pattern="^plan_basic$"))
    app.add_handler(CallbackQueryHandler(plan_premium_cb, pattern="^plan_premium$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_basic$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_premium$"))
    app.add_handler(CallbackQueryHandler(contact_us_cb, pattern="^contact_us$"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
    app.add_handler(conv_reg)
    app.add_handler(conv_support)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print(f"Bot Started! Withdraw 200-1000 + 7% Fee + Once Per Day System Active!")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
