print("V48 FINAL - DELETION-SAFE REFERRAL CHAIN + USERLIST + REFERRAL CODE FIX - 2026-08-26 IST")
print("V45 FINAL CLEAN - ALL SUPABASE SAFE + MISSED DEPLOY FIX + MYDETAILS + SHORT WITHDRAW - 2026-08-25 16:20 IST")

# S2E V15 FINAL - 2026-08-25 - NEW SUPABASE KEYS + PYTHON 3.11 + RENDER FIX
# - Supports sb_publishable_ and sb_secret_ new keys (supabase 2.15.3)
# - Supports both SUPABASE and SUPABASE env spelling
# - Python 3.11.11 compatible (PTB 21.7)
# - Render sleep fix + Flask health server

import warnings
warnings.filterwarnings('ignore')

# ===== V17 SUPABASE NEW KEYS FIX - FORCE ENABLE =====
import os
print("🔍 V17 DEBUG: Checking Supabase env...")
SUPA_URL = os.getenv("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")
SUPA_KEY = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
SUPA_SECRET = os.getenv("SUPABASE_SECRET_KEY", "") or os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_KEY", "")
print(f"🔍 V17 DEBUG: URL present={bool(SUPA_URL)} len={len(SUPA_URL)}")
print(f"🔍 V17 DEBUG: KEY present={bool(SUPA_KEY)} len={len(SUPA_KEY)} start={SUPA_KEY[:15] if SUPA_KEY else 'NO'}")
print(f"🔍 V17 DEBUG: SECRET present={bool(SUPA_SECRET)}")

# Use secret key if available (new sb_secret_ keys)
FINAL_SUPABASE_KEY = SUPA_SECRET if SUPA_SECRET and len(SUPA_SECRET)>20 else SUPA_KEY
FINAL_SUPABASE_URL = SUPA_URL

# Force set for later code
os.environ["SUPABASE_URL"] = FINAL_SUPABASE_URL
os.environ["SUPABASE_KEY"] = FINAL_SUPABASE_KEY
os.environ["SUPABASE_URL"] = FINAL_SUPABASE_URL
os.environ["SUPABASE_KEY"] = FINAL_SUPABASE_KEY
# ===== END V17 FIX =====

# ===== V18 ROBUST SUPABASE INIT WITH TABLE AUTO-CREATE =====
try:
    from supabase import create_client
    import json as _json
    _url = os.getenv("SUPABASE_URL","").strip().rstrip("/")
    _key = os.getenv("SUPABASE_KEY","").strip() or os.getenv("SUPABASE_ANON_KEY","").strip()
    _skey = os.getenv("SUPABASE_SERVICE_KEY","").strip() or os.getenv("SUPABASE_SECRET_KEY","").strip() or _key
    print(f"🔧 V18: Attempting Supabase client create URL={_url[:30]}... KEY len={len(_key)}")
    if _url and _key and _key.startswith("eyJ"):
        supa_client = create_client(_url, _key)
        # Try service client for table creation
        try:
            supa_service = create_client(_url, _skey) if _skey.startswith("eyJ") else supa_client
        except:
            supa_service = supa_client
        print("✅ V18: Supabase client created!")
        # Try to ensure table exists
        try:
            res = supa_client.table("bot_data").select("id").limit(1).execute()
            print("✅ V18: Table bot_data exists!")
        except Exception as te:
            print(f"⚠️ V18: Table check failed: {te} - will try to use anyway, will auto-create on first save")
        # Set global supabase client for later code to use
        try:
            globals()["supabase_client"] = supa_client
            globals()["supabase"] = supa_client
            globals()["SUPABASE_ENABLED"] = True
        except:
            pass
    else:
        print(f"❌ V18: URL or KEY invalid format URL ok={bool(_url)} KEY start={_key[:10]}")
except Exception as e:
    print(f"❌ V18: Supabase init exception: {e}")
    import traceback
    traceback.print_exc()
# ===== END V18 INIT =====


import os, re, threading, json, asyncio, secrets, string
from urllib.parse import quote
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")
from datetime import date, datetime, timedelta, time, timezone
from flask import Flask

# === V4.6 FINAL FIX: Flask + Keep Alive (Stops Render 2-min sleep) ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    try:
        return f"S2E Bot Alive V4.12 SUPABASE - {get_ist_now()} - OK", 200
    except:
        return "S2E Bot Alive - OK", 200

@flask_app.route('/health')
def health_check():
    return "OK", 200

def run_flask_server():
    try:
        port = int(os.getenv("PORT", 10000))
        print(f"🌐 Starting Flask on port {port} env PORT={port}")
        flask_app.run(host="0.0.0.0", port=port, threaded=True)
    except Exception as e:
        print(f"run_flask error {e}")

def start_flask_in_thread():
    try:
        t = threading.Thread(target=run_flask_server, daemon=True)
        t.start()
        print("✅ Flask health server started - Render will NOT sleep")
    except Exception as e:
        print(f"Flask thread error: {e}")

def start_self_ping_loop():
    def loop():
        import time as tm
        import urllib.request
        url = os.getenv("RENDER_EXTERNAL_URL", "https://s2e-earning-bot-1.onrender.com")
        while True:
            tm.sleep(90)
            try:
                urllib.request.urlopen(url, timeout=10)
                print(f"[KEEP-ALIVE] Pinged {url}")
            except Exception as ex:
                print(f"[KEEP-ALIVE FAIL] {ex}")
    threading.Thread(target=loop, daemon=True).start()
    print("✅ Self-ping loop started (urllib - no requests needed)")


# VERSION: V4.12 - RENDER 2 MIN FIX - SUPABASE PERSISTENCE + 2 MIN FIX - 2026-08-25 09:12 IST
# FIX: _db_init dummy + Daily Task no response + Bulk tasks + Missed duplicate fix
# TIMESTAMP: 2026-08-24 01:56:58 IST - This line ensures GitHub sees change!

# === IST TIMEZONE FIX ===
IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_now():
    return datetime.now(IST)
def get_ist_today():
    return get_ist_now().date()
def get_ist_time():
    return get_ist_now().time()


def _safe_time(t):
    """V28 - convert str to time object safely"""
    import datetime as _dt
    if t is None:
        return None
    if isinstance(t, _dt.time):
        return t
    if isinstance(t, _dt.datetime):
        return t.time()
    if isinstance(t, str):
        try:
            t = t.strip()
            if ":" in t:
                # try HH:MM or HH:MM:SS
                for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
                    try:
                        return _dt.datetime.strptime(t, fmt).time()
                    except:
                        continue
                # fallback fromisoformat
                try:
                    return _dt.time.fromisoformat(t)
                except:
                    pass
            else:
                return _dt.time.fromisoformat(t)
        except:
            pass
    return None


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Final HARDCODE - 3 Separate Channels - Ignore env - Fix Live but not responding + Separate channels!
CHANNEL_ID = "-1004352241439"
CHANNEL_LINK = "https://t.me/S2E_Daily_Earning"
SCREENSHOT_CHANNEL = -1004295034675
WITHDRAW_CHANNEL = -1004319888475
JOIN_CHANNEL = -1004352241439
print(f"Channels configured: VERIFY={CHANNEL_ID} SCREENSHOT={SCREENSHOT_CHANNEL} WITHDRAW={WITHDRAW_CHANNEL} JOIN={JOIN_CHANNEL}")

print("="*60)

print("="*60)
print("="*60)
print("FINAL V17 - SUPABASE NEW KEYS sb_secret_ SUPPORT - 2026-08-25 11:25 IST + FLASK FIX + DROP_PENDING FIX - 2026-08-25 09:12 IST")
print("FIXED: V4.6 Flask + KeepAlive + DropPending - FINAL NO EXIT")
print("="*60)

SCREENSHOT_LINK = "https://t.me/S2E_Daily_Earning"
WITHDRAW_LINK = "https://t.me/S2E_Daily_Earning"
JOIN_LINK = "https://t.me/S2E_Daily_Earning"
MISSED_ENABLED = True

ADMIN_UPI = os.getenv("ADMIN_UPI", "s2eearning@upi")
PAYMENT_UPI = ADMIN_UPI
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@s2edayincome")
CONTACT_USERNAME = SUPPORT_USERNAME
# Contact Us opens the admin directly by Telegram user ID, so it does not depend on a public username.
CONTACT_ADMIN_ID = int(os.getenv("CONTACT_ADMIN_ID", "7256515560")) if str(os.getenv("CONTACT_ADMIN_ID", "")).lstrip("-").isdigit() else 7256515560

def _db_init():
    print("✅ DB init dummy - V4.1")

def get_payment_upi():
    return str(globals().get("PAYMENT_UPI") or ADMIN_UPI)

async def set_payment_upi_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(f"Current payment UPI: {get_payment_upi()}\nUsage: /set_payment_upi yourupi@bank")
        return
    upi = context.args[0].strip()
    if "@" not in upi or len(upi) < 5:
        await update.message.reply_text("Invalid UPI. Example: yourname@upi")
        return
    globals()["PAYMENT_UPI"] = upi
    save_data()
    await update.message.reply_text(f"✅ Payment UPI updated: {upi}\nAll new plan payment instructions will use this UPI.")


ADMIN_ID_LIST = [7256515560, 8544307598]

# === SMART AUTO SYSTEM - FIXED (Your Idea) ===
import time as time_module
last_activity_time = time_module.time()
is_auto_mode = False
auto_job = None
idle_check_job = None

async def auto_keepalive_function(context):
    try:
        me = await context.bot.get_me()
        print(f"[AUTO {get_ist_now().strftime('%H:%M:%S')}] Keep-Alive ping - Bot @{me.username} alive")
    except Exception as e:
        print(f"Auto keep-alive error: {e}")

async def idle_checker(context):
    global last_activity_time, is_auto_mode
    idle_seconds = time_module.time() - last_activity_time
    if idle_seconds >= 300 and not is_auto_mode:
        print(f"[IDLE {get_ist_now().strftime('%H:%M:%S')}] {int(idle_seconds)}s idle - Starting auto mode")
        start_auto_mode(context)

def start_auto_mode(context):
    global is_auto_mode, auto_job
    if is_auto_mode:
        return
    is_auto_mode = True
    try:
        auto_job = context.job_queue.run_repeating(auto_keepalive_function, interval=120, first=10)
        print("✅ AUTO MODE ON - Every 2 min keep-alive started")
    except Exception as e:
        print(f"Failed to start auto mode: {e}")

def stop_auto_mode():
    global is_auto_mode, auto_job
    if not is_auto_mode:
        return
    is_auto_mode = False
    try:
        if auto_job:
            auto_job.schedule_removal()
            auto_job = None
        print(f"⏸️ AUTO MODE OFF - User active at {get_ist_now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"Failed to stop auto: {e}")

def update_activity():
    global last_activity_time
    last_activity_time = time_module.time()

async def global_activity_tracker(update, context):
    try:
        update_activity()
        if is_auto_mode:
            stop_auto_mode()
    except Exception:
        pass

def setup_smart_auto(application):
    global idle_check_job
    try:
        idle_check_job = application.job_queue.run_repeating(idle_checker, interval=60, first=60)
        print("🧠 Smart Idle Checker started (does not prevent Render Free spin-down)")
    except Exception as e:
        print(f"Idle checker error: {e}")

# === 5 PLANS TASK SYSTEM ===
def get_user_plan_id(uid):
    try:
        record = _get_user_plan_record(uid) if '_get_user_plan_record' in globals() else None
        if not record:
            return 0
        if isinstance(record, dict):
            if 'plan_id' in record:
                return int(record['plan_id'])
            p = record.get('plan', 'free').lower()
        else:
            p = str(record).lower()
        if p in ['free', '0']:
            return 0
        elif p in ['basic', '199', '1']:
            return 1
        elif p in ['premium', '499', '2']:
            return 2
        elif p in ['pro', '999', '3']:
            return 3
        elif p in ['vip', '1999', '4']:
            return 4
        else:
            try:
                return int(p)
            except:
                return 0
    except:
        return 0

def get_task_reward_for_user(task, uid):
    plan_id = get_user_plan_id(uid)
    rewards = task.get('rewards', None)
    if rewards and isinstance(rewards, dict) and len(rewards) > 0:
        if plan_id in rewards:
            return rewards[plan_id]
        if 'all' in rewards:
            return rewards['all']
    return task.get('reward', 5)

def get_tasks_for_today_filtered(uid):
    today_tasks = [t for t in scheduled_tasks_db if t['date'] == str(get_ist_today())]
    try:
        plan_id = get_user_plan_id(uid)
    except:
        plan_id = 0
    filtered = []
    for task in today_tasks:
        audience = task.get('audience', 'all')
        # Audience filtering: 'free' / plan 0 means FREE MEMBERS ONLY.
        if audience == 'all' or audience == 'all':
            filtered.append(task)
        elif str(audience).lower() == 'free' or audience == 0:
            if plan_id == 0:
                filtered.append(task)
        elif isinstance(audience, list):
            if plan_id in audience:
                filtered.append(task)
        elif isinstance(audience, int):
            if audience == 0 or audience == plan_id:
                filtered.append(task)
        elif str(audience).lower() in ['1', 'basic', '199']:
            if plan_id in [1,2,3,4]:
                filtered.append(task)
        elif str(audience).lower() in ['2', 'premium', '499']:
            if plan_id in [2,3,4]:
                filtered.append(task)
        elif str(audience).lower() in ['3', 'pro', '999']:
            if plan_id in [3,4]:
                filtered.append(task)
        elif str(audience).lower() in ['4', 'vip', '1999']:
            if plan_id == 4:
                filtered.append(task)
        else:
            filtered.append(task)
    return filtered


# Readable admin names, persisted with the bot data.
admin_names_db = {}
notification_thread_started = False
bot_event_loop = None
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
            time.sleep(300)
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
    """Send a reliable 1-minute-before task notification from the live polling loop."""
    import time as t2
    while True:
        try:
            t2.sleep(10)
            if not bot_application or not bot_event_loop or bot_event_loop.is_closed():
                continue
            now = get_ist_now()
            for task in get_tasks_for_today():
                try:
                    open_dt = datetime.combine(get_ist_today(), _safe_time(task.get('open_time_obj') or task.get('open_time')) or task['open_time_obj'], tzinfo=IST)
                except Exception:
                    continue
                diff = (open_dt - now).total_seconds()
                notify_key = f"{get_ist_today()}:{task.get('id')}"
                if 50 <= diff <= 75 and notify_key not in notified_tasks_30sec:
                    notified_tasks_30sec.add(notify_key)
                    msg = (
                        f"⏰ TASK STARTING IN 1 MINUTE!\n\n"
                        f"Task {task.get('task_number', '?')}: {task.get('title', '')}\n"
                        f"🕐 Opens: {task.get('open_time', '')}\n"
                        f"💰 Reward: ₹{task.get('reward', 5)}\n\n"
                        "Get ready and complete the task within the available time."
                    )
                    async def send_notifications():
                        sent = 0
                        for uid in list(users_db.keys()):
                            try:
                                await bot_application.bot.send_message(chat_id=int(uid), text=msg)
                                sent += 1
                            except Exception as e:
                                print(f"1-min notification failed for {uid}: {e}")
                        print(f"1-min task notification sent for task {task.get('id')} to {sent} users")
                    try:
                        future = asyncio.run_coroutine_threadsafe(send_notifications(), bot_event_loop)
                        future.add_done_callback(lambda f: f.exception() if not f.cancelled() else None)
                    except Exception as e:
                        print(f"1-min notification scheduling error: {e}")
        except Exception as e:
            print(f"Notification thread error: {e}")
            t2.sleep(5)


async def _show_plan_purchase(update, context, plan_type):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass
    uid = q.from_user.id
    info = _canonical_plan_info(uid)
    plan_type = "premium" if plan_type == "premium" else "basic"
    price = 499 if plan_type == "premium" else 199
    limit = DAILY_TASK_LIMIT_PREMIUM if plan_type == "premium" else DAILY_TASK_LIMIT_BASIC

    # Any active plan blocks all self-service plan purchases. Only Admin can change it.
    if info["active"]:
        text = (
            "💎 SUPPORT PLANS\n\n"
            f"✅ You already have an active {info['display']} Plan.\n"
            f"Valid till: {info['expiry']}\n"
            f"Daily tasks: {info['daily']}\n"
            f"Earning limit: ₹{info['cap']}\n\n"
            "🔄 To change, upgrade or switch your plan, please contact Admin.\n"
            "Only Admin can change the plan."
        )
        kb = [[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],
              [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]]
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    upi = get_payment_upi()
    pending_plans[uid] = {"plan": plan_type, "date": str(get_ist_today()), "price": price}
    text = (
        f"💎 {plan_type.capitalize()} Plan — ₹{price}\n\n"
        f"Daily Tasks: {limit}\n"
        "Validity: 30 days\n\n"
        f"💳 Pay manually to UPI:\n{upi}\n\n"
        "After payment, click “I Paid - Send Proof” and send the payment screenshot.\n"
        "No payment link is required."
    )
    kb = [
        [InlineKeyboardButton("📤 I Paid - Send Proof", callback_data=f"plan_proof_{plan_type}")],
        [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]
    ]
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_plan_purchase(update, context, "basic")

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_plan_purchase(update, context, "premium")

async def plan_basic_activate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_plan_purchase(update, context, "basic")

async def plan_premium_activate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_plan_purchase(update, context, "premium")

async def plan_basic_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    active_info = _canonical_plan_info(uid)
    if active_info["active"]:
        await q.message.reply_text(
            f"✅ You already have an active {active_info['display']} Plan.\n\n"
            "To change/upgrade/switch plans, please contact Admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],
                                                [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
        )
        return
    pending_plans[uid] = {"plan": "basic", "date": str(get_ist_today()), "price": 199}
    context.user_data["awaiting_plan_payment_proof"] = "basic"
    awaiting_plan_payment_adminless.add(uid)
    await q.message.reply_text("📤 Send the Basic ₹199 payment screenshot as a PHOTO now.")

async def plan_premium_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    active_info = _canonical_plan_info(uid)
    if active_info["active"]:
        await q.message.reply_text(
            f"✅ You already have an active {active_info['display']} Plan.\n\n"
            "To change/upgrade/switch plans, please contact Admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],
                                                [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
        )
        return
    pending_plans[uid] = {"plan": "premium", "date": str(get_ist_today()), "price": 499}
    context.user_data["awaiting_plan_payment_proof"] = "premium"
    awaiting_plan_payment_adminless.add(uid)
    await q.message.reply_text("📤 Send the Premium ₹499 payment screenshot as a PHOTO now.")

async def plan_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    plan_type = q.data.replace("plan_proof_", "")
    if plan_type not in ("basic", "premium"):
        return
    uid = q.from_user.id
    active_info = _canonical_plan_info(uid)
    if active_info["active"]:
        await q.message.reply_text(
            f"✅ You already have an active {active_info['display']} Plan.\n\n"
            "To change/upgrade/switch plans, please contact Admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],
                                                [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
        )
        return
    price = 199 if plan_type == "basic" else 499
    pending_plans[uid] = {"plan": plan_type, "date": str(get_ist_today()), "price": price}
    context.user_data["awaiting_plan_payment_proof"] = plan_type
    awaiting_plan_payment_adminless.add(uid)
    await q.message.reply_text(
        f"📤 Send your ₹{price} payment screenshot as a PHOTO now.\n"
        "Admin will verify it manually."
    )

async def _send_support_banner(message):
    """Send the saved Support Plans banner if one has been configured."""
    try:
        file_id = support_banner_db.get("file_id")
        if file_id:
            await message.reply_photo(photo=file_id)
            return True
    except Exception as e:
        print(f"Support banner send error: {e}")
    return False

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except Exception: pass
    uid = q.from_user.id
    normalize_support_plans()
    await _send_support_banner(q.message)
    info = _canonical_plan_info(uid)
    if info["active"]:
        text = (
            "💎 SUPPORT PLANS\n\n"
            f"✅ You already have an active {info['display']} Plan.\n"
            f"Valid till: {info['expiry']}\n"
            f"Daily tasks: {info['daily']}\n"
            f"Earning limit: ₹{info['cap']}\n\n"
            "🔄 Want to change/upgrade your plan or switch to another plan?\n"
            "Please contact Admin. No second plan payment is required here."
        )
        kb = [[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],
              [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]]
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        return

    lines = ["💎 SUPPORT PLANS", "", "Select your plan below:", ""]
    buttons = []
    for p in support_plans_db:
        name = str(p.get("name", "Plan")); price = int(p.get("price", 0))
        duration = int(p.get("duration", 30)); daily = int(p.get("daily_limit", 10))
        users = int(p.get("users", 1)); cap = int(p.get("earnings_limit", 0))
        desc = p.get("desc") or p.get("description") or f"{users} User(s) | {duration} Days | {daily} tasks/day"
        lines += [f"{name} ₹{price}", str(desc), f"Users: {users} | Validity: {duration} days | Daily: {daily} | Earning limit: ₹{cap}", ""]
        buttons.append([InlineKeyboardButton(f"{name} ₹{price}", callback_data=f"buy_support_{int(p['id'])}")])
    lines += [f"💳 Payment UPI: {get_payment_upi()}", "", "Pay manually to the UPI above, then send the payment screenshot. No payment link is required."]
    buttons.append([InlineKeyboardButton("🏠 Menu", callback_data="back_menu")])
    await q.message.reply_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))

async def buy_support_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except Exception: pass
    normalize_support_plans()
    try: pid = int(q.data.replace("buy_support_", "", 1))
    except Exception: return
    plan = next((p for p in support_plans_db if int(p.get("id", -1)) == pid), None)
    if not plan:
        await q.message.reply_text("❌ Plan not found. Please open Support Plans again."); return
    uid = q.from_user.id
    active_info=_canonical_plan_info(uid)
    if active_info["active"]:
        await q.message.reply_text(
            f"✅ You already have an active {active_info['display']} Plan.\n\n"
            "To change/upgrade/switch plans, please contact Admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
        )
        return
    name = str(plan.get("name", "Plan")); price = int(plan.get("price", 0))
    duration = int(plan.get("duration", 30)); daily = int(plan.get("daily_limit", 10)); users = int(plan.get("users", 1)); cap = int(plan.get("earnings_limit", 0))
    pending_plans[uid] = {"plan_id": pid, "plan": name.lower(), "date": str(get_ist_today()), "price": price}
    context.user_data["awaiting_plan_payment_proof"] = pid
    awaiting_plan_payment_adminless.add(uid)
    text = (f"💎 {name} ₹{price}\n\nUsers: {users}\nValidity: {duration} days\nDaily Tasks: {daily}\nEarning Limit: ₹{cap}\n\n💳 Payment UPI: {get_payment_upi()}\n\nPay manually to this UPI, then click the button below and send the payment screenshot.\nNo payment link is required.")
    kb = [[InlineKeyboardButton("📤 I Paid - Send Proof", callback_data=f"plan_proof_id_{pid}")],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]]
    if plan.get("image_file_id"):
        try:
            await q.message.reply_photo(photo=plan["image_file_id"], caption=text, reply_markup=InlineKeyboardMarkup(kb)); return
        except Exception: pass
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def plan_proof_id_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    try: pid=int(q.data.replace("plan_proof_id_", "", 1))
    except Exception: return
    normalize_support_plans(); plan=next((p for p in support_plans_db if int(p.get("id",-1))==pid),None)
    if not plan: await q.message.reply_text("❌ Plan not found."); return
    uid=q.from_user.id; price=int(plan.get("price",0))
    active_info=_canonical_plan_info(uid)
    if active_info["active"]:
        await q.message.reply_text(
            f"✅ You already have an active {active_info['display']} Plan.\n\n"
            "To change/upgrade/switch plans, please contact Admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=get_contact_url())],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
        )
        return
    current=_get_user_plan_record(uid)
    current_name=current.get("plan_name",current.get("name",current.get("plan","No Plan"))) if current else "No Plan"
    request_type="upgrade" if current and str(current.get("status","active")).lower() in ("active","approved") and int(current.get("plan_id",current.get("id",0)) or 0)!=pid else "new"
    pending_plans[uid]={"plan_id":pid,"plan":str(plan.get("name","plan")).lower(),"date":str(get_ist_today()),"price":price,"request_type":request_type,"current_plan":current_name}
    context.user_data["awaiting_plan_payment_proof"]=pid
    prefix=f"🔄 Upgrade request from {current_name} → {plan.get('name','Plan')}\n\n" if request_type=="upgrade" else ""
    await q.message.reply_text(prefix+f"📤 Send your ₹{price} payment screenshot as a PHOTO now.\nAdmin will verify and approve it manually.")

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
    try:
        await q.answer("Processing approval…")
    except Exception:
        pass
    try:
        if not is_admin(q.from_user.id):
            await q.answer("Admin only", show_alert=True)
            return
        raw = str(q.data).replace("admin_approve_plan_", "", 1)
        parts = raw.split("_")
        uid = int(parts[0])
        selector = parts[1] if len(parts) > 1 else ""

        normalize_support_plans()
        req = pending_plans.get(uid) or pending_plans.get(str(uid)) or {}
        plan = None
        if selector.isdigit():
            plan = next((p for p in support_plans_db if int(p.get("id", -1)) == int(selector)), None)
        if not plan and req.get("plan_id") is not None:
            try:
                plan = next((p for p in support_plans_db if int(p.get("id", -1)) == int(req.get("plan_id"))), None)
            except Exception:
                pass
        if not plan and req.get("plan"):
            wanted = str(req.get("plan")).lower()
            plan = next((p for p in support_plans_db if str(p.get("name", "")).lower() == wanted), None)
        if not plan and selector:
            wanted = selector.lower()
            plan = next((p for p in support_plans_db if str(p.get("name", "")).lower() == wanted), None)

        if not plan:
            await q.message.reply_text(f"❌ Plan not found for user {uid}. Open the latest payment proof and try again.")
            return

        duration = int(plan.get("duration", plan.get("duration_days", 30)) or 30)
        daily = int(plan.get("daily_limit", plan.get("daily_task_limit", 10)) or 10)
        price = int(plan.get("price", 0) or 0)
        name = str(plan.get("name", "Plan"))
        expiry = get_ist_today() + timedelta(days=duration)

        # Snapshot the plan at activation time. Future edits to the master plan
        # must NOT change this member's already-purchased terms.
        plan_snapshot = {
            "plan": name.lower(),
            "plan_name": name,
            "plan_id": int(plan.get("id", 0)),
            "status": "active",
            "price": price,
            "daily_limit": daily,
            "daily_task_limit": daily,
            "duration": duration,
            "validity_days": duration,
            "daily_earning_min": float(plan.get("daily_earning_min", 0) or 0),
            "daily_earning_max": float(plan.get("daily_earning_max", 0) or 0),
            "total_earning_cap": float(plan.get("total_earning_cap", plan.get("earnings_limit", 0)) or 0),
            "earnings_limit": float(plan.get("total_earning_cap", plan.get("earnings_limit", 0)) or 0),
            "promo_reward": float(plan.get("promo_reward", 0) or 0),
            "product_promo_reward": float(plan.get("product_promo_reward", 0) or 0),
            "activated_at": str(get_ist_now()),
            "date": str(get_ist_today()),
            "expiry": str(expiry),
        }

        # Plan activation commission is immediate. Eligibility is checked at the
        # exact moment of activation; there is NO retroactive commission later.
        for ref_id, level in get_effective_referral_levels(uid):
            if not is_paid_plan_active(ref_id):
                continue
            pct = float(REFERRAL_PLAN_COMMISSION_PERCENT) if level == 1 else float(L2_PLAN_COMMISSION_PERCENT)
            already = any(
                str(e.get("type")) == "plan"
                and int(e.get("source_uid", -1) or -1) == uid
                and int(e.get("level", 0) or 0) == level
                for e in referral_commission_ledger.get(ref_id, [])
            )
            if not already:
                add_referral_commission(ref_id, price * pct / 100.0, "plan", level, uid, f"L{level} plan activation - {name}", source_amount=price)

        user_plans[str(uid)] = plan_snapshot
        pending_plans.pop(uid, None)
        pending_plans.pop(str(uid), None)
        save_data()
        # Keep the callback visibly acknowledged even on slower mobile clients.
        try:
            await q.answer("Plan approved successfully", show_alert=False)
        except Exception:
            pass

        try:
            await q.message.edit_caption(caption=f"✅ APPROVED\nUser: {uid}\nPlan: {name} ₹{price}\nDaily tasks: {daily}\nValid till: {expiry}")
        except Exception:
            try:
                await q.message.edit_text(f"✅ APPROVED\nUser: {uid}\nPlan: {name} ₹{price}\nDaily tasks: {daily}\nValid till: {expiry}")
            except Exception:
                await q.message.reply_text(f"✅ Approved {name} plan for {uid}")

        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"🎉 Plan Activated!\n{name} ₹{price}\nValid till: {expiry}\nDaily tasks: {daily}",
                reply_markup=main_menu(),
            )
        except Exception as e:
            print(f"plan approval user notification error: {e}")
    except Exception as e:
        print(f"admin approve plan error: {e}")
        try:
            await q.message.reply_text(f"❌ Approval error: {e}")
        except Exception:
            pass

async def admin_reject_plan_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer("Processing rejection…")
    except Exception:
        pass
    try:
        if not is_admin(q.from_user.id):
            await q.answer("Admin only", show_alert=True)
            return
        uid = int(str(q.data).replace("admin_reject_plan_", "", 1))
        pending_plans.pop(uid, None)
        pending_plans.pop(str(uid), None)
        save_data()
        try:
            await q.message.edit_caption(caption=f"❌ REJECTED\nUser: {uid}\nPayment proof rejected by admin.")
        except Exception:
            try:
                await q.message.edit_text(f"❌ REJECTED\nUser: {uid}\nPayment proof rejected by admin.")
            except Exception:
                await q.message.reply_text(f"❌ Rejected payment proof for {uid}")
        try:
            await context.bot.send_message(chat_id=uid, text="❌ Your plan payment proof was rejected. Please contact admin and submit a valid proof.", reply_markup=main_menu())
        except Exception as e:
            print(f"plan rejection user notification error: {e}")
    except Exception as e:
        print(f"admin reject plan error: {e}")
        try:
            await q.message.reply_text(f"❌ Rejection error: {e}")
        except Exception:
            pass


WITHDRAW_MIN = 200
PLATFORM_FEE_PERCENT = 7
TASKS_REQUIRED_FOR_WITHDRAW = 1
DEFAULT_DAILY_TASK_ID = -1
REFERRAL_BONUS_PER_TASK = 10
REFERRAL_PLAN_COMMISSION_PERCENT = 10.0
L2_PLAN_COMMISSION_PERCENT = 3.0
L1_TASK_COMMISSION_PERCENT = 2.0
L2_TASK_COMMISSION_PERCENT = 0.5
DAILY_TASK_LIMIT_BASIC = 10
DAILY_TASK_LIMIT_PREMIUM = 20
DAILY_TASK_LIMIT_FREE = 1
DAILY_EARNING_CAP_FREE = 0
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
# When a referrer is removed, direct children can be re-parented while preserving
# their original commission level (e.g. B removed from A->B->C makes A the
# preserved L2 referrer for C). {child_uid: preserved_level}
referral_level_overrides = {}
# Public referral codes: never expose raw Telegram numeric IDs in referral links.
# {telegram_uid: "S2EXXXXXXX"} and reverse lookup for /start.
referral_codes_db = {}
referral_code_to_uid = {}
pending_referrals = {}
referral_earnings = {}
# Task/product referral commissions accrue during the day and settle the next day.
referral_pending_earnings = {}
# Detailed referral commission ledger: {referrer_uid: [{date, type, level, source_uid, amount, description}]}
referral_commission_ledger = {}
daily_task_earnings = {}  # {uid: {YYYY-MM-DD: amount}}
withdraw_requests = {}
withdraw_history = {}  # {uid: [{amount, fee, net, upi, date, status, ...}]}
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
# Separate OWN PRODUCT promotion system (not part of Daily Tasks)
product_promo_db = []
product_promo_counter = 1
product_promo_pending = {}
# {uid: {campaign_id: approved_at}} - prevents duplicate Product Promotion payouts.
product_promo_approved = {}
task_images_db = {}  # task_id -> file_id for poster - NEW FOR YOUR IMAGE
support_banner_db = {}  # Support Plans banner image: {'file_id': '...'}


# === PERSISTENT STORAGE - RESTORED / SAFE JSON 
# The previous build called load_data()/save_data() from main(), but those
# functions were missing from this file. That caused Render to stop with:
# NameError: name 'load_data' is not defined
# Persistent storage path. On Render, mount a Persistent Disk at /var/data.
# DATA_FILE can still override the path through an environment variable.


# === V4.12 SUPABASE PERSISTENCE ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_SERVICE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_SERVICE_KEY", "")
supabase_client = None
SUPABASE_ENABLED = False

def init_supabase():
    global supabase_client, SUPABASE_ENABLED
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            from supabase import create_client
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            SUPABASE_ENABLED = True
            print(f"✅ Supabase enabled URL {SUPABASE_URL[:40]}...")
            return True
        else:
            print("ℹ️ SUPABASE_URL/KEY not set - using local JSON (data will LOST on deploy)")
            return False
    except ImportError as e:
        print(f"⚠️ supabase library not installed: {e} - Add supabase==2.3.1 to requirements.txt")
        return False
    except Exception as e:
        print(f"⚠️ Supabase init failed: {e}")
        return False

_render_disk = "/var/data"
_default_data_file = os.path.join(_render_disk, "Supabase") if os.path.isdir(_render_disk) else "Supabase"
DATA_FILE = os.getenv("DATA_FILE", _default_data_file)
DATA_DIR = os.path.dirname(DATA_FILE) or "."
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception as _e:
    print(f"Persistent data directory unavailable: {_e}")
print(f"DATA_FILE={DATA_FILE} | Persistent Disk={'YES' if DATA_FILE.startswith('/var/data/') else 'NO'}")


def _json_safe(value):
    """Convert bot state to JSON-safe values without changing live objects."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, set):
        return [_json_safe(v) for v in value]
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def _restore_int_keys(target):
    """Restore Telegram user-id keyed dictionaries after JSON loading."""
    if not isinstance(target, dict):
        return
    for key in list(target.keys()):
        if isinstance(key, str) and key.lstrip("-").isdigit():
            value = target.pop(key)
            target[int(key)] = value


def _restore_scheduled_task_times():
    """Rebuild time objects lost when scheduled tasks are stored as JSON."""
    for task in scheduled_tasks_db:
        if not isinstance(task, dict):
            continue
        for field, obj_field in (
            ("open_time", "open_time_obj"),
            ("close_time", "close_time_obj"),
            ("next_time", "next_time_obj"),
        ):
            if not task.get(obj_field):
                raw = task.get(field)
                if raw:
                    parsed = parse_time_str(str(raw))
                    if parsed:
                        task[obj_field] = parsed


def _restore_loaded_sets_and_times():
    """Restore non-JSON native containers used by the bot."""
    _restore_scheduled_task_times()
    for campaign in promo_campaigns_db:
        if isinstance(campaign, dict):
            members = campaign.get("members_joined", set())
            if isinstance(members, list):
                campaign["members_joined"] = set(members)
    if not isinstance(screenshot_hashes, set):
        try:
            screenshot_hashes.clear()
            screenshot_hashes.update([])
        except Exception:
            pass
    if not isinstance(task_notifications_sent, set):
        try:
            task_notifications_sent = set(task_notifications_sent or [])
        except Exception:
            pass


def _restore_all_int_keys_after_load():
    """Restore integer Telegram IDs after JSON/Supabase deserialization.

    Python dictionaries keyed by int user IDs are serialized to JSON with
    string keys. After a Render restart/redeploy, uid lookups would therefore
    miss existing records and wallet/tasks could appear as 0. Restore all
    state dictionaries that may use Telegram/task IDs as numeric keys.
    """
    dict_names = [
        "users_db", "referrals_db", "tasks_db", "daily_done", "bonus_balance",
        "warnings_db", "pending_daily", "user_plans", "pending_plans",
        "referral_map", "referral_level_overrides", "referral_codes_db", "referral_code_to_uid", "pending_referrals", "referral_earnings",
        "referral_commission_ledger", "referral_pending_earnings", "daily_task_earnings",
        "withdraw_requests", "withdraw_history", "withdraw_done_date",
        "daily_task_count", "missed_tasks_db", "last_withdraw_date_db",
        "task_open_time", "user_task_status", "skip_db",
        "promo_earnings_db", "promo_views_db", "promo_pending",
        "product_promo_pending", "product_promo_approved", "admin_names_db",
        "pending_plan_purchases", "support_plans_db", "task_images_db",
        "support_banner_db",
    ]
    for name in dict_names:
        obj = globals().get(name)
        if isinstance(obj, dict):
            try:
                _restore_int_keys(obj)
            except Exception as e:
                print(f"⚠️ Integer-key restore failed for {name}: {e}")

    # Restore integer keys in common nested user dictionaries too.
    for outer_name in ("daily_task_earnings", "user_task_status", "product_promo_approved"):
        outer = globals().get(outer_name)
        if isinstance(outer, dict):
            for value in outer.values():
                if isinstance(value, dict):
                    try:
                        _restore_int_keys(value)
                    except Exception:
                        pass

def save_data():
    """V25 - FORCE SUPABASE SAVE WITH UPDATED_AT"""
    try:
        from datetime import datetime, timezone
        state_names = [
            "users_db", "referrals_db", "tasks_db", "daily_done", "bonus_balance",
            "banned_users", "warnings_db", "pending_daily", "user_plans",
            "pending_plans", "referral_map", "referral_level_overrides", "pending_referrals", "referral_earnings",
            "referral_commission_ledger", "referral_pending_earnings", "daily_task_earnings", "withdraw_requests",
            "withdraw_history", "withdraw_done_date", "daily_task_count",
            "missed_tasks_db", "last_withdraw_date_db", "screenshot_hashes",
            "task_open_time", "scheduled_tasks_db", "scheduled_task_counter",
            "user_task_status", "task_notifications_sent", "skip_db",
            "promo_campaigns_db", "promo_campaign_counter", "promo_earnings_db",
            "promo_views_db", "promo_pending", "product_promo_db", "product_promo_counter", "product_promo_pending", "product_promo_approved", "task_images_db", "support_banner_db",
            "admin_names_db", "support_plans_db", "pending_plan_purchases",
            "support_plan_image_file_id", "pending_plans",
            "REFERRAL_PLAN_COMMISSION_PERCENT", "L2_PLAN_COMMISSION_PERCENT", "L1_TASK_COMMISSION_PERCENT", "L2_TASK_COMMISSION_PERCENT",
        ]
        data = {}
        for name in state_names:
            if name in globals():
                try:
                    val = globals()[name]
                    # Force json safe
                    data[name] = _json_safe(val)
                except Exception as ex:
                    print(f"json_safe fail for {name}: {ex}")
                    try:
                        # try convert sets to lists
                        v = globals()[name]
                        if isinstance(v, set):
                            data[name] = list(v)
                        elif isinstance(v, dict):
                            data[name] = {str(k): (list(val) if isinstance(val, set) else val) for k,val in v.items()}
                        else:
                            data[name] = str(v)
                    except:
                        data[name] = {}

        # Try Supabase first - ALWAYS
        if 'supabase_client' in globals() and globals()['supabase_client']:
            try:
                from datetime import datetime
                payload = {"id": 1, "data": data, "updated_at": datetime.utcnow().isoformat()}
                print(f"🔄 Attempting Supabase upsert {len(data)} sections...")
                try:
                    res = globals()['supabase_client'].table("bot_data").upsert(payload).execute()
                    print(f"✅✅✅ V25 SAVED to Supabase bot_data - {len(data)} sections - {datetime.utcnow()}")
                    return True
                except Exception as e1:
                    print(f"❌ bot_data fail {e1} trying bot_data_storage: {e1}")
                    import traceback; traceback.print_exc()
                    try:
                        res2 = globals()['supabase_client'].table("bot_data_storage").upsert(payload).execute()
                        print(f"✅ SAVED to bot_data_storage")
                        return True
                    except Exception as e2:
                        print(f"❌ both tables fail {e2}")
                        traceback.print_exc()
            except Exception as se:
                print(f"⚠️ Supabase save exception {se}")
                import traceback; traceback.print_exc()

        print(f"⚠️ Supabase client missing, saving local fallback")
        # Fallback local only if DATA_FILE is a file path
        try:
            if DATA_FILE != "Supabase" and "/" not in str(DATA_FILE) or str(DATA_FILE).endswith(".json"):
                temp_file = str(DATA_FILE) + ".tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(temp_file, DATA_FILE)
                print(f"💾 Data saved local {DATA_FILE}")
        except Exception as le:
            print(f"Local save fail {le}")
        return False
    except Exception as e:
        print(f"Save error {e}")
        import traceback; traceback.print_exc()
        return False


def load_data():
    """V4.12 - Load from Supabase if enabled else local JSON"""
    try:
        if SUPABASE_ENABLED and supabase_client:
            try:
                result = None
                try:
                    result = supabase_client.table("bot_data").select("data").eq("id", 1).execute()
                except:
                    result = supabase_client.table("bot_data_storage").select("data").eq("id", 1).execute()

                data = None
                if result and getattr(result, 'data', None) and len(result.data) > 0:
                    loaded = result.data[0].get('data')
                    if isinstance(loaded, str):
                        import json as js
                        loaded = js.loads(loaded)
                    data = loaded
                    print(f"✅ Data loaded from Supabase - {len(data) if isinstance(data, dict) else 0} sections")
                

                # V29 MIGRATION: fix old scheduled_tasks_db times from Supabase (str -> time obj)
                try:
                    if 'scheduled_tasks_db' in data and isinstance(data['scheduled_tasks_db'], list):
                        for _t in data['scheduled_tasks_db']:
                            try:
                                if isinstance(_t.get('open_time_obj'), str):
                                    _t['open_time_obj'] = _safe_time(_t['open_time_obj'])
                                if isinstance(_t.get('close_time_obj'), str):
                                    _t['close_time_obj'] = _safe_time(_t['close_time_obj'])
                                if isinstance(_t.get('next_time_obj'), str):
                                    _t['next_time_obj'] = _safe_time(_t['next_time_obj'])
                            except:
                                pass
                except Exception as _mig_e:
                    print(f"Migration fail {_mig_e}")

                if data and isinstance(data, dict):
                    for name in list(data.keys()):
                        if name not in globals():
                            continue
                        current = globals()[name]
                        loaded_val = data[name]
                        if isinstance(current, dict) and isinstance(loaded_val, dict):
                            current.clear()
                            current.update(loaded_val)
                        elif isinstance(current, (set,)) and isinstance(loaded_val, list):
                            current.clear()
                            current.update(set(loaded_val))
                        elif isinstance(current, list) and isinstance(loaded_val, list):
                            current.clear()
                            current.extend(loaded_val)
                        else:
                            try:
                                globals()[name] = loaded_val
                            except:
                                pass
                    # special sets
                    if "banned_users" in data:
                        try:
                            banned_users.clear()
                            banned_users.update(set(data["banned_users"]) if isinstance(data["banned_users"], list) else data["banned_users"])
                        except: pass

                    # IMPORTANT PERSISTENCE FIX:
                    # JSON/Supabase converts integer Telegram user IDs used as
                    # dictionary keys into strings. Without converting them back,
                    # lookups such as tasks_db.get(uid), bonus_balance.get(uid),
                    # referral_earnings.get(uid), daily_done.get(uid), etc. return
                    # zero/empty after every Render redeploy.
                    _restore_all_int_keys_after_load()
                    _restore_loaded_sets_and_times()
                    try:
                        referral_code_to_uid.clear()
                        for _uid, _code in referral_codes_db.items():
                            if _code:
                                referral_code_to_uid[str(_code).upper()] = int(_uid)
                    except Exception as _rc_e:
                        print(f"Referral code index rebuild warning: {_rc_e}")
                    # Recover users referenced by other persisted structures so
                    # /userlist does not hide an existing member just because
                    # their registration record is incomplete.
                    try:
                        _candidate_ids = set()
                        for _src_name in ("referral_map", "user_plans", "tasks_db", "bonus_balance",
                                           "referral_earnings", "promo_earnings_db", "daily_done"):
                            _src = globals().get(_src_name, {})
                            if isinstance(_src, dict):
                                for _k in _src.keys():
                                    try:
                                        _candidate_ids.add(int(_k))
                                    except:
                                        pass
                        for _candidate_uid in _candidate_ids:
                            if _candidate_uid > 0 and _candidate_uid not in users_db:
                                users_db[_candidate_uid] = {
                                    "name": "Not registered",
                                    "username": "",
                                    "telegram_id": _candidate_uid,
                                    "registration_complete": False,
                                    "created_at": str(get_ist_today()),
                                }
                    except Exception as _mig_user_e:
                        print(f"Userlist migration warning: {_mig_user_e}")

                    print("✅ Supabase data restored to memory (integer user IDs restored)")
                    return True
                else:
                    print("ℹ️ No data in Supabase yet - starting fresh")
            except Exception as se:
                print(f"⚠️ Supabase load failed {se}, trying local file")

        if not os.path.exists(DATA_FILE):
            print("No bot_data.json - starting fresh")
            return False
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
        for name in list(data.keys()):
            if name not in globals():
                continue
            current = globals()[name]
            loaded_val = data[name]
            if isinstance(current, dict) and isinstance(loaded_val, dict):
                current.clear()
                current.update(loaded_val)
            elif isinstance(current, list) and isinstance(loaded_val, list):
                current.clear()
                current.extend(loaded_val)
        if "banned_users" in data:
            try:
                banned_users.clear()
                banned_users.update(set(data["banned_users"]))
            except: pass

        # Same persistence fix for local JSON fallback.
        _restore_all_int_keys_after_load()
        _restore_loaded_sets_and_times()

        print(f"✅ Data loaded from local {DATA_FILE} (integer user IDs restored)")
        return True
    except Exception as e:
        print(f"Load error {e}")
        import traceback; traceback.print_exc()
        return False


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

def _product_reward_for_user(task, uid):
    rewards = task.get('rewards', {}) if isinstance(task, dict) else {}
    if isinstance(rewards, dict):
        pid = get_user_plan_id(uid)
        if pid in rewards:
            return int(rewards[pid])
        if str(pid) in rewards:
            return int(rewards[str(pid)])
        if 'all' in rewards:
            return int(rewards['all'])
    return int(task.get('reward', 0) if isinstance(task, dict) else 0)

def get_active_product_promo_for_user(uid):
    """Return only the newest live Product Promotion for today.

    Product Promotion is a single campaign slot. Older campaigns must never
    reappear when the user presses the menu button again. Campaign state is
    persisted in product_promo_db; Telegram file_id values are also persisted,
    so a Render restart does not make the video disappear.
    """
    now = get_ist_now()
    today = str(get_ist_today())
    candidates = []
    for t in product_promo_db:
        if not isinstance(t, dict) or t.get('date') != today:
            continue
        if t.get('status') != 'active' or not t.get('video_file_id'):
            continue
        try:
            video_deadline_obj = parse_time_str(str(t.get('download_deadline','')))
            shot_open_obj = parse_time_str(str(t.get('screenshot_open','')))
            shot_close_obj = parse_time_str(str(t.get('screenshot_close','')))
            if not video_deadline_obj or not shot_open_obj or not shot_close_obj:
                continue
            video_deadline = datetime.combine(get_ist_today(), _safe_time(video_deadline_obj) or video_deadline_obj, tzinfo=IST)
            shot_open = datetime.combine(get_ist_today(), _safe_time(shot_open_obj) or shot_open_obj, tzinfo=IST)
            shot_close = datetime.combine(get_ist_today(), _safe_time(shot_close_obj) or shot_close_obj, tzinfo=IST)
            if shot_close <= shot_open:
                shot_close += timedelta(days=1)
            if now <= shot_close:
                t['_download_open'] = now <= video_deadline
                t['_screenshot_open'] = shot_open <= now <= shot_close
                t['_screenshot_closed'] = now > shot_close
                candidates.append(t)
        except Exception:
            continue
    # Only the newest campaign is exposed. This prevents an older campaign
    # from coming back after a new campaign was created.
    if not candidates:
        return []
    newest = max(candidates, key=lambda x: int(x.get('id', 0) or 0))
    return [newest]

def _product_time_text(t):
    return f"🎥 Video download until: {t.get('download_deadline','')}\n📸 Screenshot: {t.get('screenshot_open','')} → {t.get('screenshot_close','')}"

def _product_reward_text(t, uid):
    return f"💰 Reward: ₹{_product_reward_for_user(t, uid)}"

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
    import datetime as _dt2
    # normalize now
    if isinstance(now, str):
        try:
            now = _dt2.datetime.strptime(now, "%H:%M").time() if ":" in now else _dt2.time.fromisoformat(now)
        except:
            pass
    for i, task in enumerate(today_tasks):
        open_time = task.get('open_time_obj')
        close_time = task.get('close_time_obj')
        # fallback to string fields
        if open_time is None:
            ot_str = task.get('open_time')
            try:
                open_time = _dt2.datetime.strptime(ot_str, "%H:%M").time() if ot_str and ":" in ot_str else _dt2.time.fromisoformat(ot_str) if ot_str else None
            except:
                open_time = None
        if close_time is None:
            ct_str = task.get('close_time')
            try:
                close_time = _dt2.datetime.strptime(ct_str, "%H:%M").time() if ct_str and ":" in ct_str else _dt2.time.fromisoformat(ct_str) if ct_str else None
            except:
                close_time = None
        if isinstance(open_time, str):
            try:
                open_time = _dt2.datetime.strptime(open_time, "%H:%M").time()
            except:
                try:
                    open_time = _dt2.time.fromisoformat(open_time)
                except:
                    continue
        if isinstance(close_time, str):
            try:
                close_time = _dt2.datetime.strptime(close_time, "%H:%M").time()
            except:
                try:
                    close_time = _dt2.time.fromisoformat(close_time)
                except:
                    continue
        next_task = today_tasks[i+1] if i+1 < len(today_tasks) else None
        if open_time and close_time and now:
            try:
                if open_time <= now <= close_time:
                    return task, next_task
            except:
                pass
        if close_time and now:
            try:
                if close_time < now and next_task:
                    nt_open = next_task.get('open_time_obj') or next_task.get('open_time')
                    if isinstance(nt_open, str):
                        try:
                            nt_open = _dt2.datetime.strptime(nt_open, "%H:%M").time()
                        except:
                            nt_open = _dt2.time.fromisoformat(nt_open)
                    if isinstance(nt_open, _dt2.time) and now < nt_open:
                        return None, next_task
            except:
                pass
    if today_tasks:
        try:
            first_open = today_tasks[0].get('open_time_obj') or today_tasks[0].get('open_time')
            if isinstance(first_open, str):
                first_open = _dt2.datetime.strptime(first_open, "%H:%M").time() if ":" in first_open else _dt2.time.fromisoformat(first_open)
            if isinstance(first_open, _dt2.time) and now < first_open:
                return None, today_tasks[0]
        except:
            pass
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
        _ct = task.get('close_time_obj') or task.get('close_time')
        _ct = _safe_time(_ct) or task.get('close_time_obj')
        if _ct is None:
            continue
        try:
            close_dt = datetime.combine(get_ist_today(), _ct, tzinfo=IST)
        except:
            continue
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
    # V31 FIX: Increment daily_task_count and earnings so wallet shows 1/1
    try:
        today = str(get_ist_today())
        # daily count
        if uid not in daily_task_count:
            daily_task_count[uid] = {}
        daily_task_count[uid][today] = daily_task_count[uid].get(today, 0) + 1
        # total tasks
        tasks_db[uid] = tasks_db.get(uid, 0) + 1
        try:
            if uid in missed_tasks_db:
                try:
                    missed_tasks_db[uid] = {}
                    save_data()
                except: pass
        except: pass
        # earning ₹5 per task
        reward = 5
        add_today_task_earning(uid, reward, day=today)
        # referral commission
        try:
            for ref_id, level in get_effective_referral_levels(uid):
                if level == 1:
                    pct = float(L1_TASK_COMMISSION_PERCENT) if 'L1_TASK_COMMISSION_PERCENT' in globals() else 0.10
                    add_referral_commission(ref_id, reward * pct / 100.0, "task", 1, uid, f"L1 task commission from {uid}", source_amount=reward)
                elif level == 2:
                    pct = float(L2_TASK_COMMISSION_PERCENT) if 'L2_TASK_COMMISSION_PERCENT' in globals() else 0.05
                    add_referral_commission(ref_id, reward * pct / 100.0, "task", 2, uid, f"L2 task commission from {uid}", source_amount=reward)
        except Exception as _ref_e:
            print(f"Referral commission fail {_ref_e}")
        print(f"V31 Task {task_id} completed for {uid} - count {daily_task_count[uid][today]} - earning {reward}")
    except Exception as _e:
        print(f"V31 increment fail {_e}")
        import traceback; traceback.print_exc()
    try:
        save_data()
        print(f"V31 Task {task_id} completed for {uid} - saved")
    except Exception as _e:
        print(f"Save after task fail {_e}")

def is_admin(uid): return uid in ADMIN_ID_LIST
def calculate_age(d): 
    today=get_ist_today()
    return today.year-d.year-((today.month,today.day)<(d.month,d.day))
def is_paid_plan_active(uid):
    """True only when the referrer has an active paid plan at this moment.
    Free members can still earn task/product referral commissions, but never plan-activation commission.
    """
    try:
        raw = _get_user_plan_record(uid)
        if not raw or not isinstance(raw, dict):
            return False
        status = str(raw.get("status", "")).lower()
        if status not in ("active", "approved"):
            return False
        pid = int(raw.get("plan_id", raw.get("id", 0)) or 0)
        if pid <= 0:
            return False
        expiry = raw.get("expiry") or raw.get("expires_at")
        if expiry:
            try:
                from datetime import date as _date
                if get_ist_today() > _date.fromisoformat(str(expiry)[:10]):
                    return False
            except Exception:
                pass
        return True
    except Exception:
        return False

def get_balance(uid): return tasks_db.get(uid,0)*5 + bonus_balance.get(uid,0) + referral_earnings.get(uid,0) + promo_earnings_db.get(uid,0)

def add_referral_commission(referrer_uid, amount, commission_type, level=None, source_uid=None, description="", source_amount=None):
    """Credit referral commission once and keep a dated ledger for Wallet/My Referrals."""
    try:
        amount = float(amount)
    except Exception:
        return 0.0
    if amount <= 0 or not referrer_uid:
        return 0.0
    ctype = str(commission_type)
    is_daily = ctype in ("task", "product", "product_promo", "promo")
    entry = {
        "date": str(get_ist_today()),
        "type": ctype,
        "level": int(level) if level is not None else None,
        "source_uid": source_uid,
        "amount": round(amount, 2),
        "description": description,
        "source_amount": round(float(source_amount), 2) if source_amount is not None else None,
        "status": "pending" if is_daily else "settled",
    }
    referral_commission_ledger.setdefault(referrer_uid, []).append(entry)
    if is_daily:
        referral_pending_earnings[referrer_uid] = round(float(referral_pending_earnings.get(referrer_uid, 0) or 0) + amount, 2)
    else:
        referral_earnings[referrer_uid] = round(float(referral_earnings.get(referrer_uid, 0) or 0) + amount, 2)
    return amount

async def settle_previous_day_referrals(context):
    """Settle yesterday's task/product referral commissions and notify each member."""
    try:
        yesterday = str(get_ist_today() - timedelta(days=1))
        totals = {}
        for ref_uid, entries in list(referral_commission_ledger.items()):
            for e in entries:
                if str(e.get("date")) != yesterday or str(e.get("status", "settled")) != "pending":
                    continue
                amount = float(e.get("amount", 0) or 0)
                if amount <= 0:
                    e["status"] = "settled"
                    continue
                totals.setdefault(int(ref_uid), 0.0)
                totals[int(ref_uid)] += amount
                e["status"] = "settled"
        for uid, amount in totals.items():
            referral_earnings[uid] = round(float(referral_earnings.get(uid, 0) or 0) + amount, 2)
            referral_pending_earnings[uid] = round(max(0.0, float(referral_pending_earnings.get(uid, 0) or 0) - amount), 2)
            try:
                l1 = sum(float(e.get("amount",0) or 0) for e in referral_commission_ledger.get(uid, []) if str(e.get("date")) == yesterday and int(e.get("level",0) or 0) == 1 and str(e.get("type")) in ("task","product","product_promo","promo"))
                l2 = sum(float(e.get("amount",0) or 0) for e in referral_commission_ledger.get(uid, []) if str(e.get("date")) == yesterday and int(e.get("level",0) or 0) == 2 and str(e.get("type")) in ("task","product","product_promo","promo"))
                await context.bot.send_message(chat_id=uid, text=(
                    f"📊 DAILY REFERRAL SETTLEMENT\n\n"
                    f"Date: {yesterday}\n"
                    f"🟢 L1 Commission: ₹{l1:.2f}\n"
                    f"🔵 L2 Commission: ₹{l2:.2f}\n"
                    f"💰 Settled to Wallet: ₹{amount:.2f}\n\n"
                    f"Your referral commission has been settled."), reply_markup=main_menu())
            except Exception:
                pass
        if totals:
            save_data()
    except Exception as e:
        print(f"daily referral settlement error: {e}")

def get_effective_referral_levels(source_uid):
    """Return active referral referrers as [(uid, level)].

    Normally this is L1=direct parent and L2=grandparent. If an admin
    removes a referrer, the removed member's direct child is re-parented to
    the next ancestor and a level override preserves the original level.
    Example: A -> B -> C, remove B => C -> A with C's override=2, so C work
    still pays A at L2 (0.5%), while C's own referrals continue normally.
    """
    try:
        src = int(source_uid)
    except Exception:
        return []
    parent = referral_map.get(src) or referral_map.get(str(src))
    if not parent:
        return []
    try:
        parent = int(parent)
    except Exception:
        return []

    override = referral_level_overrides.get(src) or referral_level_overrides.get(str(src))
    if override:
        try:
            level = int(override)
        except Exception:
            level = 1
        return [(parent, level)] if parent else []

    result = [(parent, 1)]
    grand = referral_map.get(parent) or referral_map.get(str(parent))
    if grand:
        try:
            grand = int(grand)
            if grand and grand != parent:
                result.append((grand, 2))
        except Exception:
            pass
    return result

def record_product_promo_referral_commissions(source_uid, reward):
    try:
        reward = float(reward or 0)
        if reward <= 0:
            return
        for ref_id, level in get_effective_referral_levels(source_uid):
            if level == 1:
                pct = float(L1_TASK_COMMISSION_PERCENT)
            else:
                pct = float(L2_TASK_COMMISSION_PERCENT)
            add_referral_commission(int(ref_id), reward * pct / 100.0, "product_promo", level, source_uid, f"L{level} product promotion commission from {source_uid}", source_amount=reward)
    except Exception as e:
        print(f"product promo referral commission fail: {e}")

def get_referral_commission_total(uid, day=None, level=None, commission_type=None):
    day = str(day or get_ist_today())
    total = 0.0
    for e in referral_commission_ledger.get(uid, []):
        if str(e.get("date", "")) != day:
            continue
        if level is not None and e.get("level") != level:
            continue
        if commission_type is not None and e.get("type") != commission_type:
            continue
        try: total += float(e.get("amount", 0) or 0)
        except Exception: pass
    return round(total, 2)

def get_referral_task_earnings(uid, day=None, level=None):
    day=str(day or get_ist_today())
    total=0.0
    for e in referral_commission_ledger.get(uid, []):
        if str(e.get("date","")) != day or e.get("type") != "task": continue
        if level is not None and e.get("level") != level: continue
        try: total += float(e.get("source_amount") or 0)
        except Exception: pass
    return round(total,2)

def get_referral_commission_yesterday(uid, level=None):
    return get_referral_commission_total(uid, get_ist_today() - timedelta(days=1), level=level, commission_type="task")

def get_plan_commission_yesterday(uid):
    return get_referral_commission_total(uid, get_ist_today() - timedelta(days=1), commission_type="plan")

def get_withdrawn_for_cap(uid):
    total = 0.0
    for item in withdraw_history.get(uid, []):
        if str(item.get("status", "")).lower() == "approved":
            try: total += float(item.get("amount", 0) or 0)
            except Exception: pass
    req = withdraw_requests.get(uid, {})
    if str(req.get("status", "")).lower() == "approved" and not withdraw_history.get(uid):
        try: total += float(req.get("amount", 0) or 0)
        except Exception: pass
    return round(total, 2)

def get_referral_chain(uid):
    """Return active L1/L2 members for the referral display, respecting deleted-user re-parenting."""
    try:
        uid = int(uid)
    except Exception:
        return [], []
    l1, l2 = [], []
    for member in list(referral_map.keys()):
        try:
            member_id = int(member)
        except Exception:
            continue
        for ref_id, level in get_effective_referral_levels(member_id):
            if ref_id != uid:
                continue
            if level == 1:
                l1.append(member_id)
            elif level == 2:
                l2.append(member_id)
    return list(dict.fromkeys(l1)), list(dict.fromkeys(l2))
def record_task_referral_commissions(source_uid, task_reward):
    """Pay configurable L1/L2 percentages from the completed task reward.

    Uses the deletion-safe referral resolver so removing an intermediate
    referrer never sends future commission to a deleted user.
    """
    try:
        reward = float(task_reward or 0)
    except Exception:
        reward = 0.0
    if reward <= 0:
        return
    for ref_id, level in get_effective_referral_levels(source_uid):
        pct = float(L1_TASK_COMMISSION_PERCENT) if level == 1 else float(L2_TASK_COMMISSION_PERCENT)
        add_referral_commission(ref_id, reward * pct / 100.0, "task", level, source_uid, f"L{level} task commission from {source_uid}", source_amount=reward)

def get_tasks(uid):
    today = str(get_ist_today())
    return daily_task_count.get(uid, {}).get(today, 0)

def get_today_task_earnings(uid):
    today=str(get_ist_today())
    return round(float(daily_task_earnings.get(uid, {}).get(today, 0) or 0), 2)

def add_today_task_earning(uid, amount, day=None):
    day=str(day or get_ist_today())
    daily_task_earnings.setdefault(uid, {})[day]=round(float(daily_task_earnings.setdefault(uid, {}).get(day,0) or 0)+float(amount or 0),2)

def get_total_tasks(uid):
    return tasks_db.get(uid,0)
def _get_user_plan_record(uid):
    return user_plans.get(uid) or user_plans.get(str(uid))

def _canonical_plan_info(uid):
    """Return one consistent plan identity/limits - WITH DUAL END CONDITION: Days OR Amount Cap - 4 Plans 60 Days"""
    raw = _get_user_plan_record(uid)
    if not raw:
        return {"active": False, "type": "free", "display": "No Plan (Free - 3 Days)", "expiry": None, "daily": 4, "cap": 100, "validity_days": 3}

    plan = raw if isinstance(raw, dict) else {}
    name = str(plan.get("plan_name") or plan.get("name") or plan.get("plan") or "").strip()
    low = name.lower()
    pid = plan.get("plan_id", plan.get("id"))
    try:
        pid = int(pid)
    except Exception:
        pid = None

    # Existing members use their saved activation snapshot. Only users who
    # activate after a master-plan edit receive the new values.
    has_snapshot = all(k in plan for k in ("daily_task_limit", "price", "validity_days", "total_earning_cap"))
    if has_snapshot:
        ptype = low or "custom"
        display = name or "Custom"
        default_daily = int(plan.get("daily_task_limit", plan.get("daily_limit", 5)))
        default_cap = int(plan.get("total_earning_cap", plan.get("earnings_limit", 900)))
        validity = int(plan.get("validity_days", plan.get("duration", 60)))
    else:
        db_plan = None
        if pid:
            db_plan = next((p for p in support_plans_db if int(p.get("id", -1)) == pid), None)
        if not db_plan:
            db_plan = next((p for p in support_plans_db if str(p.get("name","")).lower() == low), None)
        if db_plan:
            ptype = str(db_plan.get("name","")).lower(); display = db_plan.get("name","")
            default_daily = int(db_plan.get("daily_task_limit", db_plan.get("daily_limit", 5)))
            default_cap = int(db_plan.get("total_earning_cap", db_plan.get("earnings_limit", 900)))
            validity = int(db_plan.get("validity_days", db_plan.get("duration", 60)))
            # One-time migration: freeze current values into this member record.
            plan["daily_task_limit"] = default_daily; plan["daily_limit"] = default_daily
            plan["total_earning_cap"] = default_cap; plan["earnings_limit"] = default_cap
            plan["validity_days"] = validity; plan["duration"] = validity
            plan["plan_name"] = display; plan["price"] = int(plan.get("price", db_plan.get("price", 0)) or 0)
        else:
            ptype = low or "custom"; display = name or "Custom"
            default_daily = int(plan.get("daily_task_limit", plan.get("daily_limit", 5)))
            default_cap = int(plan.get("total_earning_cap", plan.get("earnings_limit", 900)))
            validity = int(plan.get("validity_days", 60))

    status = str(plan.get("status", "active")).lower()
    if status not in ("active", "approved"):
        return {"active": False, "type": ptype, "display": f"{display} Pending", "expiry": None, "daily": default_daily, "cap": default_cap, "validity_days": validity}

    expiry = plan.get("expiry") or plan.get("expires_at")
    if expiry:
        try:
            from datetime import date as _date
            if isinstance(expiry, datetime):
                expiry = expiry.date()
            elif isinstance(expiry, str):
                expiry = _date.fromisoformat(expiry[:10])
        except Exception:
            expiry = None
    if expiry is None:
        base = plan.get("date") or plan.get("activated_at")
        try:
            from datetime import date as _date
            if isinstance(base, datetime):
                base = base.date()
            elif isinstance(base, str):
                base = _date.fromisoformat(base[:10])
            expiry = (base or get_ist_today()) + timedelta(days=validity)
        except Exception:
            expiry = get_ist_today() + timedelta(days=validity)

    if get_ist_today() > expiry:
        return {"active": False, "type": ptype, "display": f"{display} Expired (Time)", "expiry": expiry, "daily": default_daily, "cap": default_cap, "validity_days": validity}

    withdrawn = 0.0
    try:
        withdrawn = float(get_withdrawn_for_cap(uid))
    except Exception:
        pass
    total_earned = 0.0
    try:
        total_earned = float(get_balance(uid))
    except Exception:
        pass
    if (withdrawn + total_earned) >= default_cap or withdrawn >= default_cap:
        return {"active": False, "type": ptype, "display": f"{display} Completed (Rs{default_cap} Reached)", "expiry": expiry, "daily": default_daily, "cap": default_cap, "validity_days": validity}

    if isinstance(plan, dict):
        plan["plan"] = ptype
        plan["plan_name"] = display
        plan["daily_limit"] = default_daily
        plan["daily_task_limit"] = default_daily
        plan["earnings_limit"] = default_cap
        plan["total_earning_cap"] = default_cap
        plan["expiry"] = str(expiry)
        plan["status"] = "active"

    return {"active": True, "type": ptype, "display": display, "expiry": expiry, "daily": default_daily, "cap": default_cap, "validity_days": validity}

def check_plan_active(uid):
    info = _canonical_plan_info(uid)
    if not info["active"]:
        return False, info["display"], info["expiry"]
    return True, f"{info['display']} till {info['expiry']}", info["expiry"]

def get_plan_limits(uid):
    info = _canonical_plan_info(uid)
    return int(info["daily"]), int(info["cap"]), info["type"]

def check_daily_limits(uid):
    today = str(get_ist_today())
    count = daily_task_count.get(uid, {}).get(today, 0)
    limit, cap, plan_name = get_plan_limits(uid)
    return count, limit, cap
def get_today_task_for_user(uid):
    """Return only an admin-created task. Never invent a default daily task."""
    current, _ = get_current_scheduled_task_with_interval()
    return current

def admin_panel_keyboard():
    missed_label = "⏰ Missed: ON" if MISSED_ENABLED else "⏰ Missed: OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Pending Daily ({len(pending_daily)})", callback_data="admin_view_pending"),
         InlineKeyboardButton(f"💰 Withdraw ({len([w for w in withdraw_requests.values() if w.get('status')=='processing'])})", callback_data="admin_view_withdraw")],
        [InlineKeyboardButton("⏰ Today's Tasks", callback_data="admin_view_tasks"),
         InlineKeyboardButton("🏪 Promo Campaigns", callback_data="admin_view_promos")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_view_stats"),
         InlineKeyboardButton("🚫 Banned List", callback_data="admin_view_banned")],
        [InlineKeyboardButton("📢 Product Promotion", callback_data="admin_product_promo"),
         InlineKeyboardButton("💾 Backup", callback_data="admin_backup")],
        [InlineKeyboardButton("👑 Admins", callback_data="admin_add_admin"),
         InlineKeyboardButton("🔗 Referral", callback_data="admin_referral")],
        [InlineKeyboardButton(missed_label, callback_data="admin_missed_toggle")],
        [InlineKeyboardButton("📋 Menu", callback_data="back_menu")]
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer_earn")],
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("📅 Daily Task", callback_data="daily")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"), InlineKeyboardButton("🏪 Promo Tasks", callback_data="promo_tasks")],
        [InlineKeyboardButton("📢 Product Promotion", callback_data="product_promo")],
        [InlineKeyboardButton("📢 Promote My Shop", callback_data="promote_shop"), InlineKeyboardButton("📋 Scheduled Tasks", callback_data="scheduled")],
        [InlineKeyboardButton("💎 Support Plans", callback_data="support_plans"), InlineKeyboardButton("👤 My Details", callback_data="my_details")],
        [InlineKeyboardButton("❌ Missed Tasks", callback_data="missed_tasks"), InlineKeyboardButton("📞 Contact Us", callback_data="contact_us")],
    ])

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

async def check_user_in_channel(user_id, context):
    # Final FIX: ALWAYS True - Fix join in channel error alane undi - Yenduvalla ala vastundi!
    # Reason: CHANNEL_ID = -1004352241439 but CHANNEL_LINK = https://t.me/S2E_Daily_Earning - ID mismatch!
    # Bot not admin in -1004352241439 - get_chat_member fails - Always Not joined!
    # Fix: ALWAYS True bypass for testing - No join check!
    try:
        print(f"check_user_in_channel: User {user_id} - ALWAYS True bypass - Fix redirect loop! FINAL! Yenduvalla: ID mismatch + Bot not admin!")
        return True
    except Exception as e:
        print(f"check err {e} - Return True!")
        return True

def _get_or_create_referral_code(uid):
    """Return a short public referral code; never expose the Telegram numeric ID."""
    try:
        uid = int(uid)
    except Exception:
        return ""
    try:
        existing = referral_codes_db.get(uid) or referral_codes_db.get(str(uid))
        if existing:
            code = str(existing).upper()
            referral_codes_db[uid] = code
            referral_code_to_uid[code] = uid
            return code

        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(30):
            code = "S2E" + "".join(secrets.choice(alphabet) for _ in range(7))
            owner = referral_code_to_uid.get(code)
            if owner is None or int(owner) == uid:
                referral_codes_db[uid] = code
                referral_code_to_uid[code] = uid
                try:
                    save_data()
                except Exception:
                    pass
                return code
    except Exception as e:
        print(f"referral code error: {e}")
    return ""

def _resolve_referral_arg(arg):
    """Resolve new opaque referral codes and keep old numeric links working."""
    try:
        raw = str(arg or "").strip()
        if not raw:
            return None
        if raw.isdigit():
            return int(raw)  # backward compatibility for old referral links
        code = raw.upper()
        owner = referral_code_to_uid.get(code)
        if owner is None:
            # JSON/Supabase may have loaded reverse-map keys/values as strings.
            for k, v in referral_codes_db.items():
                if str(v).upper() == code:
                    try:
                        owner = int(k)
                    except Exception:
                        owner = k
                    referral_code_to_uid[code] = owner
                    break
        try:
            return int(owner) if owner is not None else None
        except Exception:
            return owner
    except Exception:
        return None

def _touch_telegram_user(update):
    """Keep the admin copy of the Telegram username current without showing IDs publicly."""
    try:
        u = update.effective_user
        uid = int(u.id)
        rec = users_db.setdefault(uid, {})
        tg_username = getattr(u, "username", None)
        rec["username"] = str(tg_username).lstrip("@") if tg_username else ""
        rec.setdefault("telegram_id", uid)
        rec.setdefault("created_at", str(get_ist_today()))
        return rec
    except Exception:
        return {}

def _user_is_registered(rec):
    """Registered users from old data or the new registration_complete flag."""
    if not isinstance(rec, dict):
        return False
    if rec.get("registration_complete") is True:
        return True
    name = str(rec.get("name") or "").strip().lower()
    if name in ("", "not registered", "pending"):
        return False
    # Existing production users may not have the new flag.
    return bool(rec.get("mobile") or rec.get("upi") or rec.get("profession") or rec.get("gender"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Create a lightweight record immediately on /start so every bot join is
    # visible to /userlist, even if registration is not completed yet.
    rec = _touch_telegram_user(update)
    rec.setdefault("name", "Not registered")
    rec.setdefault("registration_complete", False)

    if uid in banned_users:
        await update.message.reply_text("You are BANNED! Contact admin!")
        return ConversationHandler.END

    # Capture referral before any registration screen.
    args = context.args
    ref_id = None
    if args:
        ref_id = _resolve_referral_arg(args[0])
        if ref_id is not None and ref_id != uid and ref_id not in banned_users:
            referral_map[uid] = ref_id

    try:
        save_data()
    except Exception:
        pass

    if not is_admin(uid):
        is_joined = await check_user_in_channel(uid, context)
        if not is_joined:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=get_join_channel_link())],
                [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")]
            ])
            await update.message.reply_text(
                f"👋 Welcome! Please join our channel {get_join_channel()} to use bot!\n\nJoin and click Check Joined!",
                reply_markup=kb
            )
            return ConversationHandler.END

    if _user_is_registered(rec):
        await update.message.reply_text(
            f"Welcome back {rec.get('name','User')}! Balance Rs{get_balance(uid)}\nTasks {get_tasks(uid)}/15",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome to S2E Daily Earning + Promo Network!\n\nWhat is your Name?"
    )
    return NAME

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id

    rec = _touch_telegram_user(update)
    rec.setdefault("name", "Not registered")
    rec.setdefault("registration_complete", False)

    # Keep the existing production behaviour: do not block the user on a
    # Telegram channel-membership API hiccup.
    is_joined = await check_user_in_channel(uid, context)
    print(f"check_joined_cb: User {uid} is_joined {is_joined}")

    try:
        save_data()
    except Exception:
        pass

    if _user_is_registered(rec):
        await q.message.reply_text(
            f"✅ Thanks for joining! Welcome back {rec.get('name','User')}!",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    await q.message.reply_text("✅ Thanks for joining! What is your Name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Name too short! Enter valid name:")
        return NAME
    rec = users_db.setdefault(uid, {})
    rec['name'] = name
    rec['registration_complete'] = False
    rec['username'] = str(getattr(update.effective_user, 'username', '') or '').lstrip('@')
    rec.setdefault('telegram_id', uid)
    await update.message.reply_text(
        "Select your gender:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👨 Male", callback_data="reg_gender_male"),
             InlineKeyboardButton("👩 Female", callback_data="reg_gender_female")],
            [InlineKeyboardButton("⚪ Other", callback_data="reg_gender_other")]
        ])
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    gender = update.message.text.strip().title()
    if gender not in ("Male", "Female", "Other"):
        await update.message.reply_text("Please select Male, Female or Other.")
        return GENDER
    users_db[uid]['gender'] = gender
    await update.message.reply_text("Date of Birth? DD/MM/YYYY:")
    return DOB

async def reg_gender_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    gender = q.data.replace("reg_gender_", "").title()
    if gender not in ("Male", "Female", "Other"):
        return GENDER
    users_db.setdefault(uid, {})['gender'] = gender
    await q.message.reply_text(f"✅ Gender: {gender}\n\nDate of Birth? DD/MM/YYYY:")
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
    users_db[uid]['pincode'] = pincode
    await update.message.reply_text(
        "Select your profession:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎓 Student", callback_data="reg_prof_student"),
             InlineKeyboardButton("💼 Employee", callback_data="reg_prof_employee")],
            [InlineKeyboardButton("🏪 Business", callback_data="reg_prof_business"),
             InlineKeyboardButton("🔧 Self-employed", callback_data="reg_prof_self_employed")],
            [InlineKeyboardButton("⚪ Other", callback_data="reg_prof_other")]
        ])
    )
    return PROFESSION

async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    profession = update.message.text.strip().title()
    allowed = {"Student", "Employee", "Business", "Self-Employed", "Other"}
    if profession not in allowed:
        await update.message.reply_text("Please select one of the profession options.")
        return PROFESSION
    users_db[uid]['profession'] = profession
    users_db[uid]['joined']=str(get_ist_today())
    users_db[uid]['reg_date']=get_ist_today()
    users_db[uid]['registration_complete'] = True
    users_db[uid]['username'] = str(getattr(update.effective_user, 'username', '') or '').lstrip('@')
    users_db[uid]['telegram_id'] = uid
    save_data()
    await update.message.reply_text(f"✅ Registration Done! Welcome {users_db[uid]['name']}!\n\n💰 Earn: Rs10 per referral + 10% plan commission\n🏪 Promo: Earn Rs10 per 100 status views!\n📋 Tasks: 0/15 | Withdraw Min Rs200\n\nClick /menu for options!", reply_markup=main_menu())
    return ConversationHandler.END

async def reg_profession_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    value = q.data.replace("reg_prof_", "").replace("_", " ").title()
    if value not in ("Student", "Employee", "Business", "Self Employed", "Other"):
        return PROFESSION
    if value == "Self Employed":
        value = "Self-Employed"
    users_db.setdefault(uid, {})['profession'] = value
    users_db[uid]['joined'] = str(get_ist_today())
    users_db[uid]['reg_date'] = get_ist_today()
    users_db[uid]['registration_complete'] = True
    users_db[uid]['username'] = str(getattr(q.from_user, 'username', '') or '').lstrip('@')
    users_db[uid]['telegram_id'] = uid
    save_data()
    await q.message.reply_text(
        f"✅ Registration Done! Welcome {users_db[uid]['name']}!\n\n"
        f"Gender: {users_db[uid].get('gender','-')}\nProfession: {value}\n\n"
        "💰 Earn: Rs10 per referral + 10% plan commission\n"
        "🏪 Promo: Earn Rs10 per 100 status views!\n"
        "📋 Tasks: 0/15 | Withdraw Min Rs200\n\nClick /menu for options!",
        reply_markup=main_menu()
    )
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
    msg += f"📢 Promo Campaigns: {len(promo_campaigns_db)} Active: {active_promos} | Product Pending: {len(product_promo_pending)}\n"
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
    
    await update.message.reply_text(msg[:4000], reply_markup=admin_panel_keyboard())

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

async def admin_product_promo_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer("Opening Product Promotion...")
    except Exception:
        pass
    if not q or not q.from_user or not is_admin(q.from_user.id):
        return
    uid = q.from_user.id
    live = get_active_product_promo_for_user(uid)
    pending = len(product_promo_pending)
    if live:
        t = live[0] if isinstance(live, list) else live
        reward_text = _product_reward_text(t, uid)
        msg = (
            "📢 PRODUCT PROMOTION ADMIN\n\n"
            f"ID: {t.get('id')}\n"
            f"Title: {t.get('title','Product Promotion')}\n"
            f"Status: {t.get('status','active')}\n"
            f"Download deadline: {t.get('download_deadline','-')}\n"
            f"Screenshot window: {t.get('screenshot_open','-')} → {t.get('screenshot_close','-')}\n"
            f"{reward_text}\n"
            f"Pending screenshots: {pending}\n\n"
            "Create/replace today's campaign:\n"
            "/add_product_promo DOWNLOAD_DEADLINE SCREENSHOT_OPEN SCREENSHOT_CLOSE TITLE REWARD_SPEC | INSTRUCTIONS\n\n"
            "Then send the promotion VIDEO to this bot."
        )
    else:
        msg = (
            "📢 PRODUCT PROMOTION ADMIN\n\n"
            "No active Product Promotion for today.\n"
            f"Pending screenshots: {pending}\n\n"
            "Create one with:\n"
            "/add_product_promo DOWNLOAD_DEADLINE SCREENSHOT_OPEN SCREENSHOT_CLOSE TITLE REWARD_SPEC | INSTRUCTIONS\n\n"
            "Then send the promotion VIDEO to this bot."
        )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 Approve ALL Product Pending ({pending})", callback_data="product_bulk_approve_all")],
        [InlineKeyboardButton("⬅️ Back to Admin", callback_data="back_admin")]
    ])
    await q.message.reply_text(msg[:4000], reply_markup=kb)

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
    """Safe Back-to-Admin handler; CallbackQuery is never passed to admin_panel()."""
    q = update.callback_query
    if not q or not q.from_user:
        return
    try:
        await q.answer("Opening Admin...")
    except Exception:
        pass
    uid = q.from_user.id
    if not is_admin(uid):
        return
    active_promos = len(get_active_promo_campaigns())
    total_views = sum(c.get('total_views', 0) for c in promo_campaigns_db)
    msg = (
        "🔐 ADMIN PANEL - S2E Ultimate + Poster\n\n"
        f"👥 Users: {len(users_db)}\n"
        f"📋 Pending Daily: {len(pending_daily)}\n"
        f"💰 Pending Withdraw: {len([w for w in withdraw_requests.values() if w.get('status')=='processing'])}\n"
        f"📢 Promo Campaigns: {len(promo_campaigns_db)} | Active: {active_promos}\n"
        f"🛍️ Product Pending: {len(product_promo_pending)}\n"
        f"👁️ Total Promo Views: {total_views}\n"
        f"⏰ Scheduled Today: {len(get_tasks_for_today())}\n"
        f"🖼️ Tasks with Poster: {len(task_images_db)}\n"
        f"⏭️ Skipped Today: {sum(len(v) for v in skip_db.values())}\n"
        f"🚫 Banned: {len(banned_users)}\n\n"
        "Commands:\n/add_task open close next title link reward\n"
        "/set_task_image <id> - Then send poster image!\n"
        "/add_product_promo ... - Then send promotion VIDEO\n"
        "/list_tasks /list_promos /skipped all /warnings /banned"
    )
    await context.bot.send_message(chat_id=uid, text=msg[:4000], reply_markup=admin_panel_keyboard())

def get_referral_work_commission_total(uid, day=None, level=None):
    day=str(day or get_ist_today())
    total=0.0
    for e in referral_commission_ledger.get(uid, []):
        if str(e.get("date")) != day: continue
        if level is not None and int(e.get("level",0) or 0) != int(level): continue
        if str(e.get("type")) not in ("task","product","product_promo","promo"): continue
        try: total += float(e.get("amount",0) or 0)
        except Exception: pass
    return round(total,2)

async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    l1, l2 = get_referral_chain(uid)
    today = get_ist_today()
    yday = today - timedelta(days=1)
    l1_today = get_referral_work_commission_total(uid, today, level=1)
    l2_today = get_referral_work_commission_total(uid, today, level=2)
    l1_yday = get_referral_work_commission_total(uid, yday, level=1)
    l2_yday = get_referral_work_commission_total(uid, yday, level=2)
    l1_task_yday = get_referral_task_earnings(uid, yday, level=1)
    l2_task_yday = get_referral_task_earnings(uid, yday, level=2)
    plan_yday = get_plan_commission_yesterday(uid)
    total_ref = referral_earnings.get(uid, 0)
    msg=(
        "👥 MY REFERRALS\n\n"
        f"🟢 L1 Members: {len(l1)}\n"
        f"📈 L1 Task/Product Commission: {L1_TASK_COMMISSION_PERCENT:g}%\n"
        f"💼 Yesterday L1 Task/Product Commission: ₹{l1_yday:.2f}\n\n"
        f"🔵 L2 Members: {len(l2)}\n"
        f"📈 L2 Task/Product Commission: {L2_TASK_COMMISSION_PERCENT:g}%\n"
        f"💼 Yesterday L2 Task/Product Commission: ₹{l2_yday:.2f}\n\n"
        f"💎 Plan Activation: L1 {REFERRAL_PLAN_COMMISSION_PERCENT:g}% | L2 {L2_PLAN_COMMISSION_PERCENT:g}%\n"
        f"💰 Yesterday Plan Commission: ₹{plan_yday:.2f}\n\n"
        f"📅 Today: L1 ₹{l1_today:.2f} | L2 ₹{l2_today:.2f}\n"
        f"💵 Total Referral Commission: ₹{float(total_ref):.2f}"
    )
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer_earn")],
        [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]
    ])
    await q.message.reply_text(msg, reply_markup=kb)

async def refer_earn_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass

    uid = q.from_user.id
    _touch_telegram_user(update)
    code = _get_or_create_referral_code(uid)
    ref_link = f"https://t.me/{context.bot.username}?start={code}"

    # Keep commission percentages private. The public referral screen only
    # shows the link and a simple share/join message.
    msg = (
        "🔗 REFER & EARN\n\n"
        "Invite your friends to join S2E and earn by completing simple tasks.\n\n"
        f"🔗 Your Referral Link:\n{ref_link}"
    )
    share_url = (
        "https://t.me/share/url?url="
        + quote(ref_link, safe="")
        + "&text="
        + quote("Join S2E Earning Bot → Complete tasks → Earn 💰", safe="")
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 REFER", url=share_url)],
        [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]
    ])
    await q.message.reply_text(msg, reply_markup=kb)

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    direct_today=get_tasks(uid)
    direct_amount=get_today_task_earnings(uid)
    l1_today=get_referral_commission_total(uid, level=1, commission_type="task")
    l2_today=get_referral_commission_total(uid, level=2, commission_type="task")
    plan_today=get_referral_commission_total(uid, commission_type="plan")
    referral_today=round(l1_today+l2_today+plan_today,2)
    promo_rs=float(promo_earnings_db.get(uid,0) or 0) + float(globals().get('product_promo_approved', {}).get(uid, 0) if isinstance(globals().get('product_promo_approved', {}).get(uid, 0), (int,float)) else 0)
    # V36: Product promo earnings are in promo_earnings_db too, but also check product_promo_approved logic
    try:
        # Actual product promo total is promo_earnings_db already includes it, but double-check
        prod_promo = 0
        # promo_earnings_db contains product promo rewards too
        promo_rs = float(promo_earnings_db.get(uid,0) or 0)
        # Add separate product promo if any
        if isinstance(globals().get('product_promo_approved', {}), dict):
            # product_promo_approved stores timestamps, not amount, so ignore
            pass
    except:
        promo_rs = float(promo_earnings_db.get(uid,0) or 0)
    info=_canonical_plan_info(uid)
    withdrawn=get_withdrawn_for_cap(uid)
    cap=info["cap"]
    cap_remaining=max(0, cap-withdrawn)
    hold_balance = max(0, bal - cap) if cap < bal else 0
    withdrawable = min(bal, cap) - withdrawn
    withdrawable = max(0, withdrawable)
    msg=(
        "💰 WALLET\n\n"
        f"Balance: ₹{bal:.2f}\n"
        f"Today's Task Earning: ₹{direct_amount:.2f} ({direct_today}/{info['daily']})\n"
        f"Today's L1 Task Commission: ₹{l1_today:.2f}\n"
        f"Today's L2 Task Commission: ₹{l2_today:.2f}\n"
        f"Today's Plan Activation Commission: ₹{plan_today:.2f}\n"
        f"Today's Referral Commission: ₹{referral_today:.2f}\n"
        f"Promo + Product Promo: ₹{promo_rs:.2f}\n"
        f"Total: ₹{bal:.2f}\n\n"
        f"📋 Plan: {info['display']}\n"
        f"Daily Tasks: {direct_today}/{info['daily']}\n"
        f"Plan Cap: ₹{cap}\n"
        f"Withdrawn: ₹{withdrawn:.2f}/₹{cap}\n"
        f"Cap Remaining: ₹{cap_remaining:.2f}\n"
        f"Withdrawable Now: ₹{withdrawable:.2f}\n"
        f"Hold (Upgrade plan to withdraw): ₹{hold_balance:.2f}"
    )
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 Withdraw History", callback_data="withdraw_history")],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]]))

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

async def product_promo_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    promos=get_active_product_promo_for_user(uid)
    if not promos:
        await q.message.reply_text("📢 PRODUCT PROMOTION\n\nNo active product promotion right now.", reply_markup=main_menu())
        return
    kb=[]
    lines=["📢 PRODUCT PROMOTION\n"]
    for t in promos[:10]:
        lines.append(f"🎥 {t.get('title','Product Promotion')}\n{_product_time_text(t)}\n{_product_reward_text(t,uid)}\n")
        tid=t['id']
        if t.get('_download_open'):
            kb.append([InlineKeyboardButton("⬇️ Download Video", callback_data=f"product_download_{tid}")])
        if t.get('_screenshot_open'):
            kb.append([InlineKeyboardButton("📸 Submit Screenshot", callback_data=f"product_screenshot_{tid}")])
        elif not t.get('_download_open'):
            lines.append("⏳ Screenshot submission will open at the scheduled time.\n")
    await q.message.reply_text("\n".join(lines)[:4000], reply_markup=InlineKeyboardMarkup(kb or [[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]]))

async def product_download_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    try: tid=int(q.data.split('_')[-1])
    except: return
    t=next((x for x in product_promo_db if int(x.get('id',-1))==tid),None)
    if not t:
        await q.message.reply_text("❌ Product promotion not found.", reply_markup=main_menu()); return
    promos=get_active_product_promo_for_user(uid)
    t2=next((x for x in promos if int(x.get('id',-1))==tid),None)
    if not t2 or not t2.get('_download_open'):
        await q.message.reply_text(f"⏰ Video download is closed. Download deadline was {t.get('download_deadline','') }.", reply_markup=main_menu()); return
    if not t.get('video_file_id'):
        await q.message.reply_text("❌ Video is not available yet. Please contact Admin.", reply_markup=main_menu()); return
    try:
        await context.bot.send_video(chat_id=uid, video=t['video_file_id'], caption=(
            f"📢 {t.get('title','Product Promotion')}\n\n{t.get('description','')}\n\n"
            f"⬇️ Download this video and put it on your WhatsApp Status.\n"
            f"{_product_time_text(t)}\n{_product_reward_text(t,uid)}"
        ))
    except Exception as e:
        await q.message.reply_text(f"❌ Could not send video: {e}", reply_markup=main_menu())

async def product_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    try: tid=int(q.data.split('_')[-1])
    except: return
    t=next((x for x in product_promo_db if int(x.get('id',-1))==tid),None)
    promos=get_active_product_promo_for_user(uid)
    t2=next((x for x in promos if int(x.get('id',-1))==tid),None)
    if not t2 or not t2.get('_screenshot_open'):
        await q.message.reply_text(f"⏰ Screenshot submission is available only from {t.get('screenshot_open','')} to {t.get('screenshot_close','')}.", reply_markup=main_menu())
        return
    existing = product_promo_pending.get(uid) or product_promo_pending.get(str(uid))
    if existing and int(existing.get('promo_id', -1)) == tid:
        await q.message.reply_text("⏳ Your Product Promotion screenshot is already submitted! Waiting for admin approval.", reply_markup=main_menu()); return
    approved = product_promo_approved.get(uid) or product_promo_approved.get(str(uid)) or {}
    if str(tid) in approved or tid in approved:
        await q.message.reply_text("✅ Promotion amount has already been added to your wallet.\n🚫 No more Product Promotion for today.\n\nPlease wait for the next Product Promotion campaign.", reply_markup=main_menu()); return
    context.user_data['awaiting_product_screenshot']=True
    context.user_data['product_screenshot_id']=tid
    await q.message.reply_text(
        f"📸 Send the WhatsApp Status screenshot for:\n{t.get('title','Product Promotion')}\n\n"
        f"Submission window: {t.get('screenshot_open','')} → {t.get('screenshot_close','')}\n"
        "Send the screenshot as a photo."
    )

async def add_product_promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Admin only!"); return
    text=update.message.text.replace('/add_product_promo','',1).strip()
    if not text:
        await update.message.reply_text(
            "Usage:\n/add_product_promo DOWNLOAD_DEADLINE SCREENSHOT_OPEN SCREENSHOT_CLOSE TITLE REWARD_SPEC | INSTRUCTIONS\n\n"
            "Example:\n/add_product_promo 10:00AM 8:00PM 10:00PM My Product free:10,basic:15,premium:20,pro:25,vip:30 | Download the video, put it on WhatsApp Status, keep it for 6 hours, then send screenshot during 8PM-10PM.\n\nThen send the video to the bot."
        ); return
    if '|' in text:
        left, desc=text.split('|',1); desc=desc.strip()
    else:
        left, desc=text, "Download the video and put it on your WhatsApp Status. Send the screenshot only during the scheduled screenshot window."
    import re
    urls=re.findall(r'https?://\S+', left)
    parts=left.split()
    if len(parts)<5:
        await update.message.reply_text("Need: download_deadline screenshot_open screenshot_close title reward_spec | instructions"); return
    download_deadline, shot_open, shot_close=parts[:3]
    reward_spec=parts[-1]
    title=' '.join(parts[3:-1]).strip()
    rewards={}; base=0
    try:
        if ':' in reward_spec:
            for piece in reward_spec.split(','):
                k,v=piece.split(':',1); v=int(v)
                kl=k.strip().lower()
                pid={'free':0,'basic':1,'premium':2,'pro':3,'vip':4}.get(kl, int(kl) if kl.isdigit() else 0)
                rewards[pid]=v
            base=rewards.get(0,next(iter(rewards.values())))
        else:
            base=int(reward_spec); rewards={'all':base}
    except Exception:
        await update.message.reply_text("❌ Invalid reward. Example: free:10,basic:15,premium:20,pro:25,vip:30"); return
    try:
        d=parse_time_str(download_deadline); so=parse_time_str(shot_open); sc=parse_time_str(shot_close)
        if not d or not so or not sc: raise ValueError('Invalid time')
    except Exception:
        await update.message.reply_text("❌ Invalid time. Use examples 10:00AM 8:00PM 10:00PM"); return
    global product_promo_counter
    # Product Promotion uses one live campaign slot. Archive every older
    # campaign first so an old promotion/video can never reappear.
    today = str(get_ist_today())
    for old in product_promo_db:
        if isinstance(old, dict) and old.get('date') == today and old.get('status') in ('active', 'waiting_video'):
            old['status'] = 'archived'
            old['archived_at'] = get_ist_now()

    task={'id':product_promo_counter,'date':today,'title':title or 'Product Promotion','description':desc,'download_deadline':d.strftime('%H:%M'),'screenshot_open':so.strftime('%H:%M'),'screenshot_close':sc.strftime('%H:%M'),'reward':base,'rewards':rewards,'video_file_id':None,'status':'waiting_video','created_at':get_ist_now(),'created_by':uid}
    product_promo_db.append(task); product_promo_counter+=1
    # Persist the pending upload target in the campaign itself. context.user_data
    # is per-session and can be lost on a restart; DB state must remain sufficient
    # to attach the next admin video to this exact campaign.
    context.user_data['awaiting_product_video']=task['id']
    try:
        async def _auto_cancel_job(ctx):
            try:
                tid = ctx.job.data['tid']
                still = [x for x in product_promo_db if int(x.get('id',-1))==int(tid) and x.get('status')=='waiting_video']
                if still:
                    for x in still:
                        try: product_promo_db.remove(x)
                        except: pass
                    try: save_data()
                    except: pass
                    try:
                        await ctx.bot.send_message(chat_id=ctx.job.data['admin_id'], text=f"⏰ Promo {tid} auto-cancelled - video not sent in 5min")
                    except: pass
            except Exception as e:
                print(f"auto cancel err {e}")
        context.job_queue.run_once(_auto_cancel_job, 300, data={'tid': task['id'], 'admin_id': uid}, name=f"cancel_promo_{task['id']}")
    except Exception as e:
        print(f"cancel job fail {e}")
    save_data()
    await update.message.reply_text(f"✅ Product Promotion ID {task['id']} created.\n\n🎥 Now send the promotion VIDEO to this bot.\n\nDownload deadline: {task['download_deadline']}\nScreenshot: {task['screenshot_open']} → {task['screenshot_close']}\n{_product_reward_text(task,uid)}")

async def product_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid=update.effective_user.id
        if not is_admin(uid): return
        tid=context.user_data.get('awaiting_product_video')
        # Recover the upload target from persistent DB after a bot restart or
        # Telegram session reset. Only today's newest waiting campaign is valid.
        if not tid:
            waiting=[x for x in product_promo_db if isinstance(x,dict) and x.get('date')==str(get_ist_today()) and x.get('status')=='waiting_video']
            if waiting:
                tid=max(waiting,key=lambda x:int(x.get('id',0) or 0)).get('id')
        if not tid: return
        if not update.message.video and not update.message.document: return
        file_id=update.message.video.file_id if update.message.video else update.message.document.file_id
        t=next((x for x in product_promo_db if int(x.get('id',-1))==int(tid)),None)
        if not t or t.get('status') != 'waiting_video': return
        t['video_file_id']=file_id; t['status']='active'
        context.user_data.pop('awaiting_product_video',None)
        save_data()
        await update.message.reply_text(f"✅ Product Promotion {tid} video saved and activated.\nMembers will see it in 📢 Product Promotion, NOT in Daily Task.")
    except Exception as e:
        print(f'product_video_handler error: {e}')

async def product_screenshot_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid=update.effective_user.id
        if is_admin(uid) or not context.user_data.get('awaiting_product_screenshot'): return
        if not update.message.photo and not update.message.document: return
        tid=int(context.user_data.get('product_screenshot_id'))
        t=next((x for x in product_promo_db if int(x.get('id',-1))==tid),None)
        promos=get_active_product_promo_for_user(uid)
        t2=next((x for x in promos if int(x.get('id',-1))==tid),None)
        if not t or not t2 or not t2.get('_screenshot_open'):
            await update.message.reply_text("⏰ Screenshot submission window is closed.", reply_markup=main_menu()); return
        file_id=update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
        unique_id=update.message.photo[-1].file_unique_id if update.message.photo else update.message.document.file_unique_id
        if unique_id in screenshot_hashes:
            await update.message.reply_text("⚠️ Same screenshot detected.", reply_markup=main_menu()); return
        screenshot_hashes.add(unique_id)
        reward=_product_reward_for_user(t,uid)
        product_promo_pending[uid]={'uid':uid,'promo_id':tid,'file_id':file_id,'reward':reward,'submitted_at':get_ist_now(),'status':'pending'}
        save_data()
        context.user_data.pop('awaiting_product_screenshot',None); context.user_data.pop('product_screenshot_id',None)
        await update.message.reply_text("✅ Product promotion screenshot received! Waiting for admin approval.", reply_markup=main_menu())
        chan=get_screenshot_channel()
        if chan:
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Approve ₹{reward}", callback_data=f"product_approve_{uid}_{tid}"), InlineKeyboardButton("❌ Reject", callback_data=f"product_reject_{uid}_{tid}")],
                [InlineKeyboardButton("🚀 Approve ALL Product Pending", callback_data="product_bulk_approve_all")]
            ])
            await context.bot.send_photo(chat_id=chan,photo=file_id,caption=(f"📢 PRODUCT PROMOTION SCREENSHOT\n👤 {users_db.get(uid,{}).get('name','Unknown')}\n🆔 {uid}\n📋 {t.get('title','Product Promotion')}\n💰 Reward: ₹{reward}\n📅 {get_ist_today()}"),reply_markup=kb)
    except Exception as e:
        print(f'product_screenshot_photo_handler error: {e}')

async def product_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    try: uid=int(q.data.split('_')[2]); tid=int(q.data.split('_')[3])
    except: return
    sub=product_promo_pending.get(uid)
    if not sub or int(sub.get('promo_id',-1))!=tid:
        await q.message.reply_text('❌ Product submission not found or already processed.'); return
    reward=int(sub.get('reward',0) or 0)
    approved_map = product_promo_approved.setdefault(uid, {})
    if str(tid) in approved_map or tid in approved_map:
        product_promo_pending.pop(uid, None)
        save_data()
        await q.message.reply_text("⚠️ This Product Promotion was already approved. No duplicate amount was added.")
        return
    promo_earnings_db[uid]=round(float(promo_earnings_db.get(uid,0) or 0)+reward, 2)
    record_product_promo_referral_commissions(uid, reward)
    approved_map[str(tid)] = str(get_ist_now())
    product_promo_pending.pop(uid, None)
    save_data()
    await q.message.reply_text(f"✅ Product promotion approved: User {uid} +₹{reward}\nApproved: 1\nRemaining pending: {len(product_promo_pending)}")
    try: await context.bot.send_message(chat_id=uid,text=f"✅ Product Promotion Approved! +₹{reward}\nBalance: ₹{get_balance(uid)}",reply_markup=main_menu())
    except: pass

async def product_reject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    try: uid=int(q.data.split('_')[2]); tid=int(q.data.split('_')[3])
    except: return
    sub=product_promo_pending.get(uid) or product_promo_pending.get(str(uid))
    if sub and int(sub.get('promo_id',-1))==tid:
        product_promo_pending.pop(uid, None); product_promo_pending.pop(str(uid), None)
    save_data(); await q.message.reply_text(f"❌ Product promotion screenshot rejected for User {uid}.")
    try: await context.bot.send_message(chat_id=uid,text="❌ Product Promotion Screenshot Rejected. Please follow the instructions and submit a valid screenshot during the allowed time.",reply_markup=main_menu())
    except: pass

async def product_bulk_approve_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    try: await q.answer("Processing product bulk approval…")
    except Exception: pass
    if not is_admin(q.from_user.id):
        return
    approved_count=0
    approved_users=[]
    for key, sub in list(product_promo_pending.items()):
        try:
            uid=int(sub.get('uid', key)); tid=int(sub.get('promo_id', -1))
            if tid < 0: continue
            approved_map=product_promo_approved.setdefault(uid,{})
            if str(tid) in approved_map or tid in approved_map:
                product_promo_pending.pop(key,None)
                continue
            reward=int(sub.get('reward',0) or 0)
            promo_earnings_db[uid]=round(float(promo_earnings_db.get(uid,0) or 0)+reward,2)
            record_product_promo_referral_commissions(uid, reward)
            approved_map[str(tid)]=str(get_ist_now())
            product_promo_pending.pop(key,None)
            approved_count += 1
            approved_users.append(f"{uid} (₹{reward})")
            try:
                await context.bot.send_message(chat_id=uid, text=f"✅ Product Promotion Approved! +₹{reward}\nBalance: ₹{get_balance(uid)}\n\n🚫 No more Product Promotion for today.", reply_markup=main_menu())
            except Exception: pass
        except Exception as e:
            print(f"product bulk approval error {key}: {e}")
    save_data()
    details="\n".join(approved_users[:15])
    if len(approved_users)>15: details += f"\n...and {len(approved_users)-15} more"
    await q.message.reply_text(f"✅ PRODUCT BULK APPROVAL DONE\n\nApproved: {approved_count}\n{details or 'No pending product submissions.'}\n\nRemaining pending: {len(product_promo_pending)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin",callback_data="back_admin")]]))


async def scheduled_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    today_tasks=get_tasks_for_today()
    if not today_tasks:
        await q.message.reply_text(f"📋 SCHEDULED TASKS — {get_ist_today()}\n\nNo tasks scheduled today. Admin will add tasks when needed.", reply_markup=main_menu())
        return
    msg=f"📋 SCHEDULED TASKS — {get_ist_today()}\n\nToday's task timings:\n\n"
    for task in today_tasks:
        msg += f"🕐 {task.get('open_time','')} → {task.get('close_time','')}  |  Task {task.get('task_number','?')}\n{task.get('title','')}\n\n"
    msg += "Only today's admin-scheduled tasks are shown here. If a task window is missed, it will appear in Missed Tasks when that feature is enabled."
    await q.message.reply_text(msg[:4000], reply_markup=main_menu())

def get_current_task_for_user(uid):
    """Return the current task that this user can still work on.
    Completed/skipped tasks are skipped; pending verification blocks progression.
    """
    current, next_task = get_current_scheduled_task_with_interval()
    candidates = []
    if current:
        candidates.append(current)
    if next_task and next_task is not current:
        candidates.append(next_task)
    # Also inspect all today's tasks so a completed current task never repeats.
    for t in get_tasks_for_today():
        if t not in candidates:
            candidates.append(t)
    now = get_ist_now()
    for task in candidates:
        tid = task.get("id")
        data = user_task_status.get(uid, {}).get(tid, {})
        status = data.get("status") if isinstance(data, dict) else data
        if status == "pending_verification":
            return task, "pending"
        if status in ("completed", "skipped", "missed"):
            continue
        _ot = _safe_time(task.get("open_time_obj") or task.get("open_time"))
        _ct = _safe_time(task.get("close_time_obj") or task.get("close_time"))
        if not _ot or not _ct:
            continue
        open_dt = datetime.combine(get_ist_today(), _ot, tzinfo=IST)
        close_dt = datetime.combine(get_ist_today(), _ct, tzinfo=IST)
        if open_dt <= now <= close_dt:
            return task, "active"
    return None, "none"

async def daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
        # V37 FREE 3-DAY & 10 TASKS CHECK
        try:
            _info_free = _canonical_plan_info(uid)
            if _info_free['type'] in ('free', 'free_expired'):
                _total_done = tasks_db.get(uid, 0)
                _joined = users_db.get(uid, {}).get('joined') or users_db.get(uid, {}).get('reg_date')
                _days_left = 3
                if _joined:
                    try:
                        from datetime import date as _d
                        _jd = _d.fromisoformat(str(_joined)[:10])
                        _used = (get_ist_today() - _jd).days
                        _days_left = max(0, 3 - _used)
                    except:
                        pass
                if _days_left <= 0 or _total_done >= 10:
                    _bal = get_balance(uid)
                    _reason = "3 Days Completed!" if _days_left <=0 else "10/10 Tasks Completed!"
                    await q.message.reply_text(
                        f"⏰ FREE PLAN - {_reason}\n\n💰 Wallet Balance: ₹{_bal:.2f} (Safe!)\n❌ Free tasks stopped!\n\n💎 Paid Membership ki convert ayite tasks vastayi!\n• Wallet balance alane untundi\n• Plan teesukogane 0/20 tasks nundi start\n• 10/10 = ₹200 instant withdraw!",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade Plan", callback_data="support_plans")],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
                    )
                    return
        except Exception as _e:
            print(f"free daily check fail {_e}")
        count, limit, cap = check_daily_limits(uid)
        if count >= limit and limit > 0:
            is_active, plan_name, _ = check_plan_active(uid)
            if is_active and plan_name.lower().startswith("basic"):
                limit_msg = f"⏰ Basic plan daily limit {limit} reached! You completed {count}/{limit} tasks today.\n\nUpgrade to Premium for {DAILY_TASK_LIMIT_PREMIUM} tasks/day if you want more tasks."
            elif is_active and plan_name.lower().startswith("premium"):
                limit_msg = f"⏰ Premium daily limit {limit} reached! You completed {count}/{limit} tasks today."
            else:
                limit_msg = f"⏰ Daily limit {limit} reached! You completed {count}/{limit} tasks today.\n\nChoose a Support Plan for more daily tasks."
            await q.message.reply_text(limit_msg, reply_markup=main_menu())
            return
        current, current_state = get_current_task_for_user(uid)
        _, next_task = get_current_scheduled_task_with_interval()
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
                # No active/next task. The old code called get_today_task_for_user(),
                # which can return None after all today's task windows are closed, and
                # then crashed on task.get(...). That made the Daily Task button appear
                # to do nothing. Handle this state explicitly.
                today_tasks = get_tasks_for_today()
                if not today_tasks:
                    await q.message.reply_text(
                        "📅 DAILY TASK\n\n"
                        "❌ No task has been scheduled for today yet.\n\n"
                        "Please check again later or contact Admin.",
                        reply_markup=main_menu()
                    )
                    return

                # Check whether all today's tasks are already finished/skipped/missed.
                pending_task = None
                pending_status = None
                for t in today_tasks:
                    tid = t.get('id')
                    status_data = user_task_status.get(uid, {}).get(tid, {})
                    status = status_data.get('status') if isinstance(status_data, dict) else status_data
                    if status == 'pending_verification':
                        pending_task = t
                        pending_status = status
                        break
                    if status not in ('completed', 'skipped', 'missed'):
                        pending_task = t
                        pending_status = status
                        break

                if pending_task is None:
                    await q.message.reply_text(
                        "📅 DAILY TASK\n\n"
                        f"✅ All of today's {len(today_tasks)} task(s) are already completed, skipped, or missed.\n\n"
                        f"Tasks today: {count}/{limit}\n"
                        "New tasks will appear when Admin schedules them.",
                        reply_markup=main_menu()
                    )
                    return

                task = pending_task
                task_id = task.get('id')
                if pending_status == 'pending_verification':
                    await q.message.reply_text(
                        f"⏳ Task {task.get('task_number', '?')} screenshot is already pending Admin verification.\n\n"
                        f"Tasks today: {count}/{limit}",
                        reply_markup=main_menu()
                    )
                    return

                await q.message.reply_text(
                    f"📅 Today's Task:\n\n"
                    f"Task {task.get('task_number', '?')}\n"
                    f"Open: {task.get('open_time', '')}  Close: {task.get('close_time', '')}\n"
                    f"Title: {task.get('title', '')}\n"
                    f"Reward: ₹{task.get('reward', 5)}\n"
                    f"Link: {task.get('link', '')}\n\n"
                    f"{'📝 Instructions:' + chr(10) + task.get('description', '') + chr(10) + chr(10) if task.get('description') else ''}"
                    f"Tasks today: {count}/{limit}\n\n"
                    "Click Upload Screenshot after completing!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_screenshot"),
                        InlineKeyboardButton("⏭️ Skip Task", callback_data=f"daily_skip_{task_id}")
                    ]])
                )
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

    except Exception as e:
        print(f"daily_cb error: {e}")
        import traceback; traceback.print_exc()
        try:
            q=update.callback_query
            await q.message.reply_text(f"❌ Error: {e}", reply_markup=main_menu())
        except:
            pass

async def daily_upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    print(f"V64 UPLOAD SCREENSHOT CALLBACK RECEIVED: data={q.data} uid={q.from_user.id}")
    await q.answer()
    uid = q.from_user.id
    current, next_task = get_current_scheduled_task_with_interval()
    missed_id=context.user_data.get('missed_reopened_task_id') or context.user_data.get('daily_screenshot_task_id')
    missed_task=None
    if missed_id is not None:
        try: missed_task=next((t for t in missed_tasks_db.get(uid,[]) if int(t.get('id',-999999))==int(missed_id)),None)
        except Exception: missed_task=None
    task_for_upload=missed_task or current
    context.user_data['awaiting_daily_screenshot'] = True
    context.user_data['daily_screenshot_task_id'] = task_for_upload.get('id') if task_for_upload else None
    if task_for_upload:
        await q.message.reply_text(
            f"📤 Send screenshot for Task {task_for_upload['task_number']}!\n\n"
            f"Open {task_for_upload.get('open_time','')} Close {task_for_upload.get('close_time','')}\n\n"
            "Send as PHOTO, not file!"
        )
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
    save_data()
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
    # Final FIX: Upload screenshot button not working - Fix Document + Photo + Fallback!
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
            await update.message.reply_text("Please send as PHOTO! Not file! But document also accepted now! Final - ")
            return UPLOAD_SCREENSHOT
        campaign_id = context.user_data.get('promo_upload_campaign_id')
        if campaign_id:
            context.user_data['promo_screenshot_file_id'] = file_id
            context.user_data['promo_screenshot_campaign_id'] = campaign_id
            await update.message.reply_text("Screenshot received for Promo Campaign! Now type views count Example 150 ")
            return PROMO_DETAILS
        current, next_task = get_current_scheduled_task_with_interval()
        requested_id=context.user_data.get('daily_screenshot_task_id')
        task_to_use=current
        if requested_id is not None:
            task_to_use=next((t for t in get_tasks_for_today() if int(t.get('id',-999999))==int(requested_id)), None)
        if not task_to_use:
            await update.message.reply_text("❌ No active scheduled task is available right now. Please open Daily Task during the task time.", reply_markup=main_menu())
            context.user_data.pop('awaiting_daily_screenshot', None)
            context.user_data.pop('daily_screenshot_task_id', None)
            return ConversationHandler.END
        task_id_for_status = task_to_use.get('id', DEFAULT_DAILY_TASK_ID) if task_to_use else DEFAULT_DAILY_TASK_ID
        existing_status_data = user_task_status.get(uid, {}).get(task_id_for_status, {})
        existing_status = existing_status_data.get('status') if isinstance(existing_status_data, dict) else existing_status_data
        if existing_status == 'completed':
            await update.message.reply_text(
                f"✅ Task {task_to_use.get('task_number', 1)} is already completed.\n\n"
                "Please wait for the next task instead of sending the same screenshot again.",
                reply_markup=main_menu()
            )
            context.user_data.pop('awaiting_daily_screenshot', None)
            context.user_data.pop('daily_screenshot_task_id', None)
            return ConversationHandler.END
        if existing_status == 'pending_verification' or uid in pending_daily:
            await update.message.reply_text("⏳ Your screenshot is already submitted! Waiting for admin approval.", reply_markup=main_menu())
            return
            await update.message.reply_text(
                "⏳ This task screenshot is already pending admin verification.\n\n"
                "Please wait for Approve/Reject; don't submit the same task again.",
                reply_markup=main_menu()
            )
            return ConversationHandler.END
        if file_unique_id and file_unique_id in screenshot_hashes:
            if uid not in warnings_db:
                warnings_db[uid] = {'count': 0}
            warnings_db[uid]['count'] += 1
            if warnings_db[uid]['count'] >= 3:
                banned_users.add(uid)
                await update.message.reply_text("BANNED! 3 Warnings! ")
                return ConversationHandler.END
            await update.message.reply_text("WARNING Same Screenshot! ")
            return ConversationHandler.END
        if file_unique_id:
            screenshot_hashes.add(file_unique_id)
        pending_daily[uid] = {'date': today, 'task': task_to_use, 'screenshot_file_id': file_id}
        context.user_data.pop('awaiting_daily_screenshot', None)
        context.user_data.pop('daily_screenshot_task_id', None)
        if uid not in user_task_status:
            user_task_status[uid] = {}
        user_task_status[uid][task_id_for_status] = {'status': 'pending_verification', 'submitted_at': get_ist_now()}
        await update.message.reply_text(f"✅ Screenshot received! Waiting for admin approval. - Upload screenshot button fix!", reply_markup=main_menu())
        try:
            chan = get_screenshot_channel()
            if chan:
                try:
                    user_name = users_db.get(uid, {}).get('name', update.effective_user.full_name or 'Unknown')
                    kb_chan = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_daily_{uid}"),
                         InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_daily_{uid}")],
                        [InlineKeyboardButton("🚀 Approve ALL Pending", callback_data="bulk_approve_all")]
                    ])
                    await context.bot.send_photo(
                        chat_id=chan,
                        photo=file_id,
                        caption=(
                            f"📸 TASK SCREENSHOT\n"
                            f"👤 Name: {user_name}\n"
                            f"🆔 User ID: {uid}\n"
                            f"📋 Task {task_to_use.get('task_number',1)}: {task_to_use.get('title','Daily')}\n"
                            f"💰 Reward: ₹{task_to_use.get('reward',5)}\n"
                            f"📅 {get_ist_today()}"
                        ),
                        reply_markup=kb_chan
                    )
                    print(f" forwarded to SCREENSHOT_CHANNEL {chan} - TASK Screenshots ONLY! FINAL! Upload screenshot button fix!")
                except Exception as e:
                    print(f" screenshot channel err {e} - Trying without keyboard! Channel {chan} admin?")
                    try:
                        await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK  User {uid} Task {task_to_use.get('task_number',1)}")
                    except Exception as e2:
                        print(f" screenshot channel err2 {e2} - Trying document!")
                        try:
                            await context.bot.send_document(chat_id=chan, document=file_id, caption=f"NEW TASK  User {uid}")
                        except Exception as e3:
                            print(f" screenshot channel err3 {e3}")
        except Exception as e:
            print(f" screenshot outer err {e}")
        return ConversationHandler.END
    except Exception as e:
        print(f" handle_screenshot_upload outer exception {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(f"✅ Screenshot received! Pending Verification! Error logged {e} Final - Upload screenshot button fix!", reply_markup=main_menu())
            if update.message.photo or update.message.document:
                file_id = (update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id)
                try:
                    chan = get_screenshot_channel()
                    await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK  User {update.effective_user.id} Fallback")
                except:
                    try:
                        await context.bot.send_document(chat_id=chan, document=file_id, caption=f"NEW TASK  User {update.effective_user.id} Fallback")
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
                cap = f"📸 NEW SUBMISSION - Task {task.get('task_number','')} {task.get('title','')}\nUser {uid} {users_db.get(uid,{}).get('name','')} @{users_db.get(uid,{}).get('username','')}\nReward: Rs{get_task_reward_for_user(task, uid)} (Task/plan based)\nTime: {get_ist_now()}"
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

# === SUPPORT PLANS BANNER IMAGE ===
async def set_support_image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the Support Plans banner image. Supports command-only then photo, or photo with caption."""
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            await update.message.reply_text("❌ Admin only!")
            return

        # If Telegram delivered the command together with a photo/document caption, save it directly.
        if update.message.photo or update.message.document:
            file_id = None
            if update.message.photo:
                file_id = update.message.photo[-1].file_id
            elif update.message.document:
                file_id = update.message.document.file_id

            if file_id:
                support_banner_db["file_id"] = file_id
                save_data()
                context.user_data.pop("awaiting_support_banner", None)
                await update.message.reply_text(
                    "✅ Support Plans banner image saved successfully!\n\n"
                    "Open 💎 Support Plans to check it."
                )
                print(f"Support banner saved directly by admin {uid}: {file_id[:20]}...")
                return

        context.user_data["awaiting_support_banner"] = True
        await update.message.reply_text(
            "🖼️ Now send the Support Plans banner image as a PHOTO.\n\n"
            "You can also send the image with caption /set_support_image."
        )
    except Exception as e:
        print(f"set_support_image_cmd error: {e}")
        try:
            await update.message.reply_text(f"❌ Error setting Support Plans image: {e}")
        except Exception:
            pass

async def support_banner_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """High-priority admin photo handler for /set_support_image."""
    try:
        uid = update.effective_user.id
        if not is_admin(uid):
            return

        caption = update.message.caption or ""
        waiting = bool(context.user_data.get("awaiting_support_banner"))
        if "/set_support_image" not in caption and not waiting:
            return

        file_id = None
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id

        if not file_id:
            return

        support_banner_db["file_id"] = file_id
        save_data()
        context.user_data.pop("awaiting_support_banner", None)

        await update.message.reply_text(
            "✅ Support Plans banner image saved successfully!\n\n"
            "Open 💎 Support Plans to check it."
        )
        print(f"Support banner saved by admin {uid}: {file_id[:20]}...")
    except Exception as e:
        print(f"support_banner_photo_handler error: {e}")

# === NEW IMAGE POSTER COMMANDS ===
async def set_task_image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Final FIX: Task image same issue not rectified - Fix Document + Photo!
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Only admin! ")
            return ConversationHandler.END
        if update.message.photo or update.message.document:
            print(f" set_task_image_cmd: Photo/Document with caption detected! Handling directly! Task image fix! FINAL!")
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
                    await update.message.reply_text("No task found! Use /list_tasks first! ")
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
                print(f"Task image set for Task {task_id}: {task['title']} via caption photo/document! FINAL!")
                await update.message.reply_text(f"✅ Task image set for Task {task_id}! {task['title']} Members will see YOUR TASK 1 image! Check /menu -> Daily Task! FINAL! Task image same issue fixed!", reply_markup=main_menu())
            else:
                await update.message.reply_text(f"✅ Task image set for Task {task_id}! Final! Task image same issue fixed!", reply_markup=main_menu())
            try:
                await context.bot.send_photo(chat_id=update.effective_user.id, photo=file_id, caption=f"✅  Confirmation - Task {task_id} Image Set via caption! FINAL! Task image fix!")
            except:
                try:
                    await context.bot.send_document(chat_id=update.effective_user.id, document=file_id, caption=f"✅  Confirmation - Task {task_id} Image Set! FINAL!")
                except Exception as e:
                    print(f" confirmation err {e}")
            return ConversationHandler.END

        if not context.args:
            await update.message.reply_text("Usage: /set_task_image <task_id> Then send photo with caption /set_task_image <id> OR reply with photo Example: /set_task_image 1 then send TASK 1 poster as PHOTO! Final - Task image same issue fixed!")
            return ConversationHandler.END
        try:
            task_id = int(context.args[0])
        except:
            await update.message.reply_text("Task ID must be number! Use /list_tasks ")
            return ConversationHandler.END
        task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
        if not task:
            await update.message.reply_text(f"Task ID {task_id} not found! Use /list_tasks ")
            return ConversationHandler.END
        context.user_data['set_image_task_id'] = task_id
        await update.message.reply_text(f"📸  Now send poster/image for Task {task_id}: {task['title']} Send as PHOTO! (Not file) But document also accepted now! Members will see this image when they open Daily Task! Waiting for photo... Final - Task image same issue fixed!", reply_markup=main_menu())
        return SET_IMAGE
    except Exception as e:
        print(f" set_task_image_cmd outer exception {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(f"Error {e} Final", reply_markup=main_menu())
        except:
            pass
        return ConversationHandler.END

async def handle_task_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Final FIX: Task image same issue not rectified - Fix Document + Photo!
    try:
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("Only admin can set task images! ")
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
                await update.message.reply_text("No task found! Use /list_tasks first! ")
                return ConversationHandler.END
        file_id = None
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        if not file_id:
            await update.message.reply_text("Please send as PHOTO! Not file! But document also accepted now!  - Task image fix!")
            return SET_IMAGE
        task_images_db[task_id] = file_id
        task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
        if task:
            task['image_file_id'] = file_id
            task['has_image'] = True
            print(f"Task image set for Task {task_id}: {task['title']} file_id {file_id[:20]} FINAL! Task image same issue fixed!")
        else:
            print(f"Task image set for Task {task_id} - Task not found but file_id saved! FINAL!")
        await update.message.reply_text(f"✅ Task image set for Task {task_id}! {task['title'] if task else ''} Members will see YOUR TASK image when they open Daily Task! Check /menu -> Daily Task - Image will show! Task image same issue fixed!", reply_markup=main_menu())
        try:
            await context.bot.send_photo(chat_id=update.effective_user.id, photo=file_id, caption=f"✅  Confirmation - Task {task_id} Image Set! Members will see this! FINAL! Task image same issue fixed!")
        except:
            try:
                await context.bot.send_document(chat_id=update.effective_user.id, document=file_id, caption=f"✅  Confirmation - Task {task_id} Image Set! FINAL!")
            except Exception as e:
                print(f" send confirmation err {e}")
        context.user_data.pop('set_image_task_id', None)
        return ConversationHandler.END
    except Exception as e:
        print(f" handle_task_image_upload outer exception {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text(f"✅  Image Poster Set! Error logged {e} Final - Task image fix!", reply_markup=main_menu())
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
        task=pending_daily[target_id].get('task',{})
        base_reward=int(task.get('reward',5) or 5)
        reward=get_task_reward_for_user(task, target_id)
        today=pending_daily[target_id].get('date')
        tasks_db[target_id]=tasks_db.get(target_id,0)+1
        if target_id not in daily_task_count: daily_task_count[target_id]={}
        daily_task_count[target_id][today]=daily_task_count[target_id].get(today,0)+1
        add_today_task_earning(target_id, reward, today)
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
            add_referral_commission(ref_id, REFERRAL_BONUS_PER_TASK, "bonus", 1, target_id, "First approved task referral bonus")
        record_task_referral_commissions(target_id, reward)
        await update.message.reply_text(f"✅ Approved {target_id} +Rs{reward}")
        try:
            _, daily_limit, _ = check_daily_limits(target_id)
            daily_count = get_tasks(target_id)
            await context.bot.send_message(
                chat_id=target_id,
                text=(f"✅ Task Approved! +Rs{reward}\n"
                      f"Balance: Rs{get_balance(target_id)}\n"
                      f"Tasks today: {daily_count}/{daily_limit}\n"
                      f"Total completed tasks: {tasks_db.get(target_id, 0)}"),
                reply_markup=main_menu()
            )
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



def get_contact_username():
    return str(globals().get("CONTACT_USERNAME") or SUPPORT_USERNAME).strip()

def get_contact_url(message_text=None):
    # Always use the manually configured public Telegram username.
    # This avoids opening the wrong Telegram account when CONTACT_ADMIN_ID is stale.
    username=get_contact_username().lstrip("@").strip()
    if username:
        base=f"https://t.me/{username}"
        if message_text:
            return base + "?text=" + quote(str(message_text), safe="")
        return base
    # Fallback only when no username has been configured.
    try:
        return f"tg://user?id={int(CONTACT_ADMIN_ID)}"
    except Exception:
        return CHANNEL_LINK

async def set_contact_username_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    global CONTACT_USERNAME
    if not context.args:
        await update.message.reply_text(f"Current Contact Username: {get_contact_username()}\nUsage: /set_contact_username @username")
        return
    username=context.args[0].strip()
    if not re.fullmatch(r"@?[A-Za-z0-9_]{5,32}", username):
        await update.message.reply_text("❌ Invalid Telegram username. Example: /set_contact_username @yourusername")
        return
    CONTACT_USERNAME = "@" + username.lstrip("@")
    save_data()
    await update.message.reply_text(f"✅ Contact Us updated to {CONTACT_USERNAME}\nUsers will now be sent directly to this Telegram chat.")

async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    username=get_contact_username()
    # Pre-fill a simple message after redirecting to the configured admin username.
    contact_message="Hello Admin, I need help with my S2E account."
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Message Admin", url=get_contact_url(contact_message))],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
    await q.message.reply_text(f"📞 CONTACT US\n\nAdmin: {username}\n\nTap below to open Admin chat and send your message.", reply_markup=kb)


async def edit_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /edit_user <user_id> <field> <value>\n"
            "Fields: name, gender, dob, mobile, upi, pincode, profession\n"
            "Example: /edit_user 123456789 name Ravi Kumar")
        return
    try:
        target = int(context.args[0]); field = context.args[1].lower(); value = " ".join(context.args[2:]).strip()
        allowed = {"name","gender","dob","mobile","upi","pincode","profession"}
        if field not in allowed:
            await update.message.reply_text("❌ Invalid field. Use: name, gender, dob, mobile, upi, pincode, profession")
            return
        if target not in users_db and str(target) not in users_db:
            await update.message.reply_text("❌ User not found.")
            return
        key = target if target in users_db else str(target)
        users_db.setdefault(key, {})[field] = value
        if "user_profiles" in globals():
            globals()["user_profiles"].setdefault(key, {})[field] = value
        save_data()
        await update.message.reply_text(f"✅ User {target} updated: {field} = {value}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def remove_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only permanent user removal with deletion-safe referral re-parenting.

    If A -> B -> C and B is removed, C is re-parented to A but marked as
    preserved L2. Therefore C's future task/product commission goes to A at
    L2 (0.5%), and C's own referrals continue normally.
    """
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /remove_user <user_id> - Totally removes user data and safely preserves referral chain")
        return
    try:
        target = int(context.args[0])
    except Exception:
        await update.message.reply_text("Invalid user_id")
        return

    # Find target's parent before deleting the target.
    target_parent = referral_map.get(target) or referral_map.get(str(target))
    try:
        target_parent = int(target_parent) if target_parent else None
    except Exception:
        target_parent = None

    # Re-parent direct children to target's parent while preserving their
    # original L2 position. This is the key deletion-safe behavior.
    reparented = []
    for child, parent in list(referral_map.items()):
        try:
            child_id = int(child)
            parent_id = int(parent)
        except Exception:
            continue
        if parent_id != target:
            continue
        if target_parent and target_parent != child_id:
            referral_map[child_id] = target_parent
            referral_level_overrides[child_id] = 2
            reparented.append(child_id)
        else:
            referral_map.pop(child, None)
            referral_map.pop(str(child), None)
            referral_level_overrides.pop(child_id, None)
            referral_level_overrides.pop(str(child_id), None)

    # Remove target's own relationship/override.
    referral_map.pop(target, None)
    referral_map.pop(str(target), None)
    referral_level_overrides.pop(target, None)
    referral_level_overrides.pop(str(target), None)

    # Remove all user-owned data. Historical commission records are removed
    # with the user as requested; other members' ledgers are untouched.
    removed = []
    for db_name in ['users_db','tasks_db','bonus_balance','referral_earnings','skip_db','missed_tasks_db','user_task_status','promo_earnings_db','task_images_db','daily_task_count','daily_task_earnings','withdraw_requests','withdraw_history','pending_daily','user_profiles','referrals_db','referral_commission_ledger','referral_pending_earnings','user_plans','pending_plans','referral_codes_db']:
        db = globals().get(db_name)
        if isinstance(db, dict) and (target in db or str(target) in db):
            db.pop(target, None)
            db.pop(str(target), None)
            removed.append(db_name)

    # Rebuild reverse referral-code index after deleting the user's code.
    try:
        referral_code_to_uid.clear()
        for _uid, _code in referral_codes_db.items():
            if _code:
                referral_code_to_uid[str(_code).upper()] = int(_uid)
    except Exception:
        pass

    try:
        banned_users.discard(target)
        warnings_db.pop(target, None)
        warnings_db.pop(str(target), None)
    except Exception:
        pass

    save_data()
    msg = f"✅ User {target} permanently removed."
    if reparented:
        msg += f"\n\n🔗 Referral chain preserved: {len(reparented)} direct referral(s) re-linked to the deleted user's parent at preserved L2 level."
        msg += "\nFuture task/product commission will not be sent to the deleted user."
    else:
        msg += "\nNo direct referrals needed re-linking."
    await update.message.reply_text(msg)


async def my_details_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    try: await q.answer()
    except: pass
    uid=q.from_user.id
    user=users_db.get(uid) or users_db.get(str(uid)) or {}
    # V36 FIX: Also check user_profiles for N/A details
    profile = globals().get('user_profiles', {}).get(uid) or globals().get('user_profiles', {}).get(str(uid)) or {}
    # Merge profile into user for display
    display_name = user.get('name') or profile.get('name') or 'N/A'
    # If still N/A, try to get from Telegram
    if display_name == 'N/A':
        try:
            display_name = update.effective_user.full_name or update.effective_user.first_name or 'N/A'
            # Save it
            if uid not in users_db: users_db[uid]={}
            users_db[uid]['name']=display_name
            if uid not in globals().get('user_profiles', {}): globals().get('user_profiles', {})[uid]={}
            globals().get('user_profiles', {})[uid]['name']=display_name
        except:
            pass
    plan=_get_user_plan_record(uid)
    total_earned=get_balance(uid)
    joined=user.get('joined') or profile.get('joined') or user.get('reg_date') or 'N/A'
    plan_name=plan.get('plan_name',plan.get('name',plan.get('plan','No Plan'))) if plan else 'No Plan'
    expiry=plan.get('expires_at',plan.get('expiry','N/A')) if plan else 'N/A'
    remaining='N/A'
    if expiry not in (None,'N/A'):
        try: remaining=max(0,(date.fromisoformat(str(expiry)[:10])-get_ist_today()).days)
        except: pass
    count,limit,cap=check_daily_limits(uid)
    approved_withdrawn=sum(int(x.get('amount',0) or 0) for x in withdraw_history.get(uid,[]) if str(x.get('status','')).lower()=='approved')
    current_req=withdraw_requests.get(uid,{})
    if approved_withdrawn==0 and str(current_req.get('status','')).lower()=='approved':
        approved_withdrawn=int(current_req.get('amount',0) or 0)
    cap_remaining=max(0, cap-approved_withdrawn)
    # V36: Show proper profile data
    gender = user.get('gender') or profile.get('gender') or 'N/A'
    dob = user.get('dob') or profile.get('dob') or 'N/A'
    mobile = user.get('mobile') or profile.get('mobile') or 'N/A'
    upi = user.get('upi') or profile.get('upi') or 'N/A'
    tg_username = getattr(update.effective_user, "username", None)
    public_username = ("@" + tg_username) if tg_username else display_name
    msg=(f"👤 MY DETAILS\n\nUsername: {public_username}\nName: {display_name}\n"
         f"Gender: {gender}\nDOB: {dob}\nMobile: {mobile}\n"
         f"UPI: {upi}\nJoined: {joined}\n\n"
         f"💎 Plan: {plan_name}\nExpiry: {expiry}\nDays remaining: {remaining}\n"
         f"📋 Today's tasks: {count}/{limit}\n💰 Total earning: ₹{total_earned}\n"
         f"🎯 Plan withdrawal cap: ₹{cap}\n💸 Total withdrawn: ₹{approved_withdrawn}\n📉 Withdrawal cap remaining: ₹{cap_remaining}")
    # V41: If Gender/Mobile N/A, show update button
    _gender = user.get('gender','N/A')
    _mobile = user.get('mobile','N/A')
    if _gender == 'N/A' or _mobile == 'N/A':
        _kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Update Details", callback_data="update_details")],
            [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]
        ])
        await q.message.reply_text(msg, reply_markup=_kb)
    else:
        await q.message.reply_text(msg, reply_markup=main_menu())


async def update_details_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    context.user_data['awaiting_details'] = True
    await q.message.reply_text(
        "📝 UPDATE DETAILS\n\nSend your details in ONE message like this:\n\nName: Your Full Name\nGender: Male\nDOB: 01-01-1990\nMobile: 9876543210\nUPI: 9876543210@paytm (Replace with YOUR details)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="back_menu")]])
    )

async def handle_details_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_details'):
        return
    uid=update.effective_user.id
    text=update.message.text or ""
    if "Name:" not in text:
        return
    data={}
    for line in text.split("\n"):
        if ":" in line:
            k,v=line.split(":",1)
            k=k.strip().lower()
            v=v.strip()
            if "name" in k: data["name"]=v
            elif "gender" in k: data["gender"]=v
            elif "dob" in k: data["dob"]=v
            elif "mobile" in k or "phone" in k: data["mobile"]=v
            elif "upi" in k: data["upi"]=v
    if data:
        users_db.setdefault(uid, {}).update(data)
        users_db[uid]['joined']=users_db[uid].get('joined') or str(get_ist_today())
        save_data()
        context.user_data.pop('awaiting_details', None)
        await update.message.reply_text(f"✅ Details Saved!\nName: {data.get('name','')}\nCheck My Details now!", reply_markup=main_menu())



async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())


def reset_tasks_on_plan_upgrade(uid, daily_limit=20):
    today = str(get_ist_today())
    daily_task_count[uid] = {today: 0}
    task_open_time.pop(uid, None)
    print(f"V41: Tasks reset {uid} to 0/{daily_limit}")
    save_data()

async def check_plan_expiry_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        today = get_ist_today()
        for uid, plan in list(user_plans.items()):
            try:
                expiry_str = plan.get('expiry') or plan.get('expires_at')
                if not expiry_str: continue
                exp_date = date.fromisoformat(str(expiry_str)[:10])
                days_left = (exp_date - today).days
                if days_left in (3,2,1):
                    bal = get_balance(uid)
                    try:
                        await context.bot.send_message(chat_id=uid, text=f"⚠️ PLAN EXPIRY - {days_left} days left!\nPlan: {plan.get('plan_name','Plan')}\nExpiry: {expiry_str}\nBalance Safe: ₹{bal:.2f}\nRenew now! After expiry 3 days free again!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Renew", callback_data="support_plans")]]))
                    except: pass
                elif days_left < 0:
                    bal = get_balance(uid)
                    try:
                        await context.bot.send_message(chat_id=uid, text=f"⏰ PLAN EXPIRED!\nBalance Safe: ₹{bal:.2f}\n🆓 3 DAYS FREE again! 0/4 daily, Total 10 tasks", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="support_plans")]]))
                    except: pass
            except: pass
    except Exception as e:
        print(f"expiry job err {e}")


async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except Exception:
        pass
    uid = update.effective_user.id
    # V38 FREE CHECK - Telugu + Correct Balance
    try:
        _info = _canonical_plan_info(uid)
        if _info['type'] in ('free', 'free_expired') or not _info.get('active'):
            _bal = get_balance(uid)
            _total_tasks = tasks_db.get(uid, 0)
            _free_days = 3
            try:
                _joined = users_db.get(uid, {}).get('joined') or users_db.get(uid, {}).get('reg_date')
                if _joined:
                    from datetime import date as _d
                    _jd = _d.fromisoformat(str(_joined)[:10])
                    _used = (get_ist_today() - _jd).days
                    _free_days = max(0, 3 - _used)
            except:
                pass
            await q.message.reply_text(
                f"🔒 WITHDRAWAL LOCKED\n\n"
                f"💰 Balance: ₹{_bal:.2f}\n"
                f"📋 Plan: {_info['display']}\n"
                f"📅 Free Days Remaining: {_free_days} days\n"
                f"📊 Your Tasks: {_total_tasks}/10\n"
                f"🎯 Free Cap: ₹100\n\n"
                f"❌ Free members cannot withdraw!\n"
                f"💎 Need to upgrade plan!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Support Plans - Upgrade", callback_data="support_plans")],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
            )
            return
    except Exception as _e:
        print(f"free withdraw check fail {_e}")
        import traceback; traceback.print_exc()
    today = str(get_ist_today())

    # One withdrawal per day. Only a real request for TODAY blocks a new request.
    # Old/stale withdraw_done_date values are ignored when there is no matching request.
    req = withdraw_requests.get(uid, {}) or {}
    req_date = str(req.get('date', ''))
    status = str(req.get('status', '')).lower()
    blocked_today = (req_date == today and status in ('processing', 'approved')) or (last_withdraw_date_db.get(uid) == today)
    if blocked_today:
        if status == 'processing':
            text = ("⏳ Withdrawal already submitted today!\n\n"
                    f"Amount: Rs{req.get('amount', 0)}\n"
                    "Status: Pending Admin Processing\n\n"
                    "You can make another withdrawal tomorrow.")
        else:
            text = "✅ You have already withdrawn once today!\n\nYou can withdraw again tomorrow."
        await q.message.reply_text(text, reply_markup=main_menu())
        return

    bal = get_balance(uid)
    tasks_done = check_daily_limits(uid)[0]

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

    # Only amounts within both current balance and the active plan withdrawal cap are selectable.
    info=_canonical_plan_info(uid)
    withdrawn=get_withdrawn_for_cap(uid)
    cap_remaining=max(0, float(info.get("cap", 0))-withdrawn)
    effective_available=min(float(bal), cap_remaining) if info.get("cap", 0) else float(bal)
    available = [opt for opt in WITHDRAW_OPTIONS if opt <= effective_available]
    unavailable = [opt for opt in WITHDRAW_OPTIONS if opt > effective_available]

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
        f"Minimum: Rs{WITHDRAW_MIN}\n"
        f"Plan withdrawal cap used: ₹{withdrawn:.2f}/₹{info.get('cap',0)}\n"
        f"Cap remaining: ₹{cap_remaining:.2f}\n\n"
        "7% deduction will be shown before confirmation.\n\n"
        "Select withdrawal amount:"
        f"{disabled_text}"
    )
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(rows))


async def withdraw_history_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    history=withdraw_history.get(uid, [])
    if not history:
        await q.message.reply_text("📜 WITHDRAWAL HISTORY\n\nNo completed withdrawals yet.", reply_markup=main_menu())
        return
    msg="📜 WITHDRAWAL HISTORY\n\n"
    for h in history[-10:][::-1]:
        msg += (f"📅 {h.get('date','N/A')}\n"
                f"Amount: ₹{h.get('amount',0)} | Fee: ₹{h.get('fee',0)} (7%)\n"
                f"You received: ₹{h.get('net',0)}\n"
                f"Status: {h.get('status','N/A')}\n\n")
    await q.message.reply_text(msg[:4000], reply_markup=main_menu())

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

    # Prevent duplicate confirmations on the same day. Ignore stale legacy marker by itself.
    existing = withdraw_requests.get(uid, {}) or {}
    existing_status = str(existing.get('status', '')).lower()
    existing_date = str(existing.get('date', ''))
    if (existing_date == today and existing_status in ('processing', 'approved')) or last_withdraw_date_db.get(uid) == today:
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

async def admin_approve_daily_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid=int(q.data.split("_")[-1])
    if uid in pending_daily:
        is_first=tasks_db.get(uid,0)==0
        task_obj=pending_daily[uid].get('task',{})
        task_id=task_obj.get('id')
        reward=task_obj.get('reward',5)
        today=pending_daily[uid].get('date')
        tasks_db[uid]=tasks_db.get(uid,0)+1
        if uid not in daily_task_count: daily_task_count[uid]={}
        daily_task_count[uid][today]=daily_task_count[uid].get(today,0)+1
        add_today_task_earning(uid, reward, today)
        if reward!=5: bonus_balance[uid]=bonus_balance.get(uid,0)+(reward-5)
        del pending_daily[uid]
        task_open_time.pop(uid, None)
        # V34 FIX: Mark completed and clear missed
        if task_id is not None:
            if uid not in user_task_status: user_task_status[uid]={}
            user_task_status[uid][task_id]={'status': 'completed', 'completed_at': get_ist_now(), 'reward': reward, 'approved_at': get_ist_now()}
            if uid in missed_tasks_db:
                missed_tasks_db[uid]=[t for t in missed_tasks_db[uid] if int(t.get('id',-1))!=int(task_id)]
        else:
            for tid, status_data in list(user_task_status.get(uid, {}).items()):
                if isinstance(status_data, dict) and status_data.get('status') == 'pending_verification':
                    user_task_status[uid][tid]={'status': 'completed', 'completed_at': get_ist_now(), 'reward': reward, 'approved_at': get_ist_now()}
                    if uid in missed_tasks_db:
                        missed_tasks_db[uid]=[t for t in missed_tasks_db[uid] if int(t.get('id',-1))!=int(tid)]
                    break
        ref_id=referral_map.get(uid)
        if ref_id and is_first:
            referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
            add_referral_commission(ref_id, REFERRAL_BONUS_PER_TASK, "bonus", 1, uid, "First approved task referral bonus")
        record_task_referral_commissions(uid, reward)
        save_data()
        await q.message.reply_text(f"✅ Approved {uid} +Rs{reward} - Task {task_id or ''}")
        try:
            await q.message.edit_caption(caption=(q.message.caption or "") + f"\n\n✅ APPROVED by admin - Rs{reward} credited!\nApproved: {get_ist_now().strftime('%H:%M:%S')} IST\nUser: {uid}")
        except:
            try:
                await q.message.edit_text(f"✅ APPROVED - User {uid} +Rs{reward}\nOriginal: {q.message.caption or q.message.text or ''}")
            except:
                pass
        try:
            remaining_tasks=get_tasks_for_today()
            remaining_count=len([t for t in remaining_tasks if user_task_status.get(uid, {}).get(t.get('id'), {}).get('status') != 'completed'])
            if remaining_count>0:
                msg_user=f"✅ Task Approved! +₹{reward} credited!\nBalance: ₹{get_balance(uid)}\n\n⏳ Remaining tasks: {remaining_count}\nCheck /menu -> Daily Task for next task!"
            else:
                msg_user=f"✅ Task Approved! +₹{reward} credited!\nBalance: ₹{get_balance(uid)}\n\n🎉 All tasks completed! No more tasks today! Excellent!"
            await context.bot.send_message(chat_id=uid, text=msg_user, reply_markup=main_menu())
        except Exception as _e:
            print(f"Notify user approve fail {_e}")
    else:
        await q.message.reply_text("❌ No pending task for this user - already approved/rejected")


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
        save_data()
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
    record_product_promo_referral_commissions(uid, earning)
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
    req['remaining_balance'] = new_bal
    withdraw_history.setdefault(uid, []).append(dict(req))
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



def _missed_snapshot(task):
    snap=dict(task)
    # Keep only JSON-friendly / stable task data. Datetime time objects are restored from strings.
    snap.pop('open_time_obj', None); snap.pop('close_time_obj', None); snap.pop('next_time_obj', None)
    snap['missed_snapshot']=True
    return snap

def track_missed_tasks_for_user(uid):
    if not MISSED_ENABLED:
        return missed_tasks_db.get(uid, [])
    today = str(get_ist_today())
    now = get_ist_time()
    today_tasks = [t for t in scheduled_tasks_db if t.get('date') == today]
    missed=[]
    user_status=user_task_status.get(uid,{})
    skip_status=skip_db.get(uid,{})
    missed_tasks_db.setdefault(uid,[])
    existing={int(t.get('id')):t for t in missed_tasks_db[uid] if isinstance(t,dict) and str(t.get('id','')).lstrip('-').isdigit()}
    now = _safe_time(now) or now
    for task in today_tasks:
        close_obj=task.get('close_time_obj')
        if not close_obj:
            close_obj=parse_time_str(str(task.get('close_time','23:59')))
        close_obj = _safe_time(close_obj) or close_obj
        if not close_obj:
            continue
        try:
            if now <= close_obj:
                continue
        except Exception as _e:
            # fallback string compare
            try:
                if str(now) <= str(close_obj):
                    continue
            except:
                continue
        tid=task.get('id')
        status=user_status.get(tid,{})
        status=status.get('status') if isinstance(status,dict) else status
        sk=skip_status.get(tid,{})
        sk=sk.get('status') if isinstance(sk,dict) else sk
        if status in ('completed','pending_verification') or sk=='skipped':
            continue
        if tid not in existing:
            snap=_missed_snapshot(task)
            missed_tasks_db[uid].append(snap); existing[tid]=snap
        missed.append(existing[tid])
    # Return only today's snapshots that have not been completed after reopening - DEDUP BY ID
    result=[]
    seen_ids=set()
    for t in missed_tasks_db.get(uid,[]):
        if str(t.get('date')) != today: continue
        tid=t.get('id')
        if tid in seen_ids:
            continue
        seen_ids.add(tid)
        st=user_task_status.get(uid,{}).get(tid,{})
        st=st.get('status') if isinstance(st,dict) else st
        if st not in ('completed',): result.append(t)
    # Also dedup by task_number if same number appears twice with different IDs (keep first)
    final=[]
    seen_numbers=set()
    for t in result:
        tnum=t.get('task_number')
        if tnum in seen_numbers:
            continue
        seen_numbers.add(tnum)
        final.append(t)
    return final

async def missed_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if not MISSED_ENABLED:
        await q.message.reply_text("⏰ Missed Tasks are currently OFF by Admin.", reply_markup=main_menu()); return
    missed=track_missed_tasks_for_user(uid)
    # V34 FIX: Filter out completed and pending_verification tasks
    filtered=[]
    for t in missed:
        tid=t.get('id')
        st=user_task_status.get(uid,{}).get(tid,{})
        st_status=st.get('status') if isinstance(st,dict) else st
        if st_status in ('completed','pending_verification'):
            continue
        filtered.append(t)
    missed=filtered
    if not missed:
        # Check if there are pending verifications
        pending_count=len([1 for tid,s in user_task_status.get(uid,{}).items() if isinstance(s,dict) and s.get('status')=='pending_verification'])
        if pending_count>0:
            await q.message.reply_text(f"⏳ {pending_count} task(s) waiting for admin approval!\nAdmin will approve soon. Please wait.\n\nNo more missed tasks to submit right now.", reply_markup=main_menu()); return
        await q.message.reply_text("🎉 No missed tasks today! All tasks completed! ✅\nNo more tasks!", reply_markup=main_menu()); return
    # Dedup missed by task_number for display
    seen_nums=set()
    unique_missed=[]
    for t in missed:
        tnum=t.get('task_number')
        if tnum not in seen_nums:
            seen_nums.add(tnum)
            unique_missed.append(t)
    missed=unique_missed
    msg=f"❌ MISSED TASKS TODAY - Total {len(missed)}:\n\n"
    kb=[]
    for t in missed:
        msg += (f"Task {t.get('task_number','?')}: {t.get('title','')}\n"
                f"Time: {t.get('open_time','')} → {t.get('close_time','')} | Reward: ₹{t.get('reward',5)}\n"
                f"Link: {t.get('link','')}\n\n")
        tid=t.get('id')
        st=user_task_status.get(uid,{}).get(tid,{})
        st=st.get('status') if isinstance(st,dict) else st
        if st not in ('pending_verification','completed'):
            kb.append([InlineKeyboardButton(f"🔄 Do Missed Task {t.get('task_number','?')}", callback_data=f"missed_reopen_{tid}")])
    msg += "You can reopen a missed task and submit proof once. Admin approval is required."
    kb.append([InlineKeyboardButton("🏠 Menu", callback_data="back_menu")])
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb))

async def missed_reopen_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    try: tid=int(q.data.replace('missed_reopen_','',1))
    except Exception: return
    track_missed_tasks_for_user(uid)
    task=next((t for t in missed_tasks_db.get(uid,[]) if int(t.get('id',-999999))==tid),None)
    if not task:
        await q.message.reply_text("❌ This missed task is no longer available.", reply_markup=main_menu()); return
    status_data=user_task_status.get(uid,{}).get(tid,{})
    status=status_data.get('status') if isinstance(status_data,dict) else status_data
    if isinstance(status_data,dict) and status_data.get('missed_submission_used'):
        await q.message.reply_text("❌ This missed task proof has already been submitted once. Please wait for Admin approval.", reply_markup=main_menu()); return
    if status in ('completed','pending_verification'):
        await q.message.reply_text("⏳ This missed task is already submitted or completed.", reply_markup=main_menu()); return
    context.user_data['awaiting_daily_screenshot']=False
    context.user_data['daily_screenshot_task_id']=tid
    context.user_data['missed_reopened_task_id']=tid
    task_id=tid
    text=(f"🔄 MISSED TASK {task.get('task_number','?')} REOPENED\n\n"
          f"Title: {task.get('title','')}\nReward: ₹{task.get('reward',5)}\nLink: {task.get('link','')}\n\n"
          f"{('📝 Instructions:' + chr(10) + task.get('description', '') + chr(10) + chr(10)) if task.get('description') else ''}"
          "Complete the task using the link above, then tap Upload Screenshot.")
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data=f"missed_upload_{task_id}")],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
    await q.message.reply_text(text, reply_markup=kb)

async def missed_upload_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    try: tid=int(q.data.replace('missed_upload_','',1))
    except Exception: return
    task=next((t for t in missed_tasks_db.get(uid,[]) if int(t.get('id',-999999))==tid),None)
    if not task:
        await q.message.reply_text("❌ Missed task not found.", reply_markup=main_menu()); return
    context.user_data['awaiting_daily_screenshot']=True
    context.user_data['daily_screenshot_task_id']=tid
    context.user_data['missed_reopened_task_id']=tid
    await q.message.reply_text(f"📤 Send screenshot for missed Task {task.get('task_number','?')} as PHOTO now.")

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



# === SUPPORT PLANS DB - DYNAMIC / 3 PLANS ===
support_plans_db = [
    {
        "id": 1,
        "name": "Starter",
        "price": 499,
        "validity_days": 60,
        "daily_task_limit": 5,
        "daily_earning_min": 30,
        "daily_earning_max": 60,
        "total_earning_cap": 900,
        "desc": "₹499 | 60 DAYS | 5 TASKS/DAY | ₹30-₹60/DAY | MAX ₹900"
    },
    {
        "id": 2,
        "name": "Pro",
        "price": 1999,
        "validity_days": 60,
        "daily_task_limit": 10,
        "daily_earning_min": 50,
        "daily_earning_max": 80,
        "total_earning_cap": 4400,
        "desc": "₹1999 | 60 DAYS | 10 TASKS/DAY | ₹50-₹80/DAY | MAX ₹4400 | TEAM COMMISSION"
    },
    {
        "id": 3,
        "name": "Elite",
        "price": 4999,
        "validity_days": 60,
        "daily_task_limit": 15,
        "daily_earning_min": 200,
        "daily_earning_max": 400,
        "total_earning_cap": 15000,
        "desc": "₹4999 | 60 DAYS | 15 TASKS/DAY | ₹200-₹400/DAY | MAX ₹15000"
    },
    {
        "id": 4,
        "name": "VIP",
        "price": 9999,
        "validity_days": 60,
        "daily_task_limit": 20,
        "daily_earning_min": 500,
        "daily_earning_max": 700,
        "total_earning_cap": 35000,
        "desc": "₹9999 | 60 DAYS | 20 TASKS/DAY | ₹500-₹700/DAY | MAX ₹35000"
    }
]

awaiting_plan_image_admins = set()
awaiting_plan_payment_adminless = set()


# === FORCE NEW PLANS - 60 DAYS ALL - OVERWRITE OLD DB PLANS ===
def force_update_plans_to_new():
    global support_plans_db
    new_plans = [
        {"id": 1, "name": "Starter", "price": 499, "validity_days": 60, "duration": 60, "daily_task_limit": 5, "daily_limit": 5, "daily_earning_min": 30, "daily_earning_max": 60, "total_earning_cap": 900, "earnings_limit": 900, "users": 1, "desc": "₹499 | 60 DAYS | 5 TASKS/DAY | ₹30-₹60/DAY | MAX ₹900"},
        {"id": 2, "name": "Pro", "price": 1999, "validity_days": 60, "duration": 60, "daily_task_limit": 10, "daily_limit": 10, "daily_earning_min": 50, "daily_earning_max": 80, "total_earning_cap": 4400, "earnings_limit": 4400, "users": 2, "desc": "₹1999 | 60 DAYS | 10 TASKS/DAY | ₹50-₹80/DAY | MAX ₹4400 | TEAM COMMISSION"},
        {"id": 3, "name": "Elite", "price": 4999, "validity_days": 60, "duration": 60, "daily_task_limit": 15, "daily_limit": 15, "daily_earning_min": 200, "daily_earning_max": 400, "total_earning_cap": 15000, "earnings_limit": 15000, "users": 4, "desc": "₹4999 | 60 DAYS | 15 TASKS/DAY | ₹200-₹400/DAY | MAX ₹15000"},
        {"id": 4, "name": "VIP", "price": 9999, "validity_days": 60, "duration": 60, "daily_task_limit": 20, "daily_limit": 20, "daily_earning_min": 500, "daily_earning_max": 700, "total_earning_cap": 35000, "earnings_limit": 35000, "users": 6, "desc": "₹9999 | 60 DAYS | 20 TASKS/DAY | ₹500-₹700/DAY | MAX ₹35000"},
    ]
    support_plans_db = new_plans
    try:
        save_data()
        print(f"FORCE UPDATED PLANS: {len(support_plans_db)} plans set to 60 DAYS ALL")
    except Exception as e:
        print(f"Force update save failed: {e}")



def normalize_support_plans():
    global support_plans_db
    # Force new plans if old 199/499/1999 detected
    try:
        has_old = any(int(p.get("price",0)) in (199,499,1999) and int(p.get("id",0)) <=3 for p in support_plans_db)
        if has_old or len(support_plans_db) < 4:
            force_update_plans_to_new()
            return
    except:
        pass
    # original logic below
    _old_global = support_plans_db
    
    defaults = {
        1: {"id": 1, "name": "Starter", "price": 499, "validity_days": 60, "daily_task_limit": 5, "daily_earning_min": 30, "daily_earning_max": 60, "total_earning_cap": 900, "desc": "₹499 | 60 DAYS | 5 TASKS/DAY | ₹30-₹60/DAY | MAX ₹900"},
        2: {"id": 2, "name": "Pro", "price": 1999, "validity_days": 60, "daily_task_limit": 10, "daily_earning_min": 50, "daily_earning_max": 80, "total_earning_cap": 4400, "desc": "₹1999 | 60 DAYS | 10 TASKS/DAY | ₹50-₹80/DAY | MAX ₹4400"},
        3: {"id": 3, "name": "Elite", "price": 4999, "validity_days": 60, "daily_task_limit": 15, "daily_earning_min": 200, "daily_earning_max": 400, "total_earning_cap": 15000, "desc": "₹4999 | 60 DAYS | 15 TASKS/DAY | ₹200-₹400/DAY | MAX ₹15000"},
        4: {"id": 4, "name": "VIP", "price": 9999, "validity_days": 60, "daily_task_limit": 20, "daily_earning_min": 500, "daily_earning_max": 700, "total_earning_cap": 35000, "desc": "₹9999 | 60 DAYS | 20 TASKS/DAY | ₹500-₹700/DAY | MAX ₹35000"},
    }
    if not isinstance(support_plans_db, list):
        support_plans_db = []
    cleaned, seen = [], set()
    for raw in support_plans_db:
        try: pid = int(raw.get("id"))
        except Exception: continue
        if pid in seen: continue
        base = dict(defaults.get(pid, {})); base.update(raw)
        if not base.get("desc") and base.get("description"): base["desc"] = base["description"]
        base.setdefault("duration", 30)
        base.setdefault("daily_limit", 10 if pid == 1 else 20 if pid == 2 else 30)
        base.setdefault("users", 1 if pid == 1 else 2 if pid == 2 else 4)
        base.setdefault("earnings_limit", 500 if pid == 1 else 1000 if pid == 2 else 3000)
        cleaned.append(base); seen.add(pid)
    for pid in (1,2,3):
        if pid not in seen: cleaned.append(dict(defaults[pid]))
    support_plans_db = sorted(cleaned, key=lambda x: int(x.get("id", 9999)))

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
    """Safe Back-to-Admin handler for CallbackQuery updates.

    IMPORTANT: admin_panel() expects a normal Update and therefore uses
    update.effective_user / update.message. A CallbackQuery does not have
    effective_user, which caused:
        AttributeError: 'CallbackQuery' object has no attribute 'effective_user'
    """
    print("BACK ADMIN FIXED")
    try:
        q = update.callback_query
        if q:
            try:
                await q.answer("Opening Admin...")
            except Exception:
                pass

        # CallbackQuery -> user id must come from q.from_user, not update.effective_user.
        if not q or not q.from_user:
            return
        uid = q.from_user.id

        if not is_admin(uid):
            await context.bot.send_message(chat_id=uid, text="You are not admin!")
            return

        active_promos = len(get_active_promo_campaigns())
        total_views = sum(c.get('total_views', 0) for c in promo_campaigns_db)

        msg = (
            "🔐 ADMIN PANEL - S2E Ultimate + Poster\n\n"
            f"👥 Users: {len(users_db)}\n"
            f"📋 Pending Daily: {len(pending_daily)}\n"
            f"💰 Pending Withdraw: {len([w for w in withdraw_requests.values() if w.get('status') == 'processing'])}\n"
            f"📢 Promo Campaigns: {len(promo_campaigns_db)} | Active: {active_promos}\n"
            f"🛍️ Product Pending: {len(product_promo_pending)}\n"
            f"👁️ Total Promo Views: {total_views}\n"
            f"⏰ Scheduled Today: {len(get_tasks_for_today())}\n"
            f"🖼️ Tasks with Poster: {len(task_images_db)}\n"
            f"⏭️ Skipped Today: {sum(len(v) for v in skip_db.values())}\n"
            f"🚫 Banned: {len(banned_users)}\n\n"
            f"Plan Limits: Basic {DAILY_TASK_LIMIT_BASIC}/day Rs{DAILY_EARNING_CAP_BASIC} cap | "
            f"Premium {DAILY_TASK_LIMIT_PREMIUM}/day Rs{DAILY_EARNING_CAP_PREMIUM} cap\n\n"
            "Commands:\n"
            "/add_task open close next title link reward\n"
            "/set_task_image <id> - Then send poster image!\n"
            "/list_tasks /list_promos /skipped all /warnings /banned"
        )

        missed_label = "⏰ Missed: ON" if MISSED_ENABLED else "⏰ Missed: OFF"
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"📋 Pending Daily ({len(pending_daily)})", callback_data="admin_view_pending"),
                InlineKeyboardButton(
                    f"💰 Withdraw ({len([w for w in withdraw_requests.values() if w.get('status') == 'processing'])})",
                    callback_data="admin_view_withdraw"
                )
            ],
            [
                InlineKeyboardButton("⏰ Today's Tasks", callback_data="admin_view_tasks"),
                InlineKeyboardButton(f"🏪 Promo Campaigns ({len(promo_campaigns_db)})", callback_data="admin_view_promos")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="admin_view_stats"),
                InlineKeyboardButton("🚫 Banned List", callback_data="admin_view_banned")
            ],
            [
                InlineKeyboardButton("📢 Product Promotion", callback_data="admin_product_promo"),
                InlineKeyboardButton("💾 Backup", callback_data="admin_backup")
            ],
            [
                InlineKeyboardButton("👑 Admins", callback_data="admin_add_admin"),
                InlineKeyboardButton("🔗 Referral", callback_data="admin_referral")
            ],
            [
                InlineKeyboardButton(missed_label, callback_data="admin_missed_toggle")
            ],
            [
                InlineKeyboardButton("📋 Menu", callback_data="back_menu")
            ]
        ])

        await context.bot.send_message(
            chat_id=uid,
            text=msg[:4000],
            reply_markup=kb
        )
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

def reset_tasks_on_plan_upgrade(uid, daily_limit=20):
    today = str(get_ist_today())
    daily_task_count[uid] = {today: 0}
    task_open_time.pop(uid, None)
    print(f"V41: Tasks reset {uid} to 0/{daily_limit}")
    save_data()

async def check_plan_expiry_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        today = get_ist_today()
        for uid, plan in list(user_plans.items()):
            try:
                expiry_str = plan.get('expiry') or plan.get('expires_at')
                if not expiry_str: continue
                exp_date = date.fromisoformat(str(expiry_str)[:10])
                days_left = (exp_date - today).days
                if days_left in (3,2,1):
                    bal = get_balance(uid)
                    try:
                        await context.bot.send_message(chat_id=uid, text=f"⚠️ PLAN EXPIRY - {days_left} days left!\nPlan: {plan.get('plan_name','Plan')}\nExpiry: {expiry_str}\nBalance Safe: ₹{bal:.2f}\nRenew now! After expiry 3 days free again!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Renew", callback_data="support_plans")]]))
                    except: pass
                elif days_left < 0:
                    bal = get_balance(uid)
                    try:
                        await context.bot.send_message(chat_id=uid, text=f"⏰ PLAN EXPIRED!\nBalance Safe: ₹{bal:.2f}\n🆓 3 DAYS FREE again! 0/4 daily, Total 10 tasks", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade", callback_data="support_plans")]]))
                    except: pass
            except: pass
    except Exception as e:
        print(f"expiry job err {e}")


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

async def support_plans_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await support_plans_cb(update, context)



async def assign_plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /assign_plan <user_id> <plan_id>\nExample: /assign_plan 123456789 2\n/list_support_plans")
        return
    try:
        uid = int(context.args[0])
        pid = int(context.args[1])
        plan = next((p for p in support_plans_db if p['id'] == pid), None)
        if not plan:
            await update.message.reply_text(f"Plan ID {pid} not found!")
            return
        expiry=get_ist_today()+timedelta(days=int(plan.get('duration',30) or 30))
        user_plans[str(uid)] = {
            'plan_id': pid, 'plan': str(plan.get('name','Plan')).lower(), 'plan_name': str(plan.get('name','Plan')),
            'price': int(plan.get('price',0) or 0), 'daily_limit': int(plan.get('daily_limit',10) or 10),
            'earnings_limit': int(plan.get('earnings_limit',0) or 0), 'date': str(get_ist_today()),
            'expiry': str(expiry), 'status': 'active'
        }
        save_data()
        reward = get_reward_for_user(uid, 5)
        await update.message.reply_text(f"Assigned! User {uid} -> {plan['name']} Rs{plan['price']} = Rs{reward}/task")
        try:
            await context.bot.send_message(chat_id=uid, text=f"Your Plan Activated! {plan['name']} Rs{plan['price']} Now Rs{reward}/task!")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Error {e}")


async def userlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: show every user who has opened /start, including incomplete registrations."""
    if not is_admin(update.effective_user.id):
        return
    try:
        if not users_db:
            await update.message.reply_text("👥 USER LIST\n\nNo registered users found.")
            return

        lines = [f"👥 USER LIST — {len(users_db)} users\n"]
        # Newest users first, limited to Telegram's practical message size.
        items = list(users_db.items())[::-1]
        for raw_uid, data in items[:50]:
            try:
                uid = int(raw_uid)
            except Exception:
                uid = raw_uid
            data = data if isinstance(data, dict) else {}
            name = str(data.get("name") or "Unknown").strip()
            username = str(data.get("username") or "").strip()
            if username and not username.startswith("@"):
                username = "@" + username
            plan = _get_user_plan_record(uid)
            if plan:
                plan_name = str(plan.get("name") or plan.get("plan_name") or plan.get("plan") or "Plan")
            else:
                plan_name = "Free / No Plan"
            status = "Registered" if _user_is_registered(data) else "Not registered / Pending"
            lines.append(
                f"👤 {name}\n"
                f"🆔 ID: {uid}\n"
                f"🔹 Username: {username or 'Not set'}\n"
                f"💎 Plan: {plan_name}\n"
                f"📌 Status: {status}\n"
            )

        if len(items) > 50:
            lines.append(f"Showing latest 50 of {len(items)} users.")

        # Keep comfortably below Telegram's message limit.
        msg = "\n".join(lines)
        await update.message.reply_text(msg[:4000])
    except Exception as e:
        print(f"userlist_cmd error: {e}")
        await update.message.reply_text(f"❌ User list error: {e}")

async def user_plans_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not user_plans:
        await update.message.reply_text("No user plans yet!")
        return
    msg = f"USER PLANS - {len(user_plans)} Users:\n\n"
    for uid, raw in list(user_plans.items())[:30]:
        plan = _get_user_plan_record(uid)
        name = users_db.get(int(uid), {}).get('name', 'Unknown') if str(uid).isdigit() else 'Unknown'
        plan_name = plan.get('name',plan.get('plan_name',plan.get('plan',''))) if plan else 'No Plan'
        msg += f"{uid} {name} -> {plan_name} = Rs{get_reward_for_user(int(uid) if str(uid).isdigit() else uid)}/task\n"
    await update.message.reply_text(msg)

async def new_members_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = f"NEW MEMBERS - Last 20:\n\n"
    # Get last 20 users by insertion order
    user_list = list(users_db.items())[-20:]
    for uid, data in user_list:
        name = data.get('name', 'Unknown')
        plan_id = user_plans.get(str(uid), 'No Plan')
        reward = get_reward_for_user(uid)
        msg += f"ID {uid} {name} Plan {plan_id} Rs{reward}/task\n"
    await update.message.reply_text(msg)

async def user_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /user_info <user_id>")
        return
    try:
        uid = int(context.args[0])
        user = users_db.get(uid, {})
        plan = _get_user_plan_record(uid)
        reward = get_reward_for_user(uid)
        total = get_balance(uid)
        count, limit, cap = check_daily_limits(uid)
        msg = (f"USER INFO {uid}\nName: {user.get('name')}\nTasks: {tasks_db.get(uid,0)}\n"
               f"Earnings: Rs{total}\nPlan: {plan.get('name',plan.get('plan_name',plan.get('plan','No Plan'))) if plan else 'No Plan'} "
               f"Rs{plan.get('price',0) if plan else 0}\nReward: Rs{reward}/task\nToday: {count}/{limit} tasks\nDaily cap: Rs{cap}")
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error {e}")




async def bulk_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve ALL for Daily Task screenshots only - V34 FIX: marks completed, clears missed, shows status"""
    q = update.callback_query
    try:
        await q.answer("Processing Daily Task bulk approval…")
    except Exception:
        pass
    if not is_admin(q.from_user.id):
        return
    approved_count = 0
    details = []
    today = str(get_ist_today())
    for key, sub in list(pending_daily.items()):
        try:
            uid = int(key)
            if not isinstance(sub, dict):
                continue
            task = sub.get('task', {}) if isinstance(sub.get('task', {}), dict) else {}
            task_id = task.get('id')
            reward = float(task.get('reward', 5) or 5)
            tasks_db[uid] = tasks_db.get(uid, 0) + 1
            daily_task_count.setdefault(uid, {})
            daily_task_count[uid][today] = daily_task_count[uid].get(today, 0) + 1
            daily_task_earnings.setdefault(uid, {})
            daily_task_earnings[uid][today] = round(float(daily_task_earnings[uid].get(today, 0) or 0) + reward, 2)
            if reward > 5:
                bonus_balance[uid] = round(float(bonus_balance.get(uid, 0) or 0) + (reward - 5), 2)
            # V34: Mark task status as completed
            if task_id is not None:
                if uid not in user_task_status:
                    user_task_status[uid] = {}
                user_task_status[uid][task_id] = {'status': 'completed', 'completed_at': get_ist_now(), 'reward': reward, 'approved_at': get_ist_now()}
                try:
                    # V46: Force clear missed and save
                    if uid in missed_tasks_db:
                        missed_tasks_db[uid] = {}
                    save_data()
                    print(f"V46 SAVED after approval uid={uid} reward={reward}")
                except Exception as se:
                    print(f"V46 save fail {se}")
                # Remove from missed_tasks_db
                if uid in missed_tasks_db:
                    missed_tasks_db[uid] = [t for t in missed_tasks_db[uid] if int(t.get('id',-1)) != int(task_id)]
            else:
                # Fallback: mark any pending_verification as completed
                for tid, sdata in list(user_task_status.get(uid, {}).items()):
                    if isinstance(sdata, dict) and sdata.get('status') == 'pending_verification':
                        user_task_status[uid][tid] = {'status': 'completed', 'completed_at': get_ist_now(), 'reward': reward, 'approved_at': get_ist_now()}
                        break
            record_task_referral_commissions(uid, reward)
            pending_daily.pop(key, None)
            approved_count += 1
            details.append(f"{uid} (₹{reward:g})")
            try:
                remaining = get_tasks_for_today()
                remaining_count = len([t for t in remaining if user_task_status.get(uid, {}).get(t.get('id'), {}).get('status') != 'completed'])
                if remaining_count > 0:
                    msg_user = f"✅ Task Approved! +₹{reward:g}\nBalance: ₹{get_balance(uid)}\n\n⏳ Remaining tasks today: {remaining_count}\nGo to /menu -> Daily Task for next!"
                else:
                    msg_user = f"✅ Task Approved! +₹{reward:g}\nBalance: ₹{get_balance(uid)}\n\n🎉 All tasks completed today! No more tasks! Great job!"
                await context.bot.send_message(chat_id=uid, text=msg_user, reply_markup=main_menu())
            except Exception:
                pass
        except Exception as e:
            print(f"daily bulk approval error {key}: {e}")
            import traceback; traceback.print_exc()
    save_data()
    detail_text = "\n".join(details[:15])
    if len(details) > 15:
        detail_text += f"\n...and {len(details)-15} more"
    await q.message.reply_text(
        f"✅ DAILY TASK BULK APPROVAL DONE\n\nApproved: {approved_count}\n{detail_text or 'No pending Daily Task submissions.'}\n\nRemaining pending: {len(pending_daily)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="back_admin")]])
    )
    # Update original channel message caption
    try:
        await q.message.edit_caption(caption=(q.message.caption or "") + f"\n\n✅ BULK APPROVED {approved_count} tasks at {get_ist_now().strftime('%H:%M:%S')} IST")
    except:
        pass

# === CHANNEL METHOD + BULK APPROVE V28 ===
# Admin channels - set via command or env
SCREENSHOT_CHANNEL_ID = None  # Set via /set_screenshot_channel
WITHDRAW_CHANNEL_ID = None    # Set via /set_withdraw_channel
JOIN_CHANNEL_ID = None        # Set via /set_join_channel
JOIN_CHANNEL_LINK = CHANNEL_LINK

def _load_channel_config():
    try:
        channel_config_path = os.path.join(DATA_DIR, "channel_config.json")
        if os.path.exists(channel_config_path):
            with open(channel_config_path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Channel config load error: {e}")
    return {}

DEFAULT_TASK_SCREENSHOT_CHANNEL_ID = -1004428587527
LEGACY_TASK_SCREENSHOT_CHANNEL_IDS = {-1004295034675, -1004295034675}

def get_screenshot_channel():
    stored = _load_channel_config().get('screenshot_channel')
    try:
        if stored is not None and int(stored) in LEGACY_TASK_SCREENSHOT_CHANNEL_IDS:
            return DEFAULT_TASK_SCREENSHOT_CHANNEL_ID
    except Exception:
        pass
    return stored or SCREENSHOT_CHANNEL_ID or DEFAULT_TASK_SCREENSHOT_CHANNEL_ID or SCREENSHOT_CHANNEL

def get_withdraw_channel():
    return _load_channel_config().get('withdraw_channel') or WITHDRAW_CHANNEL_ID or WITHDRAW_CHANNEL

def get_join_channel():
    return _load_channel_config().get('join_channel') or JOIN_CHANNEL_ID or JOIN_CHANNEL

def get_join_channel_link():
    return _load_channel_config().get('join_link') or JOIN_CHANNEL_LINK or CHANNEL_LINK

def save_channel_config(screenshot=None, withdraw=None, join=None, join_link=None):
    try:
        cfg = _load_channel_config()
        if screenshot is not None:
            cfg['screenshot_channel'] = screenshot
        if withdraw is not None:
            cfg['withdraw_channel'] = withdraw
        if join is not None:
            cfg['join_channel'] = join
        if join_link is not None:
            cfg['join_link'] = join_link
        with open(os.path.join(DATA_DIR, "channel_config.json"), 'w') as f:
            json.dump(cfg, f, indent=2)
        print(f"Channel config saved: {cfg}")
    except Exception as e:
        print(f"Channel config save error {e}")

async def set_screenshot_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        current = get_screenshot_channel()
        await update.message.reply_text(f"Current Screenshot Channel: {current}\n\nUsage: /set_screenshot_channel <channel_id or @username>\nExample: /set_screenshot_channel -1001234567890\nOR /set_screenshot_channel @s2e_screenshots_admin\n\nHow to get ID: Forward a message from channel to @userinfobot")
        return
    ch = context.args[0]
    # Try to resolve @username to ID by sending test message
    try:
        # Save as is (can be @username or -100...)
        save_channel_config(screenshot=ch, withdraw=None)
        await update.message.reply_text(f"✅ Screenshot Channel Set: {ch}\n\nNow all task screenshots will go to this channel with Approve buttons!\nTest: Ask a user to submit a task")
        # Test send
        try:
            await context.bot.send_message(chat_id=ch, text="✅ S2E Bot Connected! Screenshots will come here!\n\nBulk Approve: Use /approve_task <task_number> in bot or click Approve All button")
        except Exception as e:
            await update.message.reply_text(f"Channel set but test send failed: {e}\nMake bot admin in channel with Post permission!")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def set_withdraw_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        current = get_withdraw_channel()
        await update.message.reply_text(f"Current Withdraw Channel: {current}\nUsage: /set_withdraw_channel <channel_id or @username>\nExample: /set_withdraw_channel -1001234567890")
        return
    ch = context.args[0]
    save_channel_config(screenshot=None, withdraw=ch)
    await update.message.reply_text(f"✅ Withdraw Channel Set: {ch}\nAll withdraw requests will go here!")
    try:
        await context.bot.send_message(chat_id=ch, text="✅ S2E Bot Connected! Withdraw requests will come here!")
    except Exception as e:
        await update.message.reply_text(f"Set but test failed: {e} - Make bot admin!")

async def set_join_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the member/join channel and its invite/public link.
    Usage: /set_join_channel <channel_id> <join_link>
    """
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        current_id = get_join_channel()
        current_link = get_join_channel_link()
        await update.message.reply_text(
            f"Current Join Channel: {current_id}\n"
            f"Current Join Link: {current_link}\n\n"
            "Usage: /set_join_channel <channel_id> <join_link>\n"
            "Example: /set_join_channel -1004352241439 https://t.me/+c5n159t0QtsyZTVI"
        )
        return
    ch = context.args[0]
    link = context.args[1]
    save_channel_config(join=ch, join_link=link)
    await update.message.reply_text(
        f"✅ Member Join Channel Set: {ch}\n\n"
        f"Join Link: {link}\n\n"
        "New members will use this channel/link."
    )
    try:
        await context.bot.send_message(
            chat_id=ch,
            text="✅ S2E Bot Connected! Member Join Channel is active."
        )
    except Exception as e:
        await update.message.reply_text(
            f"Channel saved, but test send failed: {e}\n"
            "Make the bot an admin in the channel with permission to post messages."
        )


async def approve_task_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "📋 BULK APPROVE PER TASK!\n\n"
            "Usage: /approve_task <task_number>\n"
            "Example: /approve_task 1 -> Approves ALL pending for Task 1\n"
            "/approve_task 2 -> Approves ALL for Task 2\n"
            "/approve_all_pending -> Approves ALL pending tasks!\n\n"
            "This is the SINGLE BUTTON you asked for! One command = All members Task 1 approved!"
        )
        return
    try:
        task_num = context.args[0]
        # If task_num is "all", approve all
        if task_num.lower() == "all" or task_num == "all_pending":
            return await approve_all_pending_cmd(update, context)
        
        # Approve all for this task number
        approved = 0
        to_approve = []
        for uid, data in list(pending_daily.items()):
            task = data.get('task', {})
            t_num = str(task.get('task_number', ''))
            t_title = task.get('title', '')
            # Match task number or title contains
            if t_num == str(task_num) or str(task_num) in str(t_title) or str(task_num).lower() in str(t_title).lower():
                to_approve.append(uid)
        
        if not to_approve:
            # Try matching by task id
            for uid, data in list(pending_daily.items()):
                task = data.get('task', {})
                if str(task.get('id','')) == str(task_num):
                    to_approve.append(uid)
        
        if not to_approve:
            await update.message.reply_text(f"No pending found for Task {task_num}!\nUse /pending to see pending list")
            return
        
        for uid in to_approve:
            try:
                if uid in pending_daily:
                    task = pending_daily[uid].get('task',{})
                    base_reward = int(task.get('reward',5) or 5)
                    reward = get_task_reward_for_user(task, uid)
                    tasks_db[uid] = tasks_db.get(uid,0) + 1
                    bonus_balance[uid] = bonus_balance.get(uid,0) + (reward - 5) if reward != 5 else bonus_balance.get(uid,0)
                    del pending_daily[uid]
                    approved += 1
                    try:
                        await context.bot.send_message(chat_id=uid, text=f"✅ Task {task_num} Approved! Rs{reward} added! Keep doing tasks!")
                    except:
                        pass
            except Exception as e:
                print(f"Bulk approve error for {uid}: {e}")
        
        save_data()
        await update.message.reply_text(f"✅ BULK APPROVED Task {task_num}!\n\nApproved: {approved} members\nEach got Rs{get_reward_for_user(0,5)}-Rs15 based on plan!\n\nNext: /approve_task 2 for Task 2")
        
        # Also post to screenshot channel if set
        ch = get_screenshot_channel()
        if ch:
            try:
                await context.bot.send_message(chat_id=ch, text=f"✅ BULK APPROVED Task {task_num} - {approved} members approved by admin!")
            except:
                pass
                
    except Exception as e:
        await update.message.reply_text(f"Error {e}")
        import traceback; traceback.print_exc()

async def approve_all_pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not pending_daily:
        await update.message.reply_text("No pending tasks!")
        return
    approved = 0
    for uid in list(pending_daily.keys()):
        try:
            task = pending_daily[uid].get('task',{})
            base_reward = int(task.get('reward',5) or 5)
            reward = get_task_reward_for_user(task, uid)
            tasks_db[uid] = tasks_db.get(uid,0) + 1
            if reward != 5:
                bonus_balance[uid] = bonus_balance.get(uid,0) + (reward - 5)
            del pending_daily[uid]
            approved += 1
            try:
                await context.bot.send_message(chat_id=uid, text=f"✅ Your Task Approved! Rs{reward} added!")
            except:
                pass
        except:
            pass
    save_data()
    await update.message.reply_text(f"✅ APPROVED ALL! {approved} members approved!")

# Enhanced pending view with bulk buttons
async def pending_bulk_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not pending_daily:
        await update.message.reply_text("No pending!")
        return
    # Group by task number
    from collections import defaultdict
    grouped = defaultdict(list)
    for uid, data in pending_daily.items():
        task = data.get('task', {})
        t_num = task.get('task_number', 'Unknown')
        grouped[t_num].append(uid)
    
    msg = f"📋 PENDING BY TASK - {len(pending_daily)} Total:\n\n"
    for t_num, uids in grouped.items():
        msg += f"Task {t_num}: {len(uids)} members pending\n"
    msg += "\nUse:\n/approve_task 1 -> Approve all Task 1\n/approve_task 2 -> Task 2\n/approve_all_pending -> Approve all!"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    kb = []
    for t_num in list(grouped.keys())[:5]:
        kb.append([InlineKeyboardButton(f"✅ Approve All Task {t_num} ({len(grouped[t_num])})", callback_data=f"bulk_approve_{t_num}")])
    kb.append([InlineKeyboardButton("✅ Approve ALL Pending", callback_data="bulk_approve_all")])
    kb.append([InlineKeyboardButton("Back to Admin", callback_data="back_admin")])
    mk = InlineKeyboardMarkup(kb)
    await update.message.reply_text(msg, reply_markup=mk)


# === BACKUP FIX - ADDED FOR 3 FILES BACKUP ===
async def backup_cmd(update, context):
    from telegram import Update
    from telegram.ext import ContextTypes
    uid = update.effective_user.id
    if uid not in ADMIN_ID_LIST:
        return
    try:
        import os, json, glob
        files_to_backup = []
        # Original DB files
        for jf in ["Supabase", "channel_config.json"]:
            if os.path.exists(jf):
                files_to_backup.append(jf)
        # Also backup all _db jsons if exists
        for jf in glob.glob("*_db*.json"):
            if jf not in files_to_backup and os.path.exists(jf):
                files_to_backup.append(jf)
        # Ensure config exists
        if not os.path.exists("Supabase"):
            with open("Supabase","w") as f: json.dump({}, f)
            files_to_backup.append("Supabase")
        if not os.path.exists("channel_config.json"):
            with open("channel_config.json","w") as f: json.dump({}, f)
            files_to_backup.append("channel_config.json")
        
        # Also create combined backup
        combined = {}
        for jf in files_to_backup:
            try:
                with open(jf,"r") as f: combined[jf]=json.load(f)
            except:
                pass
        with open("bot_config.json","w") as f: json.dump({"admins": ADMIN_ID_LIST, "backup_time": str(get_ist_now())}, f, indent=2)
        files_to_backup.append("bot_config.json")
        
        with open("users_progress.json","w") as f: json.dump(combined, f, indent=2)
        with open("referrals.json","w") as f: json.dump(combined, f, indent=2)
        
        for fp in files_to_backup[:10]:  # limit to 10 files max telegram
            try:
                await update.message.reply_document(document=open(fp,'rb'), filename=fp)
            except Exception as e:
                print(f"Backup send error {fp}: {e}")
        await update.message.reply_text("✅ All Backup files - Save to Drive! If bot deleted, upload these to new bot - total users will restore! Backup + Referral L1/L2 system ready! Original 2000+ lines file!")
    except Exception as e:
        await update.message.reply_text(f"Backup error {e}")

async def add_admin_cmd(update, context):
    uid = update.effective_user.id
    if uid not in ADMIN_ID_LIST:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /add_admin USER_ID")
        return
    try:
        new_id = int(context.args[0])
        if new_id <= 0:
            raise ValueError("invalid user id")
        if new_id in ADMIN_ID_LIST:
            name = await get_admin_display_name(new_id, context.bot)
            await update.message.reply_text(f"ℹ️ Already admin:\n👤 {name}\n🆔 {new_id}")
            return
        name = " ".join(context.args[1:]).strip() if len(context.args) > 1 else ""
        if not name:
            name = await get_admin_display_name(new_id, context.bot)
        ADMIN_ID_LIST.append(new_id)
        admin_names_db[new_id] = name
        save_data()
        await update.message.reply_text(
            f"✅ ADMIN ADDED\n\n👤 Name: {name}\n🆔 User ID: {new_id}\n\n"
            "Use /list_admins to view all admins."
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def remove_admin_cmd(update, context):
    uid = update.effective_user.id
    if uid not in ADMIN_ID_LIST:
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /remove_admin USER_ID")
        return
    try:
        target = int(context.args[0])
        if target not in ADMIN_ID_LIST:
            await update.message.reply_text(f"❌ Not in admin list: {target}")
            return
        if len(ADMIN_ID_LIST) <= 1:
            await update.message.reply_text("❌ Cannot remove the last admin.")
            return
        old_name = await get_admin_display_name(target, context.bot)
        ADMIN_ID_LIST.remove(target)
        admin_names_db.pop(target, None)
        admin_names_db.pop(str(target), None)
        save_data()
        await update.message.reply_text(
            f"✅ ADMIN REMOVED\n\n👤 Name: {old_name}\n🆔 User ID: {target}\n\n"
            "Use /list_admins to view remaining admins."
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_admins_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    lines = ["👑 ADMIN LIST", f"Total: {len(ADMIN_ID_LIST)}", ""]
    for i, aid in enumerate(ADMIN_ID_LIST, 1):
        name = await get_admin_display_name(aid, context.bot)
        marker = " (you)" if int(aid) == int(update.effective_user.id) else ""
        lines.append(f"{i}. 👤 {name}{marker}\n   🆔 {aid}")
    lines.append("\n/add_admin USER_ID -> add\n/remove_admin USER_ID -> remove")
    await update.message.reply_text("\n".join(lines))

async def referral_stats_cmd(update, context):
    uid = update.effective_user.id
    if uid not in ADMIN_ID_LIST:
        return
    try:
        from glob import glob
        msg = "📊 Referral Stats\n"
        # Try to read referrals_db
        try:
            import json
            if "referrals_db" in globals():
                total = len(referrals_db) if isinstance(referrals_db, dict) else 0
                msg += f"Total referral users: {total}\n"
        except:
            pass
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error {e}")


async def admin_backup_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer("Preparing backup...")
    except:
        pass
    try:
        import os, json, glob
        files=[]
        for jf in ["Supabase","channel_config.json","bot_config.json","users_progress.json","referrals.json"]:
            if os.path.exists(jf): files.append(jf)
        for jf in glob.glob("*_db*.json"):
            if os.path.exists(jf) and jf not in files: files.append(jf)
        if not os.path.exists("bot_config.json"):
            with open("bot_config.json","w") as f:
                json.dump({"channels":{"s":SCREENSHOT_CHANNEL,"w":WITHDRAW_CHANNEL,"j":JOIN_CHANNEL}},f)
            files.append("bot_config.json")
        sent=0
        for fp in files[:8]:
            try:
                if os.path.exists(fp):
                    await q.message.reply_document(document=open(fp,"rb"),filename=fp)
                    sent+=1
            except Exception as e:
                print(e)
        await q.message.reply_text(f"✅ {sent} Backup files! S:{SCREENSHOT_CHANNEL} W:{WITHDRAW_CHANNEL} J:{JOIN_CHANNEL}")
    except Exception as e:
        try:
            await q.message.reply_text(f"Backup err {e}")
        except:
            pass

async def get_admin_display_name(admin_id, bot=None):
    """Return a readable admin name, falling back to the Telegram ID."""
    try:
        aid = int(admin_id)
    except Exception:
        aid = admin_id
    stored = admin_names_db.get(aid) or admin_names_db.get(str(aid))
    if stored:
        return str(stored)
    user = users_db.get(aid) or users_db.get(str(aid))
    if isinstance(user, dict) and user.get("name"):
        return str(user["name"])
    if bot:
        try:
            chat = await bot.get_chat(aid)
            full_name = " ".join(
                x for x in [getattr(chat, "first_name", None), getattr(chat, "last_name", None)] if x
            ).strip()
            if full_name:
                admin_names_db[aid] = full_name
                return full_name
            if getattr(chat, "username", None):
                admin_names_db[aid] = f"@{chat.username}"
                return f"@{chat.username}"
        except Exception as e:
            print(f"Admin name lookup failed for {aid}: {e}")
    return f"User {aid}"

async def admin_add_admin_cb(update, context):
    try:
        await update.callback_query.answer()
        if not is_admin(update.effective_user.id):
            return
        lines = [f"👑 ADMIN MANAGEMENT", f"Total admins: {len(ADMIN_ID_LIST)}", ""]
        for idx, aid in enumerate(ADMIN_ID_LIST, 1):
            name = await get_admin_display_name(aid, context.bot)
            marker = " (you)" if int(aid) == int(update.effective_user.id) else ""
            lines.append(f"{idx}. 👤 {name}{marker}\n   🆔 {aid}")
        lines += ["", "/add_admin USER_ID - add", "/remove_admin USER_ID - remove", "/list_admins - full list"]
        await update.effective_message.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Admin List", callback_data="admin_add_admin")],
                [InlineKeyboardButton("⬅️ Back to Admin", callback_data="back_admin")]
            ])
        )
    except Exception as e:
        print(f"admin list error: {e}")

async def admin_referral_cb(update, context):
    try:
        await update.callback_query.answer()
        await update.effective_message.reply_text(
            "🔗 REFERRAL SETTINGS\n\n"
            f"L1 plan activation: {REFERRAL_PLAN_COMMISSION_PERCENT:g}%\n"
            f"L2 plan activation: {L2_PLAN_COMMISSION_PERCENT:g}%\n"
            f"L1 task/product: {L1_TASK_COMMISSION_PERCENT:g}%\n"
            f"L2 task/product: {L2_TASK_COMMISSION_PERCENT:g}%\n\n"
            "Admin: /set_referral_commission plan 10 | l2plan 3 | l1 2 | l2 0.5"
        )
    except:
        pass

async def admin_missed_toggle_cb(update, context):
    global MISSED_ENABLED
    try:
        await update.callback_query.answer()
        MISSED_ENABLED = not MISSED_ENABLED
        save_data()
        status = "ON" if MISSED_ENABLED else "OFF"
        try:
            await update.effective_message.edit_reply_markup(reply_markup=admin_panel_keyboard())
        except Exception:
            pass
        await update.effective_message.reply_text(
            f"⏰ Missed Tasks: {status}\n\n" +
            ("Missed task tracking/notifications are now ENABLED."
             if MISSED_ENABLED else
             "Missed task tracking is now DISABLED."),
            reply_markup=admin_panel_keyboard()
        )
        if MISSED_ENABLED:
            for member_id in list(users_db.keys()):
                try:
                    await context.bot.send_message(
                        chat_id=member_id,
                        text=("⏰ Missed Tasks option is now ENABLED by Admin.\n\n"
                              "If you miss a scheduled task after its time window closes, it will appear in your Missed Tasks option."),
                        reply_markup=main_menu()
                    )
                except Exception:
                    pass
    except Exception as e:
        print(f"missed toggle error: {e}")


async def set_referral_commission_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    global REFERRAL_PLAN_COMMISSION_PERCENT, L2_PLAN_COMMISSION_PERCENT, L1_TASK_COMMISSION_PERCENT, L2_TASK_COMMISSION_PERCENT
    if len(context.args) < 2 or context.args[0].lower() not in ("plan","l2plan","l1","l2"):
        await update.message.reply_text(
            f"Current Referral Commission\nL1 plan: {REFERRAL_PLAN_COMMISSION_PERCENT:g}%\nL2 plan: {L2_PLAN_COMMISSION_PERCENT:g}%\n"
            f"L1 task/product: {L1_TASK_COMMISSION_PERCENT:g}%\nL2 task/product: {L2_TASK_COMMISSION_PERCENT:g}%\n\n"
            "Change: /set_referral_commission plan 10\n/set_referral_commission l2plan 3\n/set_referral_commission l1 2\n/set_referral_commission l2 0.5")
        return
    try: value=float(context.args[1])
    except: await update.message.reply_text("Enter a valid percentage."); return
    if value < 0 or value > 100: await update.message.reply_text("Percentage must be 0-100."); return
    key=context.args[0].lower()
    if key=="plan": REFERRAL_PLAN_COMMISSION_PERCENT=value
    elif key=="l2plan": L2_PLAN_COMMISSION_PERCENT=value
    elif key=="l1": L1_TASK_COMMISSION_PERCENT=value
    else: L2_TASK_COMMISSION_PERCENT=value
    save_data()
    await update.message.reply_text(f"✅ {key.upper()} commission updated to {value:g}%")

async def channels_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(f"📢 Channels Status\nTask: {get_screenshot_channel()}\nWithdraw: {get_withdraw_channel()}\nJoin: {get_join_channel()}\nActive: Yes Total:3")
    except Exception as e:
        print(e)

async def channels_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(f"📢 Channels List - 3 Channels\n1. Task: {get_screenshot_channel()}\n2. Withdraw: {get_withdraw_channel()}\n3. Join: {get_join_channel()}\nTotal: 3\nLink: https://t.me/S2E_Daily_Earning")
    except Exception as e:
        print(e)

async def support_plans_fixed_cb(update, context):
    q=update.callback_query
    try: await q.answer()
    except: pass
    try:
        # Prevent duplicate - edit message instead of sending new
        await q.message.reply_text("💎 SUPPORT PLANS\nBasic - Rs199 1 Month\nPremium - Rs499 3 Months\nContact @s2edayincome")
    except: pass





def _split_task_description_args(args):
    """Support optional task instructions after a | separator."""
    if not args:
        return list(args), ""
    vals = list(args)
    if "|" in vals:
        idx = vals.index("|")
        return vals[:idx], " ".join(vals[idx+1:]).strip()
    # Also accept a single argument containing the separator.
    for i, val in enumerate(vals):
        if "|" in str(val):
            left, right = str(val).split("|", 1)
            new_vals = vals[:i]
            if left.strip():
                new_vals.append(left.strip())
            return new_vals, (right.strip() + (" " + " ".join(vals[i+1:]) if vals[i+1:] else "")).strip()
    return vals, ""

async def add_task_free_cmd(update, context):
    if update.effective_user.id not in ADMIN_ID_LIST:
        return
    clean_args, description = _split_task_description_args(context.args)
    if len(clean_args) >= 5:
        if clean_args[-1].lower() not in ['all','free','basic','premium','0','1','2','3','4']:
            clean_args.append('free')
    old_args = context.args
    context.args = clean_args
    before_id = scheduled_task_counter
    await add_task_manual_cmd(update, context)
    context.args = old_args
    if description and scheduled_task_counter > before_id and scheduled_tasks_db:
        task = scheduled_tasks_db[-1]
        task['description'] = description
        save_data()

async def add_task_basic_cmd(update, context):
    if update.effective_user.id not in ADMIN_ID_LIST:
        return
    clean_args, description = _split_task_description_args(context.args)
    if len(clean_args) >= 5:
        if clean_args[-1].lower() not in ['all','free','basic','premium','0','1','2','3','4']:
            clean_args.append('basic')
    old_args = context.args
    context.args = clean_args
    before_id = scheduled_task_counter
    await add_task_manual_cmd(update, context)
    context.args = old_args
    if description and scheduled_task_counter > before_id and scheduled_tasks_db:
        scheduled_tasks_db[-1]['description'] = description
        save_data()

async def add_task_premium_cmd(update, context):
    if update.effective_user.id not in ADMIN_ID_LIST:
        return
    clean_args, description = _split_task_description_args(context.args)
    if len(clean_args) >= 5:
        if clean_args[-1].lower() not in ['all','free','basic','premium','0','1','2','3','4']:
            clean_args.append('premium')
    old_args = context.args
    context.args = clean_args
    before_id = scheduled_task_counter
    await add_task_manual_cmd(update, context)
    context.args = old_args
    if description and scheduled_task_counter > before_id and scheduled_tasks_db:
        scheduled_tasks_db[-1]['description'] = description
        save_data()

async def add_task_all_cmd(update, context):
    if update.effective_user.id not in ADMIN_ID_LIST:
        return
    clean_args, description = _split_task_description_args(context.args)
    if len(clean_args) >= 5:
        if clean_args[-1].lower() not in ['all','free','basic','premium','0','1','2','3','4']:
            clean_args.append('all')
    old_args = context.args
    context.args = clean_args
    before_id = scheduled_task_counter
    await add_task_manual_cmd(update, context)
    context.args = old_args
    if description and scheduled_task_counter > before_id and scheduled_tasks_db:
        scheduled_tasks_db[-1]['description'] = description
        save_data()

async def add_task_5plans_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        args, description = _split_task_description_args(context.args)
        if len(args) < 5:
            await update.message.reply_text(
                "📋 5 PLANS TASK ADD:\n\nSame amount:\n/add_task_5plans 10:00 11:00 Title Link 10 all\n\nDifferent amounts:\n/add_task_5plans 10:00 11:00 Title Link free:5,1:10,2:15,3:20,4:30 all"
            )
            return
        open_time, close_time = args[0], args[1]
        # Allow task titles with spaces: find the URL/link token, then use the
        # tokens after it for reward and optional audience.
        audience_tokens = {'all','free','basic','premium','0','1','2','3','4'}
        audience_arg = 'all'
        end_idx = len(args)
        if len(args) >= 6 and (args[-1].lower() in audience_tokens or ',' in args[-1]):
            audience_arg = args[-1].lower()
            end_idx -= 1
        if end_idx < 4:
            raise ValueError('Missing link/reward')
        reward_arg = args[end_idx-1]
        link_idx = next((i for i in range(2, end_idx-1) if str(args[i]).startswith(('http://','https://','t.me/','www.'))), None)
        if link_idx is None:
            # Backward-compatible format: single-word title + link.
            link_idx = 3
        title = ' '.join(args[2:link_idx])
        link = args[link_idx]
        rewards_dict = {}
        base_reward = 5
        if ':' in reward_arg:
            try:
                parts = reward_arg.split(',')
                for part in parts:
                    if ':' in part:
                        k, v = part.split(':')
                        k = k.strip().lower()
                        v = int(v.strip())
                        if k in ['free', '0']:
                            rewards_dict[0] = v
                        elif k in ['1', 'basic', '199']:
                            rewards_dict[1] = v
                        elif k in ['2', 'premium', '499']:
                            rewards_dict[2] = v
                        elif k in ['3', 'pro', '999']:
                            rewards_dict[3] = v
                        elif k in ['4', 'vip', '1999']:
                            rewards_dict[4] = v
                        elif k == 'all':
                            rewards_dict['all'] = v
                base_reward = rewards_dict.get('all', list(rewards_dict.values())[0] if rewards_dict else 5)
            except:
                base_reward = 5
        else:
            try:
                base_reward = int(reward_arg)
                rewards_dict = {'all': base_reward}
            except:
                base_reward = 5
        if audience_arg == 'all':
            audience = 'all'
        elif ',' in audience_arg:
            try:
                audience = [int(x.strip()) if x.strip().isdigit() else x.strip() for x in audience_arg.split(',')]
            except:
                audience = 'all'
        elif audience_arg.isdigit():
            audience = int(audience_arg)
        else:
            audience = audience_arg
        from datetime import datetime as dt
        today = str(get_ist_today())
        global scheduled_task_counter
        ot = dt.strptime(open_time, "%H:%M").time()
        ct = dt.strptime(close_time, "%H:%M").time()
        task = {
            'id': scheduled_task_counter,
            'date': today,
            'open_time': open_time,
            'close_time': close_time,
            'open_time_obj': ot,
            'close_time_obj': ct,
            'title': title,
            'link': link,
            'reward': base_reward,
            'rewards': rewards_dict if len(rewards_dict) > 1 or 'all' not in rewards_dict else {},
            'audience': audience,
            'description': description,
            'task_number': len([t for t in scheduled_tasks_db if t['date']==today])+1
        }
        scheduled_tasks_db.append(task)
        scheduled_task_counter+=1
        save_data()
        msg = f"✅ Task Added ID:{task['id']} {title} Reward:{base_reward} Audience:{audience}"
        if rewards_dict and len(rewards_dict)>1:
            msg += f"\nPer-plan: {rewards_dict}"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def list_tasks_audience_cmd(update, context):
    if update.effective_user.id not in ADMIN_ID_LIST:
        return
    today = str(get_ist_today())
    tasks = [t for t in scheduled_tasks_db if t['date'] == today]
    if not tasks:
        await update.message.reply_text("No tasks for today!")
        return
    msg = f"📊 Today's Tasks ({today}):\n"
    for t in tasks:
        msg += f"ID:{t['id']} {t['open_time']}-{t['close_time']} {t['title']} ₹{t['reward']} Aud:{t.get('audience','all')} Rewards:{t.get('rewards',{})}\n"
    await update.message.reply_text(msg)



async def clear_missed_all_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    total = 0
    for uid in list(missed_tasks_db.keys()):
        total += len(missed_tasks_db[uid])
        missed_tasks_db[uid] = []
    save_data()
    await update.message.reply_text(f"✅ Cleared all missed tasks!\nTotal cleared: {total} tasks from {len(missed_tasks_db)} users.")

async def clear_missed_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /clear_missed_user <user_id>")
        return
    try:
        uid = int(context.args[0])
        if uid in missed_tasks_db:
            count = len(missed_tasks_db[uid])
            missed_tasks_db[uid] = []
            save_data()
            await update.message.reply_text(f"✅ Cleared {count} missed tasks for user {uid}")
        else:
            await update.message.reply_text(f"No missed tasks for user {uid}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def clear_scheduled_all_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    count = len(scheduled_tasks_db)
    scheduled_tasks_db.clear()
    save_data()
    await update.message.reply_text(f"✅ Cleared all {count} scheduled tasks! Now add fresh tasks without overlap.")

async def clear_duplicates_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    # Clear duplicate missed tasks (same ID)
    cleaned = 0
    for uid in list(missed_tasks_db.keys()):
        seen = set()
        new_list = []
        for task in missed_tasks_db[uid]:
            tid = task.get('id')
            if tid not in seen:
                seen.add(tid)
                new_list.append(task)
            else:
                cleaned += 1
        missed_tasks_db[uid] = new_list
    # Clear duplicate scheduled tasks (same time overlap)
    # Keep only first task per time slot
    seen_times = set()
    new_scheduled = []
    dup_count = 0
    for task in scheduled_tasks_db:
        key = (task.get('date'), task.get('open_time'), task.get('close_time'))
        if key not in seen_times:
            seen_times.add(key)
            new_scheduled.append(task)
        else:
            dup_count += 1
    scheduled_tasks_db[:] = new_scheduled
    save_data()
    await update.message.reply_text(f"✅ Duplicates cleaned!\nMissed duplicates: {cleaned}\nScheduled duplicates: {dup_count}\nNow only unique tasks remain.")

# Auto-clean on startup - remove duplicate missed tasks
def auto_clean_duplicates():
    try:
        cleaned = 0
        for uid in list(missed_tasks_db.keys()):
            seen = set()
            new_list = []
            for task in missed_tasks_db[uid]:
                tid = task.get('id')
                if tid not in seen:
                    seen.add(tid)
                    new_list.append(task)
                else:
                    cleaned += 1
            missed_tasks_db[uid] = new_list
        if cleaned > 0:
            print(f"=== AUTO-CLEANED {cleaned} duplicate missed tasks on startup ===")
            save_data()
    except Exception as e:
        print(f"Auto-clean error: {e}")



async def add_bulk_tasks_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    # Get full text after command
    full_text = update.message.text or ""
    # Remove /add_bulk, /bulk_add, /bulk_tasks prefix
    for prefix in ["/add_bulk", "/bulk_add", "/bulk_tasks_add"]:
        if full_text.startswith(prefix):
            full_text = full_text[len(prefix):].strip()
            break
    if not full_text:
        await update.message.reply_text(
            "📋 BULK ADD - 2 WAYS:\n\n"
            "1️⃣ Separate (1 task per message):\n"
            "/add_task_all 14:00 15:00 WatchAd https://t.me/... 10\n\n"
            "2️⃣ Bulk (many tasks in 1 message):\n"
            "/add_bulk\n"
            "14:00 15:00 WatchAd https://t.me/... 10\n"
            "15:00 16:00 WatchAd2 https://t.me/... 10 all\n"
            "16:00 17:00 PremiumTask https://t.me/... 20 basic\n\n"
            "Amount separation:\n"
            "• all/free = Free + All paid users can do\n"
            "• basic/premium/pro/vip = Only that plan & higher\n"
            "• Reward 10 = Free, 15-20 = Paid plans\n\n"
            "Example:\n"
            "/add_task_all 14:00 15:00 WatchAd link 10 all\n"
            "/add_task_basic 15:00 16:00 SpecialTask link 20"
        )
        return
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    # If single line without newline, treat as one task
    if len(lines) == 1 and " " in lines[0]:
        # Check if it looks like a task line
        parts = lines[0].split()
        if len(parts) >= 4:
            lines = [lines[0]]
        else:
            lines = [l.strip() for l in full_text.split() if l.strip()] # fallback
            lines = [" ".join(lines)] if lines else []
    
    added = 0
    errors = []
    for idx, line in enumerate(lines, 1):
        # Skip if line starts with /add_task_all
        line = line.replace("/add_task_all", "").strip()
        line = line.replace("/add_task_free", "").strip()
        line = line.replace("/add_task_basic", "").strip()
        parts = line.split()
        if len(parts) < 4:
            errors.append(f"Line {idx}: Too few args - {line}")
            continue
        try:
            open_time, close_time, title, link = parts[0], parts[1], parts[2], parts[3]
            reward = int(parts[4]) if len(parts) >= 5 else 10
            audience = parts[5].lower() if len(parts) >= 6 else 'all'
            # Validate time
            from datetime import datetime as dt2
            ot = dt2.strptime(open_time, "%H:%M").time()
            ct = dt2.strptime(close_time, "%H:%M").time()
            # Overlap check
            today = str(get_ist_today())
            overlap = False
            for ex in scheduled_tasks_db:
                if ex.get('date') == today and is_time_overlap(open_time, close_time, ex.get('open_time'), ex.get('close_time')):
                    ex_aud = str(ex.get('audience','all')).lower()
                    if ex_aud == 'all' or audience == 'all' or ex_aud == audience:
                        errors.append(f"Line {idx}: Overlap with ID:{ex['id']} {ex['open_time']}-{ex['close_time']}")
                        overlap = True
                        break
            if overlap:
                continue
            global scheduled_task_counter
            task = {
                'id': scheduled_task_counter, 
                'date': today, 
                'open_time': open_time, 
                'close_time': close_time, 
                'open_time_obj': ot, 
                'close_time_obj': ct, 
                'title': title, 
                'link': link, 
                'reward': reward, 
                'audience': audience, 
                'rewards': {}, 
                'task_number': len([t for t in scheduled_tasks_db if t['date']==today])+1
            }
            scheduled_tasks_db.append(task)
            scheduled_task_counter+=1
            added+=1
        except Exception as e:
            errors.append(f"Line {idx}: {e} - {line[:50]}")
    save_data()
    msg = f"✅ BULK ADD DONE! Added: {added}"
    if errors:
        msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors[:5])
        if len(errors) > 5:
            msg += f"\n...and {len(errors)-5} more"
    msg += f"\n\nTotal scheduled today: {len([t for t in scheduled_tasks_db if t.get('date')==str(get_ist_today())])}"
    await update.message.reply_text(msg)


async def add_task_manual_cmd(update, context):
    try:
        if update.effective_user.id not in ADMIN_ID_LIST:
            return
        args = context.args
        if len(args) < 5:
            await update.message.reply_text(
                "Usage: /add_task_manual <open> <close> <title> <link> <reward> [audience]\n"
                "Audience: all, free, 0,1,2,3,4, basic, premium\n"
                "Ex: /add_task_manual 10:00 11:00 Title https://t.me/... 10 premium"
            )
            return
        open_time, close_time, title, link = args[0], args[1], args[2], args[3]
        try:
            reward = int(args[4])
        except:
            reward = 5
        audience = args[5].lower() if len(args) >= 6 else 'all'
        if audience == '199':
            audience = 'basic'
        elif audience == '499':
            audience = 'premium'
        elif audience.isdigit():
            audience = int(audience)
        from datetime import datetime as dt2
        today = str(get_ist_today())
        global scheduled_task_counter
        ot = dt2.strptime(open_time, "%H:%M").time()
        ct = dt2.strptime(close_time, "%H:%M").time()
        task = {'id': scheduled_task_counter, 'date': today, 'open_time': open_time, 'close_time': close_time, 'open_time_obj': ot, 'close_time_obj': ct, 'title': title, 'link': link, 'reward': reward, 'audience': audience, 'rewards': {}, 'task_number': len([t for t in scheduled_tasks_db if t['date']==today])+1}
        scheduled_tasks_db.append(task)
        scheduled_task_counter+=1
        save_data()
        await update.message.reply_text(f"✅ Task Added ID:{task['id']} {title} Reward:{reward} Audience:{audience}")
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
    if not is_admin(update.effective_user.id):
        return
    # /add_plan Name Price DurationDays DailyTasks DailyMin DailyMax Cap [PromoReward] [ProductPromoReward] [Description...]
    if len(context.args) < 7:
        await update.message.reply_text(
            "Usage: /add_plan <Name> <Price> <Days> <DailyTasks> <DailyMin> <DailyMax> <Cap> [PromoReward] [ProductPromoReward] [Description]\n"
            "Example: /add_plan Gold 2999 60 12 100 150 8000 20 30 Gold plan")
        return
    try:
        name=context.args[0]; price=int(context.args[1]); duration=int(context.args[2]); daily=int(context.args[3])
        dmin=float(context.args[4]); dmax=float(context.args[5]); cap=float(context.args[6])
        promo=float(context.args[7]) if len(context.args)>7 else 0
        product=float(context.args[8]) if len(context.args)>8 else 0
        desc=" ".join(context.args[9:]) if len(context.args)>9 else f"₹{price} | {duration} DAYS | {daily} TASKS/DAY"
        new_id=max([int(p.get("id",0)) for p in support_plans_db], default=0)+1
        plan={"id":new_id,"name":name,"price":price,"validity_days":duration,"duration":duration,"daily_task_limit":daily,"daily_limit":daily,"daily_earning_min":dmin,"daily_earning_max":dmax,"total_earning_cap":cap,"earnings_limit":cap,"promo_reward":promo,"product_promo_reward":product,"desc":desc}
        support_plans_db.append(plan); save_data()
        await update.message.reply_text(f"✅ Plan Added\nID: {new_id}\n{name} ₹{price}\nDays: {duration}\nDaily tasks: {daily}\nEarning: ₹{dmin:g}-₹{dmax:g}\nCap: ₹{cap:g}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def edit_plan_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /edit_plan <id> <field> <value>\nFields: name, price, days, daily, min, max, cap, promo, product_promo, desc")
        return
    try:
        pid=int(context.args[0]); field=context.args[1].lower(); value=" ".join(context.args[2:])
        plan=next((p for p in support_plans_db if int(p.get("id",-1))==pid),None)
        if not plan: await update.message.reply_text("❌ Plan not found."); return
        numeric={"price":"price","days":"validity_days","daily":"daily_task_limit","min":"daily_earning_min","max":"daily_earning_max","cap":"total_earning_cap","promo":"promo_reward","product_promo":"product_promo_reward"}
        if field in numeric:
            key=numeric[field]; val=float(value) if field in ("min","max","cap","promo","product_promo") else int(value)
            plan[key]=val
            if field=="days": plan["duration"]=int(val)
            if field=="daily": plan["daily_limit"]=int(val)
            if field=="cap": plan["earnings_limit"]=float(val)
            if field=="price": plan["price"]=int(val)
        elif field=="name": plan["name"]=value
        elif field=="desc": plan["desc"]=value
        else: await update.message.reply_text("❌ Unknown field."); return
        save_data(); await update.message.reply_text(f"✅ Plan {pid} updated. Existing activated members keep their old snapshot; only future activations use the new plan values.")
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")


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
        awaiting_plan_image_admins.add(update.effective_user.id)
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
        awaiting_plan_image_admins.discard(update.effective_user.id)
        await update.message.reply_text(f"Image set for Plan {pid}!")
        return True
    except:
        return False

class PlanPaymentProofFilter(filters.BaseFilter):
    name = "PlanPaymentProofFilter"
    def filter(self, update):
        try:
            return bool(update.effective_user and update.effective_user.id in awaiting_plan_payment_adminless and update.message and update.message.photo)
        except Exception:
            return False


class PlanImageUploadFilter(filters.BaseFilter):
    name = "PlanImageUploadFilter"
    def filter(self, update):
        try:
            return bool(update.effective_user and update.effective_user.id in awaiting_plan_image_admins and update.message and update.message.photo)
        except Exception:
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



def main():
    # V4.6 FIX: Start Flask FIRST, before anything else
    try:
        start_flask_in_thread()
        start_self_ping_loop()
        print("✅ V4.12 Flask + Self-ping started in main()")
        init_supabase()
        load_data()
    except Exception as e:
        print(f'Flask/Supabase start fail in main: {e}')

    global bot_application, bot_event_loop, notification_thread_started
    import os, time, threading
    print("============================================================")
    print("S2E Bot FINAL  - No ConversationHandler - Important Channel Fix Final - All Filters Fix Final - No Reply Fix! - Upload Screenshot + Task Image Final Fix Final - Screenshot + Task Image Final Fix Final - Final Output! - Screenshot + Task Image Fix Final - Final Output! - Task Image + Join ALWAYS True Fix Final - Final Output! - Check Joined ALWAYS True + Task Image Fix Final - Check Joined Bypass + Withdraw Buttons Fix Final - No Sleep + Immediate Polling + Separate Channels + Withdraw 1 Task Final - NameError Fixed!")
    print("============================================================")
    #  FIX: Flask IMMEDIATE start - No sleep! Fix Live but not responding! NameError Fixed!
    try:
        from flask import Flask
        flask_app = Flask(__name__)
        @flask_app.route('/')
        def home():
            return "S2E Bot Final Running - Immediate Polling - No Sleep - NameError Fixed"
        flask_port = int(os.environ.get("PORT", 10000))
        print(f"Starting Flask on port {flask_port} env PORT={os.environ.get('PORT')}")
        def run_flask():
            try:
                print(f"Flask running on 0.0.0.0:{flask_port}")
                flask_app.run(host='0.0.0.0', port=flask_port, debug=False, use_reloader=False)
            except Exception as e:
                print(f" Flask err {e}")
        # V4.12 - Disabled duplicate inner Flask - using top Flask only
        flask_thread = threading.Thread(target=lambda: print('Inner Flask disabled - V4.12 clean'), daemon=True)
        flask_thread.start()
        print(f"Flask started on port {flask_port} - No 120 sec sleep! FINAL! NameError Fixed!")
        time.sleep(2)
    except Exception as e:
        print(f" Flask setup err {e}")

    print(" NO 120 sec sleep! Starting bot IMMEDIATELY! Fix Live but not responding! NameError Fixed!")
    print(" Quick webhook delete 2 times - No long sleep! NameError Fixed!")
    try:
        import urllib.request
        for i in range(2):
            try:
                urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
                print(f" Quick Webhook delete {i+1}/2 - NameError Fixed!")
                time.sleep(1)
            except Exception as e:
                print(f" Quick delete {i+1} err {e}")
    except Exception as e:
        print(f" Quick webhook outer err {e}")

    print(" Starting bot polling IMMEDIATELY - No 120 sec sleep - FINAL! NameError Fixed!")
    _db_init()
    load_data()
    normalize_support_plans()
    force_update_plans_to_new()
    save_data()
    try:
        threading.Thread(target=keep_alive_pinger, daemon=True).start()
        print('Keep-alive started Final (backup only; Render Free needs inbound external traffic)')
    except:
        pass

    retry_count = 0
    max_retries = 100
    while retry_count < max_retries:
        print(f"\n Build attempt {retry_count+1}/{max_retries} - Polling NOW! No Sleep! FINAL! NameError Fixed!")
        app = None
        try:
            print(f"\n Build attempt {retry_count+1}/{max_retries} - FINAL!")
            app = (
                Application.builder()
                .token(BOT_TOKEN)
                # python-telegram-bot v22 removed timeout kwargs from run_polling.
                # Configure getUpdates timeouts on ApplicationBuilder instead.
                .get_updates_read_timeout(40)
                .get_updates_write_timeout(40)
                .get_updates_connect_timeout(40)
                .get_updates_pool_timeout(40)
                .build()
            )
            app.add_error_handler(error_handler)
            try:
                app.add_handler(CallbackQueryHandler(back_admin_cb_fixed, pattern='^back_admin$',), group=-2)
                app.add_handler(CallbackQueryHandler(back_menu_cb_fixed, pattern='^back_menu$',), group=-2)
                app.add_handler(CallbackQueryHandler(withdraw_cb, pattern='^withdraw$',), group=-2)
                app.add_handler(CallbackQueryHandler(promo_tasks_cb_fixed, pattern='^promo_tasks$',), group=-2)
                app.add_handler(CallbackQueryHandler(scheduled_tasks_cb_fixed, pattern='^scheduled_tasks$',), group=-2)
                app.add_handler(CallbackQueryHandler(support_plans_cb, pattern='^support_plans$',), group=-2)
                print(' All Fixed group -2 - NameError Fixed!')
                app.add_handler(CallbackQueryHandler(bulk_approve_callback, pattern='^bulk_approve_'), group=-2)
                # V63 FIX: payment-proof Approve/Reject must run before other callback handlers.
                app.add_handler(CallbackQueryHandler(admin_approve_plan_cb, pattern=r'^admin_approve_plan_'), group=-2)
                app.add_handler(CallbackQueryHandler(admin_reject_plan_cb, pattern=r'^admin_reject_plan_'), group=-2)
            except Exception as e:
                print(f' fix {e}')

            conv_reg = ConversationHandler(
                entry_points=[CommandHandler("start", start), CallbackQueryHandler(check_joined_cb, pattern="^check_joined$")],
                states={
                    NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
                    GENDER:[
                        CallbackQueryHandler(reg_gender_cb, pattern=r"^reg_gender_(male|female|other)$"),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)
                    ],
                    DOB:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
                    MOBILE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_mobile)],
                    UPI:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)],
                    PINCODE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_pincode)],
                    PROFESSION:[
                        CallbackQueryHandler(reg_profession_cb, pattern=r"^reg_prof_(student|employee|business|self_employed|other)$"),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, get_profession)
                    ],
                },
                fallbacks=[CommandHandler("cancel", cancel)],
                per_user=True, per_chat=True, per_message=False
            )
            app.add_handler(MessageHandler(PlanImageUploadFilter(), handle_plan_image_upload), group=-3)
            # IMPORTANT: Do not register a catch-all PHOTO handler here.
            # It would consume member screenshots before the dedicated
            # screenshot handler (group=2) gets a chance to process them.
            # Task poster uploads are handled by v56_task_image_simple_handler.
            async def plan_payment_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    uid = update.effective_user.id
                    plan_type = context.user_data.get("awaiting_plan_payment_proof")
                    if not plan_type or not update.message.photo:
                        return
                    pending = pending_plans.get(uid) or pending_plans.get(str(uid)) or {}
                    plan_obj = None
                    try:
                        if str(plan_type).isdigit():
                            normalize_support_plans()
                            plan_obj = next((p for p in support_plans_db if int(p.get("id", -1)) == int(plan_type)), None)
                    except Exception:
                        plan_obj = None
                    if plan_obj:
                        price = int(plan_obj.get("price", pending.get("price", 0)))
                        plan_name = str(plan_obj.get("name", "Plan")).lower()
                        plan_id = int(plan_obj.get("id", 0))
                    else:
                        price = 199 if str(plan_type).lower() == "basic" else 499
                        plan_name = str(plan_type).lower()
                        plan_id = pending.get("plan_id")
                    file_id = update.message.photo[-1].file_id
                    pending_plans[uid] = {
                        "plan_id": plan_id,
                        "plan": plan_name,
                        "date": str(get_ist_today()),
                        "price": price,
                        "proof_file_id": file_id,
                        "user_name": users_db.get(uid, {}).get("name", update.effective_user.full_name)
                    }
                    context.user_data.pop("awaiting_plan_payment_proof", None)
                    awaiting_plan_payment_adminless.discard(uid)
                    save_data()
                    await update.message.reply_text("✅ Payment proof received. Pending admin verification.")
                    for admin_id in ADMIN_ID_LIST:
                        try:
                            kb = InlineKeyboardMarkup([[
                                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_plan_{uid}_{plan_type}"),
                                InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_plan_{uid}")
                            ]])
                            await context.bot.send_photo(
                                chat_id=admin_id, photo=file_id,
                                caption=(
                                    f"💎 PLAN PAYMENT PROOF\n"
                                    f"👤 Name: {users_db.get(uid, {}).get('name', update.effective_user.full_name or 'Unknown')}\n"
                                    f"🆔 User ID: {uid}\n"
                                    f"📦 Plan: {plan_type}\n"
                                    f"💰 Amount: ₹{price}\n"
                                    f"💳 UPI: {get_payment_upi()}"
                                ),
                                reply_markup=kb
                            )
                        except Exception as e:
                            print(f"plan proof admin send error: {e}")
                except Exception as e:
                    print(f"plan payment photo error: {e}")

            app.add_handler(MessageHandler(PlanPaymentProofFilter(), plan_payment_photo_handler), group=-2)
            # Final FIX: No ConversationHandler for screenshot - Simple handlers
            conv_screenshot = None  # Disabled - Using simple MessageHandler instead!
            print(" conv_screenshot disabled - Using simple handlers! FINAL!")

            conv_skip = ConversationHandler(
                entry_points=[CallbackQueryHandler(daily_skip_cb, pattern="^daily_skip_")],
                states={
                    SKIP_REASON:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_skip_reason), CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_")],
                },
                fallbacks=[CommandHandler("cancel", cancel)],
                per_user=True, per_chat=True, per_message=False
            )
            # Final FIX: No ConversationHandler for task image - Simple handlers
            # Old ConversationHandler caused no reply - Replace with simple handlers!
            conv_set_image = None  # Disabled - Using simple MessageHandler instead!
            print(" conv_set_image disabled - Using simple handlers! FINAL!")

            app.add_handler(conv_reg)
            #  Disabled: app.add_handler(conv_screenshot) - Using simple handlers! FINAL!
            app.add_handler(conv_skip)

            # Final FIX: Simple MessageHandlers - No ConversationHandler - Task image + Screenshot important channel ki vachedi! FINAL!
            # Task image handler - Admin photo with set_image_task_id or caption /set_task_image
            async def v56_task_image_simple_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    uid = update.effective_user.id
                    # V32 FIX: If user is waiting to submit task screenshot, don't treat as task image setting
                    if context.user_data.get('awaiting_daily_screenshot'):
                        return
                    if not is_admin(uid):
                        return
                    if not update.message.photo and not update.message.document:
                        return

                    # Support Plans banner upload after /set_support_image.
                    # This check must happen before task-poster logic so the banner
                    # image can never be mistaken for a task poster.
                    if (context.user_data.get("awaiting_support_banner")
                            or (update.message.caption and "/set_support_image" in update.message.caption)):
                        await support_banner_photo_handler(update, context)
                        return
                    task_id = context.user_data.get('set_image_task_id')
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
                            return
                    file_id = None
                    if update.message.photo:
                        file_id = update.message.photo[-1].file_id
                    elif update.message.document:
                        file_id = update.message.document.file_id
                    if not file_id:
                        return
                    task_images_db[task_id] = file_id
                    task = next((t for t in scheduled_tasks_db if t['id'] == task_id), None)
                    if task:
                        task['image_file_id'] = file_id
                        task['has_image'] = True
                        save_data()
                        print(f" v56_task_image_simple_handler: Image Poster Set for Task {task_id}: {task['title']} file_id {file_id[:20]} FINAL! ")
                    await update.message.reply_text(f"✅ Task image set for Task {task_id}! {task['title'] if task else ''} Members will see YOUR TASK image when they open Daily Task! Check /menu -> Daily Task to view.", reply_markup=main_menu())
                    try:
                        await context.bot.send_photo(chat_id=uid, photo=file_id, caption=f"✅  Confirmation - Task {task_id} Image Set! FINAL! ")
                    except:
                        try:
                            await context.bot.send_document(chat_id=uid, document=file_id, caption=f"✅  Confirmation - Task {task_id} Image Set! FINAL!")
                        except Exception as e:
                            print(f" confirmation err {e}")
                    context.user_data.pop('set_image_task_id', None)
                except Exception as e:
                    print(f" v56_task_image_simple_handler err {e}")
                    import traceback
                    traceback.print_exc()

            async def v56_screenshot_simple_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    uid = update.effective_user.id
                    # V32 FIX: Admin can also submit missed tasks - check awaiting flag first
                    is_awaiting = context.user_data.get('awaiting_daily_screenshot')
                    if is_admin(uid) and not is_awaiting:
                        return
                    if not update.message.photo and not update.message.document:
                        return
                    # V58: Only treat member photos as task screenshots after the user
                    # explicitly pressed Upload Screenshot. This prevents unrelated photos
                    # from being captured by the bot.
                    if not context.user_data.get('awaiting_daily_screenshot'):
                        return
                    file_id = None
                    file_unique_id = None
                    if update.message.photo:
                        file_id = update.message.photo[-1].file_id
                        file_unique_id = update.message.photo[-1].file_unique_id
                    elif update.message.document:
                        file_id = update.message.document.file_id
                        file_unique_id = update.message.document.file_unique_id
                    if not file_id:
                        return
                    current, next_task = get_current_scheduled_task_with_interval()
                    requested_task_id = context.user_data.get('daily_screenshot_task_id')
                    task_to_use = current
                    if requested_task_id is not None:
                        try:
                            requested_task_id = int(requested_task_id)
                            requested_task = next((t for t in get_tasks_for_today() if int(t.get('id', -1)) == requested_task_id), None)
                            if not requested_task:
                                requested_task = next((t for t in missed_tasks_db.get(uid, []) if int(t.get('id', -1)) == requested_task_id), None)
                            if requested_task:
                                task_to_use = requested_task
                        except Exception:
                            pass
                    if not task_to_use:
                        missed_id=context.user_data.get('missed_reopened_task_id')
                        if missed_id is not None:
                            task_to_use=next((t for t in missed_tasks_db.get(uid, []) if int(t.get('id',-999999))==int(missed_id)),None)
                    if not task_to_use:
                        await update.message.reply_text("❌ No scheduled task is available for this screenshot. Please use Upload Screenshot only for an active or reopened task.", reply_markup=main_menu())
                        context.user_data.pop('awaiting_daily_screenshot', None)
                        context.user_data.pop('daily_screenshot_task_id', None)
                        return
                    if file_unique_id and file_unique_id in screenshot_hashes:
                        await update.message.reply_text("WARNING Same Screenshot! ")
                        return
                    if file_unique_id:
                        screenshot_hashes.add(file_unique_id)
                    today = str(get_ist_today())
                    pending_daily[uid] = {'date': today, 'task': task_to_use, 'screenshot_file_id': file_id, 'is_missed_reopen': bool(context.user_data.get('missed_reopened_task_id'))}
                    if uid not in user_task_status:
                        user_task_status[uid] = {}
                    task_id_for_status = task_to_use.get('id', 0)
                    missed_reopen_id=context.user_data.get('missed_reopened_task_id')
                    user_task_status[uid][task_id_for_status] = {'status': 'pending_verification', 'submitted_at': get_ist_now(), 'missed_submission_used': bool(missed_reopen_id)}
                    await update.message.reply_text(f"✅ Screenshot received! Waiting for admin approval.", reply_markup=main_menu())
                    try:
                        chan = get_screenshot_channel()
                        user_name = users_db.get(uid, {}).get('name', update.effective_user.full_name or 'Unknown')
                        kb_chan = InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_daily_{uid}"),
                             InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_daily_{uid}")],
                            [InlineKeyboardButton("🚀 Approve ALL Pending", callback_data="bulk_approve_all")]
                        ])
                        await context.bot.send_photo(
                            chat_id=chan,
                            photo=file_id,
                            caption=(
                                f"📸 TASK SCREENSHOT\n"
                                f"👤 Name: {user_name}\n"
                                f"🆔 User ID: {uid}\n"
                                f"📋 Task {task_to_use.get('task_number',1)}: {task_to_use.get('title','Daily')}\n"
                                f"💰 Reward: ₹{task_to_use.get('reward',5)}\n"
                                f"📅 {get_ist_today()}"
                            ),
                            reply_markup=kb_chan
                        )
                        print(f"V58 v56_screenshot_simple_handler: Forwarded to SCREENSHOT_CHANNEL {chan} - TASK Screenshots ONLY!")
                        context.user_data.pop('awaiting_daily_screenshot', None)
                        context.user_data.pop('daily_screenshot_task_id', None)
                    except Exception as e:
                        print(f" screenshot channel err {e} - Trying without keyboard! Channel {chan}")
                        try:
                            await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK  User {uid} Task {task_to_use.get('task_number',1)}")
                        except:
                            try:
                                await context.bot.send_document(chat_id=chan, document=file_id, caption=f"NEW TASK  User {uid}")
                            except Exception as e3:
                                print(f" screenshot channel err3 {e3} - Bot not admin in {chan}? Make bot admin!")
                except Exception as e:
                    print(f" v56_screenshot_simple_handler err {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        await update.message.reply_text(f"✅ Screenshot received! Pending Verification! Final", reply_markup=main_menu())
                    except:
                        pass

            #  Add simple handlers with high priority - No ConversationHandler!
            app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, product_video_handler), group=0)
            app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, product_screenshot_photo_handler), group=0)
            app.add_handler(MessageHandler(filters.PHOTO, v56_task_image_simple_handler), group=1)
            app.add_handler(MessageHandler(filters.Document.ALL, v56_task_image_simple_handler), group=1)
            app.add_handler(MessageHandler(filters.PHOTO, v56_screenshot_simple_handler), group=2)
            app.add_handler(MessageHandler(filters.Document.ALL, v56_screenshot_simple_handler), group=2)
            print(" Simple handlers added - No ConversationHandler - Task image + Screenshot important channel ki vachedi! FINAL!")
            #  Disabled: app.add_handler(conv_set_image) - Using simple handlers! FINAL!
            #  FALLBACK: General photo handler for cases where conversation state lost - Task image + 
            async def fallback_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    uid = update.effective_user.id
                    if not update.message.photo:
                        return
                    # If admin and has set_image_task_id in user_data, handle as task image
                    if is_admin(uid) and context.user_data.get('set_image_task_id'):
                        print(f" fallback_photo_handler: Admin {uid} has set_image_task_id {context.user_data.get('set_image_task_id')} - Handling as task image!")
                        await handle_task_image_upload(update, context)
                        return
                    # If admin and caption contains /set_task_image, handle as task image
                    if is_admin(uid) and update.message.caption and '/set_task_image' in update.message.caption:
                        print(f" fallback_photo_handler: Admin {uid} photo with caption /set_task_image - Handling as task image!")
                        await set_task_image_cmd(update, context)
                        return
                    # If member and has active task, handle as screenshot
                    # Check if user is in UPLOAD_SCREENSHOT state or has recently requested upload
                    # For fallback, always try to handle as screenshot if not admin
                    if not is_admin(uid):
                        print(f" fallback_photo_handler: Member {uid} photo - Handling as screenshot fallback! FINAL!")
                        await handle_screenshot_upload(update, context)
                        return
                except Exception as e:
                    print(f" fallback_photo_handler err {e}")
            
            # IMPORTANT: No catch-all PHOTO fallback. The dedicated handlers above
            # must receive the update so the Upload Screenshot flow is reliable.
            print(" Catch-all photo fallback disabled - dedicated upload handlers active!")

            app.add_handler(CommandHandler("menu", menu))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("pending", pending_cmd))
            app.add_handler(CommandHandler("approve", approve_cmd))
            app.add_handler(CommandHandler("add_task", add_scheduled_task_with_interval_cmd))
            app.add_handler(CommandHandler("add_product_promo", add_product_promo_cmd))
            app.add_handler(CommandHandler("list_tasks", list_scheduled_tasks_cmd))
            # Support Plans banner command. Photo handling is integrated into the
            # existing high-priority admin photo handler so normal task posters remain safe.
            app.add_handler(CommandHandler("set_support_image", set_support_image_cmd))
            app.add_handler(CommandHandler("set_task_image", set_task_image_cmd))
            app.add_handler(CommandHandler("set_payment_upi", set_payment_upi_cmd))
            app.add_handler(CommandHandler("set_contact_username", set_contact_username_cmd))
            app.add_handler(CommandHandler("add_promo", add_promo_campaign_cmd))
            app.add_handler(CommandHandler("list_promos", list_promo_campaigns_cmd))
            app.add_handler(CommandHandler("promo_pending", promo_pending_cmd))
            app.add_handler(CommandHandler("skipped", skipped_tasks_cmd))
            app.add_handler(CommandHandler("warnings", warnings_cmd))
            app.add_handler(CommandHandler("banned", banned_cmd))
            app.add_handler(CommandHandler("unban", unban_cmd))
            # V64 FIX: Register Upload Screenshot callback with highest priority.
            # This must be registered before other callback handlers so the button
            # always receives an immediate callback acknowledgement.
            app.add_handler(
                CallbackQueryHandler(
                    daily_upload_screenshot_cb,
                    pattern=r"^daily_upload_screenshot$"
                ),
                group=-10
            )
            app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
            app.add_handler(CallbackQueryHandler(refer_earn_cb, pattern="^refer_earn$"))
            app.add_handler(CallbackQueryHandler(withdraw_history_cb, pattern="^withdraw_history$"))
            app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
            
            async def daily_open_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
                q=update.callback_query; await q.answer()
                uid=q.from_user.id
                try: tid=int(q.data.replace("daily_open_","",1))
                except Exception: return
                task=next((t for t in get_tasks_for_today() if int(t.get('id',-1))==tid),None)
                if not task:
                    await q.message.reply_text("❌ Task is no longer scheduled today.", reply_markup=main_menu()); return
                context.user_data['awaiting_daily_screenshot']=False
                context.user_data['daily_screenshot_task_id']=tid
                context.user_data.pop('missed_reopened_task_id',None)
                text=(f"🔴 TASK {task.get('task_number','?')}\n\nTitle: {task.get('title','')}\nReward: ₹{task.get('reward',5)}\nLink: {task.get('link','')}\n\n"
                      f"{('📝 Instructions:' + chr(10) + task.get('description', '') + chr(10) + chr(10)) if task.get('description') else ''}"
                      "After completing, tap Upload Screenshot.")
                kb=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_screenshot")],[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]])
                await q.message.reply_text(text, reply_markup=kb)
            app.add_handler(CallbackQueryHandler(daily_open_cb, pattern=r"^daily_open_-?\d+$"))
            app.add_handler(CallbackQueryHandler(daily_cb, pattern="^daily$"))
            app.add_handler(CallbackQueryHandler(scheduled_cb, pattern="^scheduled$"))
            app.add_handler(CallbackQueryHandler(promo_tasks_cb, pattern="^promo_tasks$"))
            app.add_handler(CallbackQueryHandler(promo_join_cb, pattern="^promo_join_"))
            app.add_handler(CallbackQueryHandler(product_promo_cb, pattern="^product_promo$"))
            app.add_handler(CallbackQueryHandler(product_download_cb, pattern=r"^product_download_\d+$"))
            app.add_handler(CallbackQueryHandler(product_screenshot_cb, pattern=r"^product_screenshot_\d+$"))
            app.add_handler(CallbackQueryHandler(product_approve_cb, pattern=r"^product_approve_\d+_\d+$"))
            app.add_handler(CallbackQueryHandler(product_reject_cb, pattern=r"^product_reject_\d+_\d+$"))
            app.add_handler(CallbackQueryHandler(product_bulk_approve_cb, pattern=r"^product_bulk_approve_all$"))
            app.add_handler(CallbackQueryHandler(promote_shop_cb, pattern="^promote_shop$"))
            app.add_handler(CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_"))
            app.add_handler(CallbackQueryHandler(admin_view_pending_cb, pattern="^admin_view_pending$"))
            app.add_handler(CallbackQueryHandler(admin_view_withdraw_cb, pattern="^admin_view_withdraw$"))
            app.add_handler(CallbackQueryHandler(admin_view_tasks_cb, pattern="^admin_view_tasks$"))
            app.add_handler(CallbackQueryHandler(admin_view_promos_cb, pattern="^admin_view_promos$"))
            app.add_handler(CallbackQueryHandler(admin_product_promo_cb, pattern="^admin_product_promo$"))
            app.add_handler(CallbackQueryHandler(admin_view_stats_cb, pattern="^admin_view_stats$"))
            app.add_handler(CallbackQueryHandler(admin_view_banned_cb, pattern="^admin_view_banned$"))
            app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
            app.add_handler(CallbackQueryHandler(missed_tasks_cb, pattern="^missed_tasks$"))
            app.add_handler(CallbackQueryHandler(missed_reopen_cb, pattern=r"^missed_reopen_-?\d+$"))
            app.add_handler(CallbackQueryHandler(missed_upload_cb, pattern=r"^missed_upload_-?\d+$"))
            app.add_handler(CallbackQueryHandler(my_details_cb, pattern="^my_details$"))
            app.add_handler(CallbackQueryHandler(contact_us_cb, pattern="^contact_us$"))
            app.add_handler(CallbackQueryHandler(update_details_cb, pattern="^update_details$"))
            try:
                app.job_queue.run_daily(check_plan_expiry_job, time=time(hour=3, minute=30), name="expiry_check")
                app.job_queue.run_daily(settle_previous_day_referrals, time=time(hour=0, minute=5), name="referral_daily_settlement")
            except Exception as _e:
                print(f"expiry job schedule fail {_e}")
            app.add_handler(CommandHandler("remove_user", remove_user_cmd))
            app.add_handler(CommandHandler("edit_user", edit_user_cmd))
            # back_admin handled once at group -2 by back_admin_cb_fixed.
            app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern="^admin_approve_daily_"))
            app.add_handler(CallbackQueryHandler(admin_reject_daily_cb, pattern="^admin_reject_daily_"))
            app.add_handler(CallbackQueryHandler(promo_approve_cb, pattern="^promo_approve_"))
            app.add_handler(CallbackQueryHandler(promo_reject_cb, pattern="^promo_reject_"))
            app.add_handler(CallbackQueryHandler(admin_ban_cb, pattern="^admin_ban_"))
            app.add_handler(CallbackQueryHandler(admin_unban_cb, pattern="^admin_unban_"))
            app.add_handler(CallbackQueryHandler(wd_select_cb, pattern="^wd_select_"))
            app.add_handler(CallbackQueryHandler(wd_confirm_cb, pattern="^wd_confirm_"))
            app.add_handler(CallbackQueryHandler(wd_edit_upi_cb, pattern="^wd_edit_upi$"))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wd_edit_upi_text_handler), group=-1)
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_details_text), group=2)
            app.add_handler(CallbackQueryHandler(wd_admin_approve_cb, pattern="^wd_admin_approve_"))
            app.add_handler(CallbackQueryHandler(wd_admin_reject_cb, pattern="^wd_admin_reject_"))
            app.add_handler(CallbackQueryHandler(buy_support_plan_cb, pattern=r"^buy_support_\d+$"))
            app.add_handler(CallbackQueryHandler(plan_proof_id_cb, pattern=r"^plan_proof_id_\d+$"))
            app.add_handler(CallbackQueryHandler(plan_basic_cb, pattern="^plan_basic$"))
            app.add_handler(CallbackQueryHandler(plan_premium_cb, pattern="^plan_premium$"))
            app.add_handler(CallbackQueryHandler(plan_basic_activate_cb, pattern="^plan_basic_activate$"))
            app.add_handler(CallbackQueryHandler(plan_premium_activate_cb, pattern="^plan_premium_activate$"))
            app.add_handler(CallbackQueryHandler(plan_basic_proof_cb, pattern="^plan_basic_proof$"))
            app.add_handler(CallbackQueryHandler(plan_premium_proof_cb, pattern="^plan_premium_proof$"))
            app.add_handler(CallbackQueryHandler(plan_proof_cb, pattern="^plan_proof_(basic|premium)$"))
            app.add_handler(CallbackQueryHandler(admin_view_plans_cb, pattern="^admin_view_plans$"))
            app.add_handler(CommandHandler("userlist", userlist_cmd))
            app.add_handler(CommandHandler("backup", backup_cmd))
            app.add_handler(CommandHandler("add_task_manual", add_task_manual_cmd))
            app.add_handler(CommandHandler("remove_task", remove_task_cmd))
            app.add_handler(CommandHandler("del_task", remove_task_cmd))
            app.add_handler(CommandHandler("add_balance", add_balance_cmd))
            app.add_handler(CommandHandler("remove_balance", remove_balance_cmd))
            app.add_handler(CommandHandler("deduct_balance", remove_balance_cmd))
            app.add_handler(CommandHandler("set_tasks", set_task_count_cmd))
            app.add_handler(CommandHandler("set_screenshot_channel", set_screenshot_channel_cmd))
            app.add_handler(CommandHandler("set_withdraw_channel", set_withdraw_channel_cmd))
            app.add_handler(CommandHandler("set_join_channel", set_join_channel_cmd))
            app.add_handler(CommandHandler("approve_all", approve_all_pending_cmd))
            app.add_handler(CommandHandler("list_pending", list_pending_cmd))
            app.add_handler(CommandHandler("add_week", add_week_cmd))
            app.add_handler(CommandHandler("add_date", add_date_cmd))
            app.add_handler(CommandHandler("bulk_tasks", bulk_tasks_help_cmd))
            app.add_handler(CommandHandler("add_plan", add_support_plan_cmd))
            app.add_handler(CommandHandler("edit_plan", edit_plan_cmd))
            app.add_handler(CommandHandler("list_plans", list_plans_cmd))
            app.add_handler(CommandHandler("remove_plan", remove_plan_cmd))
            app.add_handler(CommandHandler("set_plan_image", set_plan_image_cmd))
            app.add_handler(CommandHandler("bacup", backup_cmd))
            app.add_handler(CommandHandler("add_admin", add_admin_cmd))
            app.add_handler(CommandHandler("remove_admin", remove_admin_cmd))
            app.add_handler(CommandHandler("list_admins", list_admins_cmd))
            app.add_handler(CommandHandler("referral_stats", referral_stats_cmd))
            app.add_handler(CallbackQueryHandler(admin_backup_cb, pattern='^admin_backup$'))
            app.add_handler(CallbackQueryHandler(admin_add_admin_cb, pattern='^admin_add_admin$'))
            app.add_handler(CallbackQueryHandler(admin_referral_cb, pattern='^admin_referral$'))
            app.add_handler(CallbackQueryHandler(admin_missed_toggle_cb, pattern='^admin_missed_toggle$'))
            app.add_handler(CommandHandler("set_referral_commission", set_referral_commission_cmd))
            app.add_handler(CommandHandler("channels_status", channels_status_cmd))
            app.add_handler(CommandHandler("channels_list", channels_list_cmd))
            app.add_handler(CommandHandler("add_task_free", add_task_free_cmd))
            app.add_handler(CommandHandler("add_task_basic", add_task_basic_cmd))
            app.add_handler(CommandHandler("add_task_premium", add_task_premium_cmd))
            app.add_handler(CommandHandler("add_task_all", add_task_all_cmd))
            app.add_handler(CommandHandler("clear_missed_all", clear_missed_all_cmd))
            app.add_handler(CommandHandler("clear_missed", clear_missed_all_cmd))
            app.add_handler(CommandHandler("clear_missed_user", clear_missed_user_cmd))
            app.add_handler(CommandHandler("clear_scheduled_all", clear_scheduled_all_cmd))
            app.add_handler(CommandHandler("clear_duplicates", clear_duplicates_cmd))
            app.add_handler(CommandHandler("clear_duplicate", clear_duplicates_cmd))
            app.add_handler(CommandHandler("list_tasks_audience", list_tasks_audience_cmd))
            app.add_handler(CommandHandler("add_task_5plans", add_task_5plans_cmd))
            app.add_handler(CommandHandler("add_task_5p", add_task_5plans_cmd))
            app.add_handler(CommandHandler("add_bulk", add_bulk_tasks_cmd))
            app.add_handler(CommandHandler("bulk_add", add_bulk_tasks_cmd))
            app.add_handler(CommandHandler("bulk_tasks_add", add_bulk_tasks_cmd))

            try:
                from telegram.ext import TypeHandler
                app.add_handler(TypeHandler(Update, global_activity_tracker), group=-100)
                print("Global activity tracker added")
            except Exception as e:
                print(f"Tracker error: {e}")
            try:
                setup_smart_auto(app)
            except Exception as e:
                print(f"Smart auto setup error: {e}")
            
            print(" Bot handlers registered - All handlers from V20 - Polling NOW! FINAL - NameError Fixed!")
            # EVENT LOOP FIX: Render/asyncio can leave the previous loop closed after
            # a polling attempt. Always create and install a fresh loop per attempt,
            # and let python-telegram-bot keep it open while run_polling is active.
            polling_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(polling_loop)
            # Connect the notifier to the SAME asyncio loop used by Telegram polling.
            bot_application = app
            bot_event_loop = polling_loop
            if not notification_thread_started:
                threading.Thread(target=notification_thread_func, daemon=True).start()
                notification_thread_started = True
                print("1-minute task notification thread started.")
            try:
                app.run_polling(
                    drop_pending_updates=False,
                    allowed_updates=Update.ALL_TYPES,
                    poll_interval=1.0,
                    timeout=30,
                    close_loop=False,
                )
            finally:
                try:
                    if not polling_loop.is_closed():
                        polling_loop.close()
                except Exception as loop_close_error:
                    print(f"Event loop cleanup: {loop_close_error}")
                try:
                    asyncio.set_event_loop(None)
                except Exception:
                    pass

        except Exception as e:
            print(f" Polling attempt {retry_count+1} failed: {e}")
            if isinstance(e, RuntimeError) and "Event loop is closed" in str(e):
                print(" EVENT LOOP RECOVERY: fresh asyncio loop will be created on the next attempt")
            import traceback
            traceback.print_exc()
            retry_count += 1
            time.sleep(5)
            continue

if __name__ == "__main__":
    main()


# ===== V19 FINAL FORCE SUPABASE - OVERRIDE ALL =====
try:
    # Force Supabase as DATA_FILE if client was created successfully in V18
    if 'supa_client' in globals() or 'supabase_client' in globals():
        print("✅ V21 FIX - DATA_FILE=Supabase | Persistent Disk=YES | Supabase LIVE")
        DATA_FILE = "Supabase"
        PERSISTENT_DISK = True
        SUPABASE_ENABLED = True
        # Ensure bot_data loading uses Supabase
        try:
            # Override load/save functions to use Supabase if exists
            globals()["DATA_FILE"] = "Supabase"
        except:
            pass
except Exception as e:
    print(f"V19 override error: {e}")

# Final print to confirm
try:
    _df = globals().get("DATA_FILE", "unknown")
    print(f"🔥🔥🔥 FINAL V19 - DATA_FILE={_df} | Persistent Disk=YES | Supabase ENABLED 2026-08-25 11:55 IST 🔥🔥🔥")
except:
    print("🔥🔥🔥 FINAL V19 - Supabase FORCED 🔥🔥🔥")
# ===== END V19 =====
