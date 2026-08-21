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
missed_tasks_db = {}  # {uid: [missed task dicts]}
last_withdraw_date_db = {}
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
    # ===== DUPLICATE PROTECTION - 2 times bug fix =====
    import time as _time
    _now = _time.time()
    if hasattr(add_scheduled_task_with_interval, '_last_t'):
        _elapsed = _now - add_scheduled_task_with_interval._last_t
        _last_title = getattr(add_scheduled_task_with_interval, '_last_title', '')
        if _elapsed < 8 and _last_title == title and title.strip() != "":
            print(f"⚠️ Duplicate task blocked (2x bug): {title} in {_elapsed:.1f}s")
            return False, f"Duplicate - Task already added! Wait 10 sec"
    add_scheduled_task_with_interval._last_t = _now
    add_scheduled_task_with_interval._last_title = title

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
def get_tasks(uid):
    today = str(get_ist_today())
    return daily_task_count.get(uid, {}).get(today, 0)

def get_total_tasks(uid):
    return tasks_db.get(uid,0)
def check_plan_active(uid):
    plan = user_plans.get(uid)
    if not plan: return False, "No Plan", None
    if plan.get('status') != 'active': return False, f"{plan.get('plan','')} Pending", None
    expiry = plan.get('expiry')
    if expiry and get_ist_today() > expiry: return False, f"{plan.get('plan','').upper()} Expired", expiry
    return True, f"{plan.get('plan','').upper()} till {expiry}", expiry
def get_plan_limits(uid):
    is_active, _, _ = check_plan_active(uid)
    if not is_active:
        if tasks_db.get(uid,0) == 0:
            return DAILY_TASK_LIMIT_FREE, 10, "free"
        return 0, 0, "none"
    plan = user_plans.get(uid, {}).get('plan','basic')
    if plan == 'premium':
        return DAILY_TASK_LIMIT_PREMIUM, 500, "premium"
    else:
        return DAILY_TASK_LIMIT_BASIC, 200, "basic"
def check_daily_limits(uid):
    today = str(get_ist_today())
    count = daily_task_count.get(uid, {}).get(today, 0)
    limit, cap, plan_name = get_plan_limits(uid)
    return count, limit, cap
def get_today_task_for_user(uid):
    current, next_task = get_current_scheduled_task_with_interval()
    if current:
        return current
    return {"title": "Join Channel @s2edayincome", "link": CHANNEL_LINK, "reward": 5}

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🏪 Promo Tasks", callback_data="promo_tasks"), InlineKeyboardButton("📢 Promote My Shop", callback_data="promote_shop")],
        [InlineKeyboardButton("📋 Scheduled Tasks", callback_data="scheduled"), InlineKeyboardButton("💎 Support Plans", callback_data="support_plans")],
        [InlineKeyboardButton("📞 Contact Us", callback_data="contact_us")]
    ])

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

async def check_user_in_channel(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Check channel error {e}")
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in banned_users:
        await update.message.reply_text("You are BANNED! Contact admin!")
        return ConversationHandler.END
    if not is_admin(uid):
        is_joined = await check_user_in_channel(uid, context)
        if not is_joined:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
            ])
            await update.message.reply_text(f"👋 Welcome! Please join our channel {CHANNEL_ID} to use bot!\n\nJoin and click Check Joined!", reply_markup=kb)
            return ConversationHandler.END
    args = context.args
    ref_id = None
    if args and args[0].isdigit():
        ref_id = int(args[0])
        if ref_id != uid and ref_id not in banned_users:
            referral_map[uid] = ref_id
    if uid in users_db:
        await update.message.reply_text(f"Welcome back {users_db[uid].get('name','User')}! Balance Rs{get_balance(uid)}\nTasks {get_tasks(uid)}/15", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text("Welcome to S2E Daily Earning + Promo Network!\n\nWhat is your Name?")
    return NAME

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    is_joined = await check_user_in_channel(uid, context)
    if not is_joined:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
        ])
        await q.message.reply_text(f"❌ Not joined yet! Please join {CHANNEL_ID} first!\nLink: {CHANNEL_LINK}", reply_markup=kb)
        return ConversationHandler.END
    if uid in users_db:
        await q.message.reply_text(f"✅ Thanks for joining! Welcome back {users_db[uid].get('name','User')}!", reply_markup=main_menu())
        return ConversationHandler.END
    await q.message.reply_text("✅ Thanks for joining! What is your Name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Name too short! Enter valid name:")
        return NAME
    users_db[uid] = {'name': name}
    await update.message.reply_text("Gender? Male/Female/Other:")
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]['gender'] = update.message.text.strip()
    await update.message.reply_text("Date of Birth? DD/MM/YYYY:")
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    dob_str = update.message.text.strip()
    try:
        dob = datetime.strptime(dob_str, "%d/%m/%Y").date()
        age = calculate_age(dob)
        if age < 18:
            await update.message.reply_text("Must be 18+! Enter valid DOB:")
            return DOB
        users_db[uid]['dob'] = str(dob)
        users_db[uid]['age'] = age
    except:
        await update.message.reply_text("Invalid format! Use DD/MM/YYYY:")
        return DOB
    await update.message.reply_text("Mobile Number? 10 digits:")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mobile = update.message.text.strip()
    if not mobile.isdigit() or len(mobile) != 10:
        await update.message.reply_text("Invalid! 10 digits only:")
        return MOBILE
    users_db[uid]['mobile'] = mobile
    await update.message.reply_text("UPI ID? Example: yourname@upi")
    return UPI

def is_valid_upi_format(upi):
    if not upi or "@" not in upi:
        return False, "UPI must contain @"
    parts = upi.split("@")
    if len(parts) != 2:
        return False, "Only one @ allowed"
    return True, "Valid"

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id; upi=update.message.text.strip()
    is_valid, msg = is_valid_upi_format(upi)
    if not is_valid:
        await update.message.reply_text(f"Invalid UPI! {msg} Try again:")
        return UPI
    users_db[uid]['upi']=upi
    await update.message.reply_text("Pincode? 6 digits:")
    return PINCODE

async def get_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    pincode=update.message.text.strip()
    if not pincode.isdigit() or len(pincode)!=6:
        await update.message.reply_text("Invalid Pincode! 6 digits:")
        return PINCODE
    users_db[uid]['pincode']=pincode
    await update.message.reply_text("Profession? Student/Employee/Business/Other:")
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    users_db[uid]['profession']=update.message.text.strip()
    users_db[uid]['joined']=str(get_ist_today())
    users_db[uid]['reg_date']=get_ist_today()
    await update.message.reply_text(f"✅ Registration Done! Welcome {users_db[uid]['name']}!\n\n💰 Earn: Rs10 per referral + 10% plan commission\n🏪 Promo: Earn Rs10 per 100 status views!\n📋 Tasks: 0/15 | Withdraw Min Rs200\n\nClick /menu for options!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled!", reply_markup=main_menu())
    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("You are not admin!")
        return
    active_promos = len(get_active_promo_campaigns())
    total_views = sum(c['total_views'] for c in promo_campaigns_db)
    msg = f"🔐 ADMIN PANEL - S2E Ultimate + Poster\n\n"
    msg += f"👥 Users: {len(users_db)}\n"
    msg += f"📋 Pending Daily: {len(pending_daily)}\n"
    msg += f"💰 Pending Withdraw: {len([w for w in withdraw_requests.values() if w.get('status')=='processing'])}\n"
    msg += f"📢 Promo Campaigns: {len(promo_campaigns_db)} Active: {active_promos}\n"
    msg += f"👁️ Total Promo Views: {total_views}\n"
    msg += f"⏰ Scheduled Today: {len(get_tasks_for_today())}\n"
    msg += f"🖼️ Tasks with Poster: {len(task_images_db)}\n"
    msg += f"⏭️ Skipped Today: {sum(len(v) for v in skip_db.values())}\n"
    msg += f"🚫 Banned: {len(banned_users)}\n\n"
    msg += f"Plan Limits: Basic {DAILY_TASK_LIMIT_BASIC}/day Rs{DAILY_EARNING_CAP_BASIC} cap | Premium {DAILY_TASK_LIMIT_PREMIUM}/day Rs{DAILY_EARNING_CAP_PREMIUM} cap\n\n"
    msg += f"Commands:\n"
    msg += f"/add_task open close next title link reward\n"
    msg += f"/set_task_image <id> - Then send poster image!\n"
    msg += f"Example: /add_task 12:45PM 15min 1:03PM Task 3 Google Review https://maps.app.goo.gl/xxx 5\nThen /set_task_image 1 + send TASK 3 poster!\n\n"
    msg += f"/list_tasks /list_promos /skipped all /warnings /banned"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Pending Daily ({len(pending_daily)})", callback_data="admin_view_pending"), InlineKeyboardButton(f"💰 Withdraw ({len([w for w in withdraw_requests.values() if w.get('status')=='processing'])})", callback_data="admin_view_withdraw")],
        [InlineKeyboardButton("⏰ Today's Tasks", callback_data="admin_view_tasks"), InlineKeyboardButton("🏪 Promo Campaigns", callback_data="admin_view_promos")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_view_stats"), InlineKeyboardButton("🚫 Banned List", callback_data="admin_view_banned")],
        [InlineKeyboardButton("📋 Menu", callback_data="back_menu")]
    ])
    
    await update.message.reply_text(msg[:4000], reply_markup=kb)

async def admin_view_pending_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    if not pending_daily:
        await q.message.reply_text("✅ No pending daily tasks!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))
        return
    msg = f"📋 Pending Daily Tasks - {len(pending_daily)}:\n\n"
    for uid, data in list(pending_daily.items())[:20]:
        task = data.get('task',{})
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} - Task {task.get('task_number','?')} {task.get('title','?')} Rs{task.get('reward',5)} /approve {uid}\n"
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))

async def admin_view_withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    pending_wd = {uid: data for uid, data in withdraw_requests.items() if data.get('status')=='processing'}
    if not pending_wd:
        await q.message.reply_text("✅ No pending withdraw requests!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))
        return
    msg = f"💰 Pending Withdraw - {len(pending_wd)}:\n\n"
    for uid, data in list(pending_wd.items())[:20]:
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} - Rs{data.get('amount')} Fee Rs{data.get('fee')} Net Rs{data.get('net')} UPI {data.get('upi')}\n"
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))

async def admin_view_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    today_tasks = get_tasks_for_today()
    if not today_tasks:
        await q.message.reply_text("📋 No scheduled tasks for today!\n\nAdd via:\n/add_task 12:45PM 15min 1:03PM Title https://link 5\nThen /set_task_image <id> to add poster!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))
        return
    msg = f"⏰ Scheduled Tasks Today {get_ist_today()} - Total {len(today_tasks)}:\n\n"
    for task in today_tasks:
        has_poster = "🖼️ Poster YES" if task.get('image_file_id') or task['id'] in task_images_db else "❌ No Poster"
        msg += f"ID {task['id']} Task {task['task_number']} {task['open_time']}→{task['close_time']} Next {task['next_time']} - {task['title']} Rs{task['reward']} {has_poster}\n/set_task_image {task['id']}\n"
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))

async def admin_view_promos_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    if not promo_campaigns_db:
        await q.message.reply_text("🏪 No promo campaigns!\n\nAdd via:\n/add_promo shop|owner|phone|place|category|title|desc|poster|offer|target|price", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))
        return
    msg = f"🏪 Promo Campaigns Total {len(promo_campaigns_db)}:\n\n"
    for c in promo_campaigns_db[-20:]:
        msg += f"ID {c['id']}: {c['shop_name']} {c['place']} - {c['title']} Target {c['target_views']} Views {c['total_views']} Members {len(c['members_joined'])}\n"
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))

async def admin_view_stats_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    msg = f"📊 Detailed Stats\n\nUsers: {len(users_db)}\nTasks Completed: {sum(tasks_db.values())}\nReferrals: {len(referrals_db)}\nBonus Distributed: Rs{sum(bonus_balance.values())}\nReferral Earnings: Rs{sum(referral_earnings.values())}\nPromo Earnings: Rs{sum(promo_earnings_db.values())}\nPending Daily: {len(pending_daily)}\nPromo Pending: {len(promo_pending)}\nBanned: {len(banned_users)}\nWarnings: {len(warnings_db)}\nPosters: {len(task_images_db)}"
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))

async def admin_view_banned_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    if not banned_users:
        await q.message.reply_text("✅ No banned users!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))
        return
    msg = f"🚫 Banned Users - {len(banned_users)}:\n\n"
    for uid in list(banned_users)[:20]:
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} /unban {uid}\n"
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Admin", callback_data="back_admin")]]))

async def back_admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query
        if q:
            try:
                await q.answer("Opening Admin...")
            except:
                pass
        # Call admin - handle both message and callback
        uid = update.effective_user.id
        if not is_admin(uid):
            try:
                await q.edit_message_text(f"❌ Not admin")
            except:
                await update.effective_message.reply_text(f"❌ Not admin")
            return
        # Build admin panel directly (don't call admin_cmd which expects message)
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            total_users = len(users)
            total_tasks = len(scheduled_tasks_data)
            active_campaigns = len([t for t in scheduled_tasks_data.values() if True])
            pending_daily = len([v for v in daily_verifications.values() if v.get('status')=='pending'])
            pending_wd = len([w for w in withdraw_requests.values() if w.get('status')=='pending'])
            text = f"👑 ADMIN PANEL\n\n👥 Users: {total_users}\n📋 Tasks: {total_tasks}\n⏳ Pending Daily: {pending_daily}\n💸 Pending WD: {pending_wd}\n\nCommands:\n/add_task open close next title link reward\n/set_task_image <id> - Then send poster!\nExample: /add_task 12:45PM 15min 1:03PM Task 3 Google Review https://maps.app.goo.gl/xxx 5\nThen /set_task_image 1 + send TASK 3 poster!\n\n/list_tasks /list_promos /skipped all /warnings /banned"
            keyboard = [
                [InlineKeyboardButton(f"📋 Pending Daily ({pending_daily})", callback_data="admin_view_pending"), InlineKeyboardButton(f"💰 Withdraw ({pending_wd})", callback_data="admin_view_withdraw")],
                [InlineKeyboardButton("📅 Today's Tasks", callback_data="admin_view_tasks"), InlineKeyboardButton("📢 Promo Campaigns", callback_data="admin_view_promos")],
                [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"), InlineKeyboardButton("🚫 Banned List", callback_data="admin_banned")],
                [InlineKeyboardButton("📋 Menu", callback_data="back_menu")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            if q:
                try:
                    await q.edit_message_text(text, reply_markup=markup)
                except Exception as e:
                    print(f"Edit admin failed {e}, sending new")
                    await context.bot.send_message(chat_id=uid, text=text, reply_markup=markup)
            else:
                await update.message.reply_text(text, reply_markup=markup)
        except Exception as e:
            print(f"back_admin_cb error: {e}")
            try:
                await context.bot.send_message(chat_id=update.effective_user.id, text="👑 Admin Panel - use /admin")
            except:
                pass
    except Exception as e:
        print(f"back_admin_cb outer error: {e}")

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query
        if q:
            try:
                await q.answer()
            except:
                pass
        await menu(update, context)
    except Exception as e:
        print(f"back_menu error: {e}")


async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    tasks_done=get_tasks(uid)
    today = str(get_ist_today())
    is_joined = await check_user_in_channel(uid, context)
    if not is_joined:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("Check Joined", callback_data="check_joined")]])
        await q.message.reply_text(f"You left channel {CHANNEL_ID}! Re-join! Link: {CHANNEL_LINK}", reply_markup=kb)
        return
    if last_withdraw_date_db.get(uid) == today:
        await q.message.reply_text(f"Already withdrew today! 1 per day only! Last: {today}", reply_markup=main_menu())
        return
    if tasks_done < TASKS_REQUIRED_FOR_WITHDRAW:
        await q.message.reply_text(f"Need {TASKS_REQUIRED_FOR_WITHDRAW} TODAY! You have {tasks_done}/{TASKS_REQUIRED_FOR_WITHDRAW} Total: {tasks_db.get(uid,0)}", reply_markup=main_menu())
        return
    if bal < WITHDRAW_MIN:
        await q.message.reply_text(f"Min Rs{WITHDRAW_MIN}! Balance Rs{bal}", reply_markup=main_menu())
        return
    available = [opt for opt in WITHDRAW_OPTIONS if opt <= bal]
    if not available:
        await q.message.reply_text(f"Balance Rs{bal} less than min!", reply_markup=main_menu())
        return
    kb = [[InlineKeyboardButton(f"Rs{opt}", callback_data=f"wd_select_{opt}")] for opt in available]
    kb.append([InlineKeyboardButton("Menu", callback_data="back_menu")])
    msg = f"Withdraw - Balance: Rs{bal} Available: " + ", ".join([f"Rs{o}" for o in available])
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))



async def wd_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    amount=int(q.data.split("_")[-1])
    uid=q.from_user.id
    fee=int(amount*PLATFORM_FEE_PERCENT/100)
    net=amount-fee
    upi = users_db.get(uid,{}).get('upi','Not set')
    context.user_data['withdraw_amount'] = amount
    bal = get_balance(uid)
    remaining = bal - amount
    msg = f"Withdraw Details Selected: Rs{amount} Fee {PLATFORM_FEE_PERCENT}%: Rs{fee} You Get: Rs{net} Balance: Rs{bal} Remaining: Rs{remaining} UPI: {upi} Is correct?"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"UPI Correct - Confirm Rs{amount}", callback_data=f"wd_confirm_{amount}")],[InlineKeyboardButton("Edit UPI", callback_data="wd_edit_upi")],[InlineKeyboardButton("Cancel", callback_data="back_menu")]])
    await q.message.reply_text(msg, reply_markup=kb)



async def wd_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    amount=int(q.data.split("_")[-1])
    fee=int(amount*PLATFORM_FEE_PERCENT/100)
    net=amount-fee
    upi = users_db.get(uid,{}).get('upi')
    if not upi:
        await q.message.reply_text("❌ UPI not set! Please set UPI via /start registration again!", reply_markup=main_menu())
        return
    withdraw_requests[uid]={'amount':amount, 'fee':fee, 'net':net, 'upi':upi, 'status':'processing', 'date':str(get_ist_today())}
    withdraw_done_date[uid]=str(get_ist_today())
    await q.message.reply_text(f"✅ Withdraw request submitted!\n\nAmount: Rs{amount}\nFee: Rs{fee}\nNet: Rs{net}\nUPI: {upi}\nStatus: Processing\n\nAdmin will approve within 24 hours!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"wd_admin_approve_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"wd_admin_reject_{uid}")]])
            await context.bot.send_message(chat_id=admin_id, text=f"💸 NEW Withdraw Request\nUser {users_db.get(uid,{}).get('name')} ID {uid}\nAmount: Rs{amount} Fee: Rs{fee} Net: Rs{net}\nUPI: {upi}\nBalance: Rs{get_balance(uid)}", reply_markup=kb)
        except: pass

async def admin_approve_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in pending_daily:
        is_first=tasks_db.get(uid,0)==0
        reward=pending_daily[uid].get('task',{}).get('reward',5)
        today=pending_daily[uid].get('date')
        tasks_db[uid]=tasks_db.get(uid,0)+1
        if uid not in daily_task_count: daily_task_count[uid]={}
        daily_task_count[uid][today]=daily_task_count[uid].get(today,0)+1
        if reward!=5: bonus_balance[uid]=bonus_balance.get(uid,0)+(reward-5)
        del pending_daily[uid]
        task_open_time.pop(uid, None)
        for tid, status_data in list(user_task_status.get(uid, {}).items()):
            if isinstance(status_data, dict) and status_data.get('status') == 'pending_verification':
                mark_task_completed_with_interval(uid, tid)
                break
        ref_id=referral_map.get(uid)
        if ref_id and is_first:
            referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
            referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+REFERRAL_BONUS_PER_TASK
        await q.message.reply_text(f"✅ Approved {uid} +Rs{reward}")
        try:
            await context.bot.send_message(chat_id=uid, text=f"✅ Task Approved! +Rs{reward}\nBalance: Rs{get_balance(uid)}\nTasks: {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW}", reply_markup=main_menu())
        except: pass

async def admin_reject_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in pending_daily:
        del pending_daily[uid]
        task_open_time.pop(uid, None)
        for tid, status_data in list(user_task_status.get(uid, {}).items()):
            if isinstance(status_data, dict) and status_data.get('status') == 'pending_verification':
                user_task_status[uid][tid] = {'status': 'pending', 'rejected_at': get_ist_now()}
                break
        await q.message.reply_text(f"❌ Rejected {uid}")
        try:
            await context.bot.send_message(chat_id=uid, text="❌ Task Rejected! Screenshot not valid!\n\nTips:\n- Send clear photo\n- Complete task fully\n- If already have account, use Skip with reason!", reply_markup=main_menu())
        except: pass

async def admin_ban_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    banned_users.add(uid)
    if uid in pending_daily: del pending_daily[uid]
    await q.message.reply_text(f"🚫 Banned {uid}")
    try:
        await context.bot.send_message(chat_id=uid, text="🚫 You are banned! Contact admin!")
    except: pass

async def admin_unban_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    banned_users.discard(uid)
    if uid in warnings_db: warnings_db[uid]['count']=0
    await q.message.reply_text(f"✅ Unbanned {uid}")

async def promo_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts=q.data.split("_")
    uid=int(parts[2]); campaign_id=int(parts[3]); views=int(parts[4])
    campaign = get_promo_campaign(campaign_id)
    if not campaign: return
    earning = int(views * campaign['per_view_member_earning'] / 100)
    promo_earnings_db[uid]=promo_earnings_db.get(uid,0)+earning
    campaign['total_earnings_distributed']+=earning
    if uid in promo_pending:
        del promo_pending[uid]
    await q.message.reply_text(f"✅ Approved Promo {uid} Campaign {campaign_id} Views {views} Earn Rs{earning}")
    try:
        await context.bot.send_message(chat_id=uid, text=f"✅ Promo Approved!\nCampaign {campaign_id} {campaign['shop_name']}\nViews: {views}\nEarn: Rs{earning}\nBalance: Rs{get_balance(uid)}", reply_markup=main_menu())
    except: pass

async def promo_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts=q.data.split("_")
    uid=int(parts[2]); campaign_id=int(parts[3])
    if uid in promo_pending:
        del promo_pending[uid]
    await q.message.reply_text(f"❌ Rejected Promo {uid} Campaign {campaign_id}")
    try:
        await context.bot.send_message(chat_id=uid, text="❌ Promo Rejected! Screenshot not valid! Try again with clear views count!", reply_markup=main_menu())
    except: pass

async def wd_admin_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id):
        await q.message.reply_text("❌ Admin only!")
        return
    uid=int(q.data.split("_")[-1])
    if uid in withdraw_requests:
        req = withdraw_requests[uid]
        amount = req['amount']
        current_bal = get_balance(uid)
        bonus_balance[uid] = bonus_balance.get(uid, 0) - amount
        new_bal = get_balance(uid)
        if new_bal < 0:
            bonus_balance[uid] = bonus_balance.get(uid,0) - new_bal
            new_bal = get_balance(uid)
        req['status']='approved'
        req['approved_at'] = str(get_ist_now())
        last_withdraw_date_db[uid] = str(get_ist_today())
        await q.message.reply_text(f"Approved {uid} Rs{amount} Old Rs{current_bal} New Rs{new_bal}")
        try:
            await context.bot.send_message(chat_id=uid, text=f"Withdraw Approved! Withdrawn Rs{amount} You Get Rs{req['net']} Old Rs{current_bal} New Remaining Rs{new_bal}", reply_markup=main_menu())
        except:
            pass



async def wd_admin_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in withdraw_requests:
        withdraw_requests[uid]['status']='rejected'
        await q.message.reply_text(f"❌ Withdraw Rejected for {uid}")
        try:
            await context.bot.send_message(chat_id=uid, text="❌ Withdraw Rejected! Contact admin for reason!", reply_markup=main_menu())
        except: pass
async def error_handler(update, context):
    print(f"Polling error: {context.error}")
    import traceback
    traceback.print_exc()
    

async def set_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args=context.args
    if not args:
        await update.message.reply_text("Usage: /set_tasks <count> or /set_tasks <user_id> <count>")
        return
    try:
        if len(args)==1:
            target=update.effective_user.id; count=int(args[0])
        else:
            target=int(args[0]); count=int(args[1])
        today=str(get_ist_today())
        tasks_db[target]=count
        if target not in daily_task_count:
            daily_task_count[target]={}
        daily_task_count[target][today]=count
        await update.message.reply_text(f"Tasks set User {target} Today {count}/15")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def set_balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args=context.args
    if not args:
        return
    try:
        if len(args)==1:
            target=update.effective_user.id; amount=int(args[0])
        else:
            target=int(args[0]); amount=int(args[1])
        tasks_db_cur=tasks_db.get(target,0)
        bonus_balance[target]=amount - tasks_db_cur*5
        await update.message.reply_text(f"Balance set Rs{get_balance(target)}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def test_withdraw_setup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    target=update.effective_user.id
    if context.args and context.args[0].isdigit():
        target=int(context.args[0])
    today=str(get_ist_today())
    tasks_db[target]=15
    if target not in daily_task_count:
        daily_task_count[target]={}
    daily_task_count[target][today]=15
    bonus_balance[target]=325
    if target in last_withdraw_date_db:
        del last_withdraw_date_db[target]
    await update.message.reply_text(f"TEST User {target} 15/15 Balance Rs{get_balance(target)}")



def track_missed_tasks_for_user(uid):
    # Check which tasks user missed today (time passed without completing)
    today = str(get_ist_today())
    now = get_ist_time()
    today_tasks = [t for t in scheduled_tasks_db if t['date'] == today]
    missed = []
    user_status = user_task_status.get(uid, {})
    skip_status = skip_db.get(uid, {})
    for task in today_tasks:
        if now > task['close_time_obj']:
            tid = task['id']
            # If not completed and not skipped, it's missed
            status = user_status.get(tid, {}).get('status') if isinstance(user_status.get(tid, {}), dict) else user_status.get(tid)
            skip = skip_status.get(tid, {}).get('status') if isinstance(skip_status.get(tid, {}), dict) else skip_status.get(tid)
            if status != 'completed' and skip != 'skipped':
                missed.append(task)
    if uid not in missed_tasks_db:
        missed_tasks_db[uid] = []
    # Merge without duplicates
    existing_ids = {t['id'] for t in missed_tasks_db[uid]}
    for t in missed:
        if t['id'] not in existing_ids:
            missed_tasks_db[uid].append(t)
    return missed_tasks_db[uid]

async def missed_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    missed = track_missed_tasks_for_user(uid)
    # Also check newly missed
    if not missed:
        await q.message.reply_text("✅ No missed tasks today! Good job! All tasks completed or skipped properly.", reply_markup=main_menu())
        return
    msg = f"❌ Missed Tasks Today - Total {len(missed)}:\n\n"
    for t in missed:
        msg += f"Task {t['task_number']}: {t['title']}\nTime: {t['open_time']}→{t['close_time']} Reward: Rs{t['reward']}\nLink: {t['link']}\n\n"
    msg += "\nTasks time over! You cannot complete now. Next tasks will come tomorrow!"
    await q.message.reply_text(msg, reply_markup=main_menu())

async def my_missed_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    missed = track_missed_tasks_for_user(uid)
    if not missed:
        await update.message.reply_text("✅ No missed tasks!", reply_markup=main_menu())
        return
    msg = f"Missed {len(missed)} tasks:\n"
    for t in missed:
        msg+=f"{t['task_number']}: {t['title']} {t['open_time']}-{t['close_time']}\n"
    await update.message.reply_text(msg, reply_markup=main_menu())


def main():
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Starting bot with Conflict protection...")
    
    retry_count = 0
    max_retries = 20
    
    while retry_count < max_retries:
        app = None
        try:
            print(f"\n🔄 Build attempt {retry_count+1}/{max_retries}")
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Register error handler first
            app.add_error_handler(error_handler)
            try:
                app.add_handler(CallbackQueryHandler(back_admin_cb, pattern="^back_admin$"), group=-1)
                app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"), group=-1)
                print("✅ Global Back buttons registered - Back to Admin fixed")
            except Exception as e:
                print(f"Global back fix: {e}")
            
            # Register all handlers
            conv_reg = ConversationHandler(
                entry_points=[CommandHandler("start", start), CallbackQueryHandler(check_joined_cb, pattern="^check_joined$")],
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
                entry_points=[CallbackQueryHandler(daily_upload_screenshot_cb, pattern="^daily_upload_screenshot$"), CallbackQueryHandler(promo_upload_cb, pattern="^promo_upload_")],
                states={
                    UPLOAD_SCREENSHOT:[MessageHandler(filters.PHOTO, handle_screenshot_upload)],
                    SKIP_REASON:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_skip_reason), CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_")],
                    PROMO_DETAILS:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_promo_views_count)],
                },
                fallbacks=[CommandHandler("cancel", cancel)],
                per_user=True, per_chat=True, per_message=False
            )
            conv_skip = ConversationHandler(
                entry_points=[CallbackQueryHandler(daily_skip_cb, pattern="^daily_skip_")],
                states={
                    SKIP_REASON:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_skip_reason), CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_")],
                },
                fallbacks=[CommandHandler("cancel", cancel)],
                per_user=True, per_chat=True, per_message=False
            )
            conv_set_image = ConversationHandler(
                entry_points=[CommandHandler("set_task_image", set_task_image_cmd)],
                states={
                    SET_IMAGE:[MessageHandler(filters.PHOTO, handle_task_image_upload)],
                },
                fallbacks=[CommandHandler("cancel", cancel)],
                per_user=True, per_chat=True, per_message=False
            )
            app.add_handler(conv_reg)
            app.add_handler(conv_screenshot)
            app.add_handler(conv_skip)
            app.add_handler(conv_set_image)
            app.add_handler(CommandHandler("menu", menu))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("pending", pending_cmd))
            app.add_handler(CommandHandler("approve", approve_cmd))
            app.add_handler(CommandHandler("add_task", add_scheduled_task_with_interval_cmd))
            app.add_handler(CommandHandler("list_tasks", list_scheduled_tasks_cmd))
            app.add_handler(CommandHandler("add_promo", add_promo_campaign_cmd))
            app.add_handler(CommandHandler("list_promos", list_promo_campaigns_cmd))
            app.add_handler(CommandHandler("promo_pending", promo_pending_cmd))
            app.add_handler(CommandHandler("skipped", skipped_tasks_cmd))
            app.add_handler(CommandHandler("warnings", warnings_cmd))
            app.add_handler(CommandHandler("banned", banned_cmd))
            app.add_handler(CommandHandler("unban", unban_cmd))
            app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
            app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
            app.add_handler(CallbackQueryHandler(daily_cb, pattern="^daily$"))
            app.add_handler(CallbackQueryHandler(scheduled_cb, pattern="^scheduled$"))
            app.add_handler(CallbackQueryHandler(promo_tasks_cb, pattern="^promo_tasks$"))
            app.add_handler(CallbackQueryHandler(promo_join_cb, pattern="^promo_join_"))
            app.add_handler(CallbackQueryHandler(promote_shop_cb, pattern="^promote_shop$"))
            app.add_handler(CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_"))
            app.add_handler(CallbackQueryHandler(admin_view_pending_cb, pattern="^admin_view_pending$"))
            app.add_handler(CallbackQueryHandler(admin_view_withdraw_cb, pattern="^admin_view_withdraw$"))
            app.add_handler(CallbackQueryHandler(admin_view_tasks_cb, pattern="^admin_view_tasks$"))
            app.add_handler(CallbackQueryHandler(admin_view_promos_cb, pattern="^admin_view_promos$"))
            app.add_handler(CallbackQueryHandler(admin_view_stats_cb, pattern="^admin_view_stats$"))
            app.add_handler(CallbackQueryHandler(admin_view_banned_cb, pattern="^admin_view_banned$"))
            app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
            app.add_handler(CallbackQueryHandler(missed_tasks_cb, pattern="^missed_tasks$"))
            app.add_handler(CallbackQueryHandler(back_admin_cb, pattern="^back_admin$"))
            app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern="^admin_approve_daily_"))
            app.add_handler(CallbackQueryHandler(admin_reject_daily_cb, pattern="^admin_reject_daily_"))
            app.add_handler(CallbackQueryHandler(promo_approve_cb, pattern="^promo_approve_"))
            app.add_handler(CallbackQueryHandler(promo_reject_cb, pattern="^promo_reject_"))
            app.add_handler(CallbackQueryHandler(admin_ban_cb, pattern="^admin_ban_"))
            app.add_handler(CallbackQueryHandler(admin_unban_cb, pattern="^admin_unban_"))
            app.add_handler(CallbackQueryHandler(wd_select_cb, pattern="^wd_select_"))
            app.add_handler(CallbackQueryHandler(wd_confirm_cb, pattern="^wd_confirm_"))
            app.add_handler(CallbackQueryHandler(wd_admin_approve_cb, pattern="^wd_admin_approve_"))
            app.add_handler(CallbackQueryHandler(wd_admin_reject_cb, pattern="^wd_admin_reject_"))
            app.add_handler(CallbackQueryHandler(support_plans_cb, pattern="^support_plans$"))
            app.add_handler(CallbackQueryHandler(plan_basic_cb, pattern="^plan_basic$"))
            app.add_handler(CallbackQueryHandler(plan_premium_cb, pattern="^plan_premium$"))
            app.add_handler(CallbackQueryHandler(plan_basic_activate_cb, pattern="^plan_basic_activate$"))
            app.add_handler(CallbackQueryHandler(plan_premium_activate_cb, pattern="^plan_premium_activate$"))
            app.add_handler(CallbackQueryHandler(plan_basic_proof_cb, pattern="^plan_basic_proof$"))
            app.add_handler(CallbackQueryHandler(plan_premium_proof_cb, pattern="^plan_premium_proof$"))
            app.add_handler(CallbackQueryHandler(admin_view_plans_cb, pattern="^admin_view_plans$"))
            app.add_handler(CallbackQueryHandler(admin_approve_plan_cb, pattern="^admin_approve_plan_"))
            app.add_handler(CallbackQueryHandler(admin_reject_plan_cb, pattern="^admin_reject_plan_"))
            
            global bot_application
            bot_application = app

            # Notifier thread - using correct function name
            try:
                threading.Thread(target=notification_thread_func, daemon=True).start()
                print("✅ Notifier started")
            except Exception as e:
                print(f"Notifier error: {e}")

            # DELETE WEBHOOK TO AVOID CONFLICT - IMPORTANT FIX
            try:
                import asyncio
                async def del_hook():
                    try:
                        await app.bot.delete_webhook(drop_pending_updates=True)
                        print("✅ Webhook deleted, polling will start")
                    except Exception as e:
                        print(f"Webhook delete: {e}")
                # Run delete webhook
                try:
                    asyncio.get_event_loop().run_until_complete(del_hook())
                except:
                    try:
                        asyncio.run(del_hook())
                    except:
                        pass
            except Exception as e:
                print(f"Delete webhook error {e}")

            print("✅ Handlers registered, starting polling...")
                        # DELETE WEBHOOK TO AVOID CONFLICT - IMPORTANT FIX
            try:
                import asyncio
                async def del_hook():
                    try:
                        await app.bot.delete_webhook(drop_pending_updates=True)
                        print("✅ Webhook deleted, polling will start")
                    except Exception as e:
                        print(f"Webhook delete: {e}")
                try:
                    asyncio.get_event_loop().run_until_complete(del_hook())
                except:
                    try:
                        asyncio.run(del_hook())
                    except:
                        pass
            except Exception as e:
                print(f"Delete webhook error {e}")

            print("✅ Handlers registered, starting polling...")
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES, close_loop=False)

            print("✅ Polling ended cleanly")
            break

        except Exception as e:
            err_str = str(e)
            print(f"❌ Polling error: {err_str[:1000]}")
            if "Conflict" in err_str or "terminated by other" in err_str:
                retry_count += 1
                print(f"Conflict detected, old instance still running! Waiting 30 sec for it to die... Retry {retry_count}/20")
                import time
                time.sleep(30)  # Wait for old instance to die
                wait_time = 20 + (retry_count * 5)
                print(f"⚠️ CONFLICT! Another instance running. Waiting {wait_time}s")
                import time as t_sleep
                t_sleep.sleep(wait_time)
                continue
            else:
                retry_count += 1
                print(f"⚠️ Other error, retrying in 10s... {retry_count}")
                import time as t_sleep
                t_sleep.sleep(10)
                continue

if __name__=="__main__":
    main()
