
import os, json, logging, threading, time
from datetime import datetime
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN","").strip()
SCREENSHOT_CHANNEL = int(os.environ.get("SCREENSHOT_CHANNEL","-1004428587527"))
WITHDRAW_CHANNEL = int(os.environ.get("WITHDRAW_CHANNEL","-1004319888475"))
JOIN_CHANNEL = int(os.environ.get("JOIN_CHANNEL","-1004352241439"))
BACKUP_CHANNEL = int(os.environ.get("BACKUP_CHANNEL","0")) # Private channel for backup, optional
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS","7256515560").split(",") if x.strip().isdigit()]

CONFIG_FILE="bot_config.json"
USERS_FILE="users_progress.json"
REFERRAL_FILE="referrals.json"

DAILY_TASKS=[{"id":i,"title":f"Task {i}"} for i in range(1,11)]

def load_json(file, default):
  try:
    if os.path.exists(file):
      with open(file) as f: return json.load(f)
  except: pass
  return default

def save_json(file, data):
  try:
    with open(file,"w") as f: json.dump(f,f if False else data)
    with open(file,"w") as f: json.dump(data,f)
  except Exception as e:
    print(f"Save error {e}")

config=load_json(CONFIG_FILE, {"missed_enabled":False,"plan_image_file_id":None,"admins":ADMIN_IDS})
users_data=load_json(USERS_FILE, {})
referrals=load_json(REFERRAL_FILE, {}) # {user_id: {referred_by, level1:[], level2:[], earnings:{l1_plan:0,l1_daily:0,l2:0}}}

def today_str():
  return datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d")

def get_completed(uid): return users_data.get(str(uid),{}).get(today_str(),[])
def set_completed(uid,tid):
  s=str(uid); t=today_str()
  if s not in users_data: users_data[s]={}
  if t not in users_data[s]: users_data[s][t]=[]
  if tid not in users_data[s][t]: users_data[s][t].append(tid)
  save_json(USERS_FILE, users_data)

def get_missed(uid):
  comp=get_completed(uid)
  return [t["id"] for t in DAILY_TASKS if t["id"] not in comp]

def is_missed_active(): return config.get("missed_enabled",False)

def is_admin(uid):
  admins=config.get("admins",ADMIN_IDS)
  return uid in admins or uid in ADMIN_IDS

def add_referral(new_user_id, referrer_id):
  if new_user_id==referrer_id: return
  new_s=str(new_user_id); ref_s=str(referrer_id)
  if new_s in referrals: return # already has referrer
  # Level 1
  referrals[new_s]={"referred_by":ref_s, "level1":[], "level2":[], "joined":today_str()}
  if ref_s not in referrals:
    referrals[ref_s]={"referred_by":None,"level1":[],"level2":[],"joined":today_str(),"earnings":{"l1_plan":0,"l1_daily":0,"l2":0}}
  if "earnings" not in referrals[ref_s]:
    referrals[ref_s]["earnings"]={"l1_plan":0,"l1_daily":0,"l2":0}
  if new_s not in referrals[ref_s]["level1"]:
    referrals[ref_s]["level1"].append(new_s)
  # Level 2 - referrer's referrer gets level2
  level1_referrer = referrals[ref_s].get("referred_by")
  if level1_referrer:
    l2_s=str(level1_referrer)
    if l2_s not in referrals:
      referrals[l2_s]={"referred_by":None,"level1":[],"level2":[],"joined":today_str(),"earnings":{"l1_plan":0,"l1_daily":0,"l2":0}}
    if "earnings" not in referrals[l2_s]:
      referrals[l2_s]["earnings"]={"l1_plan":0,"l1_daily":0,"l2":0}
    if new_s not in referrals[l2_s]["level2"]:
      referrals[l2_s]["level2"].append(new_s)
  save_json(REFERRAL_FILE, referrals)

def add_commission(user_id, type_, amount):
  # type_: plan_purchase, daily_work
  s=str(user_id)
  if s not in referrals: return
  ref_by=referrals[s].get("referred_by")
  if not ref_by: return
  ref_s=str(ref_by)
  if ref_s not in referrals: return
  if "earnings" not in referrals[ref_s]:
    referrals[ref_s]["earnings"]={"l1_plan":0,"l1_daily":0,"l2":0}
  if type_=="plan_purchase":
    # 10% to level1
    comm=amount*0.10
    referrals[ref_s]["earnings"]["l1_plan"]+=comm
    # 0.2% to level2 if exists
    l2=referrals[ref_s].get("referred_by")
    if l2:
      l2_s=str(l2)
      if l2_s in referrals:
        if "earnings" not in referrals[l2_s]:
          referrals[l2_s]["earnings"]={"l1_plan":0,"l1_daily":0,"l2":0}
        referrals[l2_s]["earnings"]["l2"]+=amount*0.002
  elif type_=="daily_work":
    # 2% to level1
    comm=amount*0.02
    referrals[ref_s]["earnings"]["l1_daily"]+=comm
    l2=referrals[ref_s].get("referred_by")
    if l2:
      l2_s=str(l2)
      if l2_s in referrals:
        if "earnings" not in referrals[l2_s]:
          referrals[l2_s]["earnings"]={"l1_plan":0,"l1_daily":0,"l2":0}
        referrals[l2_s]["earnings"]["l2"]+=amount*0.002
  save_json(REFERRAL_FILE, referrals)

logging.basicConfig(level=logging.INFO)
app_flask=Flask(__name__)
@app_flask.route('/')
def home(): return f"S2E V34 Backup+Referral Live Admins:{config.get('admins')}"

def run_flask():
  port=int(os.environ.get("PORT",10000))
  app_flask.run(host="0.0.0.0",port=port)

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
  uid=update.effective_user.id
  # Referral handling
  if context.args and len(context.args)>0:
    ref_code=context.args[0]
    if ref_code.startswith("ref_"):
      try:
        referrer_id=int(ref_code.replace("ref_",""))
        if referrer_id!=uid:
          add_referral(uid, referrer_id)
          try:
            await context.bot.send_message(referrer_id, f"🎉 New Referral! User {uid} joined via your link!\nLevel 1 count: {len(referrals.get(str(referrer_id),{}).get('level1',[]))}")
          except: pass
      except: pass

  if is_admin(uid):
    kb=[
      [InlineKeyboardButton("📋 Tasks",callback_data="user_tasks"), InlineKeyboardButton("⚠️ Missed ON/OFF",callback_data="toggle_missed")],
      [InlineKeyboardButton("💎 Plans",callback_data="supporting_plans"), InlineKeyboardButton("🖼️ Upload Plan Img",callback_data="upload_plan_image")],
      [InlineKeyboardButton("📡 Channels",callback_data="channels"), InlineKeyboardButton("📊 Missed Status",callback_data="missed_status")],
      [InlineKeyboardButton("💾 Backup",callback_data="backup"), InlineKeyboardButton("👥 Referral Stats",callback_data="referral_stats")],
      [InlineKeyboardButton("➕ Add Admin",callback_data="add_admin"), InlineKeyboardButton("📋 All Admins",callback_data="list_admins")]
    ]
    text=f"S2E Admin V34\nMissed: {'ON' if is_missed_active() else 'OFF'}\nPlan Img: {'Set' if config.get('plan_image_file_id') else 'Not Set'}\nTotal Users: {len(users_data)}\nTotal Referrals: {len(referrals)}\nAdmins: {config.get('admins')}\n\nBackup: /backup, /restore\nAdd Admin: /add_admin USER_ID\nReferral: /referral_stats"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
  else:
    # Normal user menu
    ref_link=f"https://t.me/{context.bot.username}?start=ref_{uid}"
    kb=[
      [InlineKeyboardButton("📋 Tasks",callback_data="user_tasks")],
      [InlineKeyboardButton("💎 Supporting Plans",callback_data="supporting_plans")],
      [InlineKeyboardButton("👥 My Referrals",callback_data="my_referrals"), InlineKeyboardButton("🔗 My Invite Link",callback_data="my_link")],
      [InlineKeyboardButton("⚠️ My Missed",callback_data="my_missed")]
    ]
    await update.message.reply_text(f"Welcome! 🚀\nYour Invite: {ref_link}\n\nShare & Earn: L1 10% Plan + 2% Daily, L2 0.2%", reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
  query=update.callback_query
  await query.answer()
  data=query.data
  uid=query.from_user.id
  if data=="user_tasks":
    # simple tasks view
    comp=get_completed(uid); missed=get_missed(uid)
    text=f"Today {today_str()} Done {len(comp)}/10\nMissed: {missed} Active:{is_missed_active()}"
    btns=[[InlineKeyboardButton(f"{'✅' if i in comp else '❌'} Task {i}",callback_data=f"task_{i}")] for i in range(1,11)]
    btns.append([InlineKeyboardButton("Back",callback_data="main_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))
    return
  if data.startswith("task_"):
    tid=int(data.split("_")[1])
    if tid not in get_completed(uid):
      set_completed(uid,tid)
      add_commission(uid,"daily_work",10) # example daily earning 10rs
    await query.answer("Done!")
    return
  if data=="main_menu":
    await start(update,context)
    return
  if data=="supporting_plans":
    img=config.get("plan_image_file_id")
    cap="💎 Plans: Basic 199 (HD), Standard 399 (FHD), Premium 499 (4K + Extra)\nL1: 10% Plan + 2% Daily, L2: 0.2%"
    btns=[[InlineKeyboardButton(f"Buy {p}",callback_data=f"buy_{p}")] for p in ["Basic_199","Standard_399","Premium_499"]]
    btns.append([InlineKeyboardButton("Back",callback_data="main_menu")])
    if img:
      try:
        await query.message.reply_photo(photo=img,caption=cap,reply_markup=InlineKeyboardMarkup(btns))
        return
      except: pass
    await query.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(btns))
    return
  if data.startswith("buy_"):
    plan=data.replace("buy_","")
    price=int(plan.split("_")[-1])
    add_commission(uid,"plan_purchase",price)
    await query.edit_message_text(f"✅ Selected {plan}. Admin will contact.\nYour referrer gets commission!")
    return
  if data=="my_referrals":
    r=referrals.get(str(uid),{})
    l1=len(r.get("level1",[])); l2=len(r.get("level2",[]))
    earn=r.get("earnings",{"l1_plan":0,"l1_daily":0,"l2":0})
    text=f"👥 Your Referrals\nL1 (Direct): {l1} users - 10% plan + 2% daily\nL2 (Indirect): {l2} users - 0.2%\n\nEarnings:\nL1 Plan: ₹{earn.get('l1_plan',0):.2f}\nL1 Daily: ₹{earn.get('l1_daily',0):.2f}\nL2: ₹{earn.get('l2',0):.2f}"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back",callback_data="main_menu")]]))
    return
  if data=="my_link":
    link=f"https://t.me/{context.bot.username}?start=ref_{uid}"
    await query.edit_message_text(f"🔗 Your Invite Link:\n{link}\n\nShare in WhatsApp/Telegram. L1 10% + 2%, L2 0.2%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back",callback_data="main_menu")]]))
    return
  if data=="my_missed":
    m=get_missed(uid)
    await query.edit_message_text(f"Missed: {m} Active:{is_missed_active()}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back",callback_data="main_menu")]]))
    return
  if not is_admin(uid): return
  # Admin only
  if data=="toggle_missed":
    config["missed_enabled"]=not config.get("missed_enabled",False)
    save_json(CONFIG_FILE,config)
    await query.edit_message_text(f"Missed {'ON' if config['missed_enabled'] else 'OFF'}")
    return
  if data=="upload_plan_image":
    await query.edit_message_text("Send photo with caption /set_plan_image")
    return
  if data=="channels":
    await query.edit_message_text(f"Channels S:{SCREENSHOT_CHANNEL} W:{WITHDRAW_CHANNEL} J:{JOIN_CHANNEL}")
    return
  if data=="missed_status":
    msg=f"Missed {today_str()} Active:{is_missed_active()}\n"
    for u,d in users_data.items():
      miss=[t for t in range(1,11) if t not in d.get(today_str(),[])]
      if miss: msg+=f"{u}:{miss}\n"
    await query.edit_message_text(msg[:4000])
    return
  if data=="backup":
    # send backup files
    try:
      await query.message.reply_document(document=open(USERS_FILE,'rb') if os.path.exists(USERS_FILE) else json.dumps(users_data).encode(), filename="users_progress.json", caption="Backup Users")
      await query.message.reply_document(document=open(REFERRAL_FILE,'rb') if os.path.exists(REFERRAL_FILE) else json.dumps(referrals).encode(), filename="referrals.json", caption="Backup Referrals")
      await query.message.reply_document(document=open(CONFIG_FILE,'rb'), filename="bot_config.json", caption="Backup Config")
      await query.edit_message_text("✅ Backup sent as files. Save in Google Drive!")
    except Exception as e:
      await query.edit_message_text(f"Backup error {e}")
    return
  if data=="referral_stats":
    total_l1=sum(len(v.get("level1",[])) for v in referrals.values())
    total_l2=sum(len(v.get("level2",[])) for v in referrals.values())
    text=f"📊 Referral Stats Total Users:{len(referrals)} L1:{total_l1} L2:{total_l2}\n\nTop Referrers:\n"
    sorted_ref=sorted(referrals.items(), key=lambda x: len(x[1].get("level1",[])), reverse=True)[:10]
    for uid_s, val in sorted_ref:
      text+=f"{uid_s}: L1 {len(val.get('level1',[]))} L2 {len(val.get('level2',[]))}\n"
    await query.edit_message_text(text[:4000])
    return
  if data=="add_admin":
    await query.edit_message_text("Use /add_admin USER_ID - Example: /add_admin 123456789")
    return
  if data=="list_admins":
    await query.edit_message_text(f"Admins: {config.get('admins', ADMIN_IDS)}")
    return

async def photo_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  cap=update.message.caption or ""
  if "/set_plan_image" in cap or "plan" in cap.lower():
    file_id=update.message.photo[-1].file_id
    config["plan_image_file_id"]=file_id
    save_json(CONFIG_FILE,config)
    await update.message.reply_text("✅ Plan image saved!")
    await update.message.reply_photo(photo=file_id, caption="Users will see this")

async def backup_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  try:
    await update.message.reply_document(document=open(USERS_FILE,'rb') if os.path.exists(USERS_FILE) else json.dumps(users_data).encode(), filename="users_progress.json")
    await update.message.reply_document(document=open(REFERRAL_FILE,'rb') if os.path.exists(REFERRAL_FILE) else json.dumps(referrals).encode(), filename="referrals.json")
    await update.message.reply_document(document=open(CONFIG_FILE,'rb'), filename="bot_config.json")
    await update.message.reply_text("✅ Backup files - Save to Drive. If bot deleted, upload these to new bot deployment.")
  except Exception as e:
    await update.message.reply_text(f"Backup error {e}")

async def add_admin_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  if not context.args:
    await update.message.reply_text("Usage: /add_admin USER_ID")
    return
  try:
    new_id=int(context.args[0])
    admins=config.get("admins",ADMIN_IDS.copy())
    if new_id not in admins:
      admins.append(new_id)
      config["admins"]=admins
      save_json(CONFIG_FILE,config)
      await update.message.reply_text(f"✅ Admin added: {new_id}. Now if one admin blocked, other can control. Total admins: {admins}")
    else:
      await update.message.reply_text("Already admin")
  except Exception as e:
    await update.message.reply_text(f"Error {e}")

async def set_plan_image_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  await update.message.reply_text("Send photo with caption /set_plan_image")

async def channels_status(update:Update, context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  await update.message.reply_text(f"V34 Backup+Referral\nS:{SCREENSHOT_CHANNEL} W:{WITHDRAW_CHANNEL} J:{JOIN_CHANNEL}\nAdmins:{config.get('admins')}\nUsers:{len(users_data)} Ref:{len(referrals)}")

async def referral_stats_cmd(update:Update, context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  await update.message.reply_text(f"Total referral users {len(referrals)}")

def main():
    if not BOT_TOKEN:
        print("TOKEN missing")
        return
    print("Waiting 15 sec for old instance to shutdown...")
    time.sleep(15)
    threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("add_admin", add_admin_cmd))
    app.add_handler(CommandHandler("set_plan_image", set_plan_image_cmd))
    app.add_handler(CommandHandler("channels_status", channels_status))
    app.add_handler(CommandHandler("referral_stats", referral_stats_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("V34 Starting")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
