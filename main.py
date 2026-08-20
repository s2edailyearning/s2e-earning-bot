
import os, re, threading, json
from datetime import date, datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/s2edayincome")
ADMIN_UPI = os.getenv("ADMIN_UPI", "s2eearning@upi")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@s2edayincome")

ADMIN_ID_LIST = [7256515560, 8544307598]
_env = os.getenv("ADMIN_IDS") or ""
if _env:
    for x in _env.replace(",", " ").split():
        if x.strip().isdigit():
            _id = int(x.strip())
            if _id not in ADMIN_ID_LIST: ADMIN_ID_LIST.append(_id)

DEPOSIT_LINK_BASIC = f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=500&cu=INR&tn=Basic"
DEPOSIT_LINK_PREMIUM = f"upi://pay?pa={ADMIN_UPI}&pn=S2E&am=1000&cu=INR&tn=Premium"

# === CONFIG - EASY ANTI-SCAM ===
WITHDRAW_OPTIONS = [200, 300, 500, 1000]
WITHDRAW_MIN = 200
WITHDRAW_MAX = 1000
PLATFORM_FEE_PERCENT = 7
TASKS_REQUIRED_FOR_WITHDRAW = 17
DAILY_TASK_LIMIT_BASIC = 10
DAILY_TASK_LIMIT_PREMIUM = 20
DAILY_TASK_LIMIT_FREE = 1
DAILY_EARNING_CAP_BASIC = 200
DAILY_EARNING_CAP_PREMIUM = 500

# Easy anti-scam - NO PAPER CODE!
EASY_ANTI_SCAM = True  # True = No paper code, just duplicate + name + time check
SCREENSHOT_TIME_LIMIT_MINUTES = 15  # Must upload within 15 mins after opening task

app_flask = Flask(__name__)
real_tasks_db = {}
real_tasks_basic_db = {}
real_tasks_premium_db = {}

@app_flask.route('/')
def home(): return "S2E Easy Anti-Scam - No Paper Code - User Friendly!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

NAME, GENDER, DOB, MOBILE, UPI, PINCODE, PROFESSION, UPLOAD_SCREENSHOT = range(8)

users_db = {}
referrals_db = {}
tasks_db = {}
daily_done = {}
bonus_balance = {}
banned_users = set()
warnings_db = {}  # uid -> {count, reasons, last_warning_date}
pending_daily = {}
user_plans = {}
pending_plans = {}
referral_map = {}
pending_referrals = {}
referral_earnings = {}
withdraw_requests = {}
withdraw_done_date = {}
daily_task_count = {}
daily_earning_count = {}

# Easy anti-scam storage
screenshot_hashes = set()  # file_unique_id set - prevents same image reuse
screenshot_db = {}
task_open_time = {}  # uid -> datetime when task opened

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
    data = users_db.get(uid, {})
    reg_date = data.get('reg_date')
    tasks_count = tasks_db.get(uid,0)
    if not reg_date:
        if tasks_count == 0 and not daily_done.get(uid): return True
        return False
    days_diff = (date.today() - reg_date).days
    if days_diff <= 1: return True
    if tasks_count == 0: return True
    return False
def get_plan_limits(uid):
    is_active, _, _ = check_plan_active(uid)
    if not is_active:
        if is_first_day_free(uid): return DAILY_TASK_LIMIT_FREE, 10, "free"
        return 0, 0, "none"
    plan = user_plans.get(uid, {}).get('plan','basic')
    if plan == 'premium': return DAILY_TASK_LIMIT_PREMIUM, DAILY_EARNING_CAP_PREMIUM, "premium"
    else: return DAILY_TASK_LIMIT_BASIC, DAILY_EARNING_CAP_BASIC, "basic"
def get_today_task_for_user(uid):
    today_str = str(date.today())
    plan = user_plans.get(uid, {}).get('plan','free' if is_first_day_free(uid) else 'none')
    if plan == 'premium' and today_str in real_tasks_premium_db:
        tasks = real_tasks_premium_db[today_str]
        return tasks[0] if isinstance(tasks, list) else tasks
    elif plan == 'basic' and today_str in real_tasks_basic_db:
        tasks = real_tasks_basic_db[today_str]
        return tasks[0] if isinstance(tasks, list) else tasks
    tasks = real_tasks_db.get(today_str)
    if not tasks: return {"title": "Join Sponsor Channel", "link": CHANNEL_LINK, "reward": 5, "company_payout": 0, "category": "default", "desc": "Join channel"}
    return tasks[0] if isinstance(tasks, list) else tasks
def check_daily_limits(uid):
    today_str = str(date.today())
    task_limit, earning_cap, plan_type = get_plan_limits(uid)
    if task_limit == 0: return False, "No Plan!"
    current_count = daily_task_count.get(uid, {}).get(today_str, 0)
    if current_count >= task_limit: return False, f"Daily limit {plan_type.upper()} {task_limit} tasks max"
    return True, f"{plan_type.upper()} {current_count}/{task_limit}"

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("💎 Support Plans", callback_data="support_plans"), InlineKeyboardButton("📞 Contact Us", callback_data="contact_us")]
    ])
def join_channel_keyboard(is_rejoin=False):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],[InlineKeyboardButton("✅ I Joined", callback_data="check_joined")]])

async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    cnt=referrals_db.get(uid,0)
    ref_link = f"https://t.me/{context.bot.username}?start={uid}"
    await q.message.reply_text(f"Active: {cnt} Link: {ref_link}", reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    await q.message.reply_text(f"Balance Rs{get_balance(uid)} Tasks {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW} Plan {plan_status}", reply_markup=main_menu())

# === EASY ANTI-SCAM DAILY TASK - NO PAPER CODE ===
async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    is_free_day = is_first_day_free(uid)
    if not is_active and not is_free_day:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Buy Basic Rs500", callback_data="plan_basic")],[InlineKeyboardButton("Premium Rs1000", callback_data="plan_premium")]])
        await q.message.reply_text(f"Free trial over! Plan needed: {plan_status}", reply_markup=kb); return
    can_do, limit_msg = check_daily_limits(uid)
    if not can_do:
        await q.message.reply_text(f"{limit_msg}", reply_markup=main_menu()); return
    today=str(date.today())
    if uid in pending_daily:
        await q.message.reply_text(f"Task Pending Approval! Wait!", reply_markup=main_menu()); return
    # Record task open time for time-limit check
    task_open_time[uid] = datetime.now()
    task = get_today_task_for_user(uid)
    task_limit, _, plan_type = get_plan_limits(uid)
    current_count = daily_task_count.get(uid, {}).get(today, 0)
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 Task {current_count+1}: {task.get('title')} - Open", url=task.get('link', CHANNEL_LINK))],
        [InlineKeyboardButton("📸 Upload Screenshot - Verify", callback_data="daily_upload_screenshot")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]
    ])
    await q.message.reply_text(
        f"Daily Task {current_count+1}/{task_limit} - {plan_type.upper()}\n"
        f"{task.get('title')}\nReward Rs{task.get('reward',5)} Plan {plan_status}\n\n"
        f"EASY UPLOAD: Task complete chesi screenshot teesuko, ikkade upload cheyyi!\n"
        f"No paper code needed! Just upload original screenshot within {SCREENSHOT_TIME_LIMIT_MINUTES} mins!\n"
        f"Same screenshot share cheste auto reject!",
        reply_markup=kb
    )

async def daily_upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    open_time = task_open_time.get(uid)
    if open_time:
        mins_passed = (datetime.now() - open_time).total_seconds() / 60
        if mins_passed > SCREENSHOT_TIME_LIMIT_MINUTES:
            await q.message.reply_text(f"Time over! Task open chesi {SCREENSHOT_TIME_LIMIT_MINUTES} mins lo screenshot pampali! Malli task open cheyyi!", reply_markup=main_menu())
            return ConversationHandler.END
    await q.message.reply_text(
        f"Upload Screenshot - Easy Anti-Scam\n\n"
        f"Instructions (No paper needed!):\n"
        f"1. Task complete chesina screenshot teesuko\n"
        f"2. Screenshot lo ne peru kanipinchali (Bank/Trading account lo name)\n"
        f"3. Ikkade PHOTO ga pampu! File kadu!\n"
        f"4. Same screenshot inkokaru pampithe auto reject!\n"
        f"5. {SCREENSHOT_TIME_LIMIT_MINUTES} mins lo pampali!\n\n"
        f"Now send screenshot as PHOTO:",
    )
    return UPLOAD_SCREENSHOT

async def handle_screenshot_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    today=str(date.today())
    if not update.message.photo:
        await update.message.reply_text("Please send as PHOTO, not file!")
        return UPLOAD_SCREENSHOT
    # Time limit check
    open_time = task_open_time.get(uid)
    if open_time:
        mins_passed = (datetime.now() - open_time).total_seconds() / 60
        if mins_passed > SCREENSHOT_TIME_LIMIT_MINUTES:
            await update.message.reply_text(f"Time over! {SCREENSHOT_TIME_LIMIT_MINUTES} mins lo pampali! Malli task open cheyyi!", reply_markup=main_menu())
            return ConversationHandler.END
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = photo.file_unique_id
    # === 3 WARNINGS SYSTEM - ANTI-SCAM ===
    # Anti-scam 1: Duplicate check - prevents sharing same screenshot
    if file_unique_id in screenshot_hashes:
        # Increment warning count
        if uid not in warnings_db:
            warnings_db[uid] = {'count': 0, 'reasons': [], 'history': []}
        warnings_db[uid]['count'] += 1
        warnings_db[uid]['reasons'].append(f"Duplicate screenshot on {today} - {datetime.now().isoformat()}")
        warnings_db[uid]['history'].append({'date': today, 'type': 'duplicate', 'file_id': file_unique_id})
        warnings_db[uid]['last_warning_date'] = today
        
        count = warnings_db[uid]['count']
        
        if count == 1:
            await update.message.reply_text(
                f"⚠️ WARNING 1/3 - Same Screenshot Found!\n\n"
                f"Ee screenshot ni inkokaru already use chesaru!\n"
                f"Same screenshot share chesukunatlu undi!\n\n"
                f"1st Warning ichamu! Malli original screenshot pampu!\n"
                f"3 times ayithe ban avuthavu!\n\n"
                f"Note: Admin mistake ayithe /contact lo message cheyyi!",
                reply_markup=main_menu()
            )
            return ConversationHandler.END
        elif count == 2:
            await update.message.reply_text(
                f"⚠️ WARNING 2/3 - Malli Same Screenshot!\n\n"
                f"Rendu sarlu same screenshot pampav!\n"
                f"Same screenshot share chesukunatlu undi!\n\n"
                f"2nd Warning! Inko sari cheste 3rd warning tarvata BAN avuthavu!\n"
                f"Original screenshot teesuko!",
                reply_markup=main_menu()
            )
            return ConversationHandler.END
        else:  # 3rd time - BAN
            banned_users.add(uid)
            await update.message.reply_text(
                f"🚫 BANNED! 3 Warnings Completed!\n\n"
                f"3 sarlu same screenshot share chesav!\n"
                f"Idi scam ga treat chestunnam!\n\n"
                f"Nu vvu BAN ayyav!\n"
                f"Admin mistake ayithe contact admin - admin /unban {uid} tho ban teeyochu!",
                reply_markup=ReplyKeyboardRemove()
            )
            # Notify admin
            for admin_id in ADMIN_ID_LIST:
                try:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"Unban {uid}", callback_data=f"admin_unban_{uid}")]])
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🚫 USER BANNED - 3 Warnings!\nUser {uid} Name {users_db.get(uid,{}).get('name')} Banned for duplicate screenshot 3 times!\nIf admin mistake, /unban {uid}",
                        reply_markup=kb
                    )
                except: pass
            return ConversationHandler.END
    task = get_today_task_for_user(uid)
    screenshot_hashes.add(file_unique_id)
    screenshot_db[uid] = {'file_id': file_id, 'file_unique_id': file_unique_id, 'task_date': today, 'task': task, 'upload_time': datetime.now().isoformat()}
    pending_daily[uid] = {'date': today, 'task': task, 'screenshot_file_id': file_id}
    await update.message.reply_text(f"Screenshot Received! Task: {task.get('title')} Pending Admin Verification! Admin check: Name matches your registered name? Original? Not duplicate?", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Approve Rs{task.get('reward',5)}", callback_data=f"admin_approve_daily_{uid}"),
                 InlineKeyboardButton("Reject", callback_data=f"admin_reject_daily_{uid}")],
                [InlineKeyboardButton("Ban Scam", callback_data=f"admin_ban_{uid}")]
            ])
            user_name = users_db.get(uid,{}).get('name','Unknown')
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=f"NEW SCREENSHOT - Easy Anti-Scam Check!\nUser: {user_name} ID: {uid}\nRegistered Name: {user_name}\nTask: {task.get('title')}\nCheck: Screenshot lo name {user_name} tho match ayinda? Duplicate? No - Unique!\nReward Rs{task.get('reward',5)}",
                reply_markup=kb
            )
        except: pass
    return ConversationHandler.END

async def admin_approve_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    pending = pending_daily.get(uid)
    if not pending: await q.message.reply_text(f"No pending for {uid}"); return
    reward = pending.get('task',{}).get('reward',5)
    is_first = tasks_db.get(uid,0)==0
    today = pending.get('date')
    daily_done[uid]=today
    tasks_db[uid]=tasks_db.get(uid,0)+1
    if uid not in daily_task_count: daily_task_count[uid]={}
    daily_task_count[uid][today] = daily_task_count[uid].get(today,0) + 1
    if reward!=5: bonus_balance[uid]=bonus_balance.get(uid,0)+(reward-5)
    del pending_daily[uid]
    task_open_time.pop(uid, None)
    ref_id = pending_referrals.get(uid)
    if ref_id and is_first:
        referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
        del pending_referrals[uid]
    await q.message.reply_text(f"Approved {uid} +Rs{reward}")
    try: await context.bot.send_message(chat_id=uid, text=f"Task Approved +Rs{reward} Balance Rs{get_balance(uid)}", reply_markup=main_menu())
    except: pass

async def admin_reject_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    if uid in pending_daily:
        sd = screenshot_db.get(uid)
        if sd and sd.get('file_unique_id') in screenshot_hashes:
            screenshot_hashes.discard(sd.get('file_unique_id'))
        del pending_daily[uid]
        task_open_time.pop(uid, None)
        await q.message.reply_text(f"Rejected {uid}")

async def admin_ban_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    banned_users.add(uid)
    await q.message.reply_text(f"Banned {uid} for scam!")

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    is_free = is_first_day_free(uid)
    bal=get_balance(uid)
    today_str = str(date.today())
    # Once per day check
    if withdraw_done_date.get(uid)==today_str:
        await q.message.reply_text(f"Once Per Day Only! Already withdrew today {today_str} Tomorrow try! Status /withdrawstatus", reply_markup=main_menu()); return
    if uid in withdraw_requests and withdraw_requests[uid].get('status')=='processing':
        await q.message.reply_text(f"Already Processing Amount Rs{withdraw_requests[uid].get('amount')} Check /withdrawstatus", reply_markup=main_menu()); return
    # Balance check
    if bal < WITHDRAW_MIN:
        await q.message.reply_text(f"Balance Rs{bal}/{WITHDRAW_MIN} Low! Need 200+ Tasks {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW}", reply_markup=main_menu()); return
    # Tasks required check - 17 tasks
    if get_tasks(uid) < TASKS_REQUIRED_FOR_WITHDRAW:
        await q.message.reply_text(f"Tasks Not Completed! Your {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW} Complete {TASKS_REQUIRED_FOR_WITHDRAW} for withdraw! Daily limits Basic {DAILY_TASK_LIMIT_BASIC}/day Premium {DAILY_TASK_LIMIT_PREMIUM}/day", reply_markup=main_menu()); return
    if not is_active and not is_free:
        await q.message.reply_text(f"Plan Expired/No Plan! {plan_status}", reply_markup=main_menu()); return
    # Build options with highlighting - Your idea: 566 balance -> 200,300,500 highlight, 1000 not highlight
    buttons=[]; row=[]; info_text=f"Withdraw - Balance Rs{bal} Min {WITHDRAW_MIN} Max {WITHDRAW_MAX} Once/day Multiple 100\nSelect Amount:\n"
    for amount in WITHDRAW_OPTIONS:
        if amount <= bal and amount <= WITHDRAW_MAX:
            row.append(InlineKeyboardButton(f"Rs{amount} Available", callback_data=f"wd_select_{amount}"))
            info_text+=f"Rs{amount} Available\n"
        else:
            info_text+=f"Rs{amount} Insufficient Need Rs{amount} Have Rs{bal}\n"
        if len(row)==2: buttons.append(row); row=[]
    if row: buttons.append(row)
    info_text+=f"\nExample Balance Rs566 -> 200,300,500 highlight, 1000 not highlight!\nFee {PLATFORM_FEE_PERCENT}% Platform Fee\n"
    buttons.append([InlineKeyboardButton("Check Status", callback_data="wd_status")])
    buttons.append([InlineKeyboardButton("Back", callback_data="back_menu")])
    await q.message.reply_text(info_text, reply_markup=InlineKeyboardMarkup(buttons))

async def wd_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    amount=int(q.data.split("_")[-1])
    bal=get_balance(uid)
    if amount>bal: return
    fee=int(amount*PLATFORM_FEE_PERCENT/100)
    net=amount-fee
    upi=users_db.get(uid,{}).get('upi','Not Set')
    kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"Yes Confirm Rs{amount} Net Rs{net}", callback_data=f"wd_confirm_{amount}")]])
    await q.message.reply_text(f"Amount Rs{amount} Fee {PLATFORM_FEE_PERCENT}% Rs{fee} Net Rs{net} UPI {upi} Correct?", reply_markup=kb)

async def wd_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    amount=int(q.data.split("_")[-1])
    bal=get_balance(uid)
    if amount>bal: return
    fee=int(amount*PLATFORM_FEE_PERCENT/100)
    net=amount-fee
    upi=users_db.get(uid,{}).get('upi','')
    bonus_balance[uid]=bonus_balance.get(uid,0)-amount
    if bonus_balance[uid]<0: bonus_balance[uid]=0
    withdraw_requests[uid]={'amount': amount, 'fee': fee, 'net_amount': net, 'upi': upi, 'status': 'processing', 'date': str(date.today())}
    withdraw_done_date[uid]=str(date.today())
    await q.message.reply_text(f"Withdraw Request Rs{amount} Net Rs{net} Processing!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"Approve Rs{net}", callback_data=f"wd_admin_approve_{uid}")]])
            await context.bot.send_message(chat_id=admin_id, text=f"Withdraw ID {uid} Amount Rs{amount} Net Rs{net} UPI {upi}", reply_markup=kb)
        except: pass

async def wd_status_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    wr = withdraw_requests.get(uid)
    if not wr:
        await q.message.reply_text("No active withdraw! Use menu -> Withdraw", reply_markup=main_menu())
        return
    status = wr.get('status')
    status_text = "Processing - Admin will approve 24hrs" if status=='processing' else "Completed" if status=='approved' else "Rejected"
    await q.message.reply_text(f"Withdraw Status Amount Rs{wr.get('amount')} Fee Rs{wr.get('fee')} Net Rs{wr.get('net_amount')} UPI {wr.get('upi')} Date {wr.get('date')} Status {status_text}", reply_markup=main_menu())

async def withdrawstatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    wr = withdraw_requests.get(uid)
    if not wr:
        await update.message.reply_text("No active withdraw!", reply_markup=main_menu())
        return
    await update.message.reply_text(f"Withdraw Amount Rs{wr.get('amount')} Fee Rs{wr.get('fee')} Net Rs{wr.get('net_amount')} Status {wr.get('status')} UPI {wr.get('upi')}", reply_markup=main_menu())

async def wd_admin_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    wr=withdraw_requests.get(uid)
    if not wr: return
    wr['status']='approved'
    await q.message.reply_text(f"Approved {uid}")
    try: await context.bot.send_message(chat_id=uid, text=f"Withdraw Approved Net Rs{wr.get('net_amount')} Completed!", reply_markup=main_menu())
    except: pass

async def wd_admin_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    wr=withdraw_requests.get(uid)
    if not wr: return
    bonus_balance[uid]=bonus_balance.get(uid,0)+wr.get('amount')
    withdraw_requests.pop(uid,None)
    withdraw_done_date.pop(uid,None)
    await q.message.reply_text(f"Rejected {uid}")

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    is_active, plan_status, _ = check_plan_active(q.from_user.id)
    await q.message.reply_text(f"Plans: Basic Rs500 10 tasks/day Max Rs200, Premium Rs1000 20 tasks/day Max Rs500, Your: {plan_status}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Basic Rs500", callback_data="plan_basic")],[InlineKeyboardButton("Premium Rs1000", callback_data="plan_premium")]]))

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Pay Rs500", url=DEPOSIT_LINK_BASIC)],[InlineKeyboardButton("I Paid", callback_data="verify_basic")]])
    await q.message.reply_text(f"Basic Rs500 30 Days", reply_markup=kb)

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Pay Rs1000", url=DEPOSIT_LINK_PREMIUM)],[InlineKeyboardButton("I Paid", callback_data="verify_premium")]])
    await q.message.reply_text(f"Premium Rs1000 90 Days + Bonus", reply_markup=kb)

async def verify_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    plan_type="basic" if "basic" in q.data else "premium"
    pending_plans[uid]=plan_type
    user_plans[uid]={'plan': plan_type, 'status': 'pending', 'start': date.today(), 'expiry': None}
    await q.message.reply_text(f"{plan_type.upper()} Pending!", reply_markup=main_menu())

async def admin_approve_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts=q.data.split("_")
    uid=int(parts[3]); plan_type=parts[4]
    today=date.today()
    expiry=today+timedelta(days=30 if plan_type=='basic' else 90)
    user_plans[uid]={'plan': plan_type, 'status': 'active', 'start': today, 'expiry': expiry}
    pending_plans.pop(uid,None)
    if plan_type=='premium': bonus_balance[uid]=bonus_balance.get(uid,0)+100
    await q.message.reply_text(f"Approved {plan_type} for {uid}")

async def admin_reject_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in pending_plans: del pending_plans[uid]; user_plans.pop(uid,None)

async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"Contact {SUPPORT_USERNAME}", reply_markup=main_menu())

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
        await update.message.reply_text(f"Welcome {users_db[uid]['name']} Balance Rs{get_balance(uid)} Plan {plan_status}", reply_markup=main_menu())
        return
    await update.message.reply_text(f"Welcome S2E! Day1 FREE! ID: {uid}", reply_markup=join_channel_keyboard(False))

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
    mob_clean=re.sub(r'\D','',mob)
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
    await update.message.reply_text("Menu: Today free 1st task available!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu:", reply_markup=main_menu())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if not is_admin(uid): return
    await update.message.reply_text(f"ADMIN PANEL Easy Anti-Scam No Paper!\nUsers {len(users_db)} Pending {len(pending_daily)} Screenshots {len(screenshot_hashes)}")

async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not pending_daily: await update.message.reply_text("No pending!"); return
    msg=f"Pending {len(pending_daily)}:\n"
    for uid, data in pending_daily.items():
        msg+=f"{uid} | {data.get('task',{}).get('title')} /approve {uid}\n"
    await update.message.reply_text(msg[:4000])

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: return
    try: target_id=int(context.args[0])
    except: return
    if target_id in pending_daily:
        is_first=tasks_db.get(target_id,0)==0
        reward=pending_daily[target_id].get('task',{}).get('reward',5)
        today=pending_daily[target_id].get('date')
        daily_done[target_id]=today
        tasks_db[target_id]=tasks_db.get(target_id,0)+1
        if target_id not in daily_task_count: daily_task_count[target_id]={}
        daily_task_count[target_id][today]=daily_task_count[target_id].get(today,0)+1
        if reward!=5: bonus_balance[target_id]=bonus_balance.get(target_id,0)+(reward-5)
        del pending_daily[target_id]
        task_open_time.pop(target_id, None)
        ref_id=pending_referrals.get(target_id)
        if ref_id and is_first:
            referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
            del pending_referrals[target_id]
        await update.message.reply_text(f"Approved {target_id} +Rs{reward}")

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
    conv_screenshot = ConversationHandler(
        entry_points=[CallbackQueryHandler(daily_upload_screenshot_cb, pattern="^daily_upload_screenshot$")],
        states={
            UPLOAD_SCREENSHOT:[MessageHandler(filters.PHOTO, handle_screenshot_upload)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True, per_chat=True, per_message=False
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("withdrawstatus", withdrawstatus_cmd))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("warnings", warnings_cmd))
    app.add_handler(CommandHandler("banned", banned_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
    app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(daily_cb, pattern="^daily$"))
    app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern="^admin_approve_daily_"))
    app.add_handler(CallbackQueryHandler(admin_reject_daily_cb, pattern="^admin_reject_daily_"))
    app.add_handler(CallbackQueryHandler(admin_ban_cb, pattern="^admin_ban_"))
    app.add_handler(CallbackQueryHandler(admin_unban_cb, pattern="^admin_unban_"))
    app.add_handler(CallbackQueryHandler(withdraw_cb, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(wd_select_cb, pattern="^wd_select_"))
    app.add_handler(CallbackQueryHandler(wd_status_cb, pattern="^wd_status$"))
    app.add_handler(CallbackQueryHandler(wd_confirm_cb, pattern="^wd_confirm_"))
    app.add_handler(CallbackQueryHandler(wd_admin_approve_cb, pattern="^wd_admin_approve_"))
    app.add_handler(CallbackQueryHandler(wd_admin_reject_cb, pattern="^wd_admin_reject_"))
    app.add_handler(CallbackQueryHandler(support_plans_cb, pattern="^support_plans$"))
    app.add_handler(CallbackQueryHandler(plan_basic_cb, pattern="^plan_basic$"))
    app.add_handler(CallbackQueryHandler(plan_premium_cb, pattern="^plan_premium$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_basic$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_premium$"))
    app.add_handler(CallbackQueryHandler(admin_approve_plan_cb, pattern="^admin_approve_plan_"))
    app.add_handler(CallbackQueryHandler(admin_reject_plan_cb, pattern="^admin_reject_plan_"))
    app.add_handler(CallbackQueryHandler(contact_us_cb, pattern="^contact_us$"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
    app.add_handler(conv_reg)
    app.add_handler(conv_screenshot)
    print(f"Bot Started! Easy Anti-Scam No Paper Code + 17 Tasks!")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
