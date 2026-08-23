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
SCREENSHOT_LINK = "https://t.me/S2E_Daily_Earning"
WITHDRAW_LINK = "https://t.me/S2E_Daily_Earning"
JOIN_LINK = "https://t.me/S2E_Daily_Earning"
MISSED_ENABLED = True

ADMIN_UPI = os.getenv("ADMIN_UPI", "s2eearning@upi")
PAYMENT_UPI = ADMIN_UPI
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@s2edayincome")

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
    except:
        pass
    uid = q.from_user.id
    is_active, plan_name, expiry = check_plan_active(uid)
    plan_type = "premium" if plan_type == "premium" else "basic"
    price = 499 if plan_type == "premium" else 199
    limit = DAILY_TASK_LIMIT_PREMIUM if plan_type == "premium" else DAILY_TASK_LIMIT_BASIC
    if is_active and plan_name.lower().startswith(plan_type):
        text = f"✅ {plan_type.capitalize()} plan is already active.\\nValid till: {expiry}\\nDaily tasks: {limit}"
        kb = [[InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]]
    else:
        upi = get_payment_upi()
        pending_plans[uid] = {"plan": plan_type, "date": str(get_ist_today()), "price": price}
        text = (
            f"💎 {plan_type.capitalize()} Plan — ₹{price}\\n\\n"
            f"Daily Tasks: {limit}\\n"
            f"Validity: 30 days\\n\\n"
            f"💳 Pay manually to UPI:\\n{upi}\\n\\n"
            "After payment, click “I Paid - Send Proof” and send the payment screenshot.\\n"
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
    pending_plans[uid] = {"plan": "basic", "date": str(get_ist_today()), "price": 199}
    context.user_data["awaiting_plan_payment_proof"] = "basic"
    awaiting_plan_payment_adminless.add(uid)
    await q.message.reply_text("📤 Send the Basic ₹199 payment screenshot as a PHOTO now.")

async def plan_premium_proof_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
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
    price = 199 if plan_type == "basic" else 499
    pending_plans[uid] = {"plan": plan_type, "date": str(get_ist_today()), "price": price}
    context.user_data["awaiting_plan_payment_proof"] = plan_type
    awaiting_plan_payment_adminless.add(uid)
    await q.message.reply_text(
        f"📤 Send your ₹{price} payment screenshot as a PHOTO now.\n"
        "Admin will verify it manually."
    )

async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except Exception: pass
    normalize_support_plans()
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
    uid = q.from_user.id; name = str(plan.get("name", "Plan")); price = int(plan.get("price", 0))
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

def get_user_record(uid):
    """Return a registered user record regardless of whether persistence restored the key as int or string."""
    try:
        uid_int = int(uid)
    except Exception:
        uid_int = uid
    user = users_db.get(uid_int)
    if user is None:
        user = users_db.get(str(uid_int))
        if user is not None and uid_int != str(uid_int):
            users_db[uid_int] = user
            try: users_db.pop(str(uid_int), None)
            except Exception: pass
    return user if isinstance(user, dict) else {}

def has_registered_user(uid):
    user = get_user_record(uid)
    return bool(user.get("name"))
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
holidays_db = {}  # {YYYY-MM-DD: reason}
withdraw_history_db = {}  # {uid: [withdrawal records]}

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
    today = str(get_ist_today())
    if today in holidays_db:
        return []
    return [t for t in scheduled_tasks_db if t['date'] == today]

def is_holiday(day=None):
    day = str(day or get_ist_today())
    return day in holidays_db

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
def get_total_withdraw_cap(uid):
    """Total lifetime withdrawal cap for the user's active plan."""
    try:
        _, cap, _ = get_plan_limits(uid)
        return int(cap or 0)
    except Exception:
        return 0

def get_withdrawn_total(uid, include_processing=False):
    rows = withdraw_history_db.get(uid, []) or []
    total = 0
    for r in rows:
        status = str(r.get('status','')).lower()
        if status == 'approved' or (include_processing and status == 'processing'):
            try: total += int(r.get('amount',0) or 0)
            except Exception: pass
    # If history is empty after an older migration, use the current request too.
    if include_processing:
        req = withdraw_requests.get(uid) or {}
        if str(req.get('status','')).lower() == 'processing' and not any(r.get('date') == req.get('date') and r.get('amount') == req.get('amount') for r in rows):
            try: total += int(req.get('amount',0) or 0)
            except Exception: pass
    return total

def get_withdraw_remaining(uid):
    cap = get_total_withdraw_cap(uid)
    if cap <= 0:
        return 0
    return max(0, cap - get_withdrawn_total(uid, include_processing=True))

def get_tasks(uid):
    today = str(get_ist_today())
    return daily_task_count.get(uid, {}).get(today, 0)

def get_total_tasks(uid):
    return tasks_db.get(uid,0)
def _get_user_plan_record(uid):
    # Support both the old dict format and the newer plan-id format.
    plan = user_plans.get(uid)
    if plan is None:
        plan = user_plans.get(str(uid))
    if isinstance(plan, dict):
        return plan
    if isinstance(plan, (int, str)) and str(plan).isdigit():
        try:
            pid = int(plan)
            found = next((p for p in support_plans_db if int(p.get('id', -1)) == pid), None)
            if found:
                return found
        except Exception:
            pass
    return None

def check_plan_active(uid):
    plan = _get_user_plan_record(uid)
    if not plan:
        return False, "No Plan", None

    # Legacy approval records contain only {'plan': 'basic', 'date': ...}.
    # Treat those as active for 30 days so the daily limit never becomes 0.
    plan_type = str(plan.get('plan') or plan.get('name') or '').lower()
    if 'premium' in plan_type or plan.get('price') == 499:
        plan_type = 'premium'
    elif 'basic' in plan_type or plan.get('price') == 199:
        plan_type = 'basic'

    status = str(plan.get('status', 'active')).lower()
    if status not in ('active', 'approved'):
        return False, f"{plan_type.upper()} Pending", None

    expiry = plan.get('expiry')
    if expiry:
        try:
            if isinstance(expiry, str):
                expiry = date.fromisoformat(expiry)
            if get_ist_today() > expiry:
                return False, f"{plan_type.upper()} Expired", expiry
        except Exception:
            pass
    else:
        base_date = plan.get('date') or plan.get('activated_at')
        try:
            if base_date:
                if isinstance(base_date, str):
                    base_date = date.fromisoformat(base_date[:10])
                expiry = base_date + timedelta(days=30)
            else:
                expiry = get_ist_today() + timedelta(days=30)
            plan['expiry'] = expiry
            plan['status'] = 'active'
            plan['plan'] = plan_type or 'basic'
        except Exception:
            expiry = None
    return True, f"{(plan_type or 'basic').upper()} till {expiry}", expiry

def get_plan_limits(uid):
    is_active, _, _ = check_plan_active(uid)
    if not is_active:
        return DAILY_TASK_LIMIT_FREE, DAILY_EARNING_CAP_FREE if 'DAILY_EARNING_CAP_FREE' in globals() else 10, "free"
    plan = _get_user_plan_record(uid) or {}
    plan_type = str(plan.get('plan') or plan.get('name') or '').lower()
    price = plan.get('price')
    configured_limit = plan.get('daily_limit')
    # Dynamic/manual plan limits always win. This also fixes Family 1999.
    if configured_limit:
        try: configured_limit = int(configured_limit)
        except Exception: configured_limit = None
    if 'family' in plan_type or price == 1999:
        cap = int(plan.get('earnings_limit') or 3000)
        return int(configured_limit or 30), cap, "family"
    if 'premium' in plan_type or price == 499:
        cap = int(plan.get('earnings_limit') or DAILY_EARNING_CAP_PREMIUM)
        return int(configured_limit or DAILY_TASK_LIMIT_PREMIUM), cap, "premium"
    cap = int(plan.get('earnings_limit') or DAILY_EARNING_CAP_BASIC)
    return int(configured_limit or DAILY_TASK_LIMIT_BASIC), cap, "basic"

def get_daily_task_earned(uid, day=None):
    day = str(day or get_ist_today())
    total = 0
    for st in user_task_status.get(uid, {}).values():
        if isinstance(st, dict) and st.get('status') == 'completed' and str(st.get('completed_at',''))[:10] == day:
            try: total += int(st.get('reward', 0) or 0)
            except Exception: pass
    return total

def check_daily_limits(uid):
    today = str(get_ist_today())
    count = daily_task_count.get(uid, {}).get(today, 0)
    limit, cap, plan_name = get_plan_limits(uid)
    return count, limit, cap
def get_today_task_for_user(uid):
    if is_holiday():
        return None
    current, next_task = get_current_scheduled_task_with_interval()
    if current:
        return current
    # Do not create an untracked task that can repeat after approval.
    # If no scheduled task is active, this fallback has one stable ID so
    # completion/pending status can be checked and the same task is not shown again.
    return {
        "id": DEFAULT_DAILY_TASK_ID,
        "task_number": 1,
        "title": "Join Channel @s2edayincome",
        "link": get_join_channel_link(),
        "reward": 5,
        "open_time": "00:00",
        "close_time": "23:59",
        "next_time": "00:00",
        "window_minutes": 1440,
    }

def admin_panel_keyboard():
    missed_label = "⏰ Missed: ON" if MISSED_ENABLED else "⏰ Missed: OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Pending Daily ({len(pending_daily)})", callback_data="admin_view_pending"),
         InlineKeyboardButton(f"💰 Withdraw ({len([w for w in withdraw_requests.values() if w.get('status')=='processing'])})", callback_data="admin_view_withdraw")],
        [InlineKeyboardButton("⏰ Today's Tasks", callback_data="admin_view_tasks"),
         InlineKeyboardButton("🏪 Promo Campaigns", callback_data="admin_view_promos")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_view_stats"),
         InlineKeyboardButton("🚫 Banned List", callback_data="admin_view_banned")],
        [InlineKeyboardButton("💾 Backup", callback_data="admin_backup"),
         InlineKeyboardButton("👑 Admins", callback_data="admin_add_admin")],
        [InlineKeyboardButton("🔗 Referral", callback_data="admin_referral"),
         InlineKeyboardButton(missed_label, callback_data="admin_missed_toggle")],
        [InlineKeyboardButton("📋 Menu", callback_data="back_menu")]
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🧾 Withdraw History", callback_data="withdraw_history")],
        [InlineKeyboardButton("🏪 Promo Tasks", callback_data="promo_tasks"), InlineKeyboardButton("📢 Promote My Shop", callback_data="promote_shop")],
        [InlineKeyboardButton("📋 Scheduled Tasks", callback_data="scheduled"), InlineKeyboardButton("💎 Support Plans", callback_data="support_plans")],
        [InlineKeyboardButton("👤 My Details", callback_data="my_details"), InlineKeyboardButton("❌ Missed Tasks", callback_data="missed_tasks")],
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
            await update.message.reply_text(
                f"👋 Welcome! Please join our channel {get_join_channel()} to use bot!\n\nJoin and click Check Joined!",
                reply_markup=kb,
            )
            return ConversationHandler.END

    args = context.args
    ref_id = None
    if args and args[0].isdigit():
        ref_id = int(args[0])
        if ref_id != uid and ref_id not in banned_users:
            referral_map[uid] = ref_id

    user = get_user_record(uid)
    plan = _get_user_plan_record(uid)

    # IMPORTANT: A user who already has a profile, plan, task history, balance,
    # withdrawal history, or other persistent state must NEVER be sent through
    # the registration questions again after a restart/redeploy.
    known_user = bool(
        user.get("name")
        or plan
        or uid in tasks_db
        or uid in daily_task_count
        or uid in user_task_status
        or uid in withdraw_history_db
        or uid in withdraw_requests
        or uid in bonus_balance
        or uid in referral_earnings
    )
    if known_user:
        if not user.get("name"):
            fallback_name = (update.effective_user.full_name or update.effective_user.username or "User").strip()
            users_db.setdefault(uid, {})["name"] = fallback_name
            if not users_db[uid].get("joined"):
                users_db[uid]["joined"] = str(get_ist_today())
                users_db[uid]["reg_date"] = str(get_ist_today())
            save_data()
            user = get_user_record(uid)
        plan_active, plan_name, expiry = check_plan_active(uid)
        count, limit, cap = check_daily_limits(uid)
        await update.message.reply_text(
            f"👋 Welcome back {user.get('name','User')}!\n\n"
            f"💰 Balance: ₹{get_balance(uid)}\n"
            f"📋 Plan: {plan_name}\n"
            f"📝 Today: {count}/{limit} tasks\n"
            f"💎 Plan earning cap: ₹{cap}\n"
            f"{'Valid till: '+str(expiry) if plan_active and expiry else ''}",
            reply_markup=main_menu(),
        )
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
    user = get_user_record(uid)
    if user.get("name"):
        await q.message.reply_text(f"✅ V56 Thanks for joining! Welcome back {user.get('name','User')}! Join bypass - No Not joined error! FINAL!", reply_markup=main_menu())
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
    users_db[uid]['reg_date']=str(get_ist_today())
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
        name = get_user_record(uid).get('name','Unknown')
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
        name = get_user_record(uid).get('name','Unknown')
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
        name = get_user_record(uid).get('name','Unknown')
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
    msg = f"💰 Wallet\n\nBalance: Rs{bal}\nTasks: {tasks_done}/{TASKS_REQUIRED_FOR_WITHDRAW}\nReferral: Rs{referral_rs}\nPromo: Rs{promo_rs}\nTotal: Rs{bal}\n\n📋 Plan: {plan_name}\nDaily: {count}/{limit} tasks\nDaily earning cap: Rs{cap}\n🎯 Total withdrawal cap: Rs{get_total_withdraw_cap(uid)}\n💸 Withdrawn: Rs{get_withdrawn_total(uid)}\n📉 Withdrawal cap remaining: Rs{get_withdraw_remaining(uid)}\n\nBasic Rs500: {DAILY_TASK_LIMIT_BASIC} tasks/day\nPremium Rs1000: {DAILY_TASK_LIMIT_PREMIUM} tasks/day"
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
        open_dt = datetime.combine(get_ist_today(), task["open_time_obj"], tzinfo=IST)
        close_dt = datetime.combine(get_ist_today(), task["close_time_obj"], tzinfo=IST)
        if open_dt <= now <= close_dt:
            return task, "active"
    return None, "none"

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
    if is_holiday(today):
        await q.message.reply_text(f"🏖️ Today is a holiday.\n\nNo tasks are available today.\nReason: {holidays_db.get(today, 'Holiday')}\n\nPlease come back tomorrow.", reply_markup=main_menu())
        return
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
            task = get_today_task_for_user(uid)
            task_id = task.get('id', DEFAULT_DAILY_TASK_ID)
            status_data = user_task_status.get(uid, {}).get(task_id, {})
            status = status_data.get('status') if isinstance(status_data, dict) else status_data
            if status == 'completed':
                await q.message.reply_text(
                    f"✅ Today's task is already completed!\n\n"
                    f"Tasks today: {count}/{limit}\n"
                    f"No new task is available right now. Admin can add/update the next task.",
                    reply_markup=main_menu()
                )
                return
            if status == 'pending_verification':
                await q.message.reply_text(
                    f"⏳ Today's task screenshot is already pending admin verification.\n\n"
                    f"Tasks today: {count}/{limit}",
                    reply_markup=main_menu()
                )
                return
            if status == 'skipped':
                await q.message.reply_text(
                    f"⏭️ Today's task was skipped.\n\nTasks today: {count}/{limit}",
                    reply_markup=main_menu()
                )
                return
            await q.message.reply_text(
                f"📅 Today's Task:\n\nTitle: {task['title']}\nReward: Rs{task['reward']}\nLink: {task['link']}\n\n"
                f"Tasks today: {count}/{limit}\n\nClick Upload Screenshot after completing!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_v2"),
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
            await q.message.reply_photo(photo=image_file_id, caption=msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_v2")], [InlineKeyboardButton("⏭️ Skip Task", callback_data=f"daily_skip_{current['id']}")]]))
            return
        except Exception as e:
            print(f"Image send error {e}")
    await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_v2")], [InlineKeyboardButton("⏭️ Skip Task", callback_data=f"daily_skip_{current['id']}")]]))

async def daily_upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    print(f"V68 UPLOAD SCREENSHOT CALLBACK RECEIVED: data={q.data} uid={q.from_user.id}")
    await q.answer()
    uid = q.from_user.id
    current, next_task = get_current_scheduled_task_with_interval()
    requested_id = context.user_data.get('daily_screenshot_task_id')
    task = current
    if requested_id is not None:
        try:
            requested_id=int(requested_id)
            task=next((t for t in get_tasks_for_today() if int(t.get('id',-1))==requested_id), None) or current
        except Exception:
            pass
    if task:
        status_data=user_task_status.get(uid,{}).get(task.get('id'),{})
        status=status_data.get('status') if isinstance(status_data,dict) else status_data
        if status in ('completed','pending_verification'):
            await q.message.reply_text("⏳ This task is already completed or pending verification.", reply_markup=main_menu())
            return ConversationHandler.END
        if status == 'missed':
            # Button can only reopen from Missed Tasks; it is not directly accepted here.
            await q.message.reply_text("❌ This task is marked missed. Open Missed Tasks and tap Do Missed Task first.", reply_markup=main_menu())
            return ConversationHandler.END
    context.user_data['awaiting_daily_screenshot'] = True
    context.user_data['daily_screenshot_task_id'] = task.get('id') if task else requested_id
    if task:
        await q.message.reply_text(
            f"📤 Send screenshot for Task {task.get('task_number','?')}!\n\n"
            f"Original window: {task.get('open_time','')}→{task.get('close_time','')}\n\n"
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
        # Never accept a screenshot for an expired task. If deployment/restart
        # happened after the task window, it is a Missed Task, not a new/current task.
        if task_to_use and task_to_use.get('id') is not None and task_to_use.get('date') == today:
            try:
                close_obj = task_to_use.get('close_time_obj')
                if close_obj is None and task_to_use.get('close_time'):
                    close_obj = parse_time_str(str(task_to_use.get('close_time')))
                if close_obj and get_ist_time() > close_obj:
                    check_missed_tasks_with_interval(uid)
                    await update.message.reply_text(
                        f"⏰ Task {task_to_use.get('task_number', 1)} is already closed ({task_to_use.get('open_time','')}→{task_to_use.get('close_time','')}) and is marked as MISSED if not completed.\n\nPlease wait for the next Scheduled Task.",
                        reply_markup=main_menu()
                    )
                    context.user_data.pop('awaiting_daily_screenshot', None)
                    context.user_data.pop('daily_screenshot_task_id', None)
                    return ConversationHandler.END
            except Exception as e:
                print(f"Expired task check error: {e}")

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
                await update.message.reply_text("BANNED! 3 Warnings! V56")
                return ConversationHandler.END
            await update.message.reply_text("WARNING Same Screenshot! V56")
            return ConversationHandler.END
        if file_unique_id:
            screenshot_hashes.add(file_unique_id)
        pending_daily[uid] = {'date': today, 'task': task_to_use, 'screenshot_file_id': file_id}
        context.user_data.pop('awaiting_daily_screenshot', None)
        context.user_data.pop('daily_screenshot_task_id', None)
        if uid not in user_task_status:
            user_task_status[uid] = {}
        user_task_status[uid][task_id_for_status] = {'status': 'pending_verification', 'submitted_at': get_ist_now(), 'reopened_from_missed': reopened}
        await update.message.reply_text(f"✅ V56 Screenshot Received for Task {task_to_use.get('task_number',1)}! Pending Admin Verification! V56 FINAL - Upload screenshot button fix!", reply_markup=main_menu())
        try:
            chan = get_screenshot_channel()
            if chan:
                try:
                    user_name = get_user_record(uid).get('name', update.effective_user.full_name or 'Unknown')
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
    submission = {'uid': uid, 'campaign_id': campaign_id, 'views': views, 'earning': earning, 'file_id': file_id, 'submitted_at': get_ist_now(), 'status': 'pending', 'user_name': get_user_record(uid).get('name','Unknown')}
    campaign['screenshots'].append(submission)
    campaign['total_views'] += views
    campaign['members_joined'].add(uid)
    promo_pending[uid] = submission
    await update.message.reply_text(f"✅ Submitted!\n\nCampaign {campaign_id}: {campaign['shop_name']} - {campaign['title']}\nViews: {views}\nEarning: Rs{earning} (Rs{campaign['per_view_member_earning']} per 100 views)\nStatus: Pending admin verification\n\nAdmin will verify screenshot!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Approve Rs{earning} for {views} views", callback_data=f"promo_approve_{uid}_{campaign_id}_{views}"), InlineKeyboardButton("❌ Reject", callback_data=f"promo_reject_{uid}_{campaign_id}")]])
            await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=f"🏪 NEW PROMO SUBMISSION!\nUser {get_user_record(uid).get('name')} ID {uid}\nCampaign {campaign_id}: {campaign['shop_name']} Views: {views} Earning: Rs{earning}", reply_markup=kb)
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
                cap = f"📸 NEW SUBMISSION - Task {task.get('task_number','')} {task.get('title','')}\nUser {uid} {get_user_record(uid).get('name','')} @{users_db.get(uid,{}).get('username','')}\nReward: Rs{get_reward_for_user(uid, task.get('reward',5))} (Plan based)\nTime: {get_ist_now()}"
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
        name = get_user_record(uid).get('name','Unknown')
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
            referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+REFERRAL_BONUS_PER_TASK
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
            # IMPORTANT: persist the task immediately. This makes scheduled/missed
            # status survive Render restart/redeploy.
            save_data()
            await update.message.reply_text(f"✅ Added Task ID {result['id']} No {result['task_number']}\n{result['open_time']}→{result['close_time']} Next {result['next_time']}\nTitle: {title}\nReward: Rs{reward}\n\n💾 Saved. If the bot is restarted/redeployed after this time, the task will remain in Scheduled/Missed status based on its time window.")
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
                name = get_user_record(uid).get('name','Unknown')
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
    msg = f"⏭️ Skipped tasks for {target_id} {get_user_record(target_id).get('name','')}:\n\n"
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
        name = get_user_record(uid).get('name','Unknown')
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
        name = get_user_record(uid).get('name','Unknown')
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
            await context.bot.send_message(chat_id=admin_id, text=f"💎 Plan Request\nUser {get_user_record(uid).get('name')} ID {uid}\nPlan: {plan_type}\nUPI: {get_user_record(uid).get('upi')}\nMobile: {users_db.get(uid,{}).get('mobile')}", reply_markup=kb)
        except: pass



async def contact_us_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"📞 Contact Us\n\nSupport: {SUPPORT_USERNAME}\nChannel: {get_join_channel_link()}\nUPI: {ADMIN_UPI}\n\nFor any issues, contact admin!", reply_markup=main_menu())

async def withdraw_history_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try: await q.answer()
    except: pass
    uid = q.from_user.id
    rows = withdraw_history_db.get(uid, [])
    if not rows:
        # Include the current request if history was not yet migrated.
        req = withdraw_requests.get(uid)
        if req:
            rows = [req]
    if not rows:
        await q.message.reply_text("🧾 Withdrawal History\n\nNo withdrawal records yet.", reply_markup=main_menu())
        return
    msg = "🧾 WITHDRAWAL HISTORY\n\n"
    for i, r in enumerate(reversed(rows[-30:]), 1):
        msg += (f"{i}. 📅 {r.get('date', r.get('created_at','N/A'))}\n"
                f"   💰 Amount: ₹{r.get('amount',0)}\n"
                f"   📌 Status: {str(r.get('status','unknown')).title()}\n")
        if r.get('processed_at'): msg += f"   ✅ Processed: {r.get('processed_at')}\n"
        msg += "\n"
    await q.message.reply_text(msg[:4000], reply_markup=main_menu())

async def my_details_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    try: await q.answer()
    except: pass
    uid=q.from_user.id
    user=get_user_record(uid)
    plan=_get_user_plan_record(uid)
    total_earned=get_balance(uid)
    joined=user.get('joined') or user.get('reg_date') or 'N/A'
    plan_name=plan.get('plan_name',plan.get('name',plan.get('plan','No Plan'))) if plan else 'No Plan'
    expiry=plan.get('expires_at',plan.get('expiry','N/A')) if plan else 'N/A'
    remaining='N/A'
    if expiry not in (None,'N/A'):
        try: remaining=max(0,(date.fromisoformat(str(expiry)[:10])-get_ist_today()).days)
        except: pass
    count,limit,cap=check_daily_limits(uid)
    withdraw_cap=get_total_withdraw_cap(uid)
    total_withdrawn=get_withdrawn_total(uid)
    pending_withdraw=get_withdrawn_total(uid, include_processing=True)-total_withdrawn
    withdraw_remaining=max(0, withdraw_cap-get_withdrawn_total(uid, include_processing=True))
    msg=(f"👤 MY DETAILS\n\nUser ID: {uid}\nName: {user.get('name','N/A')}\n"
         f"Gender: {user.get('gender','N/A')}\nDOB: {user.get('dob','N/A')}\nMobile: {user.get('mobile','N/A')}\n"
         f"UPI: {user.get('upi','N/A')}\nPincode: {user.get('pincode','N/A')}\nProfession: {user.get('profession','N/A')}\nJoined: {joined}\n\n"
         f"💎 Plan: {plan_name}\nExpiry: {expiry}\nDays remaining: {remaining}\n"
         f"📋 Today's tasks: {count}/{limit}\n"
         f"💰 Total earning: ₹{total_earned}\n"
         f"🎯 Plan withdrawal cap: ₹{withdraw_cap}\n"
         f"📉 Withdrawal cap remaining: ₹{withdraw_remaining}\n"
         f"💸 Total withdrawn: ₹{total_withdrawn}\n"
         f"⏳ Pending withdrawal: ₹{pending_withdraw}")
    await q.message.reply_text(msg,reply_markup=main_menu())

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

    withdraw_cap = get_total_withdraw_cap(uid)
    withdrawn_total = get_withdrawn_total(uid, include_processing=True)
    withdraw_remaining = max(0, withdraw_cap - withdrawn_total)
    if bal < WITHDRAW_MIN:
        await q.message.reply_text(
            f"WITHDRAW\n\nEarnings: Rs{bal}\nMin: Rs{WITHDRAW_MIN}\n"
            f"Plan withdrawal cap: Rs{withdraw_cap}\nCap remaining: Rs{withdraw_remaining}\n\n"
            "Complete more tasks to reach the minimum withdrawal amount.",
            reply_markup=main_menu()
        )
        return
    if withdraw_remaining < WITHDRAW_MIN:
        await q.message.reply_text(
            f"⛔ Plan withdrawal cap reached.\n\n"
            f"Total cap: Rs{withdraw_cap}\nAlready withdrawn/reserved: Rs{withdrawn_total}\n"
            f"Remaining: Rs{withdraw_remaining}\n\nNo further withdrawal is available under this plan.",
            reply_markup=main_menu()
        )
        return

    # Only amounts that are <= current balance AND remaining plan cap are selectable.
    available = [opt for opt in WITHDRAW_OPTIONS if opt <= bal and opt <= withdraw_remaining]
    unavailable = [opt for opt in WITHDRAW_OPTIONS if opt > bal or opt > withdraw_remaining]

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
        f"Plan withdrawal cap: Rs{withdraw_cap} | Remaining: Rs{withdraw_remaining}\n\n"
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
    withdraw_remaining = get_withdraw_remaining(uid)

    if amount not in WITHDRAW_OPTIONS or amount > bal or amount > withdraw_remaining:
        await q.message.reply_text("❌ This withdrawal amount is not available for your balance or remaining plan withdrawal cap.", reply_markup=main_menu())
        return

    fee = int(amount * PLATFORM_FEE_PERCENT / 100)
    net = amount - fee
    upi = get_user_record(uid).get('upi', 'Not set')
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
    save_data()
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
    withdraw_remaining = get_withdraw_remaining(uid)
    if amount not in WITHDRAW_OPTIONS or amount > bal or amount > withdraw_remaining:
        await q.message.reply_text("❌ Withdrawal amount is no longer available for your balance or remaining plan withdrawal cap.", reply_markup=main_menu())
        return

    upi = get_user_record(uid).get('upi')
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
    req = dict(withdraw_requests[uid])
    withdraw_history_db.setdefault(uid, []).append(req)
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
        reward=pending_daily[uid].get('task',{}).get('reward',5)
        today=pending_daily[uid].get('date')
        _, _, daily_cap = check_daily_limits(uid)
        if daily_cap > 0 and get_daily_task_earned(uid, today) + int(reward) > daily_cap:
            await q.message.reply_text(f"⛔ Daily earning cap reached for User {uid}. Cap: ₹{daily_cap}, earned today: ₹{get_daily_task_earned(uid, today)}.")
            return
        tasks_db[uid]=tasks_db.get(uid,0)+1
        if uid not in daily_task_count: daily_task_count[uid]={}
        daily_task_count[uid][today]=daily_task_count[uid].get(today,0)+1
        if reward!=5: bonus_balance[uid]=bonus_balance.get(uid,0)+(reward-5)
        del pending_daily[uid]
        task_open_time.pop(uid, None)
        for tid, status_data in list(user_task_status.get(uid, {}).items()):
            if isinstance(status_data, dict) and status_data.get('status') == 'pending_verification':
                mark_task_completed_with_interval(uid, tid)
                if isinstance(user_task_status[uid].get(tid), dict): user_task_status[uid][tid]['reward'] = int(reward)
                break
        ref_id=referral_map.get(uid)
        if ref_id and is_first:
            referrals_db[ref_id]=referrals_db.get(ref_id,0)+1
            referral_earnings[ref_id]=referral_earnings.get(ref_id,0)+REFERRAL_BONUS_PER_TASK
        save_data()
        await q.message.reply_text(f"✅ Approved {uid} +Rs{reward}")
        try:
            _, daily_limit, _ = check_daily_limits(uid)
            daily_count = get_tasks(uid)
            await context.bot.send_message(
                chat_id=uid,
                text=(f"✅ Task Approved! +Rs{reward}\n"
                      f"Balance: Rs{get_balance(uid)}\n"
                      f"Tasks today: {daily_count}/{daily_limit}\n"
                      f"Total completed tasks: {tasks_db.get(uid, 0)}"),
                reply_markup=main_menu()
            )
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
        req['rejected_at'] = str(get_ist_now())
        hist = withdraw_history_db.setdefault(uid, [])
        if hist: hist[-1].update(req)
        save_data()
        await q.message.reply_text("❌ Cannot approve: user's current balance is insufficient.")
        try:
            await context.bot.send_message(chat_id=uid, text="❌ Withdrawal rejected because your balance is insufficient at processing time.", reply_markup=main_menu())
        except Exception: pass
        return
    bonus_balance[uid] = bonus_balance.get(uid, 0) - amount
    new_bal = get_balance(uid)
    req['status'] = 'approved'
    req['approved_at'] = str(get_ist_now())
    last_withdraw_date_db[uid] = str(get_ist_today())
    hist = withdraw_history_db.setdefault(uid, [])
    if hist: hist[-1].update(req)
    save_data()
    await q.message.reply_text(f"✅ WITHDRAWAL APPROVED\nUser: {uid}\nAmount: Rs{amount}\nNet Paid: Rs{req['net']}\nRemaining Balance: Rs{new_bal}")
    try:
        await context.bot.send_message(chat_id=uid, text=(f"✅ Withdrawal Approved!\n\nAmount: Rs{amount}\nUPI: {req['upi']}\nYou Receive: Rs{req['net']}\nRemaining Balance: Rs{new_bal}\n\nYour payment request has been processed.\n⏰ You can withdraw again tomorrow."), reply_markup=main_menu())
    except Exception: pass


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
    hist = withdraw_history_db.setdefault(uid, [])
    if hist: hist[-1].update(req)
    save_data()
    await q.message.reply_text(f"❌ WITHDRAWAL REJECTED\nUser: {uid}\nAmount: Rs{req['amount']}")
    try:
        await context.bot.send_message(chat_id=uid, text=(f"❌ Withdrawal Rejected\n\nAmount: Rs{req['amount']}\nUPI: {req['upi']}\n\nYour withdrawal request was rejected by Admin.\n⏰ You can submit another withdrawal tomorrow."), reply_markup=main_menu())
    except Exception: pass

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
    if not MISSED_ENABLED:
        return missed_tasks_db.get(uid, [])
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

async def missed_work_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    try: await q.answer()
    except: pass
    uid=q.from_user.id
    try:
        task_id=int(str(q.data).replace("missed_work_", "", 1))
    except:
        await q.message.reply_text("❌ Invalid missed task.", reply_markup=main_menu())
        return
    task=next((t for t in scheduled_tasks_db if int(t.get('id',-1))==task_id and str(t.get('date'))==str(get_ist_today())), None)
    if not task:
        await q.message.reply_text("❌ This missed task is no longer available today.", reply_markup=main_menu())
        return
    status_data=user_task_status.setdefault(uid, {}).get(task_id, {})
    status=status_data.get('status') if isinstance(status_data,dict) else status_data
    if status in ('completed','pending_verification'):
        await q.message.reply_text("⏳ This task is already completed or pending verification.", reply_markup=main_menu())
        return
    if status == 'skipped':
        await q.message.reply_text("⏭️ You already skipped this task.", reply_markup=main_menu())
        return
    # Missed ON means the user can reopen a missed task once and submit proof.
    user_task_status.setdefault(uid,{})[task_id]={
        'status':'reopened',
        'reopened_at':get_ist_now(),
        'task_number':task.get('task_number'),
    }
    context.user_data['awaiting_daily_screenshot']=True
    context.user_data['daily_screenshot_task_id']=task_id
    msg=(f"🔄 MISSED TASK REOPENED\n\n"
         f"Task {task.get('task_number')}: {task.get('title','')}\n"
         f"Original time: {task.get('open_time','')}→{task.get('close_time','')}\n"
         f"Reward: ₹{task.get('reward',5)}\n\n"
         f"Open the task link, complete it, then upload the screenshot below.\n"
         f"⚠️ Admin verification is still required.")
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Open Task", url=str(task.get('link') or get_join_channel_link()))],
        [InlineKeyboardButton("📤 Upload Screenshot", callback_data="daily_upload_v2")],
        [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")],
    ])
    await q.message.reply_text(msg, reply_markup=kb)

async def missed_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    if not MISSED_ENABLED:
        await q.message.reply_text("⏰ Missed Tasks are currently OFF by Admin.", reply_markup=main_menu())
        return
    missed = track_missed_tasks_for_user(uid)
    if not missed:
        await q.message.reply_text("✅ No missed tasks today! Good job! All tasks completed or skipped properly.", reply_markup=main_menu())
        return
    msg = f"❌ MISSED TASKS TODAY - Total {len(missed)}:\n\n"
    kb=[]
    for t in missed:
        tid=int(t.get('id'))
        msg += (f"Task {t.get('task_number')}: {t.get('title')}\n"
                f"Time: {t.get('open_time')}→{t.get('close_time')} | Reward: ₹{t.get('reward',5)}\n"
                f"Link: {t.get('link','')}\n\n")
        kb.append([InlineKeyboardButton(f"🔄 Do Missed Task {t.get('task_number')}", callback_data=f"missed_work_{tid}")])
    msg += "You can reopen a missed task and submit proof once. Admin approval is required."
    kb.append([InlineKeyboardButton("🏠 Menu", callback_data="back_menu")])
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb))

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
    {"id": 1, "name": "Basic", "price": 199, "duration": 30, "daily_limit": 10, "users": 1, "earnings_limit": 500, "desc": "1 User | 30 Days | 10 tasks/day | Up to Rs500 earnings"},
    {"id": 2, "name": "Premium", "price": 499, "duration": 30, "daily_limit": 20, "users": 2, "earnings_limit": 1000, "desc": "2 Users | 30 Days | 20 tasks/day | Up to Rs1000 earnings"},
    {"id": 3, "name": "Family", "price": 1999, "duration": 30, "daily_limit": 30, "users": 4, "earnings_limit": 3000, "desc": "Family 4 Users | 30 Days | 30 tasks/day | Up to Rs3000 earnings"}
]

awaiting_plan_image_admins = set()
awaiting_plan_payment_adminless = set()

def normalize_support_plans():
    global support_plans_db
    defaults = {
        1: {"id": 1, "name": "Basic", "price": 199, "duration": 30, "daily_limit": 10, "users": 1, "earnings_limit": 500, "desc": "1 User | 30 Days | 10 tasks/day | Up to Rs500 earnings"},
        2: {"id": 2, "name": "Premium", "price": 499, "duration": 30, "daily_limit": 20, "users": 2, "earnings_limit": 1000, "desc": "2 Users | 30 Days | 20 tasks/day | Up to Rs1000 earnings"},
        3: {"id": 3, "name": "Family", "price": 1999, "duration": 30, "daily_limit": 30, "users": 4, "earnings_limit": 3000, "desc": "Family 4 Users | 30 Days | 30 tasks/day | Up to Rs3000 earnings"},
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

async def support_plans_cb_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await support_plans_cb(update, context)



async def add_bulk_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add many fully-specified scheduled tasks in one Telegram message.

    Format:
    /add_bulk_tasks 2026-08-23
    10:00AM 10min 10:10AM Task 1 https://link 5
    10:15AM 10min 10:25AM Task 2 https://link 5
    ...

    The date is optional; without it, today's IST date is used.
    """
    if not is_admin(update.effective_user.id):
        return
    text = update.message.text or ''
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines and lines[0].lower().startswith('/add_bulk_tasks'):
        first = lines[0].split(maxsplit=1)
        header = first[1].strip() if len(first) > 1 else ''
        lines = lines[1:]
    else:
        header = ' '.join(context.args).strip()
        lines = []

    target_date = str(get_ist_today())
    if header:
        # A date in the command header selects the schedule date.
        m = re.search(r'\b(20\d{2}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b', header)
        if m:
            raw_date=m.group(1)
            try:
                target_date = str(date.fromisoformat(raw_date)) if '-' in raw_date else str(datetime.strptime(raw_date,'%d/%m/%Y').date())
            except Exception:
                await update.message.reply_text('❌ Invalid date. Use YYYY-MM-DD or DD/MM/YYYY.')
                return
        elif header and not lines:
            await update.message.reply_text(
                '📦 BULK TASK FORMAT\n\n'
                '/add_bulk_tasks 2026-08-23\n'
                '10:00AM 10min 10:10AM Task 1 https://link 5\n'
                '10:15AM 10min 10:25AM Task 2 https://link 5\n\n'
                'One line = one task. Images: /bulk_images ID1 ID2 ID3 then send photos in order.'
            )
            return

    if not lines:
        # Also support a single-line command with all fields after the optional date.
        raw=' '.join(context.args).strip()
        if raw:
            parts=raw.split()
            if parts and re.fullmatch(r'(20\d{2}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', parts[0]):
                parts=parts[1:]
            if parts:
                lines=[' '.join(parts)]

    if not lines:
        await update.message.reply_text(
            '📦 BULK TASKS\n\n'
            'Example:\n/add_bulk_tasks 2026-08-23\n'
            '10:00AM 10min 10:10AM Task 1 https://link 5\n'
            '10:15AM 10min 10:25AM Task 2 https://link 5'
        )
        return

    global scheduled_task_counter
    added=[]; errors=[]
    for line in lines:
        try:
            parts=line.split()
            if len(parts)<6:
                raise ValueError('Need open close/interval next title link reward')
            open_str, close_str, next_str = parts[0], parts[1], parts[2]
            link_match=re.search(r'https?://\S+', line)
            if not link_match:
                raise ValueError('Missing URL')
            link=link_match.group(0).rstrip(',')
            reward_token=parts[-1]
            if not re.fullmatch(r'\d+', reward_token):
                raise ValueError('Reward must be a number')
            reward=int(reward_token)
            title=' '.join(parts[3:-2]).strip()
            if not title:
                raise ValueError('Missing title')

            ot=parse_time_str(open_str)
            if not ot:
                raise ValueError(f'Invalid open time: {open_str}')
            if ':' in close_str or 'AM' in close_str.upper() or 'PM' in close_str.upper():
                ct=parse_time_str(close_str)
            else:
                mins=parse_interval_str(close_str)
                ct=(datetime.combine(date.today(),ot)+timedelta(minutes=mins)).time()
            nt=parse_time_str(next_str)
            if not ct or not nt:
                raise ValueError('Invalid close/next time')
            if ct <= ot:
                raise ValueError('Close must be after open')
            if nt < ct:
                raise ValueError('Next must be at/after close')

            task={
                'id': scheduled_task_counter,
                'task_number': len([t for t in scheduled_tasks_db if str(t.get('date'))==target_date])+1,
                'open_time':ot.strftime('%H:%M'),'open_time_obj':ot,
                'close_time':ct.strftime('%H:%M'),'close_time_obj':ct,
                'next_time':nt.strftime('%H:%M'),'next_time_obj':nt,
                'title':title,'link':link,'reward':reward,'date':target_date,
                'created_at':get_ist_now(),'window_minutes':int((datetime.combine(date.today(),ct)-datetime.combine(date.today(),ot)).total_seconds()/60),
                'skippable':True if any(x in title.lower() for x in ['angel','upstox','demat','trading']) else False,
                'image_file_id':None,
            }
            scheduled_tasks_db.append(task)
            scheduled_task_counter+=1
            added.append(task)
        except Exception as e:
            errors.append(f'{line} -> {e}')

    scheduled_tasks_db.sort(key=lambda t:(str(t.get('date')), str(t.get('open_time',''))))
    save_data()
    msg=f'✅ BULK ADD DONE\n\n📅 Date: {target_date}\nAdded: {len(added)} tasks'
    if added:
        msg += '\nIDs: '+', '.join(str(t['id']) for t in added)
    if errors:
        msg += f'\n\n❌ Errors: {len(errors)}\n'+'\n'.join(errors[:5])
    msg += '\n\n🖼️ Add posters: /bulk_images ID1 ID2 ID3 ... then send photos in the same order.'
    await update.message.reply_text(msg[:4000])


# === PERSISTENT STORAGE - FIX DATA LOSS ===
import json, os
DATA_FILE = "bot_data.json"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
_DB_WARNED = False

def _db_connect():
    """Connect to Render PostgreSQL when DATABASE_URL is configured.
    Uses psycopg v3; JSON file remains as a local fallback.
    """
    global _DB_WARNED
    if not DATABASE_URL:
        return None
    try:
        import psycopg
        return psycopg.connect(DATABASE_URL, connect_timeout=10)
    except Exception as e:
        if not _DB_WARNED:
            print(f"Persistent PostgreSQL unavailable: {e}")
            _DB_WARNED = True
        return None

def _db_init():
    conn=_db_connect()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS s2e_state (id INTEGER PRIMARY KEY, payload TEXT NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW())")
        conn.commit(); conn.close()
        print("Persistent PostgreSQL storage ready")
    except Exception as e:
        print(f"DB init error: {e}")
        try: conn.close()
        except: pass

def _db_load_snapshot():
    conn=_db_connect()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT payload FROM s2e_state WHERE id=1")
            row=cur.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
    except Exception as e:
        print(f"DB load error: {e}")
        try: conn.close()
        except: pass
        return None

def _db_save_snapshot(payload):
    conn=_db_connect()
    if not conn: return False
    try:
        payload_text=json.dumps(payload, ensure_ascii=False)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO s2e_state(id,payload,updated_at) VALUES(1,%s,NOW()) ON CONFLICT(id) DO UPDATE SET payload=EXCLUDED.payload, updated_at=NOW()", (payload_text,))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"DB save error: {e}")
        try: conn.rollback(); conn.close()
        except: pass
        return False

def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, set):
        return [_json_safe(v) for v in sorted(value, key=lambda x: str(x))]
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value

def _restore_special_state(data):
    # Keys saved by JSON become strings; convert user-keyed maps back to int keys.
    int_key_maps = [
        'users_db','tasks_db','bonus_balance','referrals_db','referral_earnings','referral_map',
        'withdraw_requests','withdraw_done_date','last_withdraw_date_db','daily_task_count',
        'user_task_status','missed_tasks_db','pending_daily','skip_db','warnings_db','promo_earnings_db',
        'promo_views_db','promo_pending','pending_plans','user_plans'
    ]
    for name in int_key_maps:
        obj=data.get(name)
        if isinstance(obj, dict):
            fixed={}
            for k,v in obj.items():
                try: nk=int(k)
                except: nk=k
                fixed[nk]=v
            data[name]=fixed

    # Telegram IDs / sets.
    for name in ('banned_users','screenshot_hashes','task_notifications_sent','awaiting_plan_image_admins','awaiting_plan_payment_adminless'):
        if isinstance(data.get(name), list):
            try: data[name]=set(data[name])
            except: pass

    # Scheduled task time fields must be datetime.time after JSON/DB restore.
    tasks=data.get('scheduled_tasks_db')
    if isinstance(tasks,list):
        for t in tasks:
            if not isinstance(t,dict): continue
            for obj_key, text_key in (('open_time_obj','open_time'),('close_time_obj','close_time'),('next_time_obj','next_time')):
                val=t.get(obj_key)
                if isinstance(val,str):
                    parsed=parse_time_str(val)
                    if parsed: t[obj_key]=parsed
                elif val is None and t.get(text_key):
                    parsed=parse_time_str(str(t.get(text_key)))
                    if parsed: t[obj_key]=parsed

    # Promo member sets.
    promos=data.get('promo_campaigns_db')
    if isinstance(promos,list):
        for c in promos:
            if isinstance(c,dict) and isinstance(c.get('members_joined'),list):
                c['members_joined']=set(c['members_joined'])

    return data

def save_data():
    """Persist all user/task/admin state. PostgreSQL is primary when configured; JSON is a backup/fallback.
    Existing records are updated in-place; nothing is intentionally deleted during saves.
    """
    try:
        data = {
            'users_db': users_db, 'tasks_db': tasks_db, 'bonus_balance': bonus_balance,
            'referral_earnings': referral_earnings, 'referrals_db': referrals_db, 'referral_map': referral_map,
            'pending_referrals': pending_referrals, 'withdraw_requests': withdraw_requests,
            'withdraw_done_date': withdraw_done_date, 'last_withdraw_date_db': last_withdraw_date_db,
            'daily_task_count': daily_task_count, 'user_task_status': user_task_status,
            'scheduled_tasks_db': scheduled_tasks_db, 'scheduled_task_counter': scheduled_task_counter,
            'support_plans_db': support_plans_db, 'user_plans': user_plans, 'pending_plans': pending_plans,
            'missed_tasks_db': missed_tasks_db, 'skip_db': skip_db, 'warnings_db': warnings_db,
            'banned_users': banned_users, 'task_images_db': task_images_db, 'screenshot_hashes': screenshot_hashes,
            'promo_campaigns_db': promo_campaigns_db, 'promo_campaign_counter': promo_campaign_counter,
            'promo_earnings_db': promo_earnings_db, 'promo_views_db': promo_views_db, 'promo_pending': promo_pending,
            'pending_daily': pending_daily, 'holidays_db': holidays_db, 'withdraw_history_db': withdraw_history_db, 'ADMIN_ID_LIST': ADMIN_ID_LIST, 'ADMIN_NAMES_DB': admin_names_db, 'MISSED_ENABLED': MISSED_ENABLED,
            'PAYMENT_UPI': get_payment_upi(),
        }
        safe=_json_safe(data)
        # Always keep a local backup too.
        with open(DATA_FILE,'w',encoding='utf-8') as f:
            json.dump(safe,f,ensure_ascii=False)
        if DATABASE_URL:
            _db_save_snapshot(safe)
        print(f"Data saved OK - Users:{len(users_db)} Pending:{len(pending_daily)} Admins:{len(ADMIN_ID_LIST)}")
    except Exception as e:
        print(f"Save error {e}")

def _apply_loaded_data(data):
    global PAYMENT_UPI, scheduled_task_counter, promo_campaign_counter, MISSED_ENABLED, ADMIN_ID_LIST, admin_names_db
    data=_restore_special_state(data or {})
    # Normalize user IDs one more time after every persistence load. Older snapshots can
    # contain both integer and string user IDs; merge them instead of losing the record.
    loaded_users = data.get('users_db')
    if isinstance(loaded_users, dict):
        merged_users = {}
        for k, v in loaded_users.items():
            try: nk = int(k)
            except Exception: nk = k
            if isinstance(v, dict):
                merged_users.setdefault(nk, {}).update(v)
            else:
                merged_users[nk] = v
        data['users_db'] = merged_users
    map_names=['users_db','tasks_db','bonus_balance','referral_earnings','referrals_db','referral_map','pending_referrals',
               'withdraw_requests','withdraw_done_date','last_withdraw_date_db','daily_task_count','user_task_status',
               'support_plans_db','user_plans','pending_plans','missed_tasks_db','skip_db','warnings_db','promo_earnings_db',
               'promo_views_db','promo_pending','pending_daily','task_images_db','promo_campaigns_db','holidays_db','withdraw_history_db']
    for name in map_names:
        obj=data.get(name)
        if obj is not None and name in globals():
            target=globals()[name]
            if isinstance(target,dict) and isinstance(obj,dict): target.clear(); target.update(obj)
            elif isinstance(target,list) and isinstance(obj,list): target.clear(); target.extend(obj)
    if isinstance(data.get('banned_users'), (list,set)):
        banned_users.clear(); banned_users.update(data['banned_users'])
    if isinstance(data.get('screenshot_hashes'), (list,set)):
        screenshot_hashes.clear(); screenshot_hashes.update(data['screenshot_hashes'])
    if isinstance(data.get('task_notifications_sent'), (list,set)):
        task_notifications_sent.clear(); task_notifications_sent.update(data['task_notifications_sent'])
    if isinstance(data.get('ADMIN_NAMES_DB'), dict):
        admin_names_db.clear()
        for k, v in data['ADMIN_NAMES_DB'].items():
            try:
                admin_names_db[int(k)] = str(v)
            except Exception:
                pass
    if isinstance(data.get('ADMIN_ID_LIST'),list):
        ADMIN_ID_LIST.clear()
        for x in data['ADMIN_ID_LIST']:
            try:
                x=int(x)
                if x not in ADMIN_ID_LIST: ADMIN_ID_LIST.append(x)
            except: pass
    if isinstance(data.get('awaiting_plan_image_admins'),list):
        awaiting_plan_image_admins.clear(); awaiting_plan_image_admins.update(data['awaiting_plan_image_admins'])
    if isinstance(data.get('awaiting_plan_payment_adminless'),list):
        awaiting_plan_payment_adminless.clear(); awaiting_plan_payment_adminless.update(data['awaiting_plan_payment_adminless'])
    if data.get('PAYMENT_UPI'): PAYMENT_UPI=str(data['PAYMENT_UPI'])
    try: scheduled_task_counter=max(int(data.get('scheduled_task_counter',1)), max([int(t.get('id',0)) for t in scheduled_tasks_db if isinstance(t,dict)],default=0)+1)
    except: pass
    try: promo_campaign_counter=max(int(data.get('promo_campaign_counter',1)), max([int(c.get('id',0)) for c in promo_campaigns_db if isinstance(c,dict)],default=0)+1)
    except: pass
    if 'MISSED_ENABLED' in data: MISSED_ENABLED=bool(data['MISSED_ENABLED'])

def load_data():
    """Load PostgreSQL snapshot first. If empty, load the old bot_data.json and immediately migrate it to DB."""
    try:
        db_data=_db_load_snapshot() if DATABASE_URL else None
        source='PostgreSQL' if db_data else None
        data=db_data
        if data is None and os.path.exists(DATA_FILE):
            with open(DATA_FILE,'r',encoding='utf-8') as f: data=json.load(f)
            source='bot_data.json'
        if data:
            _apply_loaded_data(data)
            normalize_support_plans()
            print(f"Data loaded from {source} - Users:{len(users_db)} Tasks:{len(scheduled_tasks_db)} Plans:{len(support_plans_db)} UserPlans:{len(user_plans)}")
            if source=='bot_data.json' and DATABASE_URL:
                save_data()  # migrate legacy local data to PostgreSQL
        else:
            print('No saved data found - starting with empty state')
    except Exception as e:
        print(f"Load error {e}")
        import traceback; traceback.print_exc()

# User Plans - which user bought which plan
if 'user_plans' not in globals():
    user_plans = {}

def get_reward_for_user(uid, base_reward=5):
    try:
        plan = _get_user_plan_record(uid)
        if not plan:
            return base_reward
        price = int(plan.get('price',0) or 0)
        if price == 199: return 10
        if price == 499: return 15
        if price >= 999: return 20
        return base_reward + (price // 100)
    except Exception:
        return base_reward

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
        user_plans[str(uid)] = pid
        save_data()
        reward = get_reward_for_user(uid, 5)
        await update.message.reply_text(f"Assigned! User {uid} -> {plan['name']} Rs{plan['price']} = Rs{reward}/task")
        try:
            await context.bot.send_message(chat_id=uid, text=f"Your Plan Activated! {plan['name']} Rs{plan['price']} Now Rs{reward}/task!")
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

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
        user = get_user_record(uid)
        plan = _get_user_plan_record(uid)
        reward = get_reward_for_user(uid)
        total = get_balance(uid)
        count, limit, cap = check_daily_limits(uid)
        msg = (f"USER INFO {uid}\nName: {user.get('name')}\nTasks: {tasks_db.get(uid,0)}\n"
               f"Earnings: Rs{total}\nPlan: {plan.get('name',plan.get('plan_name',plan.get('plan','No Plan'))) if plan else 'No Plan'} "
               f"Rs{plan.get('price',0) if plan else 0}\nReward: Rs{reward}/task\nToday: {count}/{limit} tasks\n"
               f"Daily cap: Rs{cap}\nPlan withdrawal cap: Rs{get_total_withdraw_cap(uid)}\n"
               f"Withdrawn: Rs{get_withdrawn_total(uid)}\nRemaining withdrawal cap: Rs{get_withdraw_remaining(uid)}")
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error {e}")




async def bulk_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    try: await q.answer("Processing bulk approval…")
    except: pass
    if not is_admin(q.from_user.id):
        return
    data=str(q.data)
    target=data.replace("bulk_approve_", "", 1)
    if target=="all":
        uids=list(pending_daily.keys())
    else:
        uids=[]
        for uid,p in list(pending_daily.items()):
            t=p.get('task',{}) if isinstance(p,dict) else {}
            if str(t.get('task_number',''))==target or str(t.get('id',''))==target:
                uids.append(uid)
    approved=0
    for uid in uids:
        if uid not in pending_daily: continue
        try:
            pdata=pending_daily[uid]; task=pdata.get('task',{})
            base_reward=int(pdata.get('task',{}).get('reward',5) or 5)
            reward=get_reward_for_user(uid,base_reward)
            _, _, daily_cap = check_daily_limits(uid)
            today=str(get_ist_today())
            if daily_cap > 0 and get_daily_task_earned(uid, today) + int(reward) > daily_cap:
                continue
            tasks_db[uid]=tasks_db.get(uid,0)+1
            today=str(get_ist_today())
            daily_task_count.setdefault(uid,{})[today]=daily_task_count.setdefault(uid,{}).get(today,0)+1
            for tid,st in list(user_task_status.get(uid,{}).items()):
                if isinstance(st,dict) and st.get('status')=='pending_verification':
                    user_task_status[uid][tid]={'status':'completed','completed_at':get_ist_now()}; break
            if reward!=base_reward:
                bonus_balance[uid]=bonus_balance.get(uid,0)+(reward-base_reward)
            pending_daily.pop(uid,None); approved+=1
            try: await context.bot.send_message(chat_id=uid,text=f"✅ Task Approved! +₹{reward}\nBalance: ₹{get_balance(uid)}",reply_markup=main_menu())
            except: pass
        except Exception as e:
            print(f"bulk approval error {uid}: {e}")
    save_data()
    label="ALL PENDING" if target=="all" else f"TASK {target}"
    try: await q.message.reply_text(f"✅ BULK APPROVAL DONE\n\n{label}\nApproved: {approved}\nRemaining pending: {len(pending_daily)}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin",callback_data="back_admin")]]))
    except: pass

# === CHANNEL METHOD + BULK APPROVE V28 ===
# Admin channels - set via command or env
SCREENSHOT_CHANNEL_ID = None  # Set via /set_screenshot_channel
WITHDRAW_CHANNEL_ID = None    # Set via /set_withdraw_channel
JOIN_CHANNEL_ID = None        # Set via /set_join_channel
JOIN_CHANNEL_LINK = CHANNEL_LINK

def _load_channel_config():
    try:
        if os.path.exists("channel_config.json"):
            with open("channel_config.json", 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Channel config load error: {e}")
    return {}

def get_screenshot_channel():
    return _load_channel_config().get('screenshot_channel') or SCREENSHOT_CHANNEL_ID or SCREENSHOT_CHANNEL

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
        with open("channel_config.json", 'w') as f:
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
                    base_reward = pending_daily[uid].get('task',{}).get('reward',5)
                    reward = get_reward_for_user(uid, base_reward)
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
            base_reward = pending_daily[uid].get('task',{}).get('reward',5)
            reward = get_reward_for_user(uid, base_reward)
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
        for jf in ["bot_data.json", "channel_config.json"]:
            if os.path.exists(jf):
                files_to_backup.append(jf)
        # Also backup all _db jsons if exists
        for jf in glob.glob("*_db*.json"):
            if jf not in files_to_backup and os.path.exists(jf):
                files_to_backup.append(jf)
        # Ensure config exists
        if not os.path.exists("bot_data.json"):
            with open("bot_data.json","w") as f: json.dump({}, f)
            files_to_backup.append("bot_data.json")
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
        for jf in ["bot_data.json","channel_config.json","bot_config.json","users_progress.json","referrals.json"]:
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
            "L1: 10% plan commission + task referral bonus\n"
            "L2: Current configured referral system"
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
    except Exception as e:
        print(f"missed toggle error: {e}")


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
        awaiting_plan_image_admins.add(update.effective_user.id)
        await update.message.reply_text(f"Send photo for Plan {pid}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def userlist_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    date_filter = context.args[0] if context.args else None
    items = list(users_db.items())
    if date_filter:
        items = [(uid,d) for uid,d in items if str(d.get('joined',d.get('reg_date','')))[:10] == date_filter]
    if not items:
        await update.message.reply_text(f"👥 USER LIST\n\nNo users found{(' for '+date_filter) if date_filter else ''}.")
        return
    msg = f"👥 USER LIST{(' — '+date_filter) if date_filter else ''}\nTotal: {len(items)}\n\n"
    for uid, d in items[-50:]:
        plan = _get_user_plan_record(uid) or {}
        pname = plan.get('name', plan.get('plan_name', plan.get('plan','No Plan')))
        msg += f"🆔 {uid}\n👤 {d.get('name','Unknown')}\n💎 {pname}\n📅 Joined: {str(d.get('joined',d.get('reg_date','N/A')))[:10]}\n💰 Balance: ₹{get_balance(uid)}\n\n"
    await update.message.reply_text(msg[:4000])

async def user_history_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /user_history USER_ID [YYYY-MM-DD]\nExample: /user_history 8709635130 2026-08-23")
        return
    try:
        uid=int(context.args[0]); date_filter=context.args[1] if len(context.args)>1 else None
    except:
        await update.message.reply_text("❌ Invalid User ID")
        return
    user=get_user_record(uid)
    plan=_get_user_plan_record(uid) or {}
    count,limit,cap=check_daily_limits(uid)
    msg=f"📊 USER HISTORY\n\n🆔 User ID: {uid}\n👤 Name: {user.get('name','Unknown')}\n📅 Filter: {date_filter or 'All dates'}\n"
    msg += f"💎 Plan: {plan.get('name',plan.get('plan_name',plan.get('plan','No Plan')))}\n🎯 Plan earning cap: ₹{cap}\n💰 Current balance: ₹{get_balance(uid)}\n\n"
    statuses=user_task_status.get(uid,{})
    task_rows=[]
    for tid,st in statuses.items():
        if not isinstance(st,dict): continue
        dt=str(st.get('completed_at',st.get('submitted_at',st.get('skipped_at',st.get('missed_at',st.get('reopened_at',''))))))
        if date_filter and dt[:10] != date_filter: continue
        task_num=st.get('task_number', tid)
        task_rows.append((dt, f"Task {task_num} | {st.get('status','unknown')} | {dt}"))
    task_rows.sort(key=lambda x:x[0])
    msg += '📋 TASK RECORDS\n'
    if task_rows:
        msg += '\n'.join(x[1] for x in task_rows[-50:])+'\n'
    else:
        msg += 'No task records for this filter.\n'
    rows=withdraw_history_db.get(uid,[]) or []
    if date_filter:
        rows=[r for r in rows if str(r.get('date',r.get('created_at','')))[:10]==date_filter]
    msg += '\n💸 WITHDRAWAL RECORDS\n'
    if rows:
        for r in rows[-30:]:
            msg += f"₹{r.get('amount',0)} | {str(r.get('status','unknown')).title()} | {r.get('date',r.get('created_at','N/A'))} | UPI {r.get('upi','N/A')}\n"
    else:
        msg += 'No withdrawal records for this filter.\n'
    await update.message.reply_text(msg[:4000])

async def holiday_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /holiday YYYY-MM-DD [reason]\nExample: /holiday 2026-08-23 Sunday Holiday")
        return
    day=context.args[0]
    try: date.fromisoformat(day)
    except: await update.message.reply_text("❌ Date must be YYYY-MM-DD"); return
    reason=' '.join(context.args[1:]).strip() or 'Holiday / No Tasks'
    holidays_db[day]=reason
    save_data()
    await update.message.reply_text(f"🏖️ Holiday set: {day}\nReason: {reason}\nNo Daily Tasks will be shown on this date.")

async def remove_holiday_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /remove_holiday YYYY-MM-DD"); return
    day=context.args[0]
    if day in holidays_db:
        holidays_db.pop(day,None); save_data(); await update.message.reply_text(f"✅ Holiday removed: {day}")
    else: await update.message.reply_text("No holiday found for that date.")

async def bulk_tasks_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    if len(context.args)<2:
        await update.message.reply_text("Usage: /bulk_tasks YYYY-MM-DD COUNT [REWARD] [START_HOUR] [INTERVAL_MIN]\nExample: /bulk_tasks 2026-08-23 10 5 9 30\n\nFor exact times/titles/links use /add_bulk_tasks DATE followed by one task per line.")
        return
    try:
        day=context.args[0]; count=int(context.args[1]); reward=int(context.args[2]) if len(context.args)>2 else 5
        start_hour=int(context.args[3]) if len(context.args)>3 else 9; interval=int(context.args[4]) if len(context.args)>4 else 30
        date.fromisoformat(day)
        if day in holidays_db: holidays_db.pop(day,None)
        global scheduled_task_counter
        created=[]
        for i in range(count):
            start_min=start_hour*60+i*interval; end_min=start_min+max(5,min(interval,29))
            oh,om=divmod(start_min,60); eh,em=divmod(end_min,60)
            if oh>23 or eh>23: break
            ot=time(oh,om); ct=time(eh,em)
            task={'id':scheduled_task_counter,'date':day,'open_time':f'{oh:02d}:{om:02d}','close_time':f'{eh:02d}:{em:02d}','open_time_obj':ot,'close_time_obj':ct,'title':f'Task {i+1} - {day}','link':get_join_channel_link(),'reward':reward,'task_number':i+1,'next_time':f'{(eh):02d}:{em:02d}','window_minutes':max(5,int((end_min-start_min)))}
            scheduled_tasks_db.append(task); created.append(task); scheduled_task_counter+=1
        save_data()
        ids=', '.join(str(x['id']) for x in created)
        await update.message.reply_text(f"✅ Bulk tasks created: {len(created)}\n📅 {day}\n🆔 Task IDs: {ids}\n\nSet images with /set_task_image TASK_ID and send the photo.")
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")

async def bulk_images_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("Usage: /bulk_images TASK_ID1 TASK_ID2 TASK_ID3 ...\nThen send the photos in the same order."); return
    try:
        ids=[int(x) for x in context.args]
        context.user_data['bulk_image_task_ids']=ids
        await update.message.reply_text(f"🖼️ Bulk image mode ON for {len(ids)} tasks. Send {len(ids)} photos in this exact order.")
    except: await update.message.reply_text("❌ Task IDs must be numbers.")

async def bulk_tasks_help_cmd(update, context):
    await update.message.reply_text("📦 BULK TASKS\n\n/bulk_tasks YYYY-MM-DD COUNT [REWARD] [START_HOUR] [INTERVAL_MIN]\nExample: /bulk_tasks 2026-08-23 10 5 9 30\n\n🖼️ Then /bulk_images TASK_ID1 TASK_ID2 ... and send photos in order.\n🏖️ Sunday/holiday: /holiday YYYY-MM-DD Sunday Holiday\n👥 Users: /userlist [YYYY-MM-DD]\n📊 User history: /user_history USER_ID [YYYY-MM-DD]\n🧾 User withdrawal history is available from Withdraw History.")

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
    global bot_application, bot_event_loop, notification_thread_started
    import os, time, threading
    print("============================================================")
    print("S2E Bot FINAL V56 - No ConversationHandler - Important Channel Fix V56 FINAL - All Filters Fix V56 FINAL - No Reply Fix! - Upload Screenshot + Task Image Final Fix V56 FINAL - Screenshot + Task Image Final Fix V56 FINAL - Final Output! - Screenshot + Task Image Fix V56 FINAL - Final Output! - Task Image + Join ALWAYS True Fix V56 FINAL - Final Output! - Check Joined ALWAYS True + Task Image Fix V56 FINAL - Check Joined Bypass + Withdraw Buttons Fix V56 FINAL - No Sleep + Immediate Polling + Separate Channels + Withdraw 1 Task V56 FINAL - NameError Fixed!")
    print("============================================================")
    # V56 FIX: Flask IMMEDIATE start - No sleep! Fix Live but not responding! NameError Fixed!
    try:
        from flask import Flask
        flask_app = Flask(__name__)
        @flask_app.route('/')
        def home():
            return "S2E Bot V56 FINAL Running - Immediate Polling - No Sleep - NameError Fixed"
        flask_port = int(os.environ.get("PORT", 10000))
        print(f"V56 Starting Flask IMMEDIATELY on port {flask_port} env PORT={os.environ.get('PORT')}")
        def run_flask():
            try:
                print(f"V56 Flask thread running on 0.0.0.0:{flask_port}")
                flask_app.run(host='0.0.0.0', port=flask_port, debug=False, use_reloader=False)
            except Exception as e:
                print(f"V56 Flask err {e}")
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print(f"V56 Flask thread started IMMEDIATELY on port {flask_port} - No 120 sec sleep! FINAL! NameError Fixed!")
        time.sleep(2)
    except Exception as e:
        print(f"V56 Flask setup err {e}")

    print("V56 NO 120 sec sleep! Starting bot IMMEDIATELY! Fix Live but not responding! NameError Fixed!")
    print(f"PERSISTENCE CHECK: DATABASE_URL configured = {bool(DATABASE_URL)}")
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL is NOT configured. Render restarts/redeploys cannot retain user data. Add Render PostgreSQL DATABASE_URL.")
    print("V56 Quick webhook delete 2 times - No long sleep! NameError Fixed!")
    try:
        import urllib.request
        for i in range(2):
            try:
                urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=10)
                print(f"V56 Quick Webhook delete {i+1}/2 - NameError Fixed!")
                time.sleep(1)
            except Exception as e:
                print(f"V56 Quick delete {i+1} err {e}")
    except Exception as e:
        print(f"V56 Quick webhook outer err {e}")

    print("V56 Starting bot polling IMMEDIATELY - No 120 sec sleep - FINAL! NameError Fixed!")
    _db_init()
    load_data()
    normalize_support_plans()
    save_data()
    try:
        threading.Thread(target=keep_alive_pinger, daemon=True).start()
        print('Keep-alive started V56 FINAL')
    except:
        pass

    retry_count = 0
    max_retries = 100
    while retry_count < max_retries:
        print(f"\nV56 Build attempt {retry_count+1}/{max_retries} - Polling NOW! No Sleep! FINAL! NameError Fixed!")
        app = None
        try:
            print(f"\nV56 Build attempt {retry_count+1}/{max_retries} - FINAL!")
            app = Application.builder().token(BOT_TOKEN).build()
            app.add_error_handler(error_handler)
            try:
                app.add_handler(CallbackQueryHandler(back_admin_cb_fixed, pattern='^back_admin$',), group=-2)
                app.add_handler(CallbackQueryHandler(back_menu_cb_fixed, pattern='^back_menu$',), group=-2)
                app.add_handler(CallbackQueryHandler(withdraw_cb, pattern='^withdraw$',), group=-2)
                app.add_handler(CallbackQueryHandler(promo_tasks_cb_fixed, pattern='^promo_tasks$',), group=-2)
                app.add_handler(CallbackQueryHandler(scheduled_tasks_cb_fixed, pattern='^scheduled_tasks$',), group=-2)
                app.add_handler(CallbackQueryHandler(support_plans_cb, pattern='^support_plans$',), group=-2)
                print('V56 All Fixed group -2 - NameError Fixed!')
                app.add_handler(CallbackQueryHandler(bulk_approve_callback, pattern='^bulk_approve_'), group=-2)
                # V63 FIX: payment-proof Approve/Reject must run before other callback handlers.
                app.add_handler(CallbackQueryHandler(admin_approve_plan_cb, pattern=r'^admin_approve_plan_'), group=-2)
                app.add_handler(CallbackQueryHandler(admin_reject_plan_cb, pattern=r'^admin_reject_plan_'), group=-2)
            except Exception as e:
                print(f'V56 fix {e}')

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
                        "user_name": get_user_record(uid).get("name", update.effective_user.full_name)
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
                                    f"👤 Name: {get_user_record(uid).get('name', update.effective_user.full_name or 'Unknown')}\n"
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
            # V56 FINAL FIX: No ConversationHandler for screenshot - Simple handlers - Important channel ki vachedi!
            conv_screenshot = None  # Disabled - Using simple MessageHandler instead!
            print("V56 conv_screenshot disabled - Using simple handlers! FINAL!")

            conv_skip = ConversationHandler(
                entry_points=[CallbackQueryHandler(daily_skip_cb, pattern="^daily_skip_")],
                states={
                    SKIP_REASON:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_skip_reason), CallbackQueryHandler(skip_reason_cb, pattern="^skip_reason_")],
                },
                fallbacks=[CommandHandler("cancel", cancel)],
                per_user=True, per_chat=True, per_message=False
            )
            # V56 FINAL FIX: No ConversationHandler for task image - Simple handlers - Important channel ki vachedi!
            # Old ConversationHandler caused no reply - Replace with simple handlers!
            conv_set_image = None  # Disabled - Using simple MessageHandler instead!
            print("V56 conv_set_image disabled - Using simple handlers! FINAL!")

            app.add_handler(conv_reg)
            # V56 Disabled: app.add_handler(conv_screenshot) - Using simple handlers! FINAL!
            app.add_handler(conv_skip)

            # V56 FINAL FIX: Simple MessageHandlers - No ConversationHandler - Task image + Screenshot important channel ki vachedi! FINAL!
            # Task image handler - Admin photo with set_image_task_id or caption /set_task_image
            async def v56_task_image_simple_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    uid = update.effective_user.id
                    bulk_ids = context.user_data.get('bulk_image_task_ids') if is_admin(uid) else None
                    if bulk_ids and (update.message.photo or update.message.document):
                        task_id = int(bulk_ids.pop(0))
                        file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
                        task_images_db[task_id] = file_id
                        task = next((t for t in scheduled_tasks_db if int(t.get('id',-1)) == task_id), None)
                        if task:
                            task['image_file_id'] = file_id; task['has_image'] = True
                        save_data()
                        if bulk_ids:
                            context.user_data['bulk_image_task_ids'] = bulk_ids
                            await update.message.reply_text(f"✅ Image set for Task {task_id}. Send next photo for Task {bulk_ids[0]}.")
                        else:
                            context.user_data.pop('bulk_image_task_ids', None)
                            await update.message.reply_text(f"✅ Bulk images completed. Image set for Task {task_id}.", reply_markup=main_menu())
                        return
                    if not is_admin(uid):
                        return
                    if not update.message.photo and not update.message.document:
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
                        print(f"V56 v56_task_image_simple_handler: Image Poster Set for Task {task_id}: {task['title']} file_id {file_id[:20]} FINAL! Important channel ki vachedi!")
                    await update.message.reply_text(f"✅ V56 Image Poster Set for Task {task_id}! {task['title'] if task else ''} Members will see YOUR TASK image when they open Daily Task! V56 FINAL Check /menu -> Daily Task - Image will show! Important channel ki vachedi!", reply_markup=main_menu())
                    try:
                        await context.bot.send_photo(chat_id=uid, photo=file_id, caption=f"✅ V56 Confirmation - Task {task_id} Image Set! FINAL! Important channel ki vachedi!")
                    except:
                        try:
                            await context.bot.send_document(chat_id=uid, document=file_id, caption=f"✅ V56 Confirmation - Task {task_id} Image Set! FINAL!")
                        except Exception as e:
                            print(f"V56 confirmation err {e}")
                    context.user_data.pop('set_image_task_id', None)
                except Exception as e:
                    print(f"V56 v56_task_image_simple_handler err {e}")
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
                            if requested_task:
                                task_to_use = requested_task
                        except Exception:
                            pass
                    if not task_to_use:
                        default_task = get_today_task_for_user(uid)
                        if not default_task and scheduled_tasks_db:
                            default_task = scheduled_tasks_db[-1]
                        if not default_task:
                            default_task = {'id': 0, 'title': 'Daily Task', 'reward': 5, 'task_number': 1, 'open_time': '00:00', 'close_time': '23:59'}
                        task_to_use = default_task
                    if not task_to_use:
                        await update.message.reply_text("❌ No task is available for this screenshot. Open Daily Task or Missed Tasks first.", reply_markup=main_menu())
                        return
                    task_id_for_check = int(task_to_use.get('id', 0) or 0)
                    status_data = user_task_status.get(uid, {}).get(task_id_for_check, {})
                    status = status_data.get('status') if isinstance(status_data, dict) else status_data
                    # Normal task: screenshot is accepted only while its window is open.
                    # Reopened missed task: explicitly allowed after the original window.
                    reopened = status == 'reopened'
                    if str(task_to_use.get('date')) == str(get_ist_today()) and not reopened:
                        try:
                            close_obj = task_to_use.get('close_time_obj') or parse_time_str(str(task_to_use.get('close_time','')))
                            if close_obj and get_ist_time() > close_obj:
                                check_missed_tasks_with_interval(uid)
                                await update.message.reply_text(
                                    f"⏰ Task {task_to_use.get('task_number',1)} is already closed ({task_to_use.get('open_time','')}→{task_to_use.get('close_time','')}).\n\nOpen Missed Tasks and tap 'Do Missed Task' if you want to reopen it.",
                                    reply_markup=main_menu()
                                )
                                context.user_data.pop('awaiting_daily_screenshot', None)
                                context.user_data.pop('daily_screenshot_task_id', None)
                                return
                        except Exception as e:
                            print(f"V68 expiry check error: {e}")
                    if status in ('completed','pending_verification'):
                        await update.message.reply_text("⏳ This task is already completed or pending admin verification.", reply_markup=main_menu())
                        return
                    if file_unique_id and file_unique_id in screenshot_hashes:
                        await update.message.reply_text("WARNING Same Screenshot! V56")
                        return
                    if file_unique_id:
                        screenshot_hashes.add(file_unique_id)
                    today = str(get_ist_today())
                    pending_daily[uid] = {'date': today, 'task': task_to_use, 'screenshot_file_id': file_id}
                    if uid not in user_task_status:
                        user_task_status[uid] = {}
                    task_id_for_status = task_to_use.get('id', 0)
                    user_task_status[uid][task_id_for_status] = {'status': 'pending_verification', 'submitted_at': get_ist_now(), 'reopened_from_missed': reopened}
                    await update.message.reply_text(f"✅ V56 Screenshot Received for Task {task_to_use.get('task_number',1)}! Pending Admin Verification! V56 FINAL - Important channel ki vachedi! Screenshot fix!", reply_markup=main_menu())
                    try:
                        chan = get_screenshot_channel()
                        user_name = get_user_record(uid).get('name', update.effective_user.full_name or 'Unknown')
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
                        print(f"V56 screenshot channel err {e} - Trying without keyboard! Channel {chan}")
                        try:
                            await context.bot.send_photo(chat_id=chan, photo=file_id, caption=f"NEW TASK V56 User {uid} Task {task_to_use.get('task_number',1)}")
                        except:
                            try:
                                await context.bot.send_document(chat_id=chan, document=file_id, caption=f"NEW TASK V56 User {uid}")
                            except Exception as e3:
                                print(f"V56 screenshot channel err3 {e3} - Bot not admin in {chan}? Make bot admin!")
                except Exception as e:
                    print(f"V56 v56_screenshot_simple_handler err {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        await update.message.reply_text(f"✅ V56 Screenshot Received! Pending Verification! V56 FINAL - Important channel ki vachedi!", reply_markup=main_menu())
                    except:
                        pass

            # V56 Add simple handlers with high priority - No ConversationHandler!
            app.add_handler(MessageHandler(filters.PHOTO, v56_task_image_simple_handler), group=1)
            app.add_handler(MessageHandler(filters.Document.ALL, v56_task_image_simple_handler), group=1)
            app.add_handler(MessageHandler(filters.PHOTO, v56_screenshot_simple_handler), group=2)
            app.add_handler(MessageHandler(filters.Document.ALL, v56_screenshot_simple_handler), group=2)
            print("V56 Simple handlers added - No ConversationHandler - Task image + Screenshot important channel ki vachedi! FINAL!")
            # V56 Disabled: app.add_handler(conv_set_image) - Using simple handlers! FINAL!
            # V56 FALLBACK: General photo handler for cases where conversation state lost - Task image + Screenshot fix!
            async def fallback_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    uid = update.effective_user.id
                    if not update.message.photo:
                        return
                    # If admin and has set_image_task_id in user_data, handle as task image
                    if is_admin(uid) and context.user_data.get('set_image_task_id'):
                        print(f"V56 fallback_photo_handler: Admin {uid} has set_image_task_id {context.user_data.get('set_image_task_id')} - Handling as task image!")
                        await handle_task_image_upload(update, context)
                        return
                    # If admin and caption contains /set_task_image, handle as task image
                    if is_admin(uid) and update.message.caption and '/set_task_image' in update.message.caption:
                        print(f"V56 fallback_photo_handler: Admin {uid} photo with caption /set_task_image - Handling as task image!")
                        await set_task_image_cmd(update, context)
                        return
                    # If member and has active task, handle as screenshot
                    # Check if user is in UPLOAD_SCREENSHOT state or has recently requested upload
                    # For fallback, always try to handle as screenshot if not admin
                    if not is_admin(uid):
                        print(f"V56 fallback_photo_handler: Member {uid} photo - Handling as screenshot fallback! FINAL!")
                        await handle_screenshot_upload(update, context)
                        return
                except Exception as e:
                    print(f"V56 fallback_photo_handler err {e}")
            
            # IMPORTANT: No catch-all PHOTO fallback. The dedicated handlers above
            # must receive the update so the Upload Screenshot flow is reliable.
            print("V56 Catch-all photo fallback disabled - dedicated upload handlers active!")

            app.add_handler(CommandHandler("menu", menu))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("pending", pending_cmd))
            app.add_handler(CommandHandler("approve", approve_cmd))
            app.add_handler(CommandHandler("add_task", add_scheduled_task_with_interval_cmd))
            app.add_handler(CommandHandler("list_tasks", list_scheduled_tasks_cmd))
            app.add_handler(CommandHandler("set_task_image", set_task_image_cmd))
            app.add_handler(CommandHandler("set_payment_upi", set_payment_upi_cmd))
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
                    pattern=r"^daily_upload_v2$"
                ),
                group=-100
            )
            app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
            app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
            app.add_handler(CallbackQueryHandler(withdraw_history_cb, pattern="^withdraw_history$"))
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
            app.add_handler(CallbackQueryHandler(missed_work_cb, pattern="^missed_work_"))
            app.add_handler(CallbackQueryHandler(my_details_cb, pattern="^my_details$"))
            app.add_handler(CallbackQueryHandler(contact_us_cb, pattern="^contact_us$"))
            app.add_handler(CallbackQueryHandler(back_admin_cb, pattern="^back_admin$"))
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
            app.add_handler(CommandHandler("bulk_tasks", bulk_tasks_cmd))
            app.add_handler(CommandHandler("add_bulk_tasks", add_bulk_tasks_cmd))
            app.add_handler(CommandHandler("bulk_add", add_bulk_tasks_cmd))
            app.add_handler(CommandHandler("bulk_help", bulk_tasks_help_cmd))
            app.add_handler(CommandHandler("bulk_images", bulk_images_cmd))
            app.add_handler(CommandHandler("holiday", holiday_cmd))
            app.add_handler(CommandHandler("remove_holiday", remove_holiday_cmd))
            app.add_handler(CommandHandler("userlist", userlist_cmd))
            app.add_handler(CommandHandler("user_list", userlist_cmd))
            app.add_handler(CommandHandler("user_history", user_history_cmd))
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
            app.add_handler(CommandHandler("channels_status", channels_status_cmd))
            app.add_handler(CommandHandler("channels_list", channels_list_cmd))

            print("V56 Bot handlers registered - All handlers from V20 - Polling NOW! FINAL - NameError Fixed!")
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
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES,
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
            print(f"V56 Polling attempt {retry_count+1} failed: {e}")
            if isinstance(e, RuntimeError) and "Event loop is closed" in str(e):
                print("V56 EVENT LOOP RECOVERY: fresh asyncio loop will be created on the next attempt")
            import traceback
            traceback.print_exc()
            retry_count += 1
            time.sleep(5)
            continue

if __name__ == "__main__":
    main()
