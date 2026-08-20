
import os, threading
from datetime import datetime, time as dtime, timedelta
import pytz
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7600162174:AAH_test")
IST = pytz.timezone('Asia/Kolkata')
ADMIN_ID_LIST = [7256515560, 8544307598]

def get_ist_today():
    return datetime.now(IST).date()

def get_ist_now():
    return datetime.now(IST)

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot Running"
def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

scheduled_tasks_db = []
task_counter = 1

def parse_time_str(s):
    s=s.strip().upper()
    try:
        if ':' in s:
            parts=s.replace('AM','').replace('PM','').strip().split(':')
            h=int(parts[0]); m=int(parts[1].split()[0]) if len(parts)>1 else 0
            if 'PM' in s and h<12: h+=12
            if 'AM' in s and h==12: h=0
            return dtime(h,m)
        else:
            h=int(s.replace('AM','').replace('PM','').split()[0])
            if 'PM' in s and h<12: h+=12
            if 'AM' in s and h==12: h=0
            return dtime(h,0)
    except: return None

def parse_interval(s):
    s=s.lower()
    if 'min' in s: return int(s.replace('min','').strip())
    return 15

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Bot Working! ID {update.effective_user.id} Use /admin")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    print(f"/admin from {uid}")
    await update.message.reply_text(f"Admin Panel ID {uid} Bot working! Commands: /add_task 7:35PM 15min 7:51PM Test 5 /list_tasks")

async def add_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    print(f"/add_task from {uid}: {update.message.text}")
    try:
        text = update.message.text.replace('/add_task','').strip()
        if not text:
            await update.message.reply_text("Usage: /add_task 7:35PM 15min 7:51PM Title 5")
            return
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("Need 3 times")
            return
        open_s, close_s, next_s = parts[0], parts[1], parts[2]
        title = " ".join(parts[3:]) if len(parts)>3 else f"Task at {open_s}"
        open_t = parse_time_str(open_s)
        close_t = None
        if ':' in close_s or 'AM' in close_s.upper() or 'PM' in close_s.upper():
            close_t = parse_time_str(close_s)
        else:
            mins = parse_interval(close_s)
            open_dt = datetime.combine(get_ist_today(), open_t, tzinfo=IST)
            close_dt = open_dt + timedelta(minutes=mins)
            close_t = close_dt.time()
        next_t = parse_time_str(next_s)
        if not open_t or not close_t or not next_t:
            await update.message.reply_text(f"Time parse fail")
            return
        global task_counter
        task = {'id': task_counter, 'open': open_t.strftime("%H:%M"), 'close': close_t.strftime("%H:%M"), 'next': next_t.strftime("%H:%M"), 'title': title, 'date': str(get_ist_today())}
        scheduled_tasks_db.append(task)
        task_counter+=1
        await update.message.reply_text(f"Added ID {task['id']} {task['open']}->{task['close']} Title {title} Total {len(scheduled_tasks_db)}")
    except Exception as e:
        print(f"error {e}")
        await update.message.reply_text(f"Error {e}")

async def list_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not scheduled_tasks_db:
        await update.message.reply_text("No tasks")
        return
    msg = f"Tasks Total {len(scheduled_tasks_db)}:\n"
    for t in scheduled_tasks_db:
        msg+=f"ID {t['id']} {t['open']}->{t['close']} {t['title']}\n"
    await update.message.reply_text(msg[:4000])

async def error_handler(update, context):
    print(f"Error {context.error}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    print("Starting bot MINIMAL")
    retry=0
    while retry<20:
        try:
            print(f"Build attempt {retry+1}/20")
            app = Application.builder().token(os.environ.get("BOT_TOKEN", BOT_TOKEN)).build()
            app.add_error_handler(error_handler)
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("add_task", add_task_cmd))
            app.add_handler(CommandHandler("list_tasks", list_tasks_cmd))
            print("Handlers registered, starting polling")
            app.run_polling(drop_pending_updates=True)
            break
        except Exception as e:
            print(f"Error {e}")
            retry+=1
            time.sleep(10)

if __name__=="__main__":
    main()
