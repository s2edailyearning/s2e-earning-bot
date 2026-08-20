import os, threading, json
from datetime import datetime, time as dtime, timedelta, timezone
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

IST = timezone(timedelta(hours=5, minutes=30))
def get_ist_today(): return datetime.now(IST).date()

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot Running OK FIXED"

def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

TASKS_FILE = "/tmp/tasks.json"
scheduled_tasks_db = []
task_counter = 1

def load_tasks():
    global scheduled_tasks_db, task_counter
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE,'r') as f:
                data=json.load(f)
                scheduled_tasks_db=data.get('tasks',[])
                task_counter=data.get('counter',1)
    except: pass

def save_tasks():
    try:
        with open(TASKS_FILE,'w') as f:
            json.dump({'tasks':scheduled_tasks_db,'counter':task_counter}, f)
    except: pass

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

async def error_handler(update, context):
    print(f"Error: {context.error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Bot Working FIXED! ID {update.effective_user.id} Use /admin")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    print(f"/admin from {uid}")
    await update.message.reply_text(f"Admin Panel ID {uid} Bot FIXED! Commands: /add_task 8PM 15min 8:16PM Test 5 /list_tasks")

async def add_task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text=update.message.text.replace('/add_task','').strip()
        parts=text.split()
        open_s, close_s, next_s=parts[0], parts[1], parts[2]
        title=" ".join(parts[3:]) if len(parts)>3 else f"Task at {open_s}"
        def pt(s):
            s=s.strip().upper()
            try:
                if ':' in s:
                    p=s.replace('AM','').replace('PM','').strip().split(':')
                    h=int(p[0]); m=int(p[1].split()[0]) if len(p)>1 else 0
                    if 'PM' in s and h<12: h+=12
                    if 'AM' in s and h==12: h=0
                    return dtime(h,m)
                else:
                    h=int(s.replace('AM','').replace('PM','').split()[0])
                    if 'PM' in s and h<12: h+=12
                    if 'AM' in s and h==12: h=0
                    return dtime(h,0)
            except: return None
        open_t=pt(open_s)
        if ':' in close_s or 'AM' in close_s.upper() or 'PM' in close_s.upper(): close_t=pt(close_s)
        else:
            mins=int(close_s.lower().replace('min','').strip())
            from datetime import datetime as dt
            open_dt=dt.combine(get_ist_today(), open_t, tzinfo=IST)
            close_dt=open_dt+timedelta(minutes=mins)
            close_t=close_dt.time()
        next_t=pt(next_s)
        global task_counter
        load_tasks()
        task={'id':task_counter,'open':open_t.strftime("%H:%M"),'close':close_t.strftime("%H:%M"),'next':next_t.strftime("%H:%M"),'title':title,'date':str(get_ist_today())}
        scheduled_tasks_db.append(task)
        task_counter+=1
        save_tasks()
        await update.message.reply_text(f"Added ID {task['id']} {task['open']}->{task['close']} Next {task['next']} Title {title} Total {len(scheduled_tasks_db)}")
    except Exception as e:
        await update.message.reply_text(f"Error {e}")

async def list_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    load_tasks()
    if not scheduled_tasks_db:
        await update.message.reply_text("No tasks! Use /add_task")
        return
    msg=f"Tasks {get_ist_today()} Total {len(scheduled_tasks_db)}:\n"
    for t in scheduled_tasks_db:
        msg+=f"ID {t['id']} {t['open']}->{t['close']} {t['title']}\n"
    await update.message.reply_text(msg[:4000])

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    load_tasks()
    token=os.environ.get("BOT_TOKEN","")
    print(f"Token len={len(token)}")
    retry=0
    while retry<20:
        try:
            print(f"Build attempt {retry+1}/20")
            app=Application.builder().token(token).build()
            app.add_error_handler(error_handler)
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("add_task", add_task_cmd))
            app.add_handler(CommandHandler("list_tasks", list_tasks_cmd))
            print("Handlers registered, starting polling FIXED!")
            app.run_polling(drop_pending_updates=True)
            break
        except Exception as e:
            print(f"Polling error: {e}")
            retry+=1
            import time; time.sleep(10)

if __name__
