
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

# CONFIG
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

# BINARY SYSTEM CONFIG
REFERRAL_BONUS_PER_TASK = 10  # Each left+right match = Rs50
REFERRAL_PLAN_COMMISSION_PERCENT = 10  # Premium user gets Rs100 per pair
BINARY_MATCHING_BONUS_ENABLED = True

app_flask = Flask(__name__)
real_tasks_db = {}

@app_flask.route('/')
def home(): return "S2E Binary Left-Right Matching + 17 Tasks + Anti-Scam"

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
screenshot_db = {}
task_open_time = {}

# === BINARY LEFT-RIGHT SYSTEM ===
binary_tree = {}  # uid -> {'left': set(), 'right': set(), 'left_count': int, 'right_count': int, 'pairs': int, 'earnings': int}
binary_placements = {}  # new_user_id -> {'parent': parent_id, 'side': 'left'/'right'}
binary_pair_history = {}  # uid -> list of matched pairs

def init_binary_user(uid):
    if uid not in binary_tree:
        binary_tree[uid] = {'left': set(), 'right': set(), 'left_count': 0, 'right_count': 0, 'pairs_matched': 0, 'binary_earnings': 0, 'carry_left': 0, 'carry_right': 0}

def place_in_binary(new_user_id, parent_id, side=None):
    # Auto choose weaker leg if side not given
    init_binary_user(parent_id)
    init_binary_user(new_user_id)
    
    if side not in ['left', 'right']:
        # Auto placement - weaker leg
        left_count = binary_tree[parent_id]['left_count']
        right_count = binary_tree[parent_id]['right_count']
        side = 'left' if left_count <= right_count else 'right'
    
    if side == 'left':
        binary_tree[parent_id]['left'].add(new_user_id)
        binary_tree[parent_id]['left_count'] += 1
    else:
        binary_tree[parent_id]['right'].add(new_user_id)
        binary_tree[parent_id]['right_count'] += 1
    
    binary_placements[new_user_id] = {'parent': parent_id, 'side': side, 'date': str(date.today())}
    return side

def check_binary_matching(parent_id):
    # Check left-right matching and give bonus
    init_binary_user(parent_id)
    left = binary_tree[parent_id]['left_count']
    right = binary_tree[parent_id]['right_count']
    pairs_matched = binary_tree[parent_id]['pairs_matched']
    
    # Total possible pairs = min(left, right)
    total_pairs = min(left, right)
    new_pairs = total_pairs - pairs_matched
    
    if new_pairs > 0 and BINARY_MATCHING_BONUS_ENABLED:
        # Check if parent is premium for higher bonus
        plan = user_plans.get(parent_id, {}).get('plan', 'basic')
        bonus_per_pair = BINARY_BONUS_PREMIUM_PER_PAIR if plan == 'premium' else BINARY_BONUS_PER_PAIR
        
        total_bonus = new_pairs * bonus_per_pair
        
        binary_tree[parent_id]['pairs_matched'] = total_pairs
        binary_tree[parent_id]['binary_earnings'] += total_bonus
        
        # Add to referral earnings
        referral_earnings[parent_id] = referral_earnings.get(parent_id, 0) + total_bonus
        
        # History
        if parent_id not in binary_pair_history:
            binary_pair_history[parent_id] = []
        binary_pair_history[parent_id].append({
            'date': str(date.today()),
            'new_pairs': new_pairs,
            'bonus_per_pair': bonus_per_pair,
            'total_bonus': total_bonus,
            'left_count': left,
            'right_count': right
        })
        
        return new_pairs, total_bonus, bonus_per_pair
    return 0, 0, 0

def get_binary_stats(uid):
    init_binary_user(uid)
    data = binary_tree[uid]
    left = data['left_count']
    right = data['right_count']
    pairs = data['pairs_matched']
    earnings = data['binary_earnings']
    # Next pair needs
    next_pair_need = "Need 1 Left + 1 Right for next Rs50" if left == right else f"Need {1 if left > right else '1 Right' if right > left else 'Left'} for next pair"
    if left > right:
        next_need = f"Need {left - right} Right for balancing, then pairs"
    elif right > left:
        next_need = f"Need {right - left} Left for balancing"
    else:
        next_need = "Balanced! Need 1 Left + 1 Right for next pair"
    
    return left, right, pairs, earnings, next_need

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

# === BINARY TEAM CALLBACKS ===
async def support_plans_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    left, right, pairs, earnings, next_need = get_binary_stats(uid)
    init_binary_user(uid)
    
    left_list = list(binary_tree[uid]['left'])[:5]
    right_list = list(binary_tree[uid]['right'])[:5]
    
    text = (
        f"💎 BINARY TEAM - Left & Right Matching\n\n"
        f"Left Team: {left} members\n"
        f"Right Team: {right} members\n"
        f"Matched Pairs: {pairs}\n"
        f"Binary Earnings: Rs{earnings}\n\n"
        f"Bonus: Rs{BINARY_BONUS_PER_PAIR}/pair Basic, Rs{BINARY_BONUS_PREMIUM_PER_PAIR}/pair Premium\n"
        f"Left + Right = 1 Pair = Bonus!\n\n"
        f"{next_need}\n\n"
        f"As left and right increase, amount adds automatically!\n"
        f"Left members: {len(left_list)} shown\n"
        f"Right members: {len(right_list)} shown\n\n"
        f"Your Referral Link: https://t.me/{context.bot.username}?start={uid}\n"
        f"New members auto placed to weaker leg!"
    )
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref")],
        [InlineKeyboardButton("📊 Pair History", callback_data="binary_history")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
    ])
    await q.message.reply_text(text, reply_markup=kb)

async def binary_history_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    history = binary_pair_history.get(uid, [])
    if not history:
        await q.message.reply_text("No pair matching history yet! Need Left + Right for first pair!", reply_markup=main_menu())
        return
    msg = f"Pair Matching History - {len(history)} events:\n\n"
    for h in history[-10:]:
        msg += f"{h.get('date')} - {h.get('new_pairs')} pairs x Rs{h.get('bonus_per_pair')} = Rs{h.get('total_bonus')} (L{h.get('left_count')} R{h.get('right_count')})\n"
    await q.message.reply_text(msg[:4000], reply_markup=main_menu())

async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    cnt=referrals_db.get(uid,0)
    earnings = referral_earnings.get(uid,0) if 'referral_earnings' in globals() else referrals_db.get(uid,0)*10
    ref_link = f"https://t.me/{context.bot.username}?start={uid}"
    await q.message.reply_text(f"My Referrals\n\nActive Referrals: {cnt}\nReferral Earnings: Rs{earnings}\n\nBonus: Rs10 per task completed by referral\nPlan Commission: 10% when referral buys plan\n\nYour Link: {ref_link}\n\nShare link - When friend joins and completes 1st task, you get Rs10!", reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    is_active, plan_status, _ = check_plan_active(uid)
    left, right, pairs, binary_earnings, _ = get_binary_stats(uid)
    await q.message.reply_text(f"Balance Rs{get_balance(uid)} Tasks {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW} Plan {plan_status} Binary Pairs {pairs} Earnings Rs{binary_earnings} L{left} R{right}", reply_markup=main_menu())

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
    task_open_time[uid] = datetime.now()
    task = get_today_task_for_user(uid)
    task_limit, _, plan_type = get_plan_limits(uid)
    current_count = daily_task_count.get(uid, {}).get(today, 0)
    kb=InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Task {current_count+1}: {task.get('title')} - Open", url=task.get('link', CHANNEL_LINK))],
        [InlineKeyboardButton("Upload Screenshot - Verify", callback_data="daily_upload_screenshot")],
        [InlineKeyboardButton("Cancel", callback_data="back_menu")]
    ])
    await q.message.reply_text(f"Daily Task {current_count+1}/{task_limit} - {plan_type.upper()} {task.get('title')} Reward Rs{task.get('reward',5)} Plan {plan_status}", reply_markup=kb)

async def daily_upload_screenshot_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text(f"Upload Screenshot - No paper needed! Send photo within 15 mins! Duplicate check active!", reply_markup=ReplyKeyboardRemove())
    return UPLOAD_SCREENSHOT

async def handle_screenshot_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    today=str(date.today())
    if not update.message.photo:
        await update.message.reply_text("Please send as PHOTO!")
        return UPLOAD_SCREENSHOT
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_unique_id = photo.file_unique_id
    if file_unique_id in screenshot_hashes:
        if uid not in warnings_db: warnings_db[uid] = {'count': 0}
        warnings_db[uid]['count'] += 1
        count = warnings_db[uid]['count']
        if count == 1:
            await update.message.reply_text(f"WARNING 1/3 - Same Screenshot Found! Same screenshot share chesukunatlu undi! 1st Warning!", reply_markup=main_menu())
            return ConversationHandler.END
        elif count == 2:
            await update.message.reply_text(f"WARNING 2/3 - Malli Same Screenshot! 2nd Warning! Next BAN!", reply_markup=main_menu())
            return ConversationHandler.END
        else:
            banned_users.add(uid)
            await update.message.reply_text(f"BANNED! 3 Warnings! Contact admin /unban {uid}", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
    task = get_today_task_for_user(uid)
    screenshot_hashes.add(file_unique_id)
    screenshot_db[uid] = {'file_id': file_id, 'file_unique_id': file_unique_id, 'task_date': today, 'task': task}
    pending_daily[uid] = {'date': today, 'task': task, 'screenshot_file_id': file_id}
    await update.message.reply_text(f"Screenshot Received! Task {task.get('title')} Pending Admin!", reply_markup=main_menu())
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"Approve Rs{task.get('reward',5)}", callback_data=f"admin_approve_daily_{uid}"), InlineKeyboardButton("Reject", callback_data=f"admin_reject_daily_{uid}")]])
            await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=f"NEW SCREENSHOT User {users_db.get(uid,{}).get('name')} ID {uid} Task {task.get('title')} Reward Rs{task.get('reward',5)}", reply_markup=kb)
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
        # Place in binary
        side = place_in_binary(uid, ref_id)
        # Check matching bonus for parent
        new_pairs, total_bonus, bonus_per_pair = check_binary_matching(ref_id)
        if new_pairs > 0:
            try:
                await context.bot.send_message(chat_id=ref_id, text=f"💎 BINARY BONUS! {new_pairs} new pairs matched! Left+Right bonus Rs{total_bonus} (Rs{bonus_per_pair}/pair) Placed {uid} to {side} side!")
            except: pass
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
    await q.message.reply_text(f"Banned {uid}")

async def admin_unban_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    uid = int(q.data.split("_")[-1])
    banned_users.discard(uid)
    if uid in warnings_db: warnings_db[uid]['count']=0
    await q.message.reply_text(f"Unbanned {uid}")

async def withdraw_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    if bal < WITHDRAW_MIN: await q.message.reply_text(f"Balance Rs{bal}/{WITHDRAW_MIN} Low!", reply_markup=main_menu()); return
    if get_tasks(uid) < TASKS_REQUIRED_FOR_WITHDRAW: await q.message.reply_text(f"Tasks {get_tasks(uid)}/{TASKS_REQUIRED_FOR_WITHDRAW} needed!", reply_markup=main_menu()); return
    buttons=[]; row=[]; info=f"Withdraw Balance Rs{bal} Min {WITHDRAW_MIN} Max {WITHDRAW_MAX}\n"
    for amount in WITHDRAW_OPTIONS:
        if amount <= bal: row.append(InlineKeyboardButton(f"Rs{amount}", callback_data=f"wd_select_{amount}"))
        if len(row)==2: buttons.append(row); row=[]
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton("Back", callback_data="back_menu")])
    await q.message.reply_text(info, reply_markup=InlineKeyboardMarkup(buttons))

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
    await q.message.reply_text(f"Plans: Basic Rs500 10 tasks/day Max Rs200, Premium Rs1000 20 tasks/day Max Rs500 + Binary Bonus Rs50-100 per pair, Your: {plan_status}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Basic Rs500", callback_data="plan_basic")],[InlineKeyboardButton("Premium Rs1000", callback_data="plan_premium")]]))

async def plan_basic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Pay Rs500", url=DEPOSIT_LINK_BASIC)],[InlineKeyboardButton("I Paid", callback_data="verify_basic")]])
    await q.message.reply_text(f"Basic Rs500 30 Days Binary Rs50/pair", reply_markup=kb)

async def plan_premium_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    kb=InlineKeyboardMarkup([[InlineKeyboardButton("Pay Rs1000", url=DEPOSIT_LINK_PREMIUM)],[InlineKeyboardButton("I Paid", callback_data="verify_premium")]])
    await q.message.reply_text(f"Premium Rs1000 90 Days Binary Rs100/pair + Bonus", reply_markup=kb)

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
        left, right, pairs, earnings, _ = get_binary_stats(uid)
        await update.message.reply_text(f"Welcome {users_db[uid]['name']} Balance Rs{get_balance(uid)} Plan {plan_status} Binary L{left} R{right} Pairs {pairs}", reply_markup=main_menu())
        return
    await update.message.reply_text(f"Welcome S2E! Binary Left-Right Matching! Day1 FREE! ID: {uid}", reply_markup=join_channel_keyboard(False))

async def check_joined_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    users_db[uid]={'reg_date': date.today()}
    init_binary_user(uid)
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
    await update.message.reply_text("Menu: Support Plans available! Left-Right matching bonus!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu:", reply_markup=main_menu())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if not is_admin(uid): return
    banned_count = len(banned_users)
    binary_users = len(binary_tree)
    await update.message.reply_text(f"ADMIN Binary Left-Right System Users {len(users_db)} Binary {binary_users} Banned {banned_count} /pending /binary_stats")

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
            side = place_in_binary(target_id, ref_id)
            new_pairs, total_bonus, bonus_per_pair = check_binary_matching(ref_id)
            del pending_referrals[target_id]
        await update.message.reply_text(f"Approved {target_id} +Rs{reward}")

async def binary_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not binary_tree: await update.message.reply_text("No binary data!"); return
    msg = f"Binary Stats - Total {len(binary_tree)} users with teams:\n\n"
    for uid, data in list(binary_tree.items())[:20]:
        name = users_db.get(uid,{}).get('name','Unknown')
        msg += f"{uid} {name} L{data['left_count']} R{data['right_count']} Pairs {data['pairs_matched']} Earn Rs{data['binary_earnings']}\n"
    await update.message.reply_text(msg[:4000])

async def warnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not warnings_db: await update.message.reply_text("No warnings!"); return
    msg = f"Warnings {len(warnings_db)}:\n"
    for uid, data in warnings_db.items():
        msg += f"{uid} {data.get('count')}/3 /unban {uid}\n"
    await update.message.reply_text(msg[:4000])

async def banned_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not banned_users: await update.message.reply_text("No banned!"); return
    msg = f"Banned {len(banned_users)}:\n"
    for uid in banned_users:
        msg += f"{uid} /unban {uid}\n"
    await update.message.reply_text(msg[:4000])

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text("Usage /unban <id>"); return
    try: target_id=int(context.args[0])
    except: return
    banned_users.discard(target_id)
    if target_id in warnings_db: warnings_db[target_id]['count']=0
    await update.message.reply_text(f"Unbanned {target_id}")

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
        states={UPLOAD_SCREENSHOT:[MessageHandler(filters.PHOTO, handle_screenshot_upload)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True, per_chat=True, per_message=False
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("binary_stats", binary_stats_cmd))
    app.add_handler(CommandHandler("warnings", warnings_cmd))
    app.add_handler(CommandHandler("banned", banned_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
    app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(daily_cb, pattern="^daily$"))
    app.add_handler(CallbackQueryHandler(admin_approve_daily_cb, pattern="^admin_approve_daily_"))
    app.add_handler(CallbackQueryHandler(admin_reject_daily_cb, pattern="^admin_reject_daily_"))
    app.add_handler(CallbackQueryHandler(admin_ban_cb, pattern="^admin_ban_"))
    app.add_handler(CallbackQueryHandler(admin_unban_cb, pattern="^admin_unban_"))
    app.add_handler(CallbackQueryHandler(withdraw_cb, pattern="^withdraw$"))
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
    app.add_handler(conv_reg)
    app.add_handler(conv_screenshot)
    print(f"Bot Started! Binary Left-Right Matching + 17 Tasks + Anti-Scam!")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
