import os, re, threading, json, asyncio
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")
from datetime import date, datetime, timedelta, time, timezone
from flask import Flask

# === IST TIMEZONE FIX ===
IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now():
    return datetime.now(IST)
def get_ist_today():
    return get_ist_now().date()
def get_ist_time():
    return get_ist_now().time()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@s2edayincome")
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

WITHDRAW_OPTIONS = [200, 300, 500, 1000]
notified_tasks_30sec = set()
bot_application = None

def notification_thread_func():
    import asyncio
    while True:
        try:
            import time as t2
            t2.sleep(30)
            if not bot_application:
                continue
            now = get_ist_now()
            for task in get_tasks_for_today():
                try:
                    open_dt = datetime.combine(get_ist_today(), task['open_time_obj'], tzinfo=IST)
                except:
                    continue
                diff = (open_dt - now).total_seconds()
                if 0 < diff <= 65 and task['id'] not in notified_tasks_30sec:
                    notified_tasks_30sec.add(task['id'])
                    msg = f"⏰ TASK IN 30 SEC! Task {task['task_number']}: {task.get('title','')}"
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        for uid in list(users_db.keys())[:300]:
                            try:
                                loop.run_until_complete(bot_application.bot.send_message(chat_id=uid, text=msg))
                            except:
                                pass
                        loop.close()
                    except:
                        pass
        except:
            import time as t2
            t2.sleep(10)



async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    kb = [[InlineKeyboardButton("✅ Activate Basic (₹199)", callback_data="plan_basic_activate")],
          [InlineKeyboardButton("📤 Upload Proof", callback_data="plan_basic_proof")]]
    try:
        await update.callback_query.edit_message_text("💎 Basic Plan - ₹199\n10 tasks/day, ₹200 cap", reply_markup=InlineKeyboardMarkup(kb))
    except:
        pass

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    kb = [[InlineKeyboardButton("✅ Activate Premium (₹499)", callback_data="plan_premium_activate")],
          [InlineKeyboardButton("📤 Upload Proof", callback_data="plan_premium_proof")]]
    try:
        await update.callback_query.edit_message_text("🔥 Premium Plan - ₹499\n20 tasks/day, ₹500 cap", reply_markup=InlineKeyboardMarkup(kb))
    except:
        pass

async def plan_basic_activate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        await update.callback_query.edit_message_text(f"Basic Plan Activation\nPlease pay ₹199 to UPI: {ADMIN_UPI}\nAfter payment upload proof with /admin")
    except:
        pass

async def plan_premium_activate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        await update.callback_query.edit_message_text(f"Premium Plan Activation\nPlease pay ₹499 to UPI: {ADMIN_UPI}\nAfter payment upload proof with /admin")
    except:
        pass

async def plan_basic_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        await update.callback_query.edit_message_text("Please upload payment screenshot for Basic Plan. Use /admin to contact.")
    except:
        pass

async def plan_premium_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        await update.callback_query.edit_message_text("Please upload payment screenshot for Premium Plan. Use /admin to contact.")
    except:
        pass

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    kb = [[InlineKeyboardButton("Basic ₹199", callback_data="plan_basic")],
          [InlineKeyboardButton("Premium ₹499", callback_data="plan_premium")]]
    try:
        await update.callback_query.edit_message_text("Choose your plan:", reply_markup=InlineKeyboardMarkup(kb))
    except:
        pass

async def admin_view_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        await update.callback_query.edit_message_text(f"Pending plans: {len(pending_plans)}")
    except:
        pass

async def admin_approve_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        uid = int(update.callback_query.data.replace("admin_approve_plan_",""))
        if uid in pending_plans:
            user_plans[uid] = pending_plans[uid]
            del pending_plans[uid]
            await update.callback_query.edit_message_text(f"Approved plan for {uid}")
            try:
                await context.bot.send_message(chat_id=uid, text="Your plan approved!")
            except:
                pass
    except Exception as e:
        print(e)

async def admin_reject_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
    except:
        pass
    try:
        uid = int(update.callback_query.data.replace("admin_reject_plan_",""))
        if uid in pending_plans:
            del pending_plans[uid]
            await update.callback_query.edit_message_text(f"Rejected plan for {uid}")
    except Exception as e:
        print(e)


WITHDRAW_MIN = 200
PLATFORM_FEE_PERCENT = 7
TASKS_REQUIRED_FOR_WITHDRAW = 15
REFERRAL_BONUS_PER_TASK = 10
REFERRAL_PLAN_COMMISSION_PERCENT = 10
DAILY_TASK_LIMIT_BASIC = 10
DAILY_TASK_LIMIT_PREMIUM = 20
DAILY_TASK_LIMIT_FREE = 1
DAILY_EARNING_CAP_BASIC = 200
DAILY_EARNING_CAP_PREMIUM = 500
TASK_COMPLETION_WINDOW_MINUTES = 15

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "S2E Super Fixed + Image Poster Support"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

NAME, GENDER, DOB, MOBILE, UPI, PINCODE, PROFESSION, UPLOAD_SCREENSHOT, SKIP_REASON, PROMO_DETAILS, SET_IMAGE = range(11)

users_db = {}
referrals_db = {}
tasks_db = {}
daily_done = {}
bonus_balance = {}
banned_users = set()
warnings_db = {}
pending_daily = {}
user_plans = {}
pending_plans = {}
referral_map = {}
pending_referrals = {}
referral_earnings = {}
withdraw_requests = {}
withdraw_done_date = {}
daily_task_count = {}
last_withdraw_date_db = {}  # one withdraw per day
screenshot_hashes = set()
task_open_time = {}
scheduled_tasks_db = []
scheduled_task_counter = 1
user_task_status = {}
task_notifications_sent = set()
skip_db = {}
skip_reasons_list = ["Already have account", "Not interested", "Technical issue", "Already completed", "Don't have required documents", "Other - Type reason"]
promo_campaigns_db = []
promo_campaign_counter = 1
promo_earnings_db = {}
promo_views_db = {}
promo_pending = {}
task_images_db = {}  # task_id -> file_id for poster - NEW FOR YOUR IMAGE

def add_promo_campaign(shop_name, owner_name, phone, place, category, title, description, poster_link, offer, target_views=10000, per_100_views_price=20, per_view_member_earning=10):
    global promo_campaign_counter
    campaign = {
        'id': promo_campaign_counter,
        'shop_name': shop_name,
        'owner_name': owner_name,
        'phone': phone,
        'place': place,
        'category': category,
        'title': title,
        'description': description,
        'poster_link': poster_link,
        'offer': offer,
        'target_views': target_views,
        'per_100_views_price': per_100_views_price,
        'per_view_member_earning': per_view_member_earning,
        'per_sale_commission_percent': 10,
        'status': 'active',
        'created_at': get_ist_now(),
        'expiry': get_ist_today() + timedelta(days=7),
        'total_views': 0,
        'total_sales': 0,
        'total_earnings_distributed': 0,
        'members_joined': set(),
        'screenshots': []
    }
    promo_campaigns_db.append(campaign)
    promo_campaign_counter += 1
    return campaign

def get_active_promo_campaigns():
    today = get_ist_today()
    return [c for c in promo_campaigns_db if c['status'] == 'active' and c['expiry'] >= today]

def get_promo_campaign(campaign_id):
    for c in promo_campaigns_db:
        if c['id'] == campaign_id:
            return c
    return None

def parse_time_str(time_str):
    time_str = time_str.strip().upper()
    try:
        if ':' in time_str:
            parts = time_str.replace('AM','').replace('PM','').strip().split(':')
            hour = int(parts[0])
            minute = int(parts[1].split()[0]) if len(parts)>1 else 0
            if 'PM' in time_str and hour < 12:
                hour += 12
            if 'AM' in time_str and hour == 12:
                hour = 0
            return time(hour, minute)
        else:
            hour = int(time_str.replace('AM','').replace('PM','').split()[0])
            if 'PM' in time_str and hour < 12:
                hour += 12
            if 'AM' in time_str and hour == 12:
                hour = 0
            return time(hour, 0)
    except:
        return None

def parse_interval_str(interval_str):
    interval_str = interval_str.lower().strip()
    try:
        if 'min' in interval_str:
            return int(re.findall(r'\d+', interval_str)[0])
        elif 'hour' in interval_str or 'hr' in interval_str:
            hours = int(re.findall(r'\d+', interval_str)[0])
            return hours * 60
        else:
            return int(interval_str)
    except:
        return TASK_COMPLETION_WINDOW_MINUTES

def add_scheduled_task_with_interval(open_time_str, close_time_or_interval, next_time_str, title, link, reward=5, image_file_id=None):
    global scheduled_task_counter
    open_time = parse_time_str(open_time_str)
    if not open_time:
        return False, f"Invalid open {open_time_str}"
    close_time = None
    if ':' in close_time_or_interval or 'AM' in close_time_or_interval.upper() or 'PM' in close_time_or_interval.upper():
        close_time = parse_time_str(close_time_or_interval)
        if not close_time:
            return False, f"Invalid close {close_time_or_interval}"
    else:
        interval_mins = parse_interval_str(close_time_or_interval)
        open_dt = datetime.combine(get_ist_today(), open_time, tzinfo=IST)
        close_dt = open_dt + timedelta(minutes=interval_mins)
        close_time = close_dt.time()
    next_time = parse_time_str(next_time_str)
    if not next_time:
        return False, f"Invalid next {next_time_str}"
    open_dt = datetime.combine(get_ist_today(), open_time, tzinfo=IST)
    close_dt = datetime.combine(get_ist_today(), close_time, tzinfo=IST)
    next_dt = datetime.combine(get_ist_today(), next_time, tzinfo=IST)
    if close_dt <= open_dt:
        return False, f"Close {close_time.strftime('%H:%M')} must be after open"
    if next_dt < close_dt:
        return False, f"Next {next_time.strftime('%H:%M')} must be after close"
    task = {
        'id': scheduled_task_counter,
        'task_number': len([t for t in scheduled_tasks_db if t['date'] == str(get_ist_today())]) + 1,
        'open_time': open_time.strftime("%H:%M"),
        'open_time_obj': open_time,
        'close_time': close_time.strftime("%H:%M"),
        'close_time_obj': close_time,
        'next_time': next_time.strftime("%H:%M"),
        'next_time_obj': next_time,
        'title': title,
        'link': link,
        'reward': reward,
        'date': str(get_ist_today()),
        'created_at': get_ist_now(),
        'window_minutes': int((close_dt - open_dt).total_seconds() / 60),
        'skippable': True if any(x in title.lower() for x in ['angel', 'upstox', 'demat', 'trading']) else False,
        'image_file_id': image_file_id
    }
    if image_file_id:
        task_images_db[task['id']] = image_file_id
    scheduled_tasks_db.append(task)
    scheduled_tasks_db.sort(key=lambda x: x['open_time'])
    scheduled_task_counter += 1
    return True, task

def get_tasks_for_today():
    return [t for t in scheduled_tasks_db if t['date'] == str(get_ist_today())]

def get_current_scheduled_task_with_interval():
    now = get_ist_time()
    today_tasks = get_tasks_for_today()
    if not today_tasks:
        return None, None
    for i, task in enumerate(today_tasks):
        open_time = task['open_time_obj']
        close_time = task['close_time_obj']
        next_task = today_tasks[i+1] if i+1 < len(today_tasks) else None
        if open_time <= now <= close_time:
            return task, next_task
        if close_time < now:
            if next_task and now < next_task['open_time_obj']:
                return None, next_task
    if today_tasks and now < today_tasks[0]['open_time_obj']:
        return None, today_tasks[0]
    return None, None

def check_missed_tasks_with_interval(uid):
    if uid not in user_task_status:
        user_task_status[uid] = {}
    today_tasks = get_tasks_for_today()
    now = get_ist_now()
    missed = []
    newly_missed = []
    for task in today_tasks:
        task_id = task['id']
        close_dt = datetime.combine(get_ist_today(), task['close_time_obj'], tzinfo=IST)
        status = user_task_status[uid].get(task_id, {}).get('status') if isinstance(user_task_status[uid].get(task_id), dict) else user_task_status[uid].get(task_id)
        if status in ['completed', 'skipped']:
            continue
        if now >= close_dt:
            if status != 'missed':
                if uid not in user_task_status:
                    user_task_status[uid] = {}
                user_task_status[uid][task_id] = {'status': 'missed', 'missed_at': now, 'task_number': task['task_number']}
                newly_missed.append(task)
            missed.append(task)
    return missed, newly_missed

def mark_task_completed_with_interval(uid, task_id):
    if uid not in user_task_status:
        user_task_status[uid] = {}
    user_task_status[uid][task_id] = {'status': 'completed', 'completed_at': get_ist_now()}

def is_admin(uid): return uid in ADMIN_ID_LIST
def calculate_age(d): 
    today=get_ist_today()
    return today.year-d.year-((today.month,today.day)<(d.month,d.day))
def get_balance(uid): return tasks_db.get(uid,0)*5 + bonus_balance.get(uid,0) + referral_earnings.get(uid,0) + promo_earnings_db.get(uid,0)
