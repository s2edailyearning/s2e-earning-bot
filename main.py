
import os, json, logging, threading
from datetime import datetime
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN","").strip()
SCREENSHOT_CHANNEL = int(os.environ.get("SCREENSHOT_CHANNEL","-1004428587527"))
WITHDRAW_CHANNEL = int(os.environ.get("WITHDRAW_CHANNEL","-1004319888475"))
JOIN_CHANNEL = int(os.environ.get("JOIN_CHANNEL","-1004352241439"))
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS","7256515560").split(",") if x.strip().isdigit()]

CONFIG_FILE="bot_config.json"
USERS_FILE="users_progress.json"

DAILY_TASKS=[{"id":i,"title":f"Task {i}"} for i in range(1,11)]

PLANS=[
  {"id":1,"name":"Basic Plan","price":199,"desc":"HD Quality, 1 Device, Basic Support"},
  {"id":2,"name":"Standard Plan","price":399,"desc":"Full HD, 2 Devices, Priority Support"},
  {"id":3,"name":"Premium Plan","price":499,"desc":"4K Ultra, 4 Devices, 24/7 Support + Extra Earnings"}
]

def load_config():
  try:
    if os.path.exists(CONFIG_FILE):
      with open(CONFIG_FILE) as f: return json.load(f)
  except: pass
  return {"missed_enabled":False,"plan_image_file_id":None,"plan_image_url":None}

def save_config(c):
  try:
    with open(CONFIG_FILE,"w") as f: json.dump(c,f)
  except: pass

config=load_config()

def load_users():
  try:
    if os.path.exists(USERS_FILE):
      with open(USERS_FILE) as f: return json.load(f)
  except: pass
  return {}

def save_users(d):
  try:
    with open(USERS_FILE,"w") as f: json.dump(d,f)
  except: pass

users_data=load_users()

def today_str():
  ist=pytz.timezone("Asia/Kolkata")
  return datetime.now(ist).strftime("%Y-%m-%d")

def get_completed(uid):
  return users_data.get(str(uid),{}).get(today_str(),[])

def set_completed(uid,tid):
  s=str(uid); t=today_str()
  if s not in users_data: users_data[s]={}
  if t not in users_data[s]: users_data[s][t]=[]
  if tid not in users_data[s][t]: users_data[s][t].append(tid)
  save_users(users_data)

def get_missed(uid):
  comp=get_completed(uid)
  return [t["id"] for t in DAILY_TASKS if t["id"] not in comp]

def is_missed_active():
  return config.get("missed_enabled",False)

logging.basicConfig(level=logging.INFO)
app_flask=Flask(__name__)
@app_flask.route('/')
def home(): return "S2E V33 Live"

def run_flask():
  port=int(os.environ.get("PORT",10000))
  app_flask.run(host="0.0.0.0",port=port)

def is_admin(uid): return uid in ADMIN_IDS

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
  uid=update.effective_user.id
  if is_admin(uid):
    kb=[
      [InlineKeyboardButton("📋 Tasks",callback_data="user_tasks"), InlineKeyboardButton("⚠️ Missed ON/OFF",callback_data="toggle_missed")],
      [InlineKeyboardButton("💎 Supporting Plans",callback_data="supporting_plans"), InlineKeyboardButton("🖼️ Upload Plan Image",callback_data="upload_plan_image")],
      [InlineKeyboardButton("📡 Channels",callback_data="channels"), InlineKeyboardButton("📊 Missed Status",callback_data="missed_status")]
    ]
    await update.message.reply_text(
      f"S2E Admin V33\nMissed Manual: {'✅ ON' if is_missed_active() else '❌ OFF'}\nPlan Image: {'✅ Set' if config.get('plan_image_file_id') else '❌ Not Set'}\n\nCommands:\n/enable_missed /disable_missed\n/tasks /missed\n/supporting_plans",
      reply_markup=InlineKeyboardMarkup(kb))
  else:
    await show_main_menu(update,context,True)

async def show_main_menu(update,context,is_start=False):
  kb=[
    [InlineKeyboardButton("📋 Today's Tasks",callback_data="user_tasks")],
    [InlineKeyboardButton("💎 Supporting Plans",callback_data="supporting_plans")],
    [InlineKeyboardButton("⚠️ My Missed Tasks",callback_data="my_missed")]
  ]
  text="Welcome to S2E Daily Earning Bot! 🚀"
  if is_start or update.message:
    await update.message.reply_text(text,reply_markup=InlineKeyboardMarkup(kb))
  else:
    await update.callback_query.edit_message_text(text,reply_markup=InlineKeyboardMarkup(kb))

async def show_tasks(update,context,is_start=False):
  uid=update.effective_user.id if update.effective_user else update.callback_query.from_user.id
  completed=get_completed(uid)
  missed=get_missed(uid)
  active=is_missed_active()
  text=f"Today: {today_str()}\nDone: {len(completed)}/{len(DAILY_TASKS)}\n"
  if missed and active:
    text+=f"\n⚠️ YOU MISSED {len(missed)} TASKS! 🔔\nMissed: {missed}\nComplete before 11:59 PM!\n"
  buttons=[]
  for task in DAILY_TASKS:
    tid=task["id"]
    done="✅" if tid in completed else "❌"
    hl="🔥 " if (tid in missed and active) else ""
    buttons.append([InlineKeyboardButton(f"{hl}{done} {task['title']}",callback_data=f"task_{tid}")])
  if missed and active:
    buttons.append([InlineKeyboardButton(f"🔔 Only Missed ({len(missed)})",callback_data="view_missed")])
  buttons.append([InlineKeyboardButton("⬅️ Back",callback_data="main_menu")])
  markup=InlineKeyboardMarkup(buttons)
  if is_start or (hasattr(update,'message') and update.message):
    await update.message.reply_text(text,reply_markup=markup)
  else:
    await update.callback_query.edit_message_text(text,reply_markup=markup)

async def show_supporting_plans(update,context):
  # Show image if set
  img_id=config.get("plan_image_file_id")
  caption="💎 *S2E Supporting Plans - Comparison*\n\n"
  caption+="OTT laga clear difference:\n"
  for p in PLANS:
    caption+=f"\n*{p['name']} - ₹{p['price']}*\n{p['desc']}\n"
  caption+="\n👇 Select your plan:"
  buttons=[]
  for p in PLANS:
    buttons.append([InlineKeyboardButton(f"💎 {p['name']} - ₹{p['price']}",callback_data=f"select_plan_{p['id']}")])
  buttons.append([InlineKeyboardButton("⬅️ Back",callback_data="main_menu")])
  markup=InlineKeyboardMarkup(buttons)
  try:
    if img_id:
      if hasattr(update,'callback_query') and update.callback_query:
        await update.callback_query.message.reply_photo(photo=img_id,caption=caption,reply_markup=markup,parse_mode="Markdown")
      else:
        await update.message.reply_photo(photo=img_id,caption=caption,reply_markup=markup,parse_mode="Markdown")
    else:
      # No image set - send text + placeholder info
      caption+="\n\n⚠️ Admin has not uploaded comparison image yet"
      if hasattr(update,'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(caption,reply_markup=markup,parse_mode="Markdown")
      else:
        await update.message.reply_text(caption,reply_markup=markup,parse_mode="Markdown")
  except Exception as e:
    print(e)
    if hasattr(update,'callback_query') and update.callback_query:
      await update.callback_query.edit_message_text(caption,reply_markup=markup,parse_mode="Markdown")
    else:
      await update.message.reply_text(caption,reply_markup=markup,parse_mode="Markdown")

async def button_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):
  query=update.callback_query
  await query.answer()
  data=query.data
  uid=query.from_user.id

  if data.startswith("task_"):
    tid=int(data.split("_")[1])
    if tid not in get_completed(uid):
      set_completed(uid,tid)
      try:
        await context.bot.send_message(SCREENSHOT_CHANNEL,f"✅ Task Done User:{uid} Task:{tid} {'(MISSED RECOVERY)' if is_missed_active() else ''}")
      except: pass
      await query.answer(f"Task {tid} Done!")
    await show_tasks(update,context,False)
    return

  if data=="view_missed":
    missed=get_missed(uid)
    text=f"🔔 Missed {len(missed)} Tasks\n"
    buttons=[]
    for tid in missed:
      buttons.append([InlineKeyboardButton(f"🔥 Do Task {tid}",callback_data=f"task_{tid}")])
    buttons.append([InlineKeyboardButton("Back",callback_data="user_tasks")])
    await query.edit_message_text(text,reply_markup=InlineKeyboardMarkup(buttons))
    return

  if data=="user_tasks":
    await show_tasks(update,context,False); return
  if data=="main_menu":
    await show_main_menu(update,context,False); return
  if data=="my_missed":
    missed=get_missed(uid)
    if not missed: await query.edit_message_text("🎉 No missed!",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back",callback_data="main_menu")]])); return
    text=f"⚠️ You missed {len(missed)}: {missed}\n"
    text+="🔥 Can complete NOW!" if is_missed_active() else "⏰ Admin will enable after 7PM"
    await query.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Tasks",callback_data="user_tasks")],[InlineKeyboardButton("Back",callback_data="main_menu")]]))
    return

  if data=="supporting_plans":
    await show_supporting_plans(update,context); return

  if data.startswith("select_plan_"):
    pid=int(data.split("_")[2])
    plan=next((p for p in PLANS if p["id"]==pid),None)
    if plan:
      await query.edit_message_text(f"✅ You selected {plan['name']} - ₹{plan['price']}\n\nOur team will contact you.\nContact admin for payment.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Plans",callback_data="supporting_plans")]]))
      try:
        await context.bot.send_message(JOIN_CHANNEL,f"💎 Plan Selected User:{uid} {query.from_user.first_name} Plan:{plan['name']} ₹{plan['price']}")
      except: pass
    return

  if not is_admin(uid): return

  if data=="toggle_missed":
    config["missed_enabled"]=not config.get("missed_enabled",False)
    save_config(config)
    await query.edit_message_text(f"{'✅ Missed ON' if config['missed_enabled'] else '❌ Missed OFF'} - Users {'see' if config['missed_enabled'] else 'dont see'} highlight now")
    return
  if data=="upload_plan_image":
    await query.edit_message_text("🖼️ Send the comparison image now as PHOTO with caption /set_plan_image\n\nExample: OTT style image showing 199 vs 499 difference\nSend photo now!")
    return
  if data=="channels":
    await query.edit_message_text(f"Channels Screenshot:{SCREENSHOT_CHANNEL} ✅ Withdraw:{WITHDRAW_CHANNEL} ✅ Join:{JOIN_CHANNEL} ✅")
    return
  if data=="missed_status":
    msg=f"Missed Status Today {today_str()} Active:{is_missed_active()}\n"
    for u,d in users_data.items():
      miss=[t for t in range(1,11) if t not in d.get(today_str(),[])]
      if miss: msg+=f"User {u}: {miss}\n"
    await query.edit_message_text(msg); return

async def photo_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):
  if not is_admin(update.effective_user.id): return
  # Check if caption has /set_plan_image
  caption=update.message.caption or ""
  if "/set_plan_image" in caption or "plan" in caption.lower():
    file_id=update.message.photo[-1].file_id
    config["plan_image_file_id"]=file_id
    save_config(config)
    await update.message.reply_text(f"✅ Plan comparison image saved! File ID: {file_id[:20]}...\nNow when users click Supporting Plans, this image will show.")
    # Preview
    await update.message.reply_photo(photo=file_id,caption="✅ This is how users will see - Supporting Plans Comparison")
  else:
    # Screenshot submission flow can be here
    pass

async def tasks_cmd(update,context): await show_tasks(update,context,True)
async def missed_cmd(update,context):
  uid=update.effective_user.id; m=get_missed(uid)
  if not m: await update.message.reply_text("🎉 No missed!"); return
  await update.message.reply_text(f"Missed: {m} {'Can do NOW!' if is_missed_active() else 'Wait for admin 7PM enable'}")

async def enable_missed_cmd(update,context):
  if not is_admin(update.effective_user.id): return
  config["missed_enabled"]=True; save_config(config)
  await update.message.reply_text("✅ Manual Missed ON - Users see highlight")

async def disable_missed_cmd(update,context):
  if not is_admin(update.effective_user.id): return
  config["missed_enabled"]=False; save_config(config)
  await update.message.reply_text("❌ Missed OFF")

async def supporting_plans_cmd(update,context): await show_supporting_plans(update,context)

async def set_plan_image_cmd(update,context):
  if not is_admin(update.effective_user.id): return
  await update.message.reply_text("🖼️ Send a PHOTO with caption /set_plan_image\nI will save it as comparison image")

async def channels_status(update,context):
  if not is_admin(update.effective_user.id): return
  await update.message.reply_text(f"📡 V33 Channels ✅\nScreenshot:{SCREENSHOT_CHANNEL}\nWithdraw:{WITHDRAW_CHANNEL}\nJoin:{JOIN_CHANNEL}\nMissed:{'ON' if is_missed_active() else 'OFF'}\nPlanImg:{'Set' if config.get('plan_image_file_id') else 'Not Set'}")

def main():
  if not BOT_TOKEN: print("TOKEN missing"); return
  threading.Thread(target=run_flask,daemon=True).start()
  app=ApplicationBuilder().token(BOT_TOKEN).build()
  app.add_handler(CommandHandler("start",start))
  app.add_handler(CommandHandler("tasks",tasks_cmd))
  app.add_handler(CommandHandler("missed",missed_cmd))
  app.add_handler(CommandHandler("enable_missed",enable_missed_cmd))
  app.add_handler(CommandHandler("disable_missed",disable_missed_cmd))
  app.add_handler(CommandHandler("supporting_plans",supporting_plans_cmd))
  app.add_handler(CommandHandler("set_plan_image",set_plan_image_cmd))
  app.add_handler(CommandHandler("channels_status",channels_status))
  app.add_handler(MessageHandler(filters.PHOTO,photo_handler))
  app.add_handler(CallbackQueryHandler(button_handler))
  print("V33 Starting")
  app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
