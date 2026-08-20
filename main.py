import os, re, threading, json, asyncio
from datetime import date, datetime, timedelta, time, timezone
from flask import Flask

# === IST TIMEZONE FIX ===
IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now():
    return datetime.now(IST)
def get_ist_today():
    return get_ist_now().date()
def get_ist_time():
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
        open_dt = datetime.combine(get_ist_today(), open_time)
        close_dt = open_dt + timedelta(minutes=interval_mins)
        close_time = close_dt.time()
    next_time = parse_time_str(next_time_str)
    if not next_time:
        return False, f"Invalid next {next_time_str}"
    open_dt = datetime.combine(get_ist_today(), open_time)
    close_dt = datetime.combine(get_ist_today(), close_time)
    next_dt = datetime.combine(get_ist_today(), next_time)
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
        close_dt = datetime.combine(get_ist_today(), task['close_time_obj'])
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
def get_tasks(uid): return tasks_db.get(uid,0)
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
    q=update.callback_query; await q.answer()
    await admin_panel(q, context)

async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    cnt=referrals_db.get(uid,0)
    earnings = referral_earnings.get(uid,0)
    ref_link = f"https://t.me/{context.bot.username}?start={uid}"
    msg = f"👥 My Referrals\n\nActive: {cnt}\nEarnings: Rs{earnings}\n\n💰 Bonus Rs10 per task + 10% plan commission\n\n🔗 Your Referral Link:\n{ref_link}\n\nShare this link - When friend joins and completes task, you get Rs10!"
    await q.message.reply_text(msg, reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    tasks_done=get_tasks(uid)
    referral_rs=referral_earnings.get(uid,0)
    promo_rs=promo_earnings_db.get(uid,0)
    is_active, plan_name, expiry = check_plan_active(uid)
    count, limit, cap = check_daily_limits(uid)
    msg = f"💰 Wallet\n\nBalance: Rs{bal}\nTasks: {tasks_done}/{TASKS_REQUIRED_FOR_WITHDRAW}\nReferral: Rs{referral_rs}\nPromo: Rs{promo_rs}\nTotal: Rs{bal}\n\n📋 Plan: {plan_name}\nDaily: {count}/{limit} tasks\nCap: Rs{cap}/day\n\nBasic Rs500: {DAILY_TASK_LIMIT_BASIC} tasks/day\nPremium Rs1000: {DAILY_TASK_LIMIT_PREMIUM} tasks/day"
    await q.message.reply_text(msg, reply_markup=main_menu())

async def promo_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    active_campaigns = get_active_promo_campaigns()
    if not active_campaigns:
        msg = "🏪 Promo Tasks Ante Yemiti?\n\nNuvvu adigina idea ye - Local shops promotion!\n\n🏪 Shop owners ki customers kavali - Vallaki yela promote cheyalo talidu\n📱 Mana members (nuvvu) valla shop poster ni WhatsApp Status lo pedtaru\n👀 Nee status ni 200 mandi chustaru - Views vastayi\n💰 Nuvvu Rs10 per 100 views earn chestavu! 200 views = Rs20!\n\nExample:\nKavali Fashions shop Diwali Sale 50% Off poster istundi\nNuvvu status lo pedtav - Nee friends 250 mandi chustaru\nNuvvu screenshot upload cheste Rs25 vastundi wallet lo!\n\nIppudu active campaigns levu - Admin add chestadu!\nShop owners contact @s2edayincome"
        await q.message.reply_text(msg, reply_markup=main_menu())
        return
    msg = f"🏪 Promo Tasks - Local Shops Promotion!\n\nTotal Active: {len(active_campaigns)}\nYour Promo Earnings: Rs{promo_earnings_db.get(uid,0)}\n\n"
    for campaign in active_campaigns[:5]:
        msg += f"🏪 Campaign {campaign['id']}: {campaign['shop_name']} - {campaign['title']}\n   Offer: {campaign['offer']} Earn: Rs{campaign['per_view_member_earning']}/100 views Place: {campaign['place']}\n\n"
    msg += "Click campaign to join!"
    kb = []
    for campaign in active_campaigns[:10]:
        kb.append([InlineKeyboardButton(f"🏪 {campaign['shop_name']} - {campaign['title'][:20]}", callback_data=f"promo_join_{campaign['id']}")])
    kb.append([InlineKeyboardButton("📋 Menu", callback_data="back_menu")])
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb))

async def promo_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    try:
        campaign_id = int(q.data.split("_")[-1])
    except:
        return
    campaign = get_promo_campaign(campaign_id)
    if not campaign:
        await q.message.reply_text("Campaign not found!", reply_markup=main_menu())
        return
    campaign['members_joined'].add(uid)
    msg = f"🎉 Joined Campaign {campaign['id']}!\n\n🏪 {campaign['shop_name']} - {campaign['place']}\nTitle: {campaign['title']}\nOffer: {campaign['offer']}\nPoster: {campaign['poster_link']}\n\n📱 Steps:\n1. Download poster from link\n2. Put WhatsApp Status 24h\n3. After 24h screenshot views\n4. Upload here -> Earn Rs{campaign['per_view_member_earning']}/100 views!\nExample: 250 views = Rs25"
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Views Screenshot", callback_data=f"promo_upload_{campaign['id']}"), InlineKeyboardButton("📋 Promo Tasks", callback_data="promo_tasks")]]))

async def promo_upload_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    try:
        campaign_id = int(q.data.split("_")[-1])
    except:
        return
    context.user_data['promo_upload_campaign_id'] = campaign_id
    await q.message.reply_text(f"📤 Upload Views Screenshot for Campaign {campaign_id}\n\nSend photo of status views count (eye icon + number visible)!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="back_menu")]]))
    return UPLOAD_SCREENSHOT

async def promote_shop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    msg = "📢 Promote Your Shop via S2E Network!\n\nYou have shop in Kavali/Palmaner? Want customers? We have members!\n\nMembers put your poster on WhatsApp Status, you get views!\n\n💰 Pricing:\nRs200 per 1000 views\nMembers earn Rs10 per 100 views\nYour profit Rs10 per 100 views\n\nExample: 5000 views = Shop pays Rs1000, Members get Rs500, You profit Rs500\n\nContact @s2edayincome to start!\n\nAdmin command:\n/add_promo shop|owner|phone|place|category|title|desc|poster|offer|target|price"
    await q.message.reply_text(msg, reply_markup=main_menu())

async def scheduled_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    today_tasks = get_tasks_for_today()
    current, next_task = get_current_scheduled_task_with_interval()
    missed, _ = check_missed_tasks_with_interval(uid)
    count, limit, cap = check_daily_limits(uid)
    is_active, plan_name, _ = check_plan_active(uid)
    msg = f"📋 Scheduled Tasks Today - {get_ist_today()}\nWindow: {TASK_COMPLETION_WINDOW_MINUTES} mins\n\nYour Plan: {plan_name} Daily: {count}/{limit} Cap Rs{cap}\nTotal Tasks Today: {len(today_tasks)}\n\n"
    if not today_tasks:
        msg += "No tasks scheduled today! Admin will add tasks via /add_task\n\nExample: /add_task 12:45PM 15min 1:03PM Join Channel https://t.me/s2edayincome 5"
    else:
        for task in today_tasks:
            task_id = task['id']
            status_data = user_task_status.get(uid, {}).get(task_id, {})
            status = status_data.get('status') if isinstance(status_data, dict) else status_data
            if not status:
                skip_data = skip_db.get(uid, {}).get(task_id, {})
                if (skip_data.get('status') if isinstance(skip_data, dict) else skip_data) == 'skipped':
                    status = 'skipped'
                else:
                    status = 'pending'
            icon = "✅" if status == 'completed' else "❌" if status == 'missed' else "⏭️" if status == 'skipped' else "🔴 LIVE NOW" if current and current['id'] == task_id else "⏰"
            has_img = "🖼️" if task.get('image_file_id') or task['id'] in task_images_db else ""
            msg += f"{icon}{has_img} Task {task['task_number']} {task['open_time']}→{task['close_time']} Next {task['next_time']} - {task['title']} Rs{task['reward']} {status}\n"
    await q.message.reply_text(msg[:4000], reply_markup=main_menu())

async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if uid in banned_users:
        await q.message.reply_text("🚫 You are BANNED! Contact admin!")
        return
    if not is_admin(uid):
        is_joined = await check_user_in_channel(uid, context)
        if not is_joined:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]])
            await q.message.reply_text(f"Please join channel {CHANNEL_ID} to do tasks!", reply_markup=kb)
            return
    today=str(get_ist_today())
    count, limit, cap = check_daily_limits(uid)
    if count >= limit and limit > 0:
        await q.message.reply_text(f"⏰ Daily limit {limit} reached! You did {count} tasks today!\n\nUpgrade to Premium for {DAILY_TASK_LIMIT_PREMIUM} tasks/day!", reply_markup=main_menu())
        return
    current, next_task = get_current_scheduled_task_with_interval()
    missed, newly_missed = check_missed_tasks_with_interval(uid)
    if newly_missed:
        for nm in newly_missed:
            await q.message.reply_text(f"❌ You missed Task {nm['task_number']}! {nm['open_time']}→{nm['close_time']} - {nm['title']}", reply_markup=main_menu())
    if not current:
        next_t = next_task
        if next_t:
            msg = f"⏰ No active task now! Next Task {next_t['task_number']} at {next_t['open_time']} Close {next_t['close_time']} ({next_t['window_minutes']} mins)\n\nCheck Scheduled Tasks for list!"
            await q.message.reply_text(msg, reply_markup=main_menu())
            return
        else:
            task = get_today_task_for_user(uid)
            await q.message.reply_text(f"📅 Today's Task:\n\nTitle: {task['title']}\nReward: Rs{task['reward']}\nLink: {task['link']}\n\nClick Upload Screenshot after completing!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_screenshot"), InlineKeyboardButton("⏭️ Skip Task", callback_data=f"daily_skip_{task.get('id',0)}")]]))
            return
    task_id = current['id']
    status_data = user_task_status.get(uid, {}).get(task_id, {})
    status = status_data.get('status') if isinstance(status_data, dict) else status_data
    if status == 'completed':
        await q.message.reply_text(f"✅ Already Completed Task {current['task_number']}! Next task at {current['next_time']}", reply_markup=main_menu())
        return
    skip_data = skip_db.get(uid, {}).get(task_id, {})
    skip_status = skip_data.get('status') if isinstance(skip_data, dict) else skip_data
    if skip_status == 'skipped':
        await q.message.reply_text(f"⏭️ Already Skipped Task {current['task_number']}! Reason: {skip_data.get('reason')}", reply_markup=main_menu())
        return
    task_open_time[uid] = get_ist_now()
    msg = f"🔴 LIVE TASK {current['task_number']}\nOpen: {current['open_time']} Close: {current['close_time']} ({current['window_minutes']} mins) Next: {current['next_time']}\n\nTitle: {current['title']}\nReward: Rs{current['reward']}\nLink: {current['link']}\n\n⏰ Complete within {current['window_minutes']} mins! By {current['close_time']}!"
    if 'angel' in current['title'].lower() or 'upstox' in current['title'].lower() or 'demat' in current['title'].lower():
        msg += "\n\n⚠️ Already have account? Click Skip Task!"
    # If task has image, send photo with caption - THIS IS YOUR IMAGE FEATURE
    image_file_id = current.get('image_file_id') or task_images_db.get(current['id'])
    if image_file_id:
        try:
            await q.message.reply_photo(photo=image_file_id, caption=msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_screenshot")], [InlineKeyboardButton("⏭️ Skip Task", callback_data=f"daily_skip_{current['id']}")]]))
            return
        except Exception as e:
            print(f"Image send error {e}")
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_screenshot")], [InlineKeyboardButton("⏭️ Skip Task", callback_data=f"daily_skip_{current['id']}")]]))

async def daily_upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    current, next_task = get_current_scheduled_task_with_interval()
    if current:
        await q.message.reply_text(f"📤 Send screenshot for Task {current['task_number']}!\n\nOpen {current['open_time']} Close {current['close_time']} ({current['window_minutes']} mins)\n\nSend as PHOTO, not file!")
    else:
        await q.message.reply_text("📤 Send screenshot as PHOTO!\n\nMake sure it's for today's task!")
    return UPLOAD_SCREENSHOT

async def daily_skip_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    try:
        task_id = int(q.data.split("_")[-1])
    except:
        task_id = None
    current, next_task = get_current_scheduled_task_with_interval()
    if not current and task_id:
        task = next((t for t in get_tasks_for_today() if t['id'] == task_id), None)
        if task:
            current = task
    if not current:
        await q.message.reply_text("No active task to skip! Check Scheduled Tasks!", reply_markup=main_menu())
        return
    context.user_data['skip_task_id'] = current['id']
    context.user_data['skip_task'] = current
    msg = f"⏭️ Skip Task {current['task_number']}\n{current['open_time']}→{current['close_time']} - {current['title']}\n\nWhy skip? Select reason:"
    kb = []
    for i, reason in enumerate(skip_reasons_list):
        kb.append([InlineKeyboardButton(f"{reason}", callback_data=f"skip_reason_{i}")])
    kb.append([InlineKeyboardButton("❌ Cancel", callback_data="back_menu")])
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def skip_reason_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    try:
        reason_idx = int(q.data.split("_")[-1])
        reason = skip_reasons_list[reason_idx]
    except:
        return
    task = context.user_data.get('skip_task')
    task_id = context.user_data.get('skip_task_id')
    if not task or not task_id:
        current, _ = get_current_scheduled_task_with_interval()
        task = current
        task_id = current['id'] if current else None
    if not task or not task_id:
        return
    if reason == "Other - Type reason":
        await q.message.reply_text(f"✍️ Type your reason for skipping Task {task['task_number']} {task['title']}:\n\nExample: I already have account from 2022")
        return SKIP_REASON
    if uid not in skip_db:
        skip_db[uid] = {}
    skip_db[uid][task_id] = {'status': 'skipped', 'reason': reason, 'skipped_at': get_ist_now(), 'task_number': task['task_number'], 'title': task['title']}
    if uid not in user_task_status:
        user_task_status[uid] = {}
    user_task_status[uid][task_id] = {'status': 'skipped', 'skipped_at': get_ist_now(), 'reason': reason, 'task_number': task['task_number']}
    await q.message.reply_text(f"⏭️ Skipped Task {task['task_number']}!\nReason: {reason}\nNext task at {task['next_time']}", reply_markup=main_menu())
    context.user_data.pop('skip_task_id', None)
    context.user_data.pop('skip_task', None)

async def get_skip_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reason = update.message.text.strip()
    if len(reason) < 5:
        await update.message.reply_text("Reason too short! Type at least 5 chars!")
        return SKIP_REASON
    task = context.user_data.get('skip_task')
    task_id = context.user_data.get('skip_task_id')
    if not task or not task_id:
        current, _ = get_current_scheduled_task_with_interval()
        task = current
        task_id = current['id'] if current else None
    if not task or not task_id:
        return ConversationHandler.END
    if uid not in skip_db:
        skip_db[uid] = {}
    skip_db[uid][task_id] = {'status': 'skipped', 'reason': reason, 'skipped_at': get_ist_now(), 'task_number': task['task_number'], 'title': task['title']}
    if uid not in user_task_status:
        user_task_status[uid] = {}
    user_task_status[uid][task_id] = {'status': 'skipped', 'skipped_at': get_ist_now(), 'reason': reason, 'task_number': task['task_number']}
    await update.message.reply_text(f"⏭️ Skipped Task {task['task_number']}!\nReason: {reason}\nNext task at {task['next_time']}", reply_markup=main_menu())
    context.user_data.pop('skip_task_id', None)
    context.user_data.pop('skip_task', None)
    return ConversationHandler.END

async def handle_screenshot_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    today=str(get_ist_today())
    if not update.message.photo:
        await update.message.reply_text("Please send as PHOTO! Not file!")
        return UPLOAD_SCREENSHOT
    campaign_id = context.user_data.get('promo_upload_campaign_id')
    if campaign_id:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        context.user_data['promo_screenshot_file_id'] = file_id
        context.user_data['promo_screenshot_campaign_id'] = campaign_id
        await update.message.reply_text(f"✅ Screenshot received for Promo Campaign {campaign_id}!\n\nNow type how many views you got:\nExample: 150\nCheck your WhatsApp status -> eye icon -> views number\nType views count now:")
        return PROMO_DETAILS
    current, next_task = get_current_scheduled_task_with_interval()
    if not current:
        await update.message.reply_text("❌ No active task now! Check Scheduled Tasks for next task time!", reply_markup=main_menu())
        return ConversationHandler.END
    now = get_ist_time()
    if now > current['close_time_obj']:
        if uid not in user_task_status:
            user_task_status[uid] = {}
        user_task_status[uid][current['id']] = {'status': 'missed', 'missed_at': get_ist_now(), 'task_number': current['task_number']}
        await update.message.reply_text(f"❌ Time over! Task {current['task_number']} closed at {current['close_time']}!", reply_markup=main_menu())
        return ConversationHandler.END
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = photo.file_unique_id
    if file_unique_id in screenshot_hashes:
        if uid not in warnings_db:
            warnings_db[uid] = {'count': 0}
        warnings_db[uid]['count'] += 1
        if warnings_db[uid]['count'] >= 3:
            banned_users.add(uid)
            await update.message.reply_text("🚫 BANNED! 3 Warnings for same screenshot!")
            return ConversationHandler.END
        await update.message.reply_text(f"⚠️ WARNING {warnings_db[uid]['count']}/3 - Same Screenshot already used! Use original!")
        return ConversationHandler.END
    task = current
    screenshot_hashes.add(file_unique_id)
    pending_daily[uid] = {'date': today, 'task': task, 'screenshot_file_id': file_id}
    if uid not in user_task_status:
        user_task_status[uid] = {}
    user_task_status[uid][current['id']] = {'status': 'pending_verification', 'submitted_at': get_ist_now()}
    next_time_str = next_task['open_time'] if next_task else 'tomorrow'
    await update.message.reply_text(f"✅ Screenshot Received for Task {current['task_number']}!\n\nPending Admin Verification!\nReward: Rs{task.get('reward',5)}\nNext Task at {next_time_str}", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Approve Rs{task.get('reward',5)}", callback_data=f"admin_approve_daily_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_daily_{uid}")]])
            await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=f"📋 NEW TASK SUBMISSION\nTask {current['task_number']} {current['open_time']}→{current['close_time']}\nUser {users_db.get(uid,{}).get('name')} ID {uid}\nTask: {task.get('title')}\nReward: Rs{task.get('reward',5)}", reply_markup=kb)
        except: pass
    return ConversationHandler.END

async def get_promo_views_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    try:
        views = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Invalid! Type numbers only! Example: 150")
        return PROMO_DETAILS
    if views < 0 or views > 10000:
        await update.message.reply_text("Views must be 0-10000! Type again!")
        return PROMO_DETAILS
    campaign_id = context.user_data.get('promo_screenshot_campaign_id')
    file_id = context.user_data.get('promo_screenshot_file_id')
    campaign = get_promo_campaign(campaign_id)
    if not campaign:
        await update.message.reply_text("Campaign not found!", reply_markup=main_menu())
        return ConversationHandler.END
    earning = int(views * campaign['per_view_member_earning'] / 100)
    submission = {'uid': uid, 'campaign_id': campaign_id, 'views': views, 'earning': earning, 'file_id': file_id, 'submitted_at': get_ist_now(), 'status': 'pending', 'user_name': users_db.get(uid,{}).get('name','Unknown')}
    campaign['screenshots'].append(submission)
    campaign['total_views'] += views
    campaign['members_joined'].add(uid)
    promo_pending[uid] = submission
    await update.message.reply_text(f"✅ Submitted!\n\nCampaign {campaign_id}: {campaign['shop_name']} - {campaign['title']}\nViews: {views}\nEarning: Rs{earning} (Rs{campaign['per_view_member_earning']} per 100 views)\nStatus: Pending admin verification\n\nAdmin will verify screenshot!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Approve Rs{earning} for {views} views", callback_data=f"promo_approve_{uid}_{campaign_id}_{views}"), InlineKeyboardButton("❌ Reject", callback_data=f"promo_reject_{uid}_{campaign_id}")]])
            await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=f"🏪 NEW PROMO SUBMISSION!\nUser {users_db.get(uid,{}).get('name')} ID {uid}\nCampaign {campaign_id}: {campaign['shop_name']} Views: {views} Earning: Rs{earning}", reply_markup=kb)
        except: pass
    context.user_data.pop('promo_upload_campaign_id', None)
    context.user_data.pop('promo_screenshot_file_id', None)
    context.user_data.pop('promo_screenshot_campaign_id', None)
    return ConversationHandler.END

# === NEW IMAGE POSTER COMMANDS ===
async def set_task_image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /set_task_image <task_id>\n\nThen send photo with caption /set_task_image <id> OR reply to this message with photo\n\nExample:\nFirst add task:\n/add_task 12:45PM 15min 1:03PM Task 3 Google Review https://maps.app.goo.gl/xxx 5\nThen set image:\n/set_task_image 1\nThen send your TASK 3 poster image as PHOTO!")
        return
    try:
        task_id = int(context.args[0])
    except:
        await update.message.reply_text("Task ID must be number! Use /list_tasks to see IDs")
        return
    task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
    if not task:
        await update.message.reply_text(f"Task ID {task_id} not found! Use /list_tasks")
        return
    context.user_data['set_image_task_id'] = task_id
    await update.message.reply_text(f"📸 Now send the poster/image for Task {task_id}: {task['title']}\n\nSend as PHOTO! (Not file)\nYou can send your TASK 3 / TASK 4 images like you showed me - Members will see this image when they open Daily Task!\n\nWaiting for photo...")
    return SET_IMAGE

async def handle_task_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    task_id = context.user_data.get('set_image_task_id')
    if not task_id and update.message.caption:
        m = re.search(r'/set_task_image\s+(\d+)', update.message.caption)
        if m:
            task_id = int(m.group(1))
    if not task_id:
        # Check if admin is replying directly
        if update.message.photo and is_admin(update.effective_user.id):
            # If no task_id set but admin sends photo, try to set for last task
            if scheduled_tasks_db:
                task_id = scheduled_tasks_db[-1]['id']
            else:
                return
    if not update.message.photo:
        await update.message.reply_text("Please send as PHOTO, not file!")
        return SET_IMAGE
    file_id = update.message.photo[-1].file_id
    task_images_db[task_id] = file_id
    task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
    if task:
        task['image_file_id'] = file_id
    await update.message.reply_text(f"✅ Image Poster Set for Task {task_id}!\n{task['title'] if task else ''}\n\n🖼️ Members will now see YOUR TASK 3 / TASK 4 poster image when they click Daily Task!\n\nCheck: /menu -> Daily Task", reply_markup=main_menu())
    context.user_data.pop('set_image_task_id', None)
    return ConversationHandler.END

async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not pending_daily:
        await update.message.reply_text("✅ No pending daily tasks!")
        return
    msg = f"📋 Pending Daily Tasks - {len(pending_daily)}:\n\n"
    for uid, data in list(pending_daily.items())[:20]:
        task = data.get('task',{})
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} - Task {task.get('task_number','?')} {task.get('title','?')} /approve {uid}\n"
    await update.message.reply_text(msg[:4000])

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    try: target_id=int(context.args[0])
    except: return
    if target_id in pending_daily:
        is_first=tasks_db.get(target_id,0)==0
        reward=pending_daily[target_id].get('task',{}).get('reward',5)
        today=pending_daily[target_id].get('date')
        tasks_db[target_id]=tasks_db.get(target_id,0)+1
        if target_id not in daily_task_count: daily_task_count[target_id]={}
        daily_task_count[target_id][today]=daily_task_count[target_id].get(today,0)+1
        if reward!=5: bonus_balance[target_id]=bonus_balance.get(target_id,0)+(reward-5)
        del pending_daily[target_id]
        task_open_time.pop(target_id, None)
        for tid, status_data in list(user_task_status.get(target_id, {}).items()):
            if isinstance(status_data, dict) and status_data.get('status') == 'pending_verification':
                mark_task_completed_with_interval(target_id, tid)
                break
        ref_id=referral_map.get(target_id)
        if ref_id and is_first:
            referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
            referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+REFERRAL_BONUS_PER_TASK
        await update.message.reply_text(f"✅ Approved {target_id} +Rs{reward}")
        try:
            await context.bot.send_message(chat_id=target_id, text=f"✅ Task Approved! +Rs{reward}\nBalance: Rs{get_balance(target_id)}", reply_markup=main_menu())
        except: pass

async def add_scheduled_task_with_interval_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        if not text:
            await update.message.reply_text("Usage: /add_task open close next title reward\nExample: /add_task 2:30PM 15min 2:46PM Task 7 Test 5")
            return
    import re
    urls = re.findall(r'https?://\S+', text)
    link = urls[0] if urls else CHANNEL_LINK
    numbers = re.findall(r'\b\d+\b', text)
    reward = 5
    if numbers:
        last_num = int(numbers[-1])
        if last_num <= 100:
            reward = last_num
    time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM)?|\d{1,2}\s*(?:AM|PM)|\d+\s*min)'
    times = re.findall(time_pattern, text, re.IGNORECASE)
    if len(times) < 3:
        parts = text.split()
        if len(parts) >= 3:
            times = parts[:3]
        else:
            await update.message.reply_text("Need 3 times: open close next\nExample: 12:45PM 15min 1:03PM")
            return
    open_str, close_str, next_str = times[0], times[1], times[2]
    remaining = text
    for t in times[:3]:
        remaining = remaining.replace(t, '', 1)
    remaining = remaining.replace(link, '').strip()
    remaining = re.sub(r'\b' + str(reward) + r'\b\s*$', '', remaining).strip()
    title = remaining if remaining else f"Task at {open_str}"
    success, result = add_scheduled_task_with_interval(open_str, close_str, next_str, title, link, reward)
        if success:
            await update.message.reply_text(f"✅ Added Task ID {result['id']} No {result['task_number']}\n{result['open_time']}→{result['close_time']} Next {result['next_time']}\nTitle: {title}\nReward: Rs{reward}\nPoster optional! Use /set_task_image {result['id']}")
        else:
            await update.message.reply_text(f"❌ Failed: {result}\nTried: {open_str} {close_str} {next_str}")
    except Exception as e:
        print(f"add_task error {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:200]} Try /add_task 2:30PM 15min 2:46PM Test 5")

async def list_scheduled_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    today_tasks = get_tasks_for_today()
    if not today_tasks:
        await update.message.reply_text("No scheduled tasks for today! Add via /add_task")
        return
    msg = f"⏰ Scheduled Tasks Today {get_ist_today()} - Total {len(today_tasks)}:\n\n"
    for task in today_tasks:
        has_poster = "🖼️ Poster YES" if task.get('image_file_id') or task['id'] in task_images_db else "❌ No Poster - /set_task_image"
        msg += f"ID {task['id']} Task {task['task_number']} {task['open_time']}→{task['close_time']} Next {task['next_time']} - {task['title']} Rs{task['reward']} {has_poster}\n"
    await update.message.reply_text(msg[:4000])

async def add_promo_campaign_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = update.message.text.replace('/add_promo','').strip()
    if not text:
        await update.message.reply_text("Usage: /add_promo shop|owner|phone|place|category|title|desc|poster|offer|target|price\n\nExample: /add_promo Kavali Fashions|Ramesh|9876543210|Kavali|Clothing|Diwali Sale|All sarees 50% off|https://poster.link|50% off|10000|200")
        return
    parts = text.split('|')
    if len(parts) < 10:
        await update.message.reply_text("Need 10 fields separated by |\nshop|owner|phone|place|category|title|description|poster|offer|target_views|price")
        return
    try:
        shop_name, owner_name, phone, place, category, title, description, poster_link, offer = [p.strip() for p in parts[:9]]
        target_views = int(parts[9].strip()) if len(parts) > 9 else 10000
        per_1000_price = int(parts[10].strip()) if len(parts) > 10 else 200
        per_100_price = per_1000_price // 10
        campaign = add_promo_campaign(shop_name, owner_name, phone, place, category, title, description, poster_link, offer, target_views, per_100_price, 10)
        await update.message.reply_text(f"✅ Added Promo Campaign ID {campaign['id']}:\n{shop_name} - {title}\nTarget {target_views} views\nShop pays Rs{per_100_price}/100 views\nMember earns Rs10/100 views\nYour profit Rs{per_100_price-10}/100 views\nTotal profit if target met: Rs{(per_100_price-10)*target_views//100}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_promo_campaigns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not promo_campaigns_db:
        await update.message.reply_text("No promo campaigns! Add via /add_promo")
        return
    msg = f"🏪 Promo Campaigns Total {len(promo_campaigns_db)}:\n\n"
    for c in promo_campaigns_db[-20:]:
        msg += f"ID {c['id']}: {c['shop_name']} {c['place']} - {c['title']} Target {c['target_views']} Views {c['total_views']} Members {len(c['members_joined'])}\n"
    await update.message.reply_text(msg[:4000])

async def promo_pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not promo_pending:
        await update.message.reply_text("No pending promo submissions!")
        return
    msg = f"🏪 Pending Promo Submissions - {len(promo_pending)}:\n\n"
    for uid, data in list(promo_pending.items())[:20]:
        msg += f"👤 {uid} {data['user_name']} Campaign {data['campaign_id']} Views {data['views']} Earn Rs{data['earning']}\n"
    await update.message.reply_text(msg[:4000])

async def skipped_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /skipped user_id or /skipped all")
        return
    if context.args[0] == 'all':
        msg = f"⏭️ All skipped tasks today {get_ist_today()}:\n\n"
        total = 0
        for uid, tasks_dict in skip_db.items():
            cnt = len([tid for tid, data in tasks_dict.items() if (data.get('status') if isinstance(data, dict) else data) == 'skipped'])
            if cnt > 0:
                name = users_db.get(uid,{}).get('name','Unknown')
                msg += f"👤 {uid} {name} - Skipped {cnt} tasks /skipped {uid}\n"
                total += cnt
        msg += f"\nTotal skipped: {total}"
        await update.message.reply_text(msg[:4000] if total>0 else "No skipped tasks today!")
        return
    try:
        target_id = int(context.args[0])
    except:
        return
    if target_id not in skip_db:
        await update.message.reply_text(f"User {target_id} has no skipped tasks!")
        return
    msg = f"⏭️ Skipped tasks for {target_id} {users_db.get(target_id,{}).get('name','')}:\n\n"
    for tid, data in skip_db[target_id].items():
        if (data.get('status') if isinstance(data, dict) else data) == 'skipped':
            msg += f"Task {data.get('task_number', tid)} {data.get('title','?')} Reason: {data.get('reason','?')}\n"
    await update.message.reply_text(msg[:4000])

async def warnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not warnings_db:
        await update.message.reply_text("No warnings!")
        return
    msg = f"⚠️ Warnings - {len(warnings_db)}:\n"
    for uid, data in warnings_db.items():
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} - {data.get('count')}/3 /unban {uid}\n"
    await update.message.reply_text(msg[:4000])

async def banned_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not banned_users:
        await update.message.reply_text("No banned users!")
        return
    msg = f"🚫 Banned - {len(banned_users)}:\n"
    for uid in list(banned_users)[:20]:
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} /unban {uid}\n"
    await update.message.reply_text(msg[:4000])

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /unban <id>")
        return
    try: target_id=int(context.args[0])
    except: return
    banned_users.discard(target_id)
    if target_id in warnings_db: warnings_db[target_id]['count']=0
    await update.message.reply_text(f"✅ Unbanned {target_id}")

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"💎 Support Plans:\n\nBasic Rs500: {DAILY_TASK_LIMIT_BASIC} tasks/day Rs{DAILY_EARNING_CAP_BASIC} cap + Bonus Rs50\nPremium Rs1000: {DAILY_TASK_LIMIT_PREMIUM} tasks/day Rs{DAILY_EARNING_CAP_PREMIUM} cap + Bonus Rs100\n\n10% referral commission on plans!\n\nContact {SUPPORT_USERNAME} for payment!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Basic Rs500", callback_data="plan_basic"), InlineKeyboardButton("Premium Rs1000", callback_data="plan_premium")]]))

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"Basic Plan Rs500:\n{DAILY_TASK_LIMIT_BASIC} tasks/day\nEarning cap Rs{DAILY_EARNING_CAP_BASIC}/day\nBonus Rs50\n\nPay to UPI: {ADMIN_UPI}\nLink: upi://pay?pa={ADMIN_UPI}&pn=S2E&am=500&cu=INR&tn=Basic\n\nAfter payment, click Verify!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify Payment", callback_data="verify_basic")]]))

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"Premium Plan Rs1000:\n{DAILY_TASK_LIMIT_PREMIUM} tasks/day\nEarning cap Rs{DAILY_EARNING_CAP_PREMIUM}/day\nBonus Rs100\n\nPay to UPI: {ADMIN_UPI}\nLink: upi://pay?pa={ADMIN_UPI}&pn=S2E&am=1000&cu=INR&tn=Premium\n\nAfter payment, click Verify!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify Payment", callback_data="verify_premium")]]))

async def verify_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    plan_type = q.data.split("_")[1]
    pending_plans[uid] = {'plan': plan_type, 'date': str(get_ist_today())}
    await q.message.reply_text(f"⏳ {plan_type.capitalize()} verification pending!\n\nAdmin will approve within 24 hours!\n\nYou will get bonus after approval!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Approve {plan_type} for {uid}", callback_data=f"admin_approve_plan_{uid}_{plan_type}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_plan_{uid}")]])
            await context.bot.send_message(chat_id=admin_id, text=f"💎 Plan Request\nUser {users_db.get(uid,{}).get('name')} ID {uid}\nPlan: {plan_type}\nUPI: {users_db.get(uid,{}).get('upi')}\nMobile: {users_db.get(uid,{}).get('mobile')}", reply_markup=kb)
        except: pass

async def admin_approve_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts=q.data.split("_")
    uid=int(parts[3]); plan_type=parts[4]
    today=get_ist_today()
    expiry=today+timedelta(days=30 if plan_type=='basic' else 90)
    user_plans[uid]={'plan': plan_type, 'status': 'active', 'start': today, 'expiry': expiry}
    pending_plans.pop(uid,None)
    if plan_type=='premium': bonus_balance[uid]=bonus_balance.get(uid,0)+100
    else: bonus_balance[uid]=bonus_balance.get(uid,0)+50
    ref_id = referral_map.get(uid)
    if ref_id:
        plan_amount = 500 if plan_type=='basic' else 1000
        commission = int(plan_amount * REFERRAL_PLAN_COMMISSION_PERCENT / 100)
        referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+commission
    await q.message.reply_text(f"✅ Approved {plan_type} for {uid} till {expiry}")
    try:
        await context.bot.send_message(chat_id=uid, text=f"✅ Your {plan_type.capitalize()} plan approved till {expiry}!\nBonus added!\nBalance: Rs{get_balance(uid)}", reply_markup=main_menu())
    except: pass

async def admin_reject_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in pending_plans: del pending_plans[uid]
    await q.message.reply_text(f"❌ Rejected plan for {uid}")
    try:
        await context.bot.send_message(chat_id=uid, text="❌ Plan verification rejected! Contact admin @s2edayincome", reply_markup=main_menu())
    except: pass

async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"📞 Contact Us\n\nSupport: {SUPPORT_USERNAME}\nChannel: {CHANNEL_LINK}\nUPI: {ADMIN_UPI}\n\nFor any issues, contact admin!", reply_markup=main_menu())

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    tasks_done=get_tasks(uid)
    if tasks_done < TASKS_REQUIRED_FOR_WITHDRAW:
        await q.message.reply_text(f"❌ Need {TASKS_REQUIRED_FOR_WITHDRAW} tasks! You have {tasks_done}\n\nComplete more tasks via Daily Task!", reply_markup=main_menu())
        return
    if bal < WITHDRAW_MIN:
        await q.message.reply_text(f"❌ Min withdraw Rs{WITHDRAW_MIN}! Balance Rs{bal}\n\nEarn more via referrals and tasks!", reply_markup=main_menu())
        return
    kb = [[InlineKeyboardButton(f"Rs{opt}", callback_data=f"wd_select_{opt}")] for opt in WITHDRAW_OPTIONS if opt <= bal]
    kb.append([InlineKeyboardButton("📋 Menu", callback_data="back_menu")])
    await q.message.reply_text(f"💸 Select withdraw amount\nBalance: Rs{bal}\nMin: Rs{WITHDRAW_MIN}", reply_markup=InlineKeyboardMarkup(kb))

async def wd_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    amount=int(q.data.split("_")[-1])
    uid=q.from_user.id
    fee=int(amount*PLATFORM_FEE_PERCENT/100)
    net=amount-fee
    upi = users_db.get(uid,{}).get('upi','Not set')
    await q.message.reply_text(f"💸 Withdraw Confirmation\n\nAmount: Rs{amount}\nFee {PLATFORM_FEE_PERCENT}%: Rs{fee}\nNet You Get: Rs{net}\nUPI: {upi}\n\nConfirm?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm", callback_data=f"wd_confirm_{amount}"), InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]]))

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
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in withdraw_requests:
        withdraw_requests[uid]['status']='approved'
        await q.message.reply_text(f"✅ Withdraw Approved for {uid} Rs{withdraw_requests[uid]['net']} to {withdraw_requests[uid]['upi']}")
        try:
            await context.bot.send_message(chat_id=uid, text=f"✅ Withdraw Approved!\nNet Rs{withdraw_requests[uid]['net']} sent to {withdraw_requests[uid]['upi']}!", reply_markup=main_menu())
        except: pass

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

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).build()
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
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(back_menu_cb, pattern="^back_menu$")],
        per_user=True, per_chat=True, per_message=False
    )
    conv_skip = ConversationHandler(
        entry_points=[CallbackQueryHandler(daily_skip_cb, pattern="^daily_skip_")],
        states={
            SKIP_REASON:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_skip_reason), CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(back_menu_cb, pattern="^back_menu$")],
        per_user=True, per_chat=True, per_message=False
    )
    conv_set_image = ConversationHandler(
        entry_points=[CommandHandler("set_task_image", set_task_image_cmd)],
        states={
            SET_IMAGE:[MessageHandler(filters.PHOTO, handle_task_image_upload)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(back_menu_cb, pattern="^back_menu$")],
        per_user=True, per_chat=True, per_message=False
    )
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
    app.add_handler(CommandHandler("set_task_image", set_task_image_cmd))
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
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_basic$"))
    app.add_handler(CallbackQueryHandler(verify_plan_cb, pattern="^verify_premium$"))
    app.add_handler(CallbackQueryHandler(admin_approve_plan_cb, pattern="^admin_approve_plan_"))
    app.add_handler(CallbackQueryHandler(admin_reject_plan_cb, pattern="^admin_reject_plan_"))
    app.add_handler(CallbackQueryHandler(contact_us_cb, pattern="^contact_us$"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
    app.add_handler(CallbackQueryHandler(withdraw_cb, pattern="^withdraw$"))
    app.add_handler(conv_reg)
    app.add_handler(conv_screenshot)
    app.add_handler(conv_skip)
    app.add_handler(conv_set_image)
    # Also handle photo with caption for quick set
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"/set_task_image"), handle_task_image_upload))
    print(f"Bot Started! Super Fixed + Poster Support - TASK 3/TASK 4 Image Feature Active!")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
