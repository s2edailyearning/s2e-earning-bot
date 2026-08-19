
import os, json, re, asyncio
from datetime import datetime, date
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@S2E_Daily_Earning")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7256515560"))
IST = pytz.timezone("Asia/Kolkata")

NAME, DOB, GENDER, PROFESSION, PINCODE, UPI_ID, UPI_NAME, ACCOUNT = range(8)
TASKS_FILE, USERS_FILE, CONFIG_FILE = "tasks.json", "users.json", "config.json"
PENDING_STATUS_FILE, COMPLETIONS_FILE = "pending_status.json", "completions.json"

def load_json(f, d):
    try:
        if os.path.exists(f):
            return json.load(open(f, encoding="utf-8"))
    except: pass
    return d
def save_json(f, d):
    json.dump(d, open(f, "w", encoding="utf-8"), indent=2)

def calc_age(s):
    try:
        d,m,y = map(int, s.split("-"))
        dob = date(y,m,d)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_json(USERS_FILE, {})
    uid = str(update.effective_user.id)
    if context.args:
        context.user_data["referred_by"] = str(context.args[0])
    if uid in users and users[uid].get("verified_18"):
        kb = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/S2E_Daily_Earning")],
              [InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")],
              [InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("👥 Referrals", callback_data="my_ref")],
              [InlineKeyboardButton("🎯 Today's Tasks", callback_data="today_tasks"), InlineKeyboardButton("📱 Status Task", callback_data="status_info")]]
        await update.message.reply_text(f"Welcome back {users[uid]['name']}!\nID: {uid}\nReferral: https://t.me/{context.bot.username}?start={uid}\nBalance: Rs.{users[uid].get('balance',0)}", reply_markup=InlineKeyboardMarkup(kb))
        return ConversationHandler.END
    await update.message.reply_text("🚀 Welcome to S2E Daily Earning!\nCompany policy: Only 18+ allowed. Complete KYC.\n\n1️⃣ Full Name? (As per Aadhaar)")
    return NAME

async def get_name(update, context):
    context.user_data["name"]=update.message.text.strip()
    await update.message.reply_text(f"Hi {context.user_data['name']}!\n2️⃣ DOB? DD-MM-YYYY\nEx: 15-08-2000")
    return DOB

async def get_dob(update, context):
    dob=update.message.text.strip()
    age=calc_age(dob)
    if age is None:
        await update.message.reply_text("❌ Invalid! Use DD-MM-YYYY")
        return DOB
    if age<18:
        await update.message.reply_text(f"❌ Age {age}. Only 18+ allowed!")
        return ConversationHandler.END
    context.user_data["dob"]=dob; context.user_data["age"]=age
    await update.message.reply_text(f"✅ Age {age} Verified!\n3️⃣ Gender? Male/Female/Other")
    return GENDER

async def get_gender(update, context):
    context.user_data["gender"]=update.message.text.strip()
    await update.message.reply_text("4️⃣ Profession? Student/Employee/Self/Other")
    return PROFESSION

async def get_profession(update, context):
    context.user_data["profession"]=update.message.text.strip()
    await update.message.reply_text("5️⃣ Pincode? 6 digits\nEx: 517408")
    return PINCODE

async def get_pincode(update, context):
    pin=update.message.text.strip()
    if not re.match("^[0-9]{6}$", pin):
        await update.message.reply_text("❌ 6 digits! Ex: 517408")
        return PINCODE
    context.user_data["pincode"]=pin
    await update.message.reply_text("6️⃣ UPI ID? Ex: name@okaxis")
    return UPI_ID

async def get_upi_id(update, context):
    upi=update.message.text.strip()
    if "@" not in upi:
        await update.message.reply_text("❌ Invalid UPI! Ex: name@okaxis")
        return UPI_ID
    context.user_data["upi_id"]=upi
    await update.message.reply_text("7️⃣ UPI Display Name?")
    return UPI_NAME

async def get_upi_name(update, context):
    context.user_data["upi_name"]=update.message.text.strip()
    await update.message.reply_text("8️⃣ Bank Details (Optional): Acc, IFSC, Bank\nEx: 1234567890, SBIN0001234, SBI\nType Skip to skip")
    return ACCOUNT

async def get_account(update, context):
    context.user_data["account"]=update.message.text.strip()
    uid=str(update.effective_user.id)
    users=load_json(USERS_FILE, {})
    users[uid]={"id": update.effective_user.id, "name": context.user_data["name"], "dob": context.user_data["dob"], "age": context.user_data["age"], "gender": context.user_data["gender"], "profession": context.user_data["profession"], "pincode": context.user_data["pincode"], "upi_id": context.user_data["upi_id"], "upi_name": context.user_data["upi_name"], "account": context.user_data["account"], "verified_18": True, "balance":0, "referral_balance":0, "tasks_completed":0, "referrals":0, "premium_type":"free", "referred_by": context.user_data.get("referred_by"), "registered_at": datetime.now(IST).isoformat()}
    ref=context.user_data.get("referred_by")
    if ref and ref in users and ref!=uid:
        users[ref]["referrals"]=users[ref].get("referrals",0)+1
    save_json(USERS_FILE, users)
    await update.message.reply_text(f"✅ Registration Done {context.user_data['name']}! Age {context.user_data['age']} Verified\nLink: https://t.me/{context.bot.username}?start={uid}\nJoin channel!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url="https://t.me/S2E_Daily_Earning")]]))
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("Cancelled. /start to restart")
    return ConversationHandler.END

async def button_handler(update, context):
    q=update.callback_query; await q.answer()
    config=load_json(CONFIG_FILE, {})
    uid=str(q.from_user.id)
    users=load_json(USERS_FILE, {})
    if q.data=="today_tasks":
        tasks=load_json(TASKS_FILE, [])
        txt="📅 Today's 20 Tasks (10 AM - 7:30 PM):\n\n"
        for t in tasks[:20]:
            txt+=f"{t['id']}. {t['start_time']} - {t['title']} Rs.{t['reward']}\n"
        await q.message.reply_text(txt)
    elif q.data=="status_info":
        await q.message.reply_text(f"📱 STATUS TASK\n10 AM: Video in channel\nKeep till 8 PM\nUpload 8-10 PM\nReward 500=Rs.{config.get('rewards',{}).get('status_promo_500_plan',30)} 1000=Rs.{config.get('rewards',{}).get('status_promo_1000_plan',40)}")
    elif q.data=="wallet":
        if uid in users:
            await q.message.reply_text(f"💰 Wallet\nMain: Rs.{users[uid].get('balance',0)}\nReferral: Rs.{users[uid].get('referral_balance',0)}\nTasks: {users[uid].get('tasks_completed',0)}\nMin: {config.get('withdraw',{}).get('min_tasks',15)} tasks + Rs.{config.get('withdraw',{}).get('min_amount',200)}")
    elif q.data=="my_ref":
        if uid in users:
            await q.message.reply_text(f"👥 Referrals: {users[uid].get('referrals',0)}\nEarning: Rs.{users[uid].get('referral_balance',0)}\nLink: https://t.me/{context.bot.username}?start={uid}\nBonus Rs.20 after 10 tasks + Rs.1 per task (100 max)")

async def handle_photo(update, context):
    uid=str(update.effective_user.id)
    users=load_json(USERS_FILE, {})
    now=datetime.now(IST)
    if uid not in users or not users[uid].get("verified_18"):
        await update.message.reply_text("❌ /start registration first")
        return
    if 20 <= now.hour < 22:
        pending=load_json(PENDING_STATUS_FILE, {})
        task_id=f"status_{now.strftime('%Y-%m-%d')}"
        if task_id not in pending: pending[task_id]={}
        photo_id=update.message.photo[-1].file_id
        pending[task_id][uid]={"user_id": uid, "name": users[uid].get("name"), "plan": users[uid].get("premium_type","free"), "photo": photo_id, "time": now.isoformat(), "status": "pending"}
        save_json(PENDING_STATUS_FILE, pending)
        await update.message.reply_text("✅ Status screenshot received! Admin will verify.")
        try:
            kb=[[InlineKeyboardButton("✅ Approve", callback_data=f"st_approve_{task_id}_{uid}"), InlineKeyboardButton("❌ Fake", callback_data=f"st_fake_{task_id}_{uid}")]]
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=f"Status Pending\nUser: {users[uid].get('name')} ({uid}) Plan: {users[uid].get('premium_type','free')}", reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return
    await update.message.reply_text("✅ Screenshot received for regular task! Admin will verify.")

async def status_pending_cmd(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    pending=load_json(PENDING_STATUS_FILE, {})
    msg="📊 Pending Status:\n"
    for tid, d in pending.items():
        pc=len([u for u in d.values() if u["status"]=="pending"])
        fc=len([u for u in d.values() if u["status"]=="fake"])
        msg+=f"{tid}: Pending {pc} | Fake {fc}\n"
    msg+="\n/approve_status_500 YYYY-MM-DD\n/approve_status_1000 YYYY-MM-DD"
    await update.message.reply_text(msg)

async def approve_all_status(update, context):
    if update.effective_user.id!=ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /approve_status_500 YYYY-MM-DD")
        return
    plan="500" if "500" in update.message.text else "1000"
    task_id=f"status_{context.args[0]}"
    pending=load_json(PENDING_STATUS_FILE, {})
    users=load_json(USERS_FILE, {})
    config=load_json(CONFIG_FILE, {})
    reward=config.get("rewards",{}).get(f"status_promo_{plan}_plan", 30 if plan=="500" else 40)
    count=0
    for uid, data in list(pending.get(task_id,{}).items()):
        if data["status"]!="pending" or data["plan"]!=plan: continue
        if uid in users:
            users[uid]["balance"]=users[uid].get("balance",0)+reward
            users[uid]["tasks_completed"]=users[uid].get("tasks_completed",0)+1
        pending[task_id][uid]["status"]="approved"
        count+=1
        try: await context.bot.send_message(chat_id=int(uid), text=f"✅ Status Approved! +Rs.{reward} (Plan {plan})")
        except: pass
    save_json(PENDING_STATUS_FILE, pending); save_json(USERS_FILE, users)
    await update.message.reply_text(f"✅ Approved {count} users for {plan} with Rs.{reward} each! Fake skipped.")

async def main():
    app=Application.builder().token(BOT_TOKEN).build()
    conv=ConversationHandler(entry_points=[CommandHandler("start", start)], states={NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)], DOB:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)], GENDER:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)], PROFESSION:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_profession)], PINCODE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_pincode)], UPI_ID:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi_id)], UPI_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi_name)], ACCOUNT:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_account)]}, fallbacks=[CommandHandler("cancel", cancel)])
    app.add_handler(conv)
    app.add_handler(CommandHandler("status_pending", status_pending_cmd))
    app.add_handler(CommandHandler("approve_status_500", approve_all_status))
    app.add_handler(CommandHandler("approve_status_1000", approve_all_status))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("English Bot Started!")
    await app.run_polling()

if __name__=="__main__":
    import nest_asyncio; nest_asyncio.apply()
    asyncio.run(main())
  
