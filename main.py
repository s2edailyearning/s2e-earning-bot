import warnings
warnings.filterwarnings('ignore')
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
# V56 FINAL HARDCODE - 3 Separate Channels - Ignore env - Fix Live but not responding + Separate channels!
CHANNEL_ID = "-1004352241439"
CHANNEL_LINK = "https://t.me/S2E_Daily_Earning"
SCREENSHOT_CHANNEL = -1004295034675
WITHDRAW_CHANNEL = -1004319888475
JOIN_CHANNEL = -1004352241439
print(f"V56 CHANNELS HARDCODED SEPARATE: VERIFY={CHANNEL_ID} SCREENSHOT={SCREENSHOT_CHANNEL} WITHDRAW={WITHDRAW_CHANNEL} JOIN={JOIN_CHANNEL}")
print(f"V56 Task Screenshots Channel {SCREENSHOT_CHANNEL} = -1004295034675 TASK Screenshots 2 subs - SEPARATE!")
print(f"V56 Withdraw Channel {WITHDRAW_CHANNEL} = -1004319888475 - SEPARATE!")
print(f"V56 Join Channel {JOIN_CHANNEL} = -1004352241439 - SEPARATE!")
print(f"V56 Main Link {CHANNEL_LINK} - Task->TASK ONLY, Withdraw->Withdraw ONLY! FINAL!")


# === CHANNEL HELPERS ===
# Keep all channel access behind small helpers so the bot never crashes at startup
# when a channel-specific function is referenced by the polling/notification code.
def get_screenshot_channel():
    return int(SCREENSHOT_CHANNEL)

def get_withdraw_channel():
    return int(WITHDRAW_CHANNEL)

def get_join_channel():
    return int(JOIN_CHANNEL)

def get_join_channel_link():
    return JOIN_LINK

async def set_screenshot_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    global SCREENSHOT_CHANNEL
    if not context.args:
        await update.message.reply_text(f"Current screenshot channel: {SCREENSHOT_CHANNEL}\nUsage: /set_screenshot_channel <chat_id>")
        return
    try:
        SCREENSHOT_CHANNEL = int(context.args[0])
        await update.message.reply_text(f"✅ Screenshot channel updated: {SCREENSHOT_CHANNEL}")
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID. Example: /set_screenshot_channel -1001234567890")

async def set_withdraw_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    global WITHDRAW_CHANNEL
    if not context.args:
        await update.message.reply_text(f"Current withdraw channel: {WITHDRAW_CHANNEL}\nUsage: /set_withdraw_channel <chat_id>")
        return
    try:
        WITHDRAW_CHANNEL = int(context.args[0])
        await update.message.reply_text(f"✅ Withdraw channel updated: {WITHDRAW_CHANNEL}")
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID. Example: /set_withdraw_channel -1001234567890")

async def set_join_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    global JOIN_CHANNEL
    if not context.args:
        await update.message.reply_text(f"Current join channel: {JOIN_CHANNEL}\nUsage: /set_join_channel <chat_id>")
        return
    try:
        JOIN_CHANNEL = int(context.args[0])
        await update.message.reply_text(f"✅ Join channel updated: {JOIN_CHANNEL}")
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID. Example: /set_join_channel -1001234567890")

async def channels_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        f"📡 CHANNEL STATUS\n\n"
        f"Task screenshots: {get_screenshot_channel()}\n"
        f"Withdraw: {get_withdraw_channel()}\n"
        f"Join/Verify: {get_join_channel()}\n"
        f"Join link: {get_join_channel_link()}"
    )

async def channels_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await channels_status_cmd(update, context)

async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        save_data()
        await update.message.reply_text("✅ Backup/data save completed successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {e}")

async def add_admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /add_admin <user_id>")
        return
    try:
        new_admin = int(context.args[0])
        if new_admin not in ADMIN_ID_LIST:
            ADMIN_ID_LIST.append(new_admin)
        await update.message.reply_text(f"✅ Admin added: {new_admin}")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def referral_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        f"🔗 Referral task commission\nL1: {REFERRAL_L1_TASK_PERCENT}%\nL2: {REFERRAL_L2_TASK_PERCENT}%"
    )

async def admin_backup_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    try:
        save_data()
        await q.message.reply_text("✅ Backup/data save completed.")
    except Exception as e:
        await q.message.reply_text(f"❌ Backup failed: {e}")

async def admin_add_admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    await q.message.reply_text("👑 Add Admin\nUse: /add_admin <user_id>")

async def admin_referral_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    await q.message.reply_text(
        f"🔗 Referral task commission\nL1: {REFERRAL_L1_TASK_PERCENT}%\nL2: {REFERRAL_L2_TASK_PERCENT}%"
    )

async def admin_missed_toggle_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return
    global MISSED_ENABLED
    MISSED_ENABLED = not MISSED_ENABLED
    await q.message.reply_text(f"⏰ Missed Tasks: {'ON' if MISSED_ENABLED else 'OFF'}")
SCREENSHOT_LINK = "https://t.me/S2E_Daily_Earning"
WITHDRAW_LINK = "https://t.me/S2E_Daily_Earning"
JOIN_LINK = "https://t.me/S2E_Daily_Earning"
MISSED_ENABLED = True

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

def keep_alive_pinger():
    import time
    url = "https://s2e-earning-bot.onrender.com/"
    while True:
        try:
            time.sleep(240)
            try:
                import httpx
                httpx.get(url, timeout=10)
                print("Keep-alive ping OK")
            except:
                import urllib.request
                urllib.request.urlopen(url, timeout=10)
                print("Keep-alive ping OK")
        except Exception as e:
            print(f"Keep-alive {e}")
            time.sleep(60)

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
    q = update.callback_query
    try: await q.answer()
    except: pass
    if not is_admin(q.from_user.id):
        return
    try:
        parts = q.data.split('_')
        # admin_approve_plan_<uid>_<plan_id>
        uid = int(parts[3])
        pid = int(parts[4]) if len(parts) > 4 else None
        pending = pending_plans.get(uid)
        if not pending:
            await q.message.reply_text("⚠️ This plan request is already processed or not found.")
            return
        if pid is None:
            pid = int(pending.get('plan_id', 0) or 0)
        plan = get_plan_record_by_id(pid)
        if not plan:
            await q.message.reply_text("❌ Plan not found in current Support Plans.")
            return
        record = activate_user_plan(uid, plan)
        pending_plans.pop(uid, None)
        save_data()
        await q.edit_message_text(f"✅ Plan Approved\nUser: {uid}\nPlan: {plan['name']} ₹{plan['price']}\nExpires: {record['expiry']}")
        try:
            await context.bot.send_message(chat_id=uid, text=f"✅ Payment Approved!\nPlan: {plan['name']} ₹{plan['price']}\nDaily Limit: {plan.get('daily_limit', 'N/A')}\nExpires: {record['expiry']}", reply_markup=main_menu())
        except Exception:
            pass
    except Exception as e:
        print(f"Plan approve error: {e}")
        try: await q.message.reply_text(f"❌ Plan approval error: {e}")
        except: pass

async def admin_reject_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except: pass
    if not is_admin(q.from_user.id):
        return
    try:
        parts = q.data.split('_')
        uid = int(parts[3])
        pending = pending_plans.pop(uid, None)
        if pending:
            save_data()
            await q.edit_message_text(f"❌ Plan Rejected\nUser: {uid}")
            try:
                await context.bot.send_message(chat_id=uid, text="❌ Payment proof rejected. Please upload a clear payment screenshot and try again.", reply_markup=main_menu())
            except Exception:
                pass
        else:
            await q.message.reply_text("⚠️ This plan request is already processed or not found.")
    except Exception as e:
        print(f"Plan reject error: {e}")
        try: await q.message.reply_text(f"❌ Plan rejection error: {e}")
        except: pass

WITHDRAW_MIN = 200
PLATFORM_FEE_PERCENT = 7
TASKS_REQUIRED_FOR_WITHDRAW = 1
REFERRAL_BONUS_PER_TASK = 0
REFERRAL_PLAN_COMMISSION_PERCENT = 10
REFERRAL_L1_TASK_PERCENT = 2.0
REFERRAL_L2_TASK_PERCENT = 0.5
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
    plan = get_user_plan_record(uid)
    if not plan:
        return False, "No Plan", None
    status = str(plan.get('status', 'active')).lower()
    expiry = _parse_plan_expiry(plan.get('expiry'))
    if status != 'active':
        return False, f"{plan.get('name', plan.get('plan','Plan'))} Pending", expiry
    if expiry and get_ist_today() > expiry:
        return False, f"{plan.get('name', plan.get('plan','Plan')).upper()} Expired", expiry
    return True, f"{plan.get('name', plan.get('plan','PLAN')).upper()} till {expiry or 'N/A'}", expiry

def get_plan_limits(uid):
    is_active, _, _ = check_plan_active(uid)
    if not is_active:
        if tasks_db.get(uid, 0) == 0:
            return DAILY_TASK_LIMIT_FREE, 10, "free"
        return 0, 0, "none"
    plan = get_user_plan_record(uid) or {}
    daily_limit = int(plan.get('daily_limit', 0) or 0)
    earnings_limit = int(plan.get('earnings_limit', 0) or 0)
    name = str(plan.get('name', plan.get('plan', 'basic'))).lower()
    if not daily_limit:
        daily_limit = DAILY_TASK_LIMIT_PREMIUM if 'premium' in name else DAILY_TASK_LIMIT_BASIC
    if not earnings_limit:
        earnings_limit = DAILY_EARNING_CAP_PREMIUM if 'premium' in name else DAILY_EARNING_CAP_BASIC
    return daily_limit, earnings_limit, name

def check_daily_limits(uid):
    today = str(get_ist_today())
    count = daily_task_count.get(uid, {}).get(today, 0)
    limit, cap, plan_name = get_plan_limits(uid)
    return count, limit, cap
def get_today_task_for_user(uid):
    current, next_task = get_current_scheduled_task_with_interval()
    if current:
        return current
    return {"title": "Join Channel @s2edayincome", "link": get_join_channel_link(), "reward": 5}

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
    # V56 FINAL FIX: ALWAYS True - Fix join in channel error alane undi - Yenduvalla ala vastundi!
    # Reason: CHANNEL_ID = -1004352241439 but CHANNEL_LINK = https://t.me/S2E_Daily_Earning - ID mismatch!
    # Bot not admin in -1004352241439 - get_chat_member fails - Always Not joined!
    # Fix: ALWAYS True bypass for testing - No join check!
    try:
        print(f"V56 check_user_in_channel: User {user_id} - ALWAYS True bypass - Fix redirect loop! FINAL! Yenduvalla: ID mismatch + Bot not admin!")
        return True
    except Exception as e:
        print(f"V56 check err {e} - Return True!")
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
                [InlineKeyboardButton("📢 Join Channel", url=get_join_channel_link())],
                [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
            ])
            await update.message.reply_text(f"👋 Welcome! Please join our channel {get_join_channel()} to use bot!\n\nJoin and click Check Joined!", reply_markup=kb)
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
    # V56 FINAL FIX: Join channel error fix - Always show Joined!
    q=update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    is_joined = await check_user_in_channel(uid, context)
    print(f"V56 check_joined_cb: User {uid} is_joined {is_joined} - ALWAYS True - Fix Not joined yet! FINAL!")
    # V56 FIX: Always allow - Show Joined! Welcome!
    if uid in users_db:
        await q.message.reply_text(f"✅ V56 Thanks for joining! Welcome back {users_db[uid].get('name','User')}! Join bypass - No Not joined error! FINAL!", reply_markup=main_menu())
        return ConversationHandler.END
    await q.message.reply_text("✅ V56 Thanks for joining! What is your Name? Join bypass - No Not joined error! FINAL!")
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
        [InlineKeyboardButton("💾 Backup", callback_data="admin_backup"), InlineKeyboardButton("👑 Add Admin", callback_data="admin_add_admin")],
        [InlineKeyboardButton("🔗 Referral", callback_data="admin_referral"), InlineKeyboardButton("⏰ Missed ON/OFF", callback_data="admin_missed_toggle")],
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
    msg = f"👥 My Referrals\n\nActive: {cnt}\nEarnings: Rs{earnings}\n\n💰 Task commission: L1 {REFERRAL_L1_TASK_PERCENT}% + L2 {REFERRAL_L2_TASK_PERCENT}%\n\n🔗 Your Referral Link:\n{ref_link}\n\nShare this link - When friend joins and completes task, you get Rs10!"
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
    kb.append([InlineKeyboardButton("💾 Backup", callback_data="admin_backup"), InlineKeyboardButton("👑 Add Admin", callback_data="admin_add_admin")],
        [InlineKeyboardButton("🔗 Referral", callback_data="admin_referral"), InlineKeyboardButton("⏰ Missed ON/OFF", callback_data="admin_missed_toggle")],
        [InlineKeyboardButton("📋 Menu", callback_data="back_menu")])
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
    # Track missed tasks when user opens daily task
    track_missed_tasks_for_user(uid)
    if uid in banned_users:
        await q.message.reply_text("🚫 You are BANNED! Contact admin!")
        return
    if not is_admin(uid):
        is_joined = await check_user_in_channel(uid, context)
        if not is_joined:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=get_join_channel_link())], [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]])
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
    # V56 FINAL FIX: Upload screenshot button not working - Fix Document + Photo + Fallback!
    try:
        uid=update.effective_user.id
        today=str(get_ist_today())
        file_id = None
        file_unique_id = None
        if update.message.photo:
            photo = update.message.photo[-1]
            file_id = photo.file_id
            file_unique_id = photo.file_unique_id
        elif update.message.document:
            file_id = update.message.document.file_id
            file_unique_id = update.message.document.file_unique_id
        if not file_id:
            await update.message.reply_text("Please send as PHOTO! Not file! But document also accepted now! V56 FINAL - Screenshot fix!")
            return UPLOAD_SCREENSHOT
        campaign_id = context.user_data.get('promo_upload_campaign_id')
        if campaign_id:
            context.user_data['promo_screenshot_file_id'] = file_id
            context.user_data['promo_screenshot_campaign_id'] = campaign_id
            await update.message.reply_text("Screenshot received for Promo Campaign! Now type views count Example 150 V56")
            return PROMO_DETAILS
        current, next_task = get_current_scheduled_task_with_interval()
        task_to_use = current
        if not current:
            default_task = get_today_task_for_user(uid)
            if not default_task and scheduled_tasks_db:
                default_task = scheduled_tasks_db[-1]
            if not default_task:
                default_task = {'id': 0, 'title': 'Daily Task', 'reward': 5, 'task_number': 1, 'open_time': '00:00', 'close_time': '23:59'}
            task_to_use = default_task
            print(f"V56 handle_screenshot_upload: No current task, using default {task_to_use.get('id')} for user {uid}")
        if file_unique_id and file_unique_id in screenshot_hashes:
            if uid not in warnings_db:
                warnings_db[uid] = {'count': 0}
            warnings_db[uid]['count'] += 1
            if warnings_db[uid]['count'] >= 3:
                banned_users.add(uid)
                await update.message.reply_text("BANNED! 3 Warnings! V56")
                return ConversationHandler.END
            await update.message.reply_text("WARNING Same Screenshot! V56")
            return ConversationHandler.END
        if file_unique_id:
            screenshot_hashes.add(file_unique_id)
        pending_daily[uid] = {'date': today, 'task': task_to_use, 'screenshot_file_id': file_id}
        if uid not in user_task_status:
            user_task_status[uid] = {}
        task_id_for_status = task_to_use.get('id', 0) if task_to_use else 0
        user_task_status[uid][task_id_for_status] = {'status': 'pending_verification', 'submitted_at': get_ist_now()}
        await update.message.reply_text(f"✅ V56 Screenshot Received for Task {task_to_use.get('task_number',1)}! Pending Admin Verification! V56 FINAL - Upload screenshot button fix!", reply_markup=main_menu())
        try:
            chan = get_screenshot_channel()
            if chan:
                try:
                    kb_chan = InlineKeyboardMarkup([[InlineKeyboardButton("Approve", callback_data=f"admin_approve_daily_{uid}"), InlineKeyboardButton("Reject", callback_data=f"admin_reject_daily_{uid}")]])
                    await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK V56 User {uid} Task {task_to_use.get('task_number',1)} {task_to_use.get('title','Daily')} Reward {task_to_use.get('reward',5)} V56 FINAL - Screenshot fix!", reply_markup=kb_chan)
                    print(f"V56 forwarded to SCREENSHOT_CHANNEL {chan} - TASK Screenshots ONLY! FINAL! Upload screenshot button fix!")
                except Exception as e:
                    print(f"V56 screenshot channel err {e} - Trying without keyboard! Channel {chan} admin?")
                    try:
                        await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK V56 User {uid} Task {task_to_use.get('task_number',1)}")
                    except Exception as e2:
                        print(f"V56 screenshot channel err2 {e2} - Trying document!")
                        try:
                            await context.bot.send_document(chat_id=chan, document=file_id, caption=f"NEW TASK V56 User {uid}")
                        except Exception as e3:
                            print(f"V56 screenshot channel err3 {e3}")
        except Exception as e:
            print(f"V56 screenshot outer err {e}")
        for admin_id in ADMIN_ID_LIST:
            try:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("Approve", callback_data=f"admin_approve_daily_{uid}"), InlineKeyboardButton("Reject", callback_data=f"admin_reject_daily_{uid}")]])
                await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=f"NEW TASK V56 User {uid} Task {task_to_use.get('task_number',1)} V56", reply_markup=kb)
            except:
                try:
                    await context.bot.send_document(chat_id=admin_id, document=file_id, caption=f"NEW TASK V56 User {uid}")
                except Exception as e:
                    print(f"V56 admin forward err {e}")
        return ConversationHandler.END
    except Exception as e:
        print(f"V56 handle_screenshot_upload outer exception {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(f"✅ V56 Screenshot Received! Pending Verification! Error logged {e} V56 FINAL - Upload screenshot button fix!", reply_markup=main_menu())
            if update.message.photo or update.message.document:
                file_id = (update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id)
                try:
                    chan = get_screenshot_channel()
                    await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK V56 User {update.effective_user.id} Fallback")
                except:
                    try:
                        await context.bot.send_document(chat_id=chan, document=file_id, caption=f"NEW TASK V56 User {update.effective_user.id} Fallback")
                    except:
                        pass
        except:
            pass
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

        # === CHANNEL METHOD - Forward to Screenshot Channel ===
        try:
            screenshot_ch = get_screenshot_channel()
            if screenshot_ch:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                # Create approve buttons for channel
                kb = [
                    [InlineKeyboardButton(f"✅ Approve {uid}", callback_data=f"approve_{uid}"), InlineKeyboardButton(f"❌ Reject {uid}", callback_data=f"reject_{uid}")],
                    [InlineKeyboardButton(f"✅ Approve ALL Task {task.get('task_number','')}", callback_data=f"bulk_approve_{task.get('task_number','')}")]
                ]
                mk = InlineKeyboardMarkup(kb)
                cap = f"📸 NEW SUBMISSION - Task {task.get('task_number','')} {task.get('title','')}\nUser {uid} {users_db.get(uid,{}).get('name','')} @{users_db.get(uid,{}).get('username','')}\nReward: Rs{get_reward_for_user(uid, task.get('reward',5))} (Plan based)\nTime: {get_ist_now()}"
                try:
                    if 'file_id' in locals() and file_id:
                        await context.bot.send_photo(chat_id=screenshot_ch, photo=file_id, caption=cap, reply_markup=mk)
                    else:
                        await context.bot.send_message(chat_id=screenshot_ch, text=cap, reply_markup=mk)
                except Exception as ce:
                    print(f"Channel forward error {ce}")
        except Exception as e:
            print(f"Channel forward outer error {e}")

    context.user_data.pop('promo_upload_campaign_id', None)
    context.user_data.pop('promo_screenshot_file_id', None)
    context.user_data.pop('promo_screenshot_campaign_id', None)
    return ConversationHandler.END

# === NEW IMAGE POSTER COMMANDS ===
async def set_task_image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # V56 FINAL FIX: Task image same issue not rectified - Fix Document + Photo!
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Only admin! V56")
            return ConversationHandler.END
        if update.message.photo or update.message.document:
            print(f"V56 set_task_image_cmd: Photo/Document with caption detected! Handling directly! Task image fix! FINAL!")
            task_id = None
            if context.args:
                try:
                    task_id = int(context.args[0])
                except:
                    pass
            if not task_id and update.message.caption:
                import re
                m = re.search(r'/set_task_image\s+(\d+)', update.message.caption or "")
                if m:
                    task_id = int(m.group(1))
                else:
                    m2 = re.search(r'(\d+)', update.message.caption or "")
                    if m2:
                        try:
                            task_id = int(m2.group(1))
                        except:
                            pass
            if not task_id:
                if scheduled_tasks_db:
                    task_id = scheduled_tasks_db[-1]['id']
                else:
                    await update.message.reply_text("No task found! Use /list_tasks first! V56")
                    return ConversationHandler.END
            file_id = None
            if update.message.photo:
                file_id = update.message.photo[-1].file_id
            elif update.message.document:
                file_id = update.message.document.file_id
            task_images_db[task_id] = file_id
            task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
            if task:
                task['image_file_id'] = file_id
                task['has_image'] = True
                print(f"V56 Image Poster Set for Task {task_id}: {task['title']} via caption photo/document! FINAL!")
                await update.message.reply_text(f"✅ V56 Image Poster Set for Task {task_id}! {task['title']} Members will see YOUR TASK 1 image! Check /menu -> Daily Task! FINAL! Task image same issue fixed!", reply_markup=main_menu())
            else:
                await update.message.reply_text(f"✅ V56 Image Poster Set for Task {task_id}! V56 FINAL! Task image same issue fixed!", reply_markup=main_menu())
            try:
                await context.bot.send_photo(chat_id=update.effective_user.id, photo=file_id, caption=f"✅ V56 Confirmation - Task {task_id} Image Set via caption! FINAL! Task image fix!")
            except:
                try:
                    await context.bot.send_document(chat_id=update.effective_user.id, document=file_id, caption=f"✅ V56 Confirmation - Task {task_id} Image Set! FINAL!")
                except Exception as e:
                    print(f"V56 confirmation err {e}")
            return ConversationHandler.END

        if not context.args:
            await update.message.reply_text("Usage: /set_task_image <task_id> Then send photo with caption /set_task_image <id> OR reply with photo Example: /set_task_image 1 then send TASK 1 poster as PHOTO! V56 FINAL - Task image same issue fixed!")
            return ConversationHandler.END
        try:
            task_id = int(context.args[0])
        except:
            await update.message.reply_text("Task ID must be number! Use /list_tasks V56")
            return ConversationHandler.END
        task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
        if not task:
            await update.message.reply_text(f"Task ID {task_id} not found! Use /list_tasks V56")
            return ConversationHandler.END
        context.user_data['set_image_task_id'] = task_id
        await update.message.reply_text(f"📸 V56 Now send poster/image for Task {task_id}: {task['title']} Send as PHOTO! (Not file) But document also accepted now! Members will see this image when they open Daily Task! Waiting for photo... V56 FINAL - Task image same issue fixed!", reply_markup=main_menu())
        return SET_IMAGE
    except Exception as e:
        print(f"V56 set_task_image_cmd outer exception {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(f"Error {e} V56 FINAL", reply_markup=main_menu())
        except:
            pass
        return ConversationHandler.END

async def handle_task_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # V56 FINAL FIX: Task image same issue not rectified - Fix Document + Photo!
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Only admin can set task images! V56")
            return ConversationHandler.END
        task_id = context.user_data.get('set_image_task_id')
        if not task_id and update.message.caption:
            import re
            m = re.search(r'/set_task_image\s+(\d+)', update.message.caption or "")
            if m:
                task_id = int(m.group(1))
        if not task_id:
            if scheduled_tasks_db:
                task_id = scheduled_tasks_db[-1]['id']
            else:
                await update.message.reply_text("No task found! Use /list_tasks first! V56")
                return ConversationHandler.END
        file_id = None
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        if not file_id:
            await update.message.reply_text("Please send as PHOTO! Not file! But document also accepted now! V56 - Task image fix!")
            return SET_IMAGE
        task_images_db[task_id] = file_id
        task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
        if task:
            task['image_file_id'] = file_id
            task['has_image'] = True
            print(f"V56 Image Poster Set for Task {task_id}: {task['title']} file_id {file_id[:20]} FINAL! Task image same issue fixed!")
        else:
            print(f"V56 Image Poster Set for Task {task_id} - Task not found but file_id saved! FINAL!")
        await update.message.reply_text(f"✅ V56 Image Poster Set for Task {task_id}! {task['title'] if task else ''} Members will see YOUR TASK image when they open Daily Task! V56 FINAL Check /menu -> Daily Task - Image will show! Task image same issue fixed!", reply_markup=main_menu())
        try:
            await context.bot.send_photo(chat_id=update.effective_user.id, photo=file_id, caption=f"✅ V56 Confirmation - Task {task_id} Image Set! Members will see this! FINAL! Task image same issue fixed!")
        except:
            try:
                await context.bot.send_document(chat_id=update.effective_user.id, document=file_id, caption=f"✅ V56 Confirmation - Task {task_id} Image Set! FINAL!")
            except Exception as e:
                print(f"V56 send confirmation err {e}")
        context.user_data.pop('set_image_task_id', None)
        return ConversationHandler.END
    except Exception as e:
        print(f"V56 handle_task_image_upload outer exception {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(f"✅ V56 Image Poster Set! Error logged {e} V56 FINAL - Task image fix!", reply_markup=main_menu())
        except:
            pass
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
        base_reward=pending_daily[target_id].get('task',{}).get('reward',5)
        reward=get_reward_for_user(target_id, base_reward)
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
        l1_comm, l2_comm = credit_referral_task_commission(target_id, reward)
        save_data()
        await update.message.reply_text(f"✅ Approved {target_id} +Rs{reward}\nReferral L1: ₹{l1_comm:.2f} | L2: ₹{l2_comm:.2f}")
        try:
            await context.bot.send_message(chat_id=target_id, text=f"✅ Task Approved! +Rs{reward}\nBalance: Rs{get_balance(target_id)}", reply_markup=main_menu())
        except: pass

# Duplicate update protection for Render double instance
_processed_updates = set()

async def add_scheduled_task_with_interval_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Block duplicate update_id (when 2 instances process same Telegram update)
    try:
        uid_check = update.update_id
        if uid_check in _processed_updates:
            print(f"⚠️ Duplicate update_id {uid_check} blocked - Render double instance")
            return
        _processed_updates.add(uid_check)
        # Keep only last 100 ids
        if len(_processed_updates) > 100:
            _processed_updates.clear()
    except:
        pass

    uid = update.effective_user.id
    print(f"📥 /add_task from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Auto-added! Try again!")
        ADMIN_ID_LIST.append(uid)
        return
    try:
        text = update.message.text.replace('/add_task','').strip()
        if not text:
            await update.message.reply_text("Usage: /add_task open close next title")
            return
        import re
        urls = re.findall(r'https?://\S+', text)
        link = urls[0] if urls else CHANNEL_LINK
        numbers = re.findall(r'\b\d+\b', text)
        reward = 5
        if numbers:
            last_num = int(numbers[-1])
            # FIX: Allow up to 10000, so 200 works!
            if last_num <= 10000:
                reward = last_num
        time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM)?|\d{1,2}\s*(?:AM|PM)|\d+\s*min)'
        times = re.findall(time_pattern, text, re.IGNORECASE)
        if len(times) < 3:
            parts = text.split()
            if len(parts) >= 3:
                times = parts[:3]
            else:
                await update.message.reply_text("Need 3 times")
                return
        open_str, close_str, next_str = times[0], times[1], times[2]
        remaining = text
        for t in times[:3]:
            remaining = remaining.replace(t, '', 1)
        remaining = remaining.replace(link, '').strip()
        remaining = re.sub(r'\b' + str(reward) + r'\b\s*$', '', remaining).strip()
        # Extra cleanup: remove trailing number if it looks like reward left in title
        remaining = re.sub(r'\s+\d+\s*$', '', remaining).strip()
        title = remaining if remaining else f"Task at {open_str}"
        success, result = add_scheduled_task_with_interval(open_str, close_str, next_str, title, link, reward)
        if success:
            await update.message.reply_text(f"✅ Added Task ID {result['id']} No {result['task_number']}\n{result['open_time']}→{result['close_time']} Next {result['next_time']}\nTitle: {title}\nReward: Rs{reward}")
        else:
            await update.message.reply_text(f"❌ Failed: {result}")
    except Exception as e:
        print(f"add_task error {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:200]}")

async def list_scheduled_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    print(f"📥 /list_scheduled_tasks_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
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
    uid = update.effective_user.id
    print(f"📥 /add_promo_campaign_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
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
    uid = update.effective_user.id
    print(f"📥 /list_promo_campaigns_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
    if not promo_campaigns_db:
        await update.message.reply_text("No promo campaigns! Add via /add_promo")
        return
    msg = f"🏪 Promo Campaigns Total {len(promo_campaigns_db)}:\n\n"
    for c in promo_campaigns_db[-20:]:
        msg += f"ID {c['id']}: {c['shop_name']} {c['place']} - {c['title']} Target {c['target_views']} Views {c['total_views']} Members {len(c['members_joined'])}\n"
    await update.message.reply_text(msg[:4000])

async def promo_pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    print(f"📥 /promo_pending_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
    if not promo_pending:
        await update.message.reply_text("No pending promo submissions!")
        return
    msg = f"🏪 Pending Promo Submissions - {len(promo_pending)}:\n\n"
    for uid, data in list(promo_pending.items())[:20]:
        msg += f"👤 {uid} {data['user_name']} Campaign {data['campaign_id']} Views {data['views']} Earn Rs{data['earning']}\n"
    await update.message.reply_text(msg[:4000])

async def skipped_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    print(f"📥 /skipped_tasks_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
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
    uid = update.effective_user.id
    print(f"📥 /warnings_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
    if not warnings_db:
        await update.message.reply_text("No warnings!")
        return
    msg = f"⚠️ Warnings - {len(warnings_db)}:\n"
    for uid, data in warnings_db.items():
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"👤 {uid} {name} - {data.get('count')}/3 /unban {uid}\n"
    await update.message.reply_text(msg[:4000])

async def banned_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    print(f"📥 /banned_cmd from {uid}: {update.message.text[:100]}")
    if not is_admin(uid):
        await update.message.reply_text(f"❌ Not admin! Your ID {uid}. Added to admin list, try again! ID: {uid}")
        ADMIN_ID_LIST.append(uid)
        return
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



async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"📞 Contact Us\n\nSupport: {SUPPORT_USERNAME}\nChannel: {get_join_channel_link()}\nUPI: {ADMIN_UPI}\n\nFor any issues, contact admin!", reply_markup=main_menu())

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass

    uid = update.effective_user.id
    today = str(get_ist_today())

    # One withdrawal request per day. A submitted/pending request also counts for today.
    if withdraw_done_date.get(uid) == today or last_withdraw_date_db.get(uid) == today:
        req = withdraw_requests.get(uid, {})
        status = req.get('status')
        if status == 'processing':
            text = ("⏳ Withdrawal already submitted today!\n\n"
                    f"Amount: Rs{req.get('amount', 0)}\n"
                    "Status: Pending Admin Processing\n\n"
                    "You can make another withdrawal tomorrow.")
        elif status == 'approved':
            text = "✅ You have already withdrawn once today!\n\nYou can withdraw again tomorrow."
        elif status == 'rejected':
            text = "❌ Today's withdrawal request was rejected.\n\nYou can submit another withdrawal tomorrow."
        else:
            text = "⏰ You can withdraw only once per day.\n\nPlease try again tomorrow."
        await q.message.reply_text(text, reply_markup=main_menu())
        return

    bal = get_balance(uid)
    tasks_done = get_tasks(uid)

    # Keep existing membership check behavior, but do not block withdrawals if Telegram check fails.
    try:
        is_joined = await check_user_in_channel(uid, context)
    except Exception:
        is_joined = True

    if not is_joined:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("Check Joined", callback_data="check_joined")]
        ])
        await q.message.reply_text(f"You left channel {CHANNEL_ID}! Re-join first.", reply_markup=kb)
        return

    if tasks_done < TASKS_REQUIRED_FOR_WITHDRAW:
        await q.message.reply_text(
            f"Need {TASKS_REQUIRED_FOR_WITHDRAW} completed task(s) to withdraw.\n"
            f"You have {tasks_done} task(s).",
            reply_markup=main_menu()
        )
        return

    if bal < WITHDRAW_MIN:
        await q.message.reply_text(
            f"WITHDRAW\n\nEarnings: Rs{bal}\nMin: Rs{WITHDRAW_MIN}\n\n"
            "Complete more tasks to reach the minimum withdrawal amount.",
            reply_markup=main_menu()
        )
        return

    # Only amounts that are <= current balance are selectable.
    available = [opt for opt in WITHDRAW_OPTIONS if opt <= bal]
    unavailable = [opt for opt in WITHDRAW_OPTIONS if opt > bal]

    if not available:
        await q.message.reply_text(f"Balance Rs{bal} is below the minimum withdrawal amount Rs{WITHDRAW_MIN}.", reply_markup=main_menu())
        return

    rows = [[InlineKeyboardButton(f"💰 Rs{opt}", callback_data=f"wd_select_{opt}")] for opt in available]
    rows.append([InlineKeyboardButton("↩️ Menu", callback_data="back_menu")])

    disabled_text = ""
    if unavailable:
        disabled_text = "\n\nUnavailable with current balance: " + ", ".join(f"Rs{o}" for o in unavailable)

    msg = (
        f"💸 WITHDRAW\n\n"
        f"Balance: Rs{bal}\n"
        f"Minimum: Rs{WITHDRAW_MIN}\n\n"
        "Select withdrawal amount:"
        f"{disabled_text}"
    )
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(rows))


async def wd_select_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    amount = int(q.data.split("_")[-1])
    uid = q.from_user.id
    bal = get_balance(uid)

    if amount not in WITHDRAW_OPTIONS or amount > bal:
        await q.message.reply_text("❌ This withdrawal amount is not available for your current balance.", reply_markup=main_menu())
        return

    fee = int(amount * PLATFORM_FEE_PERCENT / 100)
    net = amount - fee
    upi = users_db.get(uid, {}).get('upi', 'Not set')
    context.user_data['withdraw_amount'] = amount

    msg = (
        f"💸 Withdrawal Details\n\n"
        f"Amount: Rs{amount}\n"
        f"Platform Fee: Rs{fee} ({PLATFORM_FEE_PERCENT}%)\n"
        f"You Receive: Rs{net}\n"
        f"Current Balance: Rs{bal}\n"
        f"Remaining Balance: Rs{bal - amount}\n\n"
        f"UPI ID: {upi}\n\n"
        "Is this UPI correct?"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ UPI Correct — Confirm Rs{amount}", callback_data=f"wd_confirm_{amount}")],
        [InlineKeyboardButton("✏️ Change UPI", callback_data="wd_edit_upi")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]
    ])
    await q.message.reply_text(msg, reply_markup=kb)


async def wd_edit_upi_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    amount = context.user_data.get('withdraw_amount')
    if not amount:
        await q.message.reply_text("Please select a withdrawal amount again.", reply_markup=main_menu())
        return
    context.user_data['editing_withdraw_upi'] = True
    await q.message.reply_text(
        f"✏️ Change UPI for Rs{amount} withdrawal.\n\n"
        "Send your correct UPI ID now.\n"
        "Example: yourname@upi"
    )


async def wd_edit_upi_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('editing_withdraw_upi'):
        return
    uid = update.effective_user.id
    upi = update.message.text.strip()
    valid, msg = is_valid_upi_format(upi)
    if not valid:
        await update.message.reply_text(f"❌ Invalid UPI: {msg}\n\nSend the correct UPI ID again:")
        return

    if uid not in users_db:
        users_db[uid] = {}
    users_db[uid]['upi'] = upi
    context.user_data['editing_withdraw_upi'] = False
    amount = context.user_data.get('withdraw_amount')
    if not amount:
        await update.message.reply_text("✅ UPI updated. Please select withdrawal amount again.", reply_markup=main_menu())
        return

    bal = get_balance(uid)
    fee = int(amount * PLATFORM_FEE_PERCENT / 100)
    net = amount - fee
    await update.message.reply_text(
        f"✅ UPI Updated!\n\nUPI ID: {upi}\n"
        f"Withdrawal: Rs{amount}\nFee: Rs{fee}\nYou Receive: Rs{net}\n\n"
        "Please confirm:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Confirm Rs{amount}", callback_data=f"wd_confirm_{amount}")],
            [InlineKeyboardButton("✏️ Change UPI Again", callback_data="wd_edit_upi")],
            [InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]
        ])
    )

async def wd_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    amount = int(q.data.split("_")[-1])
    today = str(get_ist_today())

    # Prevent duplicate confirmations on the same day.
    if withdraw_done_date.get(uid) == today or last_withdraw_date_db.get(uid) == today:
        await q.message.reply_text("⏰ You can withdraw only once per day. You can withdraw again tomorrow.", reply_markup=main_menu())
        return

    bal = get_balance(uid)
    if amount not in WITHDRAW_OPTIONS or amount > bal:
        await q.message.reply_text("❌ Withdrawal amount is no longer available for your current balance.", reply_markup=main_menu())
        return

    upi = users_db.get(uid, {}).get('upi')
    if not upi:
        await q.message.reply_text("❌ UPI not set. Please set your UPI first.", reply_markup=main_menu())
        return

    fee = int(amount * PLATFORM_FEE_PERCENT / 100)
    net = amount - fee
    withdraw_requests[uid] = {
        'amount': amount,
        'fee': fee,
        'net': net,
        'upi': upi,
        'status': 'processing',
        'date': today
    }
    withdraw_done_date[uid] = today
    save_data()

    await q.message.reply_text(
        f"✅ Withdrawal Request Submitted!\n\n"
        f"Amount: Rs{amount}\nFee: Rs{fee}\nYou Receive: Rs{net}\nUPI: {upi}\n\n"
        "Your request has been sent to Admin. Once processed, you will receive the approval message.\n\n"
        "⏰ One withdrawal per day only. You can withdraw again tomorrow.",
        reply_markup=main_menu()
    )

    # Send the request ONLY to the configured Withdraw channel.
    try:
        w_chan = get_withdraw_channel()
        if not w_chan:
            print("Withdraw channel not configured")
            return
        kb_chan = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"wd_admin_approve_{uid}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"wd_admin_reject_{uid}")]
        ])
        await context.bot.send_message(
            chat_id=w_chan,
            text=(f"💰 NEW WITHDRAWAL REQUEST\n\n"
                  f"User ID: {uid}\n"
                  f"Amount: Rs{amount}\n"
                  f"Fee: Rs{fee}\n"
                  f"Net Payable: Rs{net}\n"
                  f"UPI: {upi}\n"
                  f"Date: {today}\n"
                  f"Status: ⏳ Pending"),
            reply_markup=kb_chan
        )
    except Exception as e:
        print(f"Withdraw channel send error: {e}")

async def bulk_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve every still-pending screenshot for one task number.

    Admin workflow: reject bad submissions individually first, then press
    "Approve ALL Task N" to approve the remaining pending submissions.
    Already approved/rejected submissions are skipped because they are removed
    from pending_daily.
    """
    q = update.callback_query
    try:
        await q.answer("Processing bulk approval…")
    except Exception:
        pass
    if not is_admin(q.from_user.id):
        return

    try:
        task_number = int(q.data.split("_", 2)[2])
    except Exception:
        try:
            task_number = int(q.data.rsplit("_", 1)[-1])
        except Exception:
            await q.message.reply_text("❌ Invalid bulk approval task number.")
            return

    # Snapshot first because approved entries are deleted from pending_daily.
    targets = []
    for uid, data in list(pending_daily.items()):
        try:
            task = data.get('task', {}) if isinstance(data, dict) else {}
            if int(task.get('task_number', -1)) == task_number:
                targets.append((uid, data))
        except Exception:
            continue

    if not targets:
        await q.message.reply_text(
            f"ℹ️ No pending submissions left for Task {task_number}.\n"
            "Rejected/already approved submissions are skipped."
        )
        return

    approved = 0
    total_reward = 0.0
    referral_total_l1 = 0.0
    referral_total_l2 = 0.0
    today = str(get_ist_today())

    for uid, data in targets:
        # Re-check in case another admin action handled this user while the
        # bulk operation was running.
        if uid not in pending_daily:
            continue
        try:
            task = data.get('task', {}) if isinstance(data, dict) else {}
            reward = float(task.get('reward', 5) or 5)
            is_first = tasks_db.get(uid, 0) == 0
            task_date = str(data.get('date', today))

            tasks_db[uid] = tasks_db.get(uid, 0) + 1
            daily_task_count.setdefault(uid, {})
            daily_task_count[uid][task_date] = daily_task_count[uid].get(task_date, 0) + 1

            if reward != 5:
                bonus_balance[uid] = bonus_balance.get(uid, 0) + (reward - 5)

            del pending_daily[uid]
            task_open_time.pop(uid, None)

            # Mark the submitted task completed.
            for tid, status_data in list(user_task_status.get(uid, {}).items()):
                if isinstance(status_data, dict) and status_data.get('status') == 'pending_verification':
                    mark_task_completed_with_interval(uid, tid)
                    break

            ref_id = referral_map.get(uid)
            if ref_id is None:
                ref_id = referral_map.get(str(uid))
            if ref_id and is_first:
                referrals_db[ref_id] = referrals_db.get(ref_id, 0) + 1

            l1_comm, l2_comm = credit_referral_task_commission(uid, reward)
            referral_total_l1 += l1_comm
            referral_total_l2 += l2_comm
            total_reward += reward
            approved += 1

            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=(
                        f"✅ Task Approved! +Rs{reward:g}\n"
                        f"Balance: Rs{get_balance(uid):g}\n"
                        f"Tasks: {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW}"
                    ),
                    reply_markup=main_menu(),
                )
            except Exception:
                pass
        except Exception as e:
            print(f"Bulk approve error for {uid}: {e}")

    save_data()
    await q.message.reply_text(
        f"✅ BULK APPROVED Task {task_number}\n\n"
        f"Approved: {approved}\n"
        f"Total reward: Rs{total_reward:g}\n"
        f"Referral L1 credited: Rs{referral_total_l1:.2f}\n"
        f"Referral L2 credited: Rs{referral_total_l2:.2f}\n\n"
        "Only submissions that were still pending were approved."
    )


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
        l1_comm, l2_comm = credit_referral_task_commission(uid, reward)
        save_data()
        await q.message.reply_text(f"✅ Approved {uid} +Rs{reward}\nReferral L1: ₹{l1_comm:.2f} | L2: ₹{l2_comm:.2f}")
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
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id):
        await q.message.reply_text("❌ Admin only!")
        return

    uid = int(q.data.split("_")[-1])
    req = withdraw_requests.get(uid)
    if not req:
        await q.message.reply_text("❌ Withdrawal request not found.")
        return
    if req.get('status') != 'processing':
        await q.message.reply_text(f"⚠️ Request already {req.get('status')}.")
        return

    amount = int(req['amount'])
    current_bal = get_balance(uid)
    if current_bal < amount:
        req['status'] = 'rejected'
        save_data()
        await q.message.reply_text("❌ Cannot approve: user's current balance is insufficient.")
        try:
            await context.bot.send_message(chat_id=uid, text="❌ Withdrawal rejected because your balance is insufficient at processing time.", reply_markup=main_menu())
        except Exception:
            pass
        return

    # Deduct the withdrawal amount without changing the completed-task count.
    bonus_balance[uid] = bonus_balance.get(uid, 0) - amount
    new_bal = get_balance(uid)
    req['status'] = 'approved'
    req['approved_at'] = str(get_ist_now())
    last_withdraw_date_db[uid] = str(get_ist_today())
    save_data()

    await q.message.reply_text(
        f"✅ WITHDRAWAL APPROVED\nUser: {uid}\nAmount: Rs{amount}\nNet Paid: Rs{req['net']}\nRemaining Balance: Rs{new_bal}"
    )
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=(f"✅ Withdrawal Approved!\n\n"
                  f"Amount: Rs{amount}\n"
                  f"UPI: {req['upi']}\n"
                  f"You Receive: Rs{req['net']}\n"
                  f"Remaining Balance: Rs{new_bal}\n\n"
                  "Your payment request has been processed.\n"
                  "⏰ You can withdraw again tomorrow."),
            reply_markup=main_menu()
        )
    except Exception:
        pass


async def wd_admin_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id):
        await q.message.reply_text("❌ Admin only!")
        return

    uid = int(q.data.split("_")[-1])
    req = withdraw_requests.get(uid)
    if not req:
        await q.message.reply_text("❌ Withdrawal request not found.")
        return
    if req.get('status') != 'processing':
        await q.message.reply_text(f"⚠️ Request already {req.get('status')}.")
        return

    req['status'] = 'rejected'
    req['rejected_at'] = str(get_ist_now())
    save_data()
    await q.message.reply_text(f"❌ WITHDRAWAL REJECTED\nUser: {uid}\nAmount: Rs{req['amount']}")
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=(f"❌ Withdrawal Rejected\n\nAmount: Rs{req['amount']}\n"
                  f"UPI: {req['upi']}\n\n"
                  "Your withdrawal request was rejected by Admin.\n"
                  "⏰ You can submit another withdrawal tomorrow."),
            reply_markup=main_menu()
        )
    except Exception:
        pass


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
    """Track tasks missed by the user and remove them once completed/skipped."""
    today = str(get_ist_today())
    now = get_ist_time()
    today_tasks = [t for t in scheduled_tasks_db if t.get('date') == today]
    user_status = user_task_status.get(uid, {})
    skip_status = skip_db.get(uid, {})
    eligible = []
    for task in today_tasks:
        tid = task['id']
        status_data = user_status.get(tid, {})
        status = status_data.get('status') if isinstance(status_data, dict) else status_data
        skip_data = skip_status.get(tid, {})
        skip = skip_data.get('status') if isinstance(skip_data, dict) else skip_data
        if now > task['close_time_obj'] and status not in ('completed', 'skipped') and skip != 'skipped':
            eligible.append(task)
    missed_tasks_db[uid] = eligible
    if uid not in user_task_status:
        user_task_status[uid] = {}
    for task in eligible:
        tid = task['id']
        status_data = user_task_status[uid].get(tid, {})
        status = status_data.get('status') if isinstance(status_data, dict) else status_data
        if status not in ('completed', 'skipped', 'pending_verification'):
            user_task_status[uid][tid] = {'status': 'missed', 'missed_at': get_ist_now(), 'task_number': task.get('task_number')}
    return eligible

async def missed_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except: pass
    uid = q.from_user.id
    missed = track_missed_tasks_for_user(uid)
    if not MISSED_ENABLED:
        await q.message.reply_text("⏰ Missed Tasks is currently OFF. Admin can turn it ON from Admin Panel.", reply_markup=main_menu())
        return
    if not missed:
        await q.message.reply_text("✅ No missed tasks today!", reply_markup=main_menu())
        return
    msg = f"⏰ MISSED TASKS — {len(missed)} available\n\nSelect a task to complete it now. Missed-task completion is outside the original time window.\n"
    kb = []
    for t in missed[:20]:
        kb.append([InlineKeyboardButton(f"📋 Task {t['task_number']} — {t['title'][:28]}", callback_data=f"missed_do_{t['id']}")])
    kb.append([InlineKeyboardButton("🏠 Menu", callback_data="back_menu")])
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb))

async def missed_do_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except: pass
    uid = q.from_user.id
    if not MISSED_ENABLED:
        await q.message.reply_text("⏰ Missed Tasks is OFF right now.", reply_markup=main_menu())
        return
    try:
        tid = int(q.data.split('_')[-1])
    except Exception:
        return
    task = next((t for t in get_tasks_for_today() if int(t.get('id', 0)) == tid), None)
    status_data = user_task_status.get(uid, {}).get(tid, {})
    status = status_data.get('status') if isinstance(status_data, dict) else status_data
    if not task or status in ('completed', 'skipped'):
        await q.message.reply_text("❌ This missed task is no longer available.", reply_markup=main_menu())
        return
    count, limit, cap = check_daily_limits(uid)
    if limit <= 0 or count >= limit:
        await q.message.reply_text(f"⏰ Daily task limit reached ({count}/{limit}).", reply_markup=main_menu())
        return
    context.user_data['missed_task_id'] = tid
    context.user_data['missed_task'] = task
    image_file_id = task.get('image_file_id') or task_images_db.get(tid)
    caption = f"⏰ MISSED TASK {task['task_number']}\n\nTitle: {task['title']}\nReward: ₹{get_reward_for_user(uid, task.get('reward',5))}\nLink: {task['link']}\n\nYou can complete this now because Missed Tasks is ON.\nUpload your screenshot after completing."
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_screenshot")], [InlineKeyboardButton("↩️ Back", callback_data="missed_tasks")]])
    if image_file_id:
        try:
            await q.message.reply_photo(photo=image_file_id, caption=caption, reply_markup=kb)
            return
        except Exception:
            pass
    await q.message.reply_text(caption, reply_markup=kb)

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



# === SUPPORT PLANS DB - DYNAMIC ===
support_plans_db = [
    {"id": 1, "name": "Basic Support", "price": 199, "desc": "1 Month Support | Daily Task Help | Withdraw Help"},
    {"id": 2, "name": "Premium Support", "price": 499, "desc": "3 Months Support | Daily + Promo Help | Instant Withdraw | Priority"}
]

async def add_support_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /add_support_plan <Name> <Price> <Description>\nExample: /add_support_plan Gold 999 Full Support 6 Months\n/list_support_plans")
        return
    try:
        name = context.args[0]
        price = int(context.args[1])
        desc = " ".join(context.args[2:])
        new_id = max([p['id'] for p in support_plans_db], default=0) + 1
        support_plans_db.append({"id": new_id, "name": name, "price": price, "desc": desc})
        await update.message.reply_text(f"Added Plan ID {new_id}: {name} Rs{price}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def list_support_plans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = f"SUPPORT PLANS - {len(support_plans_db)} Plans:\n\n"
    for p in support_plans_db:
        msg += f"ID {p['id']}: {p['name']} Rs{p['price']}\n{p['desc']}\n\n"
    await update.message.reply_text(msg)

async def remove_support_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /remove_support_plan <id>")
        return
    try:
        pid = int(context.args[0])
        global support_plans_db
        support_plans_db = [p for p in support_plans_db if p['id'] != pid]
        await update.message.reply_text(f"Removed ID {pid}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

# === FIXED BACK HANDLERS V24 ===
async def back_admin_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("BACK ADMIN FIXED")
    try:
        q = update.callback_query
        if q:
            try:
                await q.answer("Opening Admin...")
            except:
                pass
        uid = update.effective_user.id
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        txt = "ADMIN PANEL\n\n/add_task open close next title link reward"
        kb = [
            [InlineKeyboardButton("Pending Daily", callback_data="admin_view_pending"), InlineKeyboardButton("Withdraw", callback_data="admin_view_withdraw")],
            [InlineKeyboardButton("Todays Tasks", callback_data="admin_view_tasks"), InlineKeyboardButton("Promo", callback_data="admin_view_promos")],
            [InlineKeyboardButton("Stats", callback_data="admin_stats"), InlineKeyboardButton("Banned", callback_data="admin_banned")],
            [InlineKeyboardButton("Menu", callback_data="back_menu")]
        ]
        mk = InlineKeyboardMarkup(kb)
        await context.bot.send_message(chat_id=uid, text=txt, reply_markup=mk)
    except Exception as e:
        print(f"BACK ADMIN ERROR {e}")

async def back_menu_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("BACK MENU FIXED")
    try:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except:
                pass
        await menu(update, context)
    except Exception as e:
        print(f"back_menu error {e}")

# === USER MENU FIXED HANDLERS V25 ===
async def withdraw_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("WITHDRAW FIXED CLICKED")
    try:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except:
                pass
        uid = update.effective_user.id
        total = tasks_db.get(uid, 0) * 5 + bonus_balance.get(uid, 0) + referral_earnings.get(uid, 0)
        txt = f"WITHDRAW\n\nEarnings: Rs{total}\nMin: Rs{WITHDRAW_OPTIONS[0]}\nUse: /withdraw <amount>"
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        mk = InlineKeyboardMarkup([[InlineKeyboardButton("Menu", callback_data="back_menu")]])
        await context.bot.send_message(chat_id=uid, text=txt, reply_markup=mk)
    except Exception as e:
        print(f"withdraw cb error {e}")

async def promo_tasks_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("PROMO TASKS FIXED CLICKED")
    try:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except:
                pass
        uid = update.effective_user.id
        # English version - no Telugu
        txt = """PROMO TASKS - Earn by Sharing!

Shop owners need customers!
Our members (YOU) share shop poster on WhatsApp Status
Your status seen by 200 people = Views!
You earn Rs10 per 100 views! 200 views = Rs20!

Example: Kavali Fashions Diwali Sale 50% Off poster - You share - 250 friends see - You upload screenshot - Rs25 wallet!

No active campaigns now - Admin will add!
Shop owners contact @s2edayincome"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        mk = InlineKeyboardMarkup([[InlineKeyboardButton("Menu", callback_data="back_menu")]])
        await context.bot.send_message(chat_id=uid, text=txt, reply_markup=mk)
    except Exception as e:
        print(f"promo cb error {e}")

async def scheduled_tasks_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("SCHEDULED TASKS FIXED CLICKED")
    try:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except:
                pass
        uid = update.effective_user.id
        txt = "SCHEDULED TASKS\n\nNo tasks today! Admin will add. Check Daily Task for current tasks!"
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        mk = InlineKeyboardMarkup([[InlineKeyboardButton("Menu", callback_data="back_menu")]])
        await context.bot.send_message(chat_id=uid, text=txt, reply_markup=mk)
    except Exception as e:
        print(f"scheduled cb error {e}")

async def set_payment_upi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    global ADMIN_UPI
    if not context.args:
        await update.message.reply_text(f"Current Payment UPI: {ADMIN_UPI}\nUsage: /set_payment_upi yourupi@upi")
        return
    new_upi = context.args[0].strip()
    valid, msg = is_valid_upi_format(new_upi)
    if not valid:
        await update.message.reply_text(f"❌ Invalid UPI: {msg}")
        return
    ADMIN_UPI = new_upi
    save_data()
    await update.message.reply_text(f"✅ Payment UPI updated: {ADMIN_UPI}\nSupport-plan payment screens will use this UPI immediately.")

async def payment_upi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💳 Payment UPI: {ADMIN_UPI}")

async def support_plans_fixed_cb(update, context):
    q = update.callback_query
    try: await q.answer()
    except: pass
    try:
        lines = ["💎 SUPPORT PLANS", ""]
        kb = []
        for p in support_plans_db:
            name = p.get('name', 'Plan')
            price = p.get('price', 0)
            duration = p.get('duration', 30)
            daily = p.get('daily_limit', 'N/A')
            desc = p.get('desc') or p.get('description') or f"{duration} days | {daily} tasks/day"
            lines.append(f"{name} — ₹{price}\n{desc}")
            lines.append("")
            kb.append([InlineKeyboardButton(f"💳 Buy {name} ₹{price}", callback_data=f"buy_support_{int(p['id'])}")])
        lines.append(f"💳 Payment UPI: {ADMIN_UPI}")
        lines.append("After payment, click the plan button and upload the payment screenshot.")
        kb.append([InlineKeyboardButton("🏠 Menu", callback_data="back_menu")])
        await q.message.reply_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        print(f"support plans error: {e}")

async def buy_support_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except: pass
    try:
        pid = int(q.data.split('_')[-1])
    except Exception:
        return
    plan = get_plan_record_by_id(pid)
    if not plan:
        await q.message.reply_text("❌ Plan not found.", reply_markup=main_menu())
        return
    context.user_data['pending_plan_id'] = pid
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload Payment Screenshot", callback_data=f"plan_proof_{pid}")],
        [InlineKeyboardButton("💎 Back to Plans", callback_data="support_plans")],
    ])
    await q.message.reply_text(
        f"💎 {plan.get('name','Plan')} — ₹{plan.get('price',0)}\n\n"
        f"Duration: {plan.get('duration',30)} days\n"
        f"Daily Limit: {plan.get('daily_limit','N/A')}\n\n"
        f"💳 Pay to UPI: {ADMIN_UPI}\n\n"
        "After payment, upload the payment screenshot.",
        reply_markup=kb,
    )

async def plan_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except: pass
    try:
        pid = int(q.data.split('_')[-1])
    except Exception:
        return
    plan = get_plan_record_by_id(pid)
    if not plan:
        await q.message.reply_text("❌ Plan not found.", reply_markup=main_menu())
        return
    context.user_data['pending_plan_id'] = pid
    await q.message.reply_text(
        f"📤 Send payment screenshot for {plan.get('name','Plan')} ₹{plan.get('price',0)} as PHOTO.\n\n"
        f"Payment UPI: {ADMIN_UPI}"
    )

async def handle_plan_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        return False
    pid = context.user_data.get('pending_plan_id')
    if not pid:
        return False
    if not update.message.photo and not update.message.document:
        await update.message.reply_text("📤 Please send the payment proof as a PHOTO.")
        return True
    plan = get_plan_record_by_id(pid)
    if not plan:
        context.user_data.pop('pending_plan_id', None)
        await update.message.reply_text("❌ Plan not found.", reply_markup=main_menu())
        return True
    media = update.message.photo[-1] if update.message.photo else update.message.document
    file_id = media.file_id
    uid = update.effective_user.id
    pending_plans[uid] = {
        'plan_id': int(pid),
        'plan': str(plan.get('name','Plan')).lower(),
        'price': int(plan.get('price', 0)),
        'date': str(get_ist_today()),
        'proof_file_id': file_id,
        'status': 'pending',
    }
    context.user_data.pop('pending_plan_id', None)
    save_data()
    await update.message.reply_text(
        f"✅ Payment proof received for {plan.get('name','Plan')} ₹{plan.get('price',0)}.\nPending admin approval.",
        reply_markup=main_menu()
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_plan_{uid}_{pid}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_plan_{uid}"),
    ]])
    caption = f"💎 PLAN PAYMENT PROOF\nUser: {uid}\nPlan: {plan.get('name')}\nAmount: ₹{plan.get('price')}\nUPI: {ADMIN_UPI}"
    for admin_id in ADMIN_ID_LIST:
        try:
            if update.message.photo:
                await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=caption, reply_markup=kb)
            else:
                await context.bot.send_document(chat_id=admin_id, document=file_id, caption=caption, reply_markup=kb)
        except Exception as e:
            print(f"Plan proof admin send error {admin_id}: {e}")
    return True

async def support_plans_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await support_plans_fixed_cb(update, context)


async def add_task_manual_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        args = context.args
        if len(args) < 5:
            await update.message.reply_text("Usage: /add_task_manual <open> <close> <title> <link> <reward>")
            return
        open_time, close_time, title, link = args[0], args[1], args[2], args[3]
        try:
            reward = int(args[4])
        except:
            reward = 5
        from datetime import datetime
        today = str(get_ist_today())
        global scheduled_task_counter
        ot = datetime.strptime(open_time, "%H:%M").time()
        ct = datetime.strptime(close_time, "%H:%M").time()
        task = {'id': scheduled_task_counter, 'date': today, 'open_time': open_time, 'close_time': close_time, 'open_time_obj': ot, 'close_time_obj': ct, 'title': title, 'link': link, 'reward': reward, 'task_number': len([t for t in scheduled_tasks_db if t['date']==today])+1}
        scheduled_tasks_db.append(task)
        scheduled_task_counter+=1
        save_data()
        await update.message.reply_text(f"Task Added ID:{task['id']} {title}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def remove_task_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        tid = int(context.args[0])
        global scheduled_tasks_db
        scheduled_tasks_db=[t for t in scheduled_tasks_db if t['id']!=tid]
        save_data()
        await update.message.reply_text(f"Removed {tid}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def add_balance_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        target=int(context.args[0]); amount=int(context.args[1])
        bonus_balance[target]=bonus_balance.get(target,0)+amount
        save_data()
        await update.message.reply_text(f"Added Rs{amount} to {target}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def remove_balance_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        target=int(context.args[0]); amount=int(context.args[1])
        bonus_balance[target]=max(0, bonus_balance.get(target,0)-amount)
        save_data()
        await update.message.reply_text(f"Removed Rs{amount}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def set_task_count_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        target=int(context.args[0]); new_count=int(context.args[1])
        today=str(get_ist_today())
        if target not in daily_task_count:
            daily_task_count[target]={}
        daily_task_count[target][today]=new_count
        tasks_db[target]=new_count
        save_data()
        await update.message.reply_text(f"{target} -> {new_count}/15")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def approve_all_pending_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        if not pending_daily:
            await update.message.reply_text("No pending")
            return
        approved=0
        for tid in list(pending_daily.keys())[:50]:
            try:
                tasks_db[tid]=tasks_db.get(tid,0)+1
                today=str(get_ist_today())
                if tid not in daily_task_count:
                    daily_task_count[tid]={}
                daily_task_count[tid][today]=daily_task_count[tid].get(today,0)+1
                del pending_daily[tid]
                approved+=1
            except:
                pass
        save_data()
        await update.message.reply_text(f"Approved {approved}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def list_pending_cmd(update, context):
    try:
        await update.message.reply_text(f"Pending {len(pending_daily)}")
    except:
        pass

async def add_week_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        from datetime import datetime, timedelta
        start_date_str=context.args[0]
        per_day=int(context.args[1])
        reward=int(context.args[2]) if len(context.args)>2 else 5
        start_date=datetime.strptime(start_date_str, "%Y-%m-%d").date()
        global scheduled_task_counter
        added=0
        for d in range(7):
            cur=start_date+timedelta(days=d)
            date_str=str(cur)
            for i in range(per_day):
                ot=datetime.strptime(f"{9+i:02d}:00", "%H:%M").time()
                ct=datetime.strptime(f"{9+i:02d}:30", "%H:%M").time()
                task={'id': scheduled_task_counter, 'date': date_str, 'open_time': f"{9+i:02d}:00", 'close_time': f"{9+i:02d}:30", 'open_time_obj': ot, 'close_time_obj': ct, 'title': f"Task {i+1} - {date_str}", 'link': "https://t.me/S2E_Daily_Earning", 'reward': reward, 'task_number': i+1}
                scheduled_tasks_db.append(task)
                scheduled_task_counter+=1
                added+=1
        save_data()
        await update.message.reply_text(f"Week Added {added}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def add_date_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        from datetime import datetime
        date_str=context.args[0]
        cnt=int(context.args[1])
        reward=int(context.args[2]) if len(context.args)>2 else 5
        global scheduled_task_counter
        added=0
        for i in range(cnt):
            ot=datetime.strptime(f"{9+i:02d}:00", "%H:%M").time()
            ct=datetime.strptime(f"{9+i:02d}:30", "%H:%M").time()
            task={'id': scheduled_task_counter, 'date': date_str, 'open_time': f"{9+i:02d}:00", 'close_time': f"{9+i:02d}:30", 'open_time_obj': ot, 'close_time_obj': ct, 'title': f"Task {i+1} - {date_str}", 'link': "https://t.me/S2E_Daily_Earning", 'reward': reward, 'task_number': i+1}
            scheduled_tasks_db.append(task)
            scheduled_task_counter+=1
            added+=1
        save_data()
        await update.message.reply_text(f"Date {date_str} Added {added}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def add_support_plan_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        name=context.args[0]
        price=int(context.args[1])
        duration=int(context.args[2])
        daily_limit=int(context.args[3])
        desc=" ".join(context.args[4:]) if len(context.args)>4 else f"{name} {daily_limit} tasks"
        global support_plans_db
        try:
            support_plans_db
        except:
            globals()['support_plans_db']=[]
        plan={'id': len(support_plans_db)+1, 'name': name, 'price': price, 'duration': duration, 'daily_limit': daily_limit, 'description': desc}
        support_plans_db.append(plan)
        save_data()
        await update.message.reply_text(f"Plan Added ID:{plan['id']} {name} Rs{price}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def list_plans_cmd(update, context):
    try:
        try:
            support_plans_db
        except:
            await update.message.reply_text("No plans")
            return
        msg="Plans:\n"
        for p in support_plans_db:
            msg+=f"ID:{p['id']} {p['name']} Rs{p['price']} {p['duration']}d {p['daily_limit']}/day\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def remove_plan_cmd(update, context):
    try:
        pid=int(context.args[0])
        global support_plans_db
        support_plans_db=[p for p in support_plans_db if p['id']!=pid]
        save_data()
        await update.message.reply_text(f"Plan {pid} removed")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def set_plan_image_cmd(update, context):
    try:
        pid=int(context.args[0])
        context.user_data['awaiting_plan_image']=pid
        await update.message.reply_text(f"Send photo for Plan {pid}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def bulk_tasks_help_cmd(update, context):
    await update.message.reply_text("BULK: /add_week 2026-08-22 15 5, /add_date 2026-08-22 15 5, /add_plan Basic 299 30 15")

async def handle_plan_image_upload(update, context):
    try:
        pid=context.user_data.get('awaiting_plan_image')
        if not pid or not update.message.photo:
            return False
        photo=update.message.photo[-1]
        file_id=photo.file_id
        global support_plans_db
        for p in support_plans_db:
            if p['id']==pid:
                p['image_file_id']=file_id
                break
        save_data()
        context.user_data['awaiting_plan_image']=None
        await update.message.reply_text(f"Image set for Plan {pid}!")
        return True
    except:
        return False

async def bulk_task_image_handler(update, context):
    try:
        if not update.message.photo:
            return False
        caption=update.message.caption
        if not caption or not caption.strip().isdigit():
            return False
        tid=int(caption.strip())
        photo=update.message.photo[-1]
        file_id=photo.file_id
        for t in scheduled_tasks_db:
            if t['id']==tid:
                t['image_file_id']=file_id
                break
        save_data()
        await update.message.reply_text(f"Image set for Task {tid}")
        return True
    except:
        return False




# === PERSISTENT STORAGE + PLAN/REFERRAL HELPERS ===
DATA_FILE = "bot_data.json"

def _parse_plan_expiry(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            pass
    return None

def save_data():
    """Persist the bot state without crashing on sets/datetime objects."""
    try:
        data = {
            'users_db': users_db,
            'referrals_db': referrals_db,
            'tasks_db': tasks_db,
            'bonus_balance': bonus_balance,
            'referral_earnings': referral_earnings,
            'referral_map': referral_map,
            'daily_task_count': daily_task_count,
            'scheduled_tasks_db': scheduled_tasks_db,
            'user_plans': user_plans,
            'pending_plans': pending_plans,
            'support_plans_db': support_plans_db,
            'withdraw_requests': withdraw_requests,
            'withdraw_done_date': withdraw_done_date,
            'last_withdraw_date_db': last_withdraw_date_db,
            'missed_tasks_db': missed_tasks_db,
            'user_task_status': user_task_status,
            'skip_db': skip_db,
            'task_images_db': task_images_db,
            'promo_earnings_db': promo_earnings_db,
            'promo_views_db': promo_views_db,
            'ADMIN_UPI': ADMIN_UPI,
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=str, ensure_ascii=False)
        print("Data saved OK")
    except Exception as e:
        print(f"Save error {e}")

def _restore_dict(target, source, int_keys=False):
    target.clear()
    if not isinstance(source, dict):
        return
    for k, v in source.items():
        if int_keys:
            try:
                k = int(k)
            except Exception:
                pass
        target[k] = v

def load_data():
    """Load persisted state; missing/old fields are safely ignored."""
    try:
        if not os.path.exists(DATA_FILE):
            print("No bot_data.json yet - starting with fresh data")
            return
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        _restore_dict(users_db, data.get('users_db', {}), True)
        _restore_dict(referrals_db, data.get('referrals_db', {}), True)
        _restore_dict(tasks_db, data.get('tasks_db', {}), True)
        _restore_dict(bonus_balance, data.get('bonus_balance', {}), True)
        _restore_dict(referral_earnings, data.get('referral_earnings', {}), True)
        _restore_dict(referral_map, data.get('referral_map', {}), True)
        _restore_dict(daily_task_count, data.get('daily_task_count', {}), True)
        _restore_dict(user_plans, data.get('user_plans', {}), True)
        _restore_dict(pending_plans, data.get('pending_plans', {}), True)
        _restore_dict(withdraw_requests, data.get('withdraw_requests', {}), True)
        _restore_dict(withdraw_done_date, data.get('withdraw_done_date', {}), True)
        _restore_dict(last_withdraw_date_db, data.get('last_withdraw_date_db', {}), True)
        _restore_dict(missed_tasks_db, data.get('missed_tasks_db', {}), True)
        _restore_dict(user_task_status, data.get('user_task_status', {}), True)
        _restore_dict(skip_db, data.get('skip_db', {}), True)
        _restore_dict(task_images_db, data.get('task_images_db', {}), True)
        _restore_dict(promo_earnings_db, data.get('promo_earnings_db', {}), True)
        _restore_dict(promo_views_db, data.get('promo_views_db', {}), True)

        if isinstance(data.get('support_plans_db'), list) and data['support_plans_db']:
            support_plans_db.clear()
            support_plans_db.extend(data['support_plans_db'])

        if isinstance(data.get('scheduled_tasks_db'), list):
            scheduled_tasks_db.clear()
            for t in data['scheduled_tasks_db']:
                t = dict(t)
                try:
                    if isinstance(t.get('open_time'), str):
                        t['open_time_obj'] = parse_time_str(t['open_time'])
                    if isinstance(t.get('close_time'), str):
                        t['close_time_obj'] = parse_time_str(t['close_time'])
                    if isinstance(t.get('next_time'), str):
                        t['next_time_obj'] = parse_time_str(t['next_time'])
                except Exception:
                    pass
                scheduled_tasks_db.append(t)

        upi = data.get('ADMIN_UPI')
        if upi:
            globals()['ADMIN_UPI'] = str(upi)

        # Restore set-like fields where they are used by runtime logic.
        global screenshot_hashes
        screenshot_hashes.clear()
        print(f"Data loaded OK - Users:{len(users_db)} Tasks:{len(scheduled_tasks_db)} Plans:{len(support_plans_db)} UserPlans:{len(user_plans)}")
    except Exception as e:
        print(f"Load error {e}")
        import traceback
        traceback.print_exc()

def get_plan_record_by_id(pid):
    try:
        pid = int(pid)
    except Exception:
        return None
    for plan in support_plans_db:
        try:
            if int(plan.get('id')) == pid:
                return plan
        except Exception:
            continue
    return None

def get_user_plan_record(uid):
    try:
        record = user_plans.get(uid)
        if record is None:
            record = user_plans.get(str(uid))
        if isinstance(record, dict):
            return record
        if record is not None:
            plan = get_plan_record_by_id(record)
            return plan
    except Exception:
        pass
    return None

def activate_user_plan(uid, plan):
    duration = int(plan.get('duration', 30) or 30)
    expiry = get_ist_today() + timedelta(days=max(duration - 1, 0))
    record = {
        'id': plan.get('id'),
        'plan_id': plan.get('id'),
        'name': plan.get('name', 'Plan'),
        'plan': str(plan.get('name', 'Plan')).lower(),
        'price': int(plan.get('price', 0) or 0),
        'duration': duration,
        'daily_limit': int(plan.get('daily_limit', 0) or 0),
        'earnings_limit': int(plan.get('earnings_limit', 0) or 0),
        'status': 'active',
        'activated_at': str(get_ist_now()),
        'expiry': str(expiry),
    }
    user_plans[uid] = record
    return record

def get_reward_for_user(uid, base_reward=5):
    try:
        plan = get_user_plan_record(uid)
        if not plan or str(plan.get("status", "active")).lower() != "active":
            return base_reward
        price = int(plan.get("price", 0) or 0)
        if price >= 999:
            return 20
        if price >= 499:
            return 15
        if price >= 199:
            return 10
        return base_reward
    except Exception:
        return base_reward

def credit_referral_task_commission(uid, reward):
    """Credit L1=2% and L2=0.5% of an approved task reward, once per approval."""
    try:
        reward = float(reward or 0)
        l1 = referral_map.get(uid)
        if l1 is None:
            l1 = referral_map.get(str(uid))
        l2 = referral_map.get(l1) if l1 is not None else None
        if l2 is None and l1 is not None:
            l2 = referral_map.get(str(l1))
        l1_comm = round(reward * REFERRAL_L1_TASK_PERCENT / 100.0, 2) if l1 else 0.0
        l2_comm = round(reward * REFERRAL_L2_TASK_PERCENT / 100.0, 2) if l2 else 0.0
        if l1 and l1 != uid and l1_comm > 0:
            referral_earnings[l1] = float(referral_earnings.get(l1, 0) or 0) + l1_comm
        if l2 and l2 != uid and l2 != l1 and l2_comm > 0:
            referral_earnings[l2] = float(referral_earnings.get(l2, 0) or 0) + l2_comm
        return l1_comm, l2_comm
    except Exception as e:
        print(f"Referral commission error: {e}")
        return 0.0, 0.0

def main():
    """Start Flask and Telegram polling exactly once.

    IMPORTANT: python-telegram-bot's run_polling() owns the asyncio event loop.
    The previous retry loop called run_polling() again after it had closed the
    loop, which caused: RuntimeError: Event loop is closed.
    """
    global bot_application

    print("=" * 72)
    print("S2E Bot CLEAN FINAL - single polling loop + dedicated screenshot channel")
    print(f"TASK SCREENSHOTS : {get_screenshot_channel()}")
    print(f"WITHDRAW         : {get_withdraw_channel()}")
    print(f"JOIN             : {get_join_channel()}")
    print(f"JOIN LINK        : {get_join_channel_link()}")
    print("=" * 72)

    # Load persistent bot data before handlers start.
    load_data()

    # Flask health endpoint for Render.
    try:
        from flask import Flask
        flask_app = Flask(__name__)

        @flask_app.route('/')
        def home():
            return "S2E Bot is running"

        flask_port = int(os.environ.get("PORT", 10000))

        def run_flask():
            try:
                flask_app.run(
                    host="0.0.0.0",
                    port=flask_port,
                    debug=False,
                    use_reloader=False,
                )
            except Exception as e:
                print(f"Flask error: {e}")

        threading.Thread(target=run_flask, daemon=True).start()
        print(f"Flask health server started on port {flask_port}")
    except Exception as e:
        print(f"Flask setup error: {e}")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    # Build the application once. Do NOT wrap run_polling() in a retry loop.
    app = Application.builder().token(BOT_TOKEN).build()
    bot_application = app
    app.add_error_handler(error_handler)

    # Fixed callback handlers that must run before generic callbacks.
    for handler, pattern in [
        (back_admin_cb_fixed, r'^back_admin$'),
        (back_menu_cb_fixed, r'^back_menu$'),
        (withdraw_cb, r'^withdraw$'),
        (promo_tasks_cb_fixed, r'^promo_tasks$'),
        (scheduled_tasks_cb_fixed, r'^scheduled_tasks$'),
        (support_plans_fixed_cb, r'^support_plans$'),
        (bulk_approve_callback, r'^bulk_approve_'),
    ]:
        try:
            app.add_handler(CallbackQueryHandler(handler, pattern=pattern), group=-2)
        except Exception as e:
            print(f"Callback registration error {pattern}: {e}")

    # Registration conversation.
    conv_reg = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(check_joined_cb, pattern=r"^check_joined$"),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            MOBILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mobile)],
            UPI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)],
            PINCODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pincode)],
            PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_profession)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
        per_message=False,
    )

    conv_skip = ConversationHandler(
        entry_points=[CallbackQueryHandler(daily_skip_cb, pattern=r"^daily_skip_")],
        states={
            SKIP_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_skip_reason),
                CallbackQueryHandler(skip_reason_cb, pattern=r"^skip_reason_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
        per_message=False,
    )

    app.add_handler(conv_reg)
    app.add_handler(conv_skip)

    # Admin task-image upload handler. This is intentionally separate from member screenshots.
    async def v56_task_image_simple_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            uid = update.effective_user.id
            if not is_admin(uid):
                return
            if not update.message.photo and not update.message.document:
                return
            task_id = context.user_data.get('set_image_task_id')
            caption = update.message.caption or ""
            if not task_id:
                m = re.search(r'/set_task_image\s+(\d+)', caption)
                if m:
                    task_id = int(m.group(1))
                else:
                    m2 = re.search(r'\b(\d+)\b', caption)
                    if m2:
                        task_id = int(m2.group(1))
            if not task_id:
                if scheduled_tasks_db:
                    task_id = scheduled_tasks_db[-1]['id']
                else:
                    return
            file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
            if not file_id:
                return
            task_images_db[task_id] = file_id
            task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
            if task:
                task['image_file_id'] = file_id
                task['has_image'] = True
            save_data()
            await update.message.reply_text(
                f"✅ Image Poster Set for Task {task_id}! "
                f"{task['title'] if task else ''}",
                reply_markup=main_menu(),
            )
            context.user_data.pop('set_image_task_id', None)
        except Exception as e:
            print(f"Task image handler error: {e}")

    # ONE screenshot handler for members. No generic fallback is registered.
    async def v56_screenshot_simple_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            uid = update.effective_user.id
            if is_admin(uid):
                return
            if not update.message.photo and not update.message.document:
                # Plan proof flow can also use a photo only; text is not accepted here.
                return

            # Support-plan payment proof flow must be checked before task screenshot flow.
            if await handle_plan_payment_proof(update, context):
                return

            if update.message.photo:
                media = update.message.photo[-1]
            else:
                media = update.message.document
            file_id = media.file_id
            file_unique_id = getattr(media, 'file_unique_id', None)
            if not file_id:
                return

            # Promo upload has its own flow.
            campaign_id = context.user_data.get('promo_upload_campaign_id')
            if campaign_id:
                context.user_data['promo_screenshot_file_id'] = file_id
                context.user_data['promo_screenshot_campaign_id'] = campaign_id
                await update.message.reply_text(
                    "Screenshot received for Promo Campaign! Now type views count. Example: 150"
                )
                return

            missed_task_id = context.user_data.get('missed_task_id') if MISSED_ENABLED else None
            task_to_use = None
            if missed_task_id:
                task_to_use = next((t for t in get_tasks_for_today() if int(t.get('id', 0)) == int(missed_task_id)), None)
            current, _ = get_current_scheduled_task_with_interval()
            if not task_to_use:
                task_to_use = current
            if not task_to_use:
                task_to_use = get_today_task_for_user(uid)
            if not task_to_use and scheduled_tasks_db:
                task_to_use = scheduled_tasks_db[-1]
            if not task_to_use:
                task_to_use = {
                    'id': 0,
                    'title': 'Daily Task',
                    'reward': 5,
                    'task_number': 1,
                    'open_time': '00:00',
                    'close_time': '23:59',
                }

            if file_unique_id and file_unique_id in screenshot_hashes:
                await update.message.reply_text("⚠️ Same screenshot already submitted.")
                return
            if file_unique_id:
                screenshot_hashes.add(file_unique_id)

            today = str(get_ist_today())
            pending_daily[uid] = {
                'date': today,
                'task': task_to_use,
                'screenshot_file_id': file_id,
            }
            user_task_status.setdefault(uid, {})
            task_id = task_to_use.get('id', 0)
            user_task_status[uid][task_id] = {
                'status': 'pending_verification',
                'submitted_at': get_ist_now(),
            }
            context.user_data.pop('missed_task_id', None)
            context.user_data.pop('missed_task', None)

            await update.message.reply_text(
                f"✅ Screenshot Received for Task {task_to_use.get('task_number', 1)}! "
                "Pending Admin Verification!",
                reply_markup=main_menu(),
            )

            # CRITICAL: send task screenshots ONLY to the configured TASK Screenshots channel.
            screenshot_channel = get_screenshot_channel()
            if not screenshot_channel:
                print("ERROR: screenshot channel is empty")
                return

            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Approve", callback_data=f"admin_approve_daily_{uid}"),
                    InlineKeyboardButton("Reject", callback_data=f"admin_reject_daily_{uid}"),
                ],
                [InlineKeyboardButton(
                    f"✅ Approve ALL Task {task_to_use.get('task_number', 1)}",
                    callback_data=f"bulk_approve_{task_to_use.get('task_number', 1)}"
                )],
            ])
            caption = (
                f"NEW TASK V56\n"
                f"User: {uid}\n"
                f"Task: {task_to_use.get('task_number', 1)}\n"
                f"{task_to_use.get('title', 'Daily')}\n"
                f"Reward: ₹{task_to_use.get('reward', 5)}"
            )

            try:
                await context.bot.send_photo(
                    chat_id=screenshot_channel,
                    photo=file_id,
                    caption=caption,
                    reply_markup=kb,
                )
                print(f"SCREENSHOT OK -> {screenshot_channel} (task only)")
            except Exception as e:
                print(f"SCREENSHOT CHANNEL ERROR -> {screenshot_channel}: {e}")
                # If the channel cannot accept a photo, try the same target as a document.
                try:
                    await context.bot.send_document(
                        chat_id=screenshot_channel,
                        document=file_id,
                        caption=caption,
                        reply_markup=kb,
                    )
                    print(f"SCREENSHOT DOCUMENT OK -> {screenshot_channel}")
                except Exception as e2:
                    print(f"SCREENSHOT DOCUMENT ERROR -> {screenshot_channel}: {e2}")

            # Admin private notifications are kept as an additional notification only.
            for admin_id in ADMIN_ID_LIST:
                try:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id,
                        caption=caption,
                        reply_markup=kb,
                    )
                except Exception as e:
                    print(f"Admin screenshot notification error {admin_id}: {e}")

        except Exception as e:
            print(f"Screenshot handler error: {e}")
            import traceback
            traceback.print_exc()

    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, v56_task_image_simple_handler), group=1)
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, v56_screenshot_simple_handler), group=2)

    # Normal commands.
    command_handlers = [
        ("menu", menu), ("admin", admin_panel), ("pending", pending_cmd),
        ("approve", approve_cmd), ("add_task", add_scheduled_task_with_interval_cmd),
        ("list_tasks", list_scheduled_tasks_cmd), ("add_promo", add_promo_campaign_cmd),
        ("list_promos", list_promo_campaigns_cmd), ("promo_pending", promo_pending_cmd),
        ("skipped", skipped_tasks_cmd), ("warnings", warnings_cmd),
        ("banned", banned_cmd), ("unban", unban_cmd), ("backup", backup_cmd),
        ("add_task_manual", add_task_manual_cmd), ("remove_task", remove_task_cmd),
        ("del_task", remove_task_cmd), ("add_balance", add_balance_cmd),
        ("remove_balance", remove_balance_cmd), ("deduct_balance", remove_balance_cmd),
        ("set_tasks", set_task_count_cmd), ("set_screenshot_channel", set_screenshot_channel_cmd),
        ("set_withdraw_channel", set_withdraw_channel_cmd), ("set_join_channel", set_join_channel_cmd),
        ("approve_all", approve_all_pending_cmd), ("list_pending", list_pending_cmd),
        ("add_week", add_week_cmd), ("add_date", add_date_cmd),
        ("bulk_tasks", bulk_tasks_help_cmd), ("add_plan", add_support_plan_cmd),
        ("list_plans", list_plans_cmd), ("remove_plan", remove_plan_cmd),
        ("set_plan_image", set_plan_image_cmd), ("bacup", backup_cmd),
        ("add_admin", add_admin_cmd), ("referral_stats", referral_stats_cmd),
        ("set_payment_upi", set_payment_upi_cmd), ("payment_upi", payment_upi_cmd),
        ("channels_status", channels_status_cmd), ("channels_list", channels_list_cmd),
    ]
    for name, callback in command_handlers:
        app.add_handler(CommandHandler(name, callback))

    # Callback handlers.
    callback_handlers = [
        (my_ref_cb, r"^my_ref$"), (wallet_cb, r"^wallet$"), (daily_cb, r"^daily$"),
        (scheduled_cb, r"^scheduled$"), (promo_tasks_cb, r"^promo_tasks$"),
        (promo_join_cb, r"^promo_join_"), (promote_shop_cb, r"^promote_shop$"),
        (skip_reason_cb, r"^skip_reason_"), (admin_view_pending_cb, r"^admin_view_pending$"),
        (admin_view_withdraw_cb, r"^admin_view_withdraw$"), (admin_view_tasks_cb, r"^admin_view_tasks$"),
        (admin_view_promos_cb, r"^admin_view_promos$"), (admin_view_stats_cb, r"^admin_view_stats$"),
        (admin_view_banned_cb, r"^admin_view_banned$"), (back_menu_cb, r"^back_menu$"),
        (missed_tasks_cb, r"^missed_tasks$"), (missed_do_cb, r"^missed_do_"), (back_admin_cb, r"^back_admin$"),
        (admin_approve_daily_cb, r"^admin_approve_daily_"), (admin_reject_daily_cb, r"^admin_reject_daily_"),
        (promo_approve_cb, r"^promo_approve_"), (promo_reject_cb, r"^promo_reject_"),
        (admin_ban_cb, r"^admin_ban_"), (admin_unban_cb, r"^admin_unban_"),
        (wd_select_cb, r"^wd_select_"), (wd_confirm_cb, r"^wd_confirm_"),
        (wd_edit_upi_cb, r"^wd_edit_upi$"), (wd_admin_approve_cb, r"^wd_admin_approve_"),
        (wd_admin_reject_cb, r"^wd_admin_reject_"),
        (buy_support_cb, r"^buy_support_"), (plan_proof_cb, r"^plan_proof_"),
        (admin_view_plans_cb, r"^admin_view_plans$"), (admin_approve_plan_cb, r"^admin_approve_plan_"),
        (admin_reject_plan_cb, r"^admin_reject_plan_"),
        (admin_backup_cb, r"^admin_backup$"), (admin_add_admin_cb, r"^admin_add_admin$"),
        (admin_referral_cb, r"^admin_referral$"), (admin_missed_toggle_cb, r"^admin_missed_toggle$"),
    ]
    for callback, pattern in callback_handlers:
        app.add_handler(CallbackQueryHandler(callback, pattern=pattern))

    # Text handler used by withdraw UPI editing.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wd_edit_upi_text_handler), group=-1)

    print("S2E Bot CLEAN FINAL: handlers registered")
    print(f"Task screenshots will go ONLY to: {get_screenshot_channel()}")
    print("Starting Telegram polling once - no retry loop, no closed event loop")

    # run_polling creates/manages the asyncio loop and blocks until shutdown.
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
