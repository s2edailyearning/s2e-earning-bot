import warnings
warnings.filterwarnings('ignore')
import os, re, threading, json, asyncio
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
        return f"S2E Bot Alive V4.6 - {get_ist_now()} - OK", 200
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


# === V4.12 SUPABASE PERSISTENCE FIX ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_SERVICE_KEY", "")
supabase_client = None
SUPABASE_ENABLED = False

def init_supabase():
    global supabase_client, SUPABASE_ENABLED
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                from supabase import create_client
                supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                SUPABASE_ENABLED = True
                print(f"✅ Supabase enabled - URL: {SUPABASE_URL[:30]}...")
                return True
            except ImportError as ie:
                print(f"⚠️ supabase-py not installed: {ie} - Installing fallback")
                SUPABASE_ENABLED = False
                return False
            except Exception as e:
                print(f"⚠️ Supabase init failed: {e}")
                SUPABASE_ENABLED = False
                return False
        else:
            print("ℹ️ SUPABASE_URL/KEY not set - Using local JSON (will lose data on deploy!)")
            SUPABASE_ENABLED = False
            return False
    except Exception as e:
        print(f"Supabase init outer error: {e}")
        SUPABASE_ENABLED = False
        return False


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


# VERSION: V4.12 - RENDER 2 MIN FIX - FINAL PERFECT - 2026-08-25 09:12 IST
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
print("FINAL V4.12 - RENDER 2 MIN SLEEP FIX + FLASK FIX + DROP_PENDING FIX - 2026-08-25 09:12 IST")
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
                    open_dt = datetime.combine(get_ist_today(), task['open_time_obj'], tzinfo=IST)
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

        # Pay the referrer 10% (or admin-configured percentage) only after successful activation.
        ref_id = referral_map.get(uid)
        already_plan_commission = any(
            str(e.get("type")) == "plan" and e.get("source_uid") == uid and e.get("description", "").endswith(f"Plan {int(plan.get('id',0))} activation")
            for e in referral_commission_ledger.get(ref_id, [])
        ) if ref_id else False
        if ref_id and not already_plan_commission:
            add_referral_commission(ref_id, price * float(REFERRAL_PLAN_COMMISSION_PERCENT) / 100.0, "plan", 1, uid, f"Plan {int(plan.get('id',0))} activation")
            save_data()

        user_plans[str(uid)] = {
            "plan": name.lower(),
            "plan_id": int(plan.get("id", 0)),
            "status": "active",
            "price": price,
            "daily_limit": daily,
            "date": str(get_ist_today()),
            "expiry": str(expiry),
        }
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
REFERRAL_PLAN_COMMISSION_PERCENT = 10
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
pending_referrals = {}
referral_earnings = {}
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


# === PERSISTENT STORAGE - RESTORED / SAFE JSON VERSION ===
# The previous build called load_data()/save_data() from main(), but those
# functions were missing from this file. That caused Render to stop with:
# NameError: name 'load_data' is not defined
# Persistent storage path. On Render, mount a Persistent Disk at /var/data.
# DATA_FILE can still override the path through an environment variable.
_render_disk = "/var/data"
_default_data_file = os.path.join(_render_disk, "bot_data.json") if os.path.isdir(_render_disk) else "bot_data.json"
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


def save_data():
    """Persist to Supabase if enabled, else to bot_data.json"""
    try:
        state_names = [
            "users_db", "referrals_db", "tasks_db", "daily_done", "bonus_balance",
            "banned_users", "warnings_db", "pending_daily", "user_plans",
            "pending_plans", "referral_map", "pending_referrals", "referral_earnings",
            "referral_commission_ledger", "daily_task_earnings", "withdraw_requests",
            "withdraw_history", "withdraw_done_date", "daily_task_count",
            "missed_tasks_db", "last_withdraw_date_db", "screenshot_hashes",
            "task_open_time", "scheduled_tasks_db", "scheduled_task_counter",
            "user_task_status", "task_notifications_sent", "skip_db",
            "promo_campaigns_db", "promo_campaign_counter", "promo_earnings_db",
            "promo_views_db", "promo_pending", "product_promo_db", "product_promo_counter", "product_promo_pending", "product_promo_approved", "task_images_db", "support_banner_db",
            "admin_names_db", "support_plans_db", "pending_plan_purchases",
            "support_plan_image_file_id", "pending_plans",
        ]
        data = {}
        for name in state_names:
            if name in globals():
                data[name] = _json_safe(globals()[name])

        # Try Supabase first
        if SUPABASE_ENABLED and supabase_client:
            try:
                # Upsert into bot_data table id=1
                payload = {"id": 1, "data": data, "updated_at": get_ist_now() if 'get_ist_now' in globals() else None}
                # Supabase table name: bot_data (user said he created)
                # Try bot_data first, if fails try bot_data_storage
                try:
                    res = supabase_client.table("bot_data").upsert(payload).execute()
                    print(f"✅ Data saved to Supabase bot_data - {len(data)} sections")
                    return True
                except Exception as e1:
                    print(f"bot_data table fail {e1}, trying bot_data_storage")
                    res = supabase_client.table("bot_data_storage").upsert(payload).execute()
                    print(f"✅ Data saved to Supabase bot_data_storage - {len(data)} sections")
                    return True
            except Exception as se:
                print(f"⚠️ Supabase save failed {se}, falling back to local file")

        # Fallback local JSON
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, DATA_FILE)
        print(f"💾 Data saved to local {DATA_FILE} - {len(data)} sections")
        return True
    except Exception as e:
        print(f"Save error: {e}")
        import traceback; traceback.print_exc()
        return False



def load_data():
    """Load from Supabase if enabled, else from bot_data.json"""
    try:
        # Try Supabase first
        if SUPABASE_ENABLED and supabase_client:
            try:
                # Try bot_data table
                result = None
                try:
                    result = supabase_client.table("bot_data").select("data").eq("id", 1).execute()
                except Exception as e1:
                    print(f"bot_data select fail {e1}, trying bot_data_storage")
                    result = supabase_client.table("bot_data_storage").select("data").eq("id", 1).execute()

                if result and hasattr(result, 'data') and result.data and len(result.data) > 0:
                    loaded_data = result.data[0].get('data')
                    if isinstance(loaded_data, str):
                        loaded_data = json.loads(loaded_data)
                    data = loaded_data
                    print(f"✅ Data loaded from Supabase - {len(data) if isinstance(data, dict) else 0} sections")
                else:
                    print("ℹ️ No data in Supabase yet - will create on first save")
                    data = None
            except Exception as se:
                print(f"⚠️ Supabase load failed {se}, trying local file")
                data = None

            if data and isinstance(data, dict):
                container_names = [
                    "users_db", "referrals_db", "tasks_db", "daily_done", "bonus_balance",
                    "warnings_db", "pending_daily", "user_plans", "pending_plans",
                    "referral_map", "pending_referrals", "referral_earnings",
                    "referral_commission_ledger", "daily_task_earnings", "withdraw_requests",
                    "withdraw_history", "withdraw_done_date", "daily_task_count",
                    "missed_tasks_db", "last_withdraw_date_db", "task_open_time",
                    "scheduled_tasks_db", "user_task_status", "skip_db", "promo_campaigns_db", "product_promo_db",
                    "promo_earnings_db", "promo_views_db", "promo_pending", "product_promo_pending", "product_promo_approved", "task_images_db",
                    "support_banner_db", "admin_names_db", "support_plans_db",
                ]
                for name in container_names:
                    if name not in data or name not in globals():
                        continue
                    current = globals()[name]
                    loaded = data[name]
                    if isinstance(current, dict) and isinstance(loaded, dict):
                        current.clear()
                        current.update(loaded)
                    elif isinstance(current, list) and isinstance(loaded, list):
                        current.clear()
                        current.extend(loaded)

                if "banned_users" in data:
                    try:
                        banned_users.clear()
                        banned_users.update(set(data["banned_users"]) if isinstance(data["banned_users"], list) else data["banned_users"])
                    except: pass
                if "screenshot_hashes" in data and "screenshot_hashes" in globals():
                    try:
                        screenshot_hashes.clear()
                        screenshot_hashes.update(data["screenshot_hashes"] if isinstance(data["screenshot_hashes"], dict) else {})
                    except: pass
                # other sets/dicts
                for extra in ["scheduled_task_counter", "promo_campaign_counter", "product_promo_counter"]:
                    if extra in data:
                        try:
                            globals()[extra] = data[extra]
                        except: pass
                print(f"✅ Supabase data restored")
                return True
            # if Supabase empty, fall through to local file attempt

        # Fallback local file
        if not os.path.exists(DATA_FILE):
            print("No bot_data.json found - starting fresh")
            return False
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            print("Load error: not JSON object")
            return False

        container_names = [
            "users_db", "referrals_db", "tasks_db", "daily_done", "bonus_balance",
            "warnings_db", "pending_daily", "user_plans", "pending_plans",
            "referral_map", "pending_referrals", "referral_earnings",
            "referral_commission_ledger", "daily_task_earnings", "withdraw_requests",
            "withdraw_history", "withdraw_done_date", "daily_task_count",
            "missed_tasks_db", "last_withdraw_date_db", "task_open_time",
            "scheduled_tasks_db", "user_task_status", "skip_db", "promo_campaigns_db", "product_promo_db",
            "promo_earnings_db", "promo_views_db", "promo_pending", "product_promo_pending", "product_promo_approved", "task_images_db",
            "support_banner_db", "admin_names_db", "support_plans_db",
        ]
        for name in container_names:
            if name not in data or name not in globals():
                continue
            current = globals()[name]
            loaded = data[name]
            if isinstance(current, dict) and isinstance(loaded, dict):
                current.clear()
                current.update(loaded)
            elif isinstance(current, list) and isinstance(loaded, list):
                current.clear()
                current.extend(loaded)
        if "banned_users" in data:
            try:
                banned_users.clear()
                banned_users.update(set(data["banned_users"]))
            except: pass
        print(f"✅ Data loaded from local {DATA_FILE}")
        return True
    except Exception as e:
        print(f"Load error: {e}")
        import traceback; traceback.print_exc()
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
    try:
        init_supabase()
    except Exception as e:
        print(f"Supabase init in main fail {e}")
    except Exception as e:
        print(f'Flask start fail in main: {e}')

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
        print(f"ENV SUPABASE_URL set: {bool(os.getenv('SUPABASE_URL'))} | KEY set: {bool(os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY'))}")
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
                    if is_admin(uid):
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
                      f"{('📝 Instructions:\n' + task.get('description', '') + '\n\n') if task.get('description') else ''}"
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
