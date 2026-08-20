import os, re, threading, json, asyncio
from datetime import date, datetime, timedelta, time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_LIST = [7256515560, 8544307598]
_env = os.getenv("ADMIN_IDS") or ""
if _env:
    for x in _env.replace(",", " ").split():
        if x.strip().isdigit():
            _id = int(x.strip())
            if _id not in ADMIN_ID_LIST: ADMIN_ID_LIST.append(_id)

# CONFIG
WITHDRAW_MIN = 200
PLATFORM_FEE_PERCENT = 7
REFERRAL_BONUS = 10
TASK_LIMIT_BASIC = 10
TASK_LIMIT_PREMIUM = 20

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "S2E Promo Marketplace - Local Shops Promotion Network"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

NAME, GENDER, DOB, MOBILE, UPI, PINCODE, PROFESSION, UPLOAD_SCREENSHOT, SKIP_REASON, PROMO_DETAILS, PROMO_BUDGET = range(11)

users_db = {}
referrals_db = {}
tasks_db = {}
bonus_balance = {}
banned_users = set()
pending_daily = {}
user_plans = {}
referral_map = {}
referral_earnings = {}
withdraw_requests = {}
daily_task_count = {}
screenshot_hashes = set()
task_open_time = {}
skip_db = {}
scheduled_tasks_db = []
scheduled_task_counter = 1
user_task_status = {}
task_notifications_sent = set()

# === PROMO MARKETPLACE - NEW IDEA ===
# Advertisers (Shop owners) database
advertisers_db = {}  # advertiser_id -> {name, shop_name, phone, place, category}
promo_campaigns_db = []  # List of promo campaigns
promo_campaign_counter = 1
promo_tasks_db = {}  # campaign_id -> list of promo tasks for members
promo_earnings_db = {}  # uid -> total promo earnings
promo_views_db = {}  # campaign_id -> total views, member_id -> views

# Campaign structure: {
#   'id': 1,
#   'shop_name': 'Kavali Fashions',
#   'owner_name': 'Ramesh',
#   'phone': '9876543210',
#   'place': 'Kavali',
#   'category': 'Clothing',
#   'title': 'Diwali Sale 50% Off',
#   'description': 'All sarees 50% off till Diwali',
#   'poster_link': 'https://...',
#   'offer': '50% off',
#   'target_views': 10000,
#   'per_100_views_price': 200,  # Shop pays Rs200 per 100 views
#   'per_view_member_earning': 10,  # Member earns Rs10 per 100 views (Rs0.1 per view)
#   'per_sale_commission': 10,  # 10% per sale
#   'status': 'active',  # active, completed, paused
#   'created_at': datetime,
#   'expiry': date,
#   'total_views': 0,
#   'total_sales': 0,
#   'total_paid': 0,
#   'members_joined': set()
# }

def add_promo_campaign(shop_name, owner_name, phone, place, category, title, description, poster_link, offer, target_views=10000, per_100_views_price=200, per_view_member_earning=10):
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
        'created_at': datetime.now(),
        'expiry': date.today() + timedelta(days=7),
        'total_views': 0,
        'total_sales': 0,
        'total_paid': 0,
        'total_earnings_distributed': 0,
        'members_joined': set(),
        'screenshots': []  # List of member submissions
    }
    promo_campaigns_db.append(campaign)
    promo_campaign_counter += 1
    return campaign

def get_active_promo_campaigns():
    today = date.today()
    return [c for c in promo_campaigns_db if c['status'] == 'active' and c['expiry'] >= today]

def get_promo_campaign(campaign_id):
    for c in promo_campaigns_db:
        if c['id'] == campaign_id:
            return c
    return None

def is_admin(uid): return uid in ADMIN_ID_LIST
def calculate_age(d): 
    today=date.today()
    return today.year-d.year-((today.month,today.day)<(d.month,d.day))
def get_balance(uid): return tasks_db.get(uid,0)*5 + bonus_balance.get(uid,0) + referral_earnings.get(uid,0) + promo_earnings_db.get(uid,0)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals", callback_data="my_ref"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📅 Daily Task", callback_data="daily"), InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🏪 Promo Tasks", callback_data="promo_tasks"), InlineKeyboardButton("📢 Promote My Shop", callback_data="promote_shop")],
        [InlineKeyboardButton("📋 Scheduled Tasks", callback_data="scheduled"), InlineKeyboardButton("💎 Support Plans", callback_data="support_plans")],
        [InlineKeyboardButton("📞 Contact Us", callback_data="contact_us")]
    ])

# === BASIC REGISTRATION (Simplified) ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in banned_users:
        await update.message.reply_text("BANNED! Contact admin!")
        return ConversationHandler.END
    args = context.args
    if args and args[0].isdigit():
        ref_id = int(args[0])
        if ref_id != uid and ref_id not in banned_users:
            referral_map[uid] = ref_id
    if uid in users_db:
        await update.message.reply_text(f"Welcome back {users_db[uid].get('name','User')}! Balance Rs{get_balance(uid)}", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text("Welcome to S2E Daily Earning + Promo Network! What is your Name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid] = {'name': update.message.text.strip()}
    await update.message.reply_text("Mobile Number? 10 digits:")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]['mobile'] = update.message.text.strip()
    await update.message.reply_text("UPI ID? Example: yourname@upi")
    return UPI

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users_db[uid]['upi'] = update.message.text.strip()
    users_db[uid]['joined'] = str(date.today())
    await update.message.reply_text(f"Registration Done! Welcome {users_db[uid]['name']}!\n\n💰 Earn: Rs10 per referral task + 10% plan commission\n🏪 Promo: Earn Rs10 per 100 status views!\n📢 Shop owners: Promote your shop via our members!", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled!", reply_markup=main_menu())
    return ConversationHandler.END

# === PROMO MARKETPLACE CALLBACKS ===
async def promo_tasks_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    
    active_campaigns = get_active_promo_campaigns()
    
    if not active_campaigns:
        await q.message.reply_text("🏪 No active promo campaigns now!\n\nShop owners can create promo: Click Promote My Shop button!\n\nAs member, you earn Rs10 per 100 status views + 10% per sale!\n\nCheck later!", reply_markup=main_menu())
        return
    
    msg = f"🏪 Promo Tasks - Earn via Shop Promotion!\n\n"
    msg += f"Total Active Campaigns: {len(active_campaigns)}\n"
    msg += f"Your Promo Earnings: Rs{promo_earnings_db.get(uid,0)}\n\n"
    
    for campaign in active_campaigns[:10]:
        members_count = len(campaign['members_joined'])
        views = campaign['total_views']
        msg += f"🏪 Campaign {campaign['id']}: {campaign['shop_name']}\n"
        msg += f"   {campaign['title']} - {campaign['offer']}\n"
        msg += f"   Place: {campaign['place']} Category: {campaign['category']}\n"
        msg += f"   Target: {campaign['target_views']} views | Done: {views} | Members: {members_count}\n"
        msg += f"   Earn: Rs{campaign['per_view_member_earning']} per 100 views + {campaign['per_sale_commission_percent']}% per sale\n"
        msg += f"   Expiry: {campaign['expiry']}\n\n"
    
    msg += "Click campaign to join and promote via your status!"
    
    # Create buttons for each campaign
    kb = []
    for campaign in active_campaigns[:10]:
        kb.append([InlineKeyboardButton(f"🏪 {campaign['shop_name']} - {campaign['title'][:20]} Rs{campaign['per_view_member_earning']}/100 views", callback_data=f"promo_join_{campaign['id']}")])
    kb.append([InlineKeyboardButton("💰 My Promo Earnings", callback_data="promo_my_earnings")])
    kb.append([InlineKeyboardButton("📋 Menu", callback_data="back_menu")])
    
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup(kb))

async def promo_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    try:
        campaign_id = int(q.data.split("_")[-1])
    except:
        await q.message.reply_text("Invalid campaign!", reply_markup=main_menu())
        return
    
    campaign = get_promo_campaign(campaign_id)
    if not campaign:
        await q.message.reply_text("Campaign not found!", reply_markup=main_menu())
        return
    
    if campaign['status'] != 'active':
        await q.message.reply_text("Campaign not active!", reply_markup=main_menu())
        return
    
    # Check if already joined
    if uid in campaign['members_joined']:
        msg = f"✅ You already joined Campaign {campaign['id']}!\n\n"
        msg += f"🏪 {campaign['shop_name']} - {campaign['title']}\n"
        msg += f"Poster: {campaign['poster_link']}\n"
        msg += f"Offer: {campaign['offer']}\n"
        msg += f"Description: {campaign['description']}\n\n"
        msg += f"📱 Steps:\n"
        msg += f"1. Save poster from link\n"
        msg += f"2. Put on your WhatsApp Status / Instagram Story\n"
        msg += f"3. Keep for 24 hours\n"
        msg += f"4. After 24h, take screenshot of views count\n"
        msg += f"5. Upload screenshot here - Earn Rs{campaign['per_view_member_earning']} per 100 views!\n\n"
        msg += f"💰 Earn: Rs{campaign['per_view_member_earning']} per 100 views\n"
        msg += f"💰 Sale: {campaign['per_sale_commission_percent']}% per sale if customer says your code {uid}\n"
        await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Upload Views Screenshot", callback_data=f"promo_upload_{campaign['id']}")],
            [InlineKeyboardButton("📋 Promo Tasks", callback_data="promo_tasks")]
        ]))
        return
    
    # Join campaign
    campaign['members_joined'].add(uid)
    if uid not in promo_views_db:
        promo_views_db[uid] = {}
    
    msg = f"🎉 Joined Campaign {campaign['id']}!\n\n"
    msg += f"🏪 Shop: {campaign['shop_name']} - {campaign['place']}\n"
    msg += f"Owner: {campaign['owner_name']} - {campaign['phone']}\n"
    msg += f"Title: {campaign['title']}\n"
    msg += f"Offer: {campaign['offer']}\n"
    msg += f"Description: {campaign['description']}\n"
    msg += f"Poster: {campaign['poster_link']}\n\n"
    msg += f"📱 How to Earn:\n"
    msg += f"1. Download poster from link above\n"
    msg += f"2. Put on WhatsApp Status (24 hours)\n"
    msg += f"3. Also put on Instagram Story if you have\n"
    msg += f"4. After 24h, screenshot your status views count\n"
    msg += f"   - WhatsApp: Open status -> eye icon -> views count visible\n"
    msg += f"   - Instagram: Story views count\n"
    msg += f"5. Upload screenshot - We verify views\n"
    msg += f"6. Earn Rs{campaign['per_view_member_earning']} per 100 views!\n"
    msg += f"   Example: 250 views = Rs25\n"
    msg += f"7. If your friend buys from shop using code {uid}, you get {campaign['per_sale_commission_percent']}% commission!\n\n"
    msg += f"💡 Tips for more views:\n"
    msg += f"- Put status at 7-9 PM when most people see\n"
    msg += f"- Write in Telugu: 'Kavali lo best offer! {campaign['shop_name']} lo {campaign['offer']}'\n"
    msg += f"- Keep status full 24 hours\n"
    msg += f"- Don't delete early!\n\n"
    msg += f"Target: {campaign['target_views']} views total from all members\n"
    msg += f"Current: {campaign['total_views']} views\n"
    
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload Views Screenshot", callback_data=f"promo_upload_{campaign['id']}")],
        [InlineKeyboardButton("📋 All Promo Tasks", callback_data="promo_tasks")]
    ]))

async def promo_upload_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    try:
        campaign_id = int(q.data.split("_")[-1])
    except:
        await q.message.reply_text("Invalid campaign!", reply_markup=main_menu())
        return
    
    campaign = get_promo_campaign(campaign_id)
    if not campaign:
        await q.message.reply_text("Campaign not found!", reply_markup=main_menu())
        return
    
    context.user_data['promo_upload_campaign_id'] = campaign_id
    
    await q.message.reply_text(f"📤 Upload Views Screenshot for Campaign {campaign_id}\n\n"
                               f"🏪 {campaign['shop_name']} - {campaign['title']}\n\n"
                               f"Requirements:\n"
                               f"1. Screenshot must show status with views count\n"
                               f"2. Views count must be visible (eye icon + number)\n"
                               f"3. Status content must be our poster\n"
                               f"4. Upload as PHOTO, not file!\n\n"
                               f"Example: WhatsApp status -> click eye -> shows 150 views\n"
                               f"Then screenshot that screen!\n\n"
                               f"Send photo now!", 
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="back_menu")]]))
    return UPLOAD_SCREENSHOT

async def promo_my_earnings_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    
    total_earnings = promo_earnings_db.get(uid,0)
    user_campaigns = [c for c in promo_campaigns_db if uid in c['members_joined']]
    
    msg = f"💰 My Promo Earnings\n\n"
    msg += f"Total Earned: Rs{total_earnings}\n"
    msg += f"Campaigns Joined: {len(user_campaigns)}\n\n"
    
    if not user_campaigns:
        msg += "You haven't joined any promo campaigns yet!\n"
        msg += "Click Promo Tasks to join and earn!"
    else:
        msg += "Your Campaigns:\n\n"
        for campaign in user_campaigns[:10]:
            # Find user's submissions for this campaign
            user_submissions = [s for s in campaign['screenshots'] if s['uid'] == uid]
            total_views = sum(s['views'] for s in user_submissions)
            total_earned = sum(s['earning'] for s in user_submissions)
            msg += f"🏪 Campaign {campaign['id']}: {campaign['shop_name']}\n"
            msg += f"   {campaign['title']} - Joined\n"
            msg += f"   Your Views: {total_views} | Earned: Rs{total_earned}\n"
            msg += f"   Submissions: {len(user_submissions)}\n\n"
    
    msg += f"\n💡 How earnings work:\n"
    msg += f"- Rs10 per 100 views (Rs0.1 per view)\n"
    msg += f"- 10% per sale via your code {uid}\n"
    msg += f"- Withdraw min Rs{WITHDRAW_MIN}\n"
    
    await q.message.reply_text(msg[:4000], reply_markup=main_menu())

async def promote_shop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    
    msg = f"📢 Promote Your Shop / Brand via S2E Network!\n\n"
    msg += f"🎯 What we do:\n"
    msg += f"- You have shop in Kavali, Palmaner, Tirupati, Nellore?\n"
    msg += f"- Want more customers but don't know how to promote?\n"
    msg += f"- We have {len(users_db)} members in local area!\n"
    msg += f"- Members put your poster on WhatsApp Status, Instagram Story\n"
    msg += f"- You get views from local people!\n\n"
    msg += f"💰 Pricing (Local Andhra Rates):\n"
    msg += f"Option 1: Per Views\n"
    msg += f"  - Rs200 per 1000 views (Rs20 per 100 views)\n"
    msg += f"  - We pay member Rs10 per 100 views, we keep Rs10 profit\n"
    msg += f"  - Example: 5000 views = Rs1000\n\n"
    msg += f"Option 2: Per Sale\n"
    msg += f"  - 10% commission per sale via member code\n"
    msg += f"  - If product Rs500, member gets Rs50, we keep Rs50\n"
    msg += f"  - You get sale, we track via code!\n\n"
    msg += f"Option 3: Combo\n"
    msg += f"  - Rs100 per 1000 views + 5% per sale\n"
    msg += f"  - Best for shops!\n\n"
    msg += f"📋 What we need from you:\n"
    msg += f"- Shop name, place, owner name, phone\n"
    msg += f"- What to promote? Offer, product, sale\n"
    msg += f"- Poster image link (or we design for Rs50 extra)\n"
    msg += f"- Target: How many views you want? 5000, 10000?\n"
    msg += f"- Budget: Rs500, Rs1000, Rs2000?\n\n"
    msg += f"🚀 How it works:\n"
    msg += f"1. You contact admin @s2edayincome\n"
    msg += f"2. We create campaign - Title, poster, offer\n"
    msg += f"3. Members join and put status\n"
    msg += f"4. Members upload views screenshot\n"
    msg += f"5. We verify and you get report\n"
    msg += f"6. You pay based on views/sales\n\n"
    msg += f"✅ Benefits:\n"
    msg += f"- Local promotion in Kavali, Nellore, Tirupati\n"
    msg += f"- Real people, not fake bots\n"
    msg += f"- WhatsApp status = trusted by friends\n"
    msg += f"- Cheaper than Facebook ads (FB Rs500 per 1000 views, we Rs200)\n"
    msg += f"- Support local business!\n\n"
    msg += f"📞 Contact to start: @s2edayincome\n"
    msg += f"Or click Create Promo Campaign (Admin only) / Admin can create via /add_promo"
    
    await q.message.reply_text(msg[:4000], reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Admin @s2edayincome", callback_data="contact_us")],
        [InlineKeyboardButton("📋 Menu", callback_data="back_menu")]
    ]))

async def handle_promo_screenshot_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    campaign_id = context.user_data.get('promo_upload_campaign_id')
    
    if not campaign_id:
        await update.message.reply_text("Campaign not found! Try again!", reply_markup=main_menu())
        return ConversationHandler.END
    
    if not update.message.photo:
        await update.message.reply_text("Please send as PHOTO!", reply_markup=main_menu())
        return UPLOAD_SCREENSHOT
    
    campaign = get_promo_campaign(campaign_id)
    if not campaign:
        await update.message.reply_text("Campaign not found!", reply_markup=main_menu())
        return ConversationHandler.END
    
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    # For demo, ask user to type views count as well (since auto OCR not implemented)
    # In real, admin verifies screenshot and enters views
    await update.message.reply_text(f"Screenshot received for Campaign {campaign_id}!\n\n"
                                   f"Now type how many views you got:\n"
                                   f"Example: 150\n"
                                   f"Check your WhatsApp status -> eye icon -> views number\n"
                                   f"Type views count now (numbers only):")
    
    # Save screenshot temporarily
    context.user_data['promo_screenshot_file_id'] = file_id
    context.user_data['promo_screenshot_campaign_id'] = campaign_id
    
    # We need to get views count from user
    # This will be handled in next message
    return PROMO_DETAILS

async def get_promo_views_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    try:
        views = int(update.message.text.strip())
    except:
        await update.message.reply_text("Invalid! Type numbers only! Example: 150")
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
    
    # Calculate earning: Rs10 per 100 views
    earning = int(views * campaign['per_view_member_earning'] / 100)
    
    # Save submission
    submission = {
        'uid': uid,
        'campaign_id': campaign_id,
        'views': views,
        'earning': earning,
        'file_id': file_id,
        'submitted_at': datetime.now(),
        'status': 'pending',
        'user_name': users_db.get(uid,{}).get('name','Unknown')
    }
    
    campaign['screenshots'].append(submission)
    campaign['total_views'] += views
    campaign['members_joined'].add(uid)
    
    # Add to pending for admin verification
    if uid not in pending_daily:
        pending_daily[uid] = {}
    # Use separate pending for promo
    if 'promo_pending' not in globals():
        global promo_pending
        promo_pending = {}
    promo_pending[uid] = submission
    
    await update.message.reply_text(f"✅ Submitted!\n\n"
                                   f"Campaign {campaign_id}: {campaign['shop_name']} - {campaign['title']}\n"
                                   f"Views: {views}\n"
                                   f"Earning: Rs{earning} (Rs{campaign['per_view_member_earning']} per 100 views)\n"
                                   f"Status: Pending admin verification\n\n"
                                   f"Admin will verify your screenshot and approve!\n"
                                   f"After approval, Rs{earning} added to wallet!\n\n"
                                   f"Keep status for 24 hours for more views! You can submit again after 24h!",
                                   reply_markup=main_menu())
    
    # Notify admin
    for admin_id in ADMIN_ID_LIST:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Approve Rs{earning} for {views} views", callback_data=f"promo_approve_{uid}_{campaign_id}_{views}"),
                 InlineKeyboardButton("Reject", callback_data=f"promo_reject_{uid}_{campaign_id}")]
            ])
            await context.bot.send_photo(
                chat_id=admin_id, 
                photo=file_id, 
                caption=f"🏪 NEW PROMO SUBMISSION!\nUser {users_db.get(uid,{}).get('name')} ID {uid}\nCampaign {campaign_id}: {campaign['shop_name']} - {campaign['title']}\nViews: {views} Earning: Rs{earning}\nShop: {campaign['place']} {campaign['phone']}",
                reply_markup=kb
            )
        except: pass
    
    context.user_data.pop('promo_upload_campaign_id', None)
    context.user_data.pop('promo_screenshot_file_id', None)
    context.user_data.pop('promo_screenshot_campaign_id', None)
    
    return ConversationHandler.END

# === ADMIN PROMO COMMANDS ===
async def add_promo_campaign_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    
    # Format: /add_promo shop_name|owner|phone|place|category|title|description|poster_link|offer|target_views|per_100_views_price
    # Example: /add_promo Kavali Fashions|Ramesh|9876543210|Kavali|Clothing|Diwali Sale 50% Off|All sarees 50% off|https://link|50% off|10000|200
    text = update.message.text.replace('/add_promo','').strip()
    if not text:
        await update.message.reply_text("Usage: /add_promo shop_name|owner|phone|place|category|title|description|poster_link|offer|target_views|price\n\n"
                                       "Example: /add_promo Kavali Fashions|Ramesh|9876543210|Kavali|Clothing|Diwali Sale|All sarees 50% off|https://poster.link|50% off|10000|200\n\n"
                                       "Shop owners contact @s2edayincome to promote!\n"
                                       "We have members in Kavali, Palmaner, Tirupati!")
        return
    
    parts = text.split('|')
    if len(parts) < 10:
        await update.message.reply_text("Need 10 fields separated by |\nshop|owner|phone|place|category|title|description|poster|offer|target_views|price_per_1000")
        return
    
    try:
        shop_name = parts[0].strip()
        owner_name = parts[1].strip()
        phone = parts[2].strip()
        place = parts[3].strip()
        category = parts[4].strip()
        title = parts[5].strip()
        description = parts[6].strip()
        poster_link = parts[7].strip()
        offer = parts[8].strip()
        target_views = int(parts[9].strip()) if len(parts) > 9 else 10000
        per_1000_price = int(parts[10].strip()) if len(parts) > 10 else 200
        per_100_price = per_1000_price // 10
        per_view_member_earning = 10  # Rs10 per 100 views to member
        
        campaign = add_promo_campaign(shop_name, owner_name, phone, place, category, title, description, poster_link, offer, target_views, per_100_price, per_view_member_earning)
        
        await update.message.reply_text(f"✅ Added Promo Campaign!\n\n"
                                       f"ID {campaign['id']}: {shop_name} - {title}\n"
                                       f"Place: {place} Category: {category}\n"
                                       f"Offer: {offer}\n"
                                       f"Target: {target_views} views\n"
                                       f"Shop pays: Rs{per_100_price} per 100 views (Rs{per_1000_price} per 1000)\n"
                                       f"Member earns: Rs{per_view_member_earning} per 100 views\n"
                                       f"Your profit: Rs{per_100_price - per_view_member_earning} per 100 views\n"
                                       f"Total profit if target met: Rs{(per_100_price - per_view_member_earning) * target_views // 100}\n\n"
                                       f"Members can now join via Promo Tasks!\n"
                                       f"Poster: {poster_link}\n\n"
                                       f"Share in group: New promo campaign {shop_name} {offer}!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}\n\nCheck format!")

async def list_promo_campaigns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not promo_campaigns_db:
        await update.message.reply_text("No promo campaigns! Add via /add_promo")
        return
    msg = f"🏪 Promo Campaigns - Total {len(promo_campaigns_db)}:\n\n"
    total_profit = 0
    total_views = 0
    for c in promo_campaigns_db[-20:]:
        profit_per_100 = c['per_100_views_price'] - c['per_view_member_earning']
        profit = profit_per_100 * c['total_views'] // 100
        total_profit += profit
        total_views += c['total_views']
        msg += f"ID {c['id']}: {c['shop_name']} {c['place']} - {c['title']}\n"
        msg += f"   {c['offer']} Target {c['target_views']} Views {c['total_views']} Members {len(c['members_joined'])} Profit Rs{profit} Status {c['status']}\n"
        msg += f"   Shop: {c['owner_name']} {c['phone']} Earnings Dist Rs{c['total_earnings_distributed']}\n\n"
    msg += f"\nTotal Views: {total_views} Total Profit: Rs{total_profit}"
    await update.message.reply_text(msg[:4000])

async def promo_pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if 'promo_pending' not in globals() or not promo_pending:
        await update.message.reply_text("No pending promo submissions!")
        return
    msg = f"Pending Promo Submissions {len(promo_pending)}:\n\n"
    for uid, data in list(promo_pending.items())[:20]:
        msg += f"{uid} {data['user_name']} Campaign {data['campaign_id']} Views {data['views']} Earn Rs{data['earning']} /promo_approve {uid} {data['campaign_id']}\n"
    await update.message.reply_text(msg[:4000])

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    active_promos = len(get_active_promo_campaigns())
    total_promo_earnings = sum(promo_earnings_db.values())
    total_views = sum(c['total_views'] for c in promo_campaigns_db)
    await update.message.reply_text(f"ADMIN Promo Marketplace + Simple Referral\n"
                                   f"Users {len(users_db)} Referrals {len(referrals_db)}\n"
                                   f"Promo Campaigns {len(promo_campaigns_db)} Active {active_promos}\n"
                                   f"Total Promo Views {total_views} Earnings Dist Rs{total_promo_earnings}\n"
                                   f"Pending Daily {len(pending_daily)} Promo Pending {len(promo_pending) if 'promo_pending' in globals() else 0}\n\n"
                                   f"Commands:\n"
                                   f"/add_promo shop|owner|phone|place|category|title|desc|poster|offer|target|price\n"
                                   f"/list_promos /promo_pending /promos\n"
                                   f"/pending /add_task /list_tasks")

async def my_ref_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid = q.from_user.id
    cnt=referrals_db.get(uid,0)
    earnings = referral_earnings.get(uid,0)
    ref_link = f"https://t.me/{context.bot.username}?start={uid}"
    await q.message.reply_text(f"My Referrals\nActive: {cnt}\nEarnings: Rs{earnings}\nBonus Rs10 per task + 10% plan commission\nYour Link: {ref_link}", reply_markup=main_menu())

async def wallet_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id
    bal=get_balance(uid)
    await q.message.reply_text(f"Wallet\nBalance Rs{bal}\nTasks {tasks_db.get(uid,0)}\nReferral Rs{referral_earnings.get(uid,0)}\nPromo Rs{promo_earnings_db.get(uid,0)}\nTotal Rs{bal}", reply_markup=main_menu())

async def back_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("Menu:", reply_markup=main_menu())

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).build()
    
    conv_reg = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            MOBILE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_mobile)],
            UPI:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True, per_chat=True, per_message=False
    )
    
    conv_promo = ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_upload_cb, pattern="^promo_upload_")],
        states={
            UPLOAD_SCREENSHOT:[MessageHandler(filters.PHOTO, handle_promo_screenshot_upload)],
            PROMO_DETAILS:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_promo_views_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True, per_chat=True, per_message=False
    )
    
    app.add_handler(CommandHandler("menu", menu)) if 'menu' in globals() else None
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("add_promo", add_promo_campaign_cmd))
    app.add_handler(CommandHandler("list_promos", list_promo_campaigns_cmd))
    app.add_handler(CommandHandler("promo_pending", promo_pending_cmd))
    app.add_handler(CallbackQueryHandler(promo_tasks_cb, pattern="^promo_tasks$"))
    app.add_handler(CallbackQueryHandler(promo_join_cb, pattern="^promo_join_"))
    app.add_handler(CallbackQueryHandler(promo_my_earnings_cb, pattern="^promo_my_earnings$"))
    app.add_handler(CallbackQueryHandler(promote_shop_cb, pattern="^promote_shop$"))
    app.add_handler(CallbackQueryHandler(my_ref_cb, pattern="^my_ref$"))
    app.add_handler(CallbackQueryHandler(wallet_cb, pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(back_menu_cb, pattern="^back_menu$"))
    app.add_handler(conv_reg)
    app.add_handler(conv_promo)
    print(f"Bot Started! Promo Marketplace - Local Shops Promotion Network!")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
