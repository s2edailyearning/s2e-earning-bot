"""
S2E Bot V65 PERFECT FINAL - NO DUPLICATES
Main S2E Public 5subs = -1004295034675
Screenshot TASK Private 2subs = -1004352241439 ONLY proofs - NOT public
Withdraw = -1004319888475
Features: Referrals, Wallet, Daily, Withdraw 200/300/500/1000 +7% +Remaining, Promo, Shop, Scheduled, Support, Contact, Admin
Fixes: Port, Conflict, /start, Withdraw button, Screenshot private only
"""
import os, threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

IST = timezone(timedelta(hours=5, minutes=30))
def now_ist(): return datetime.now(IST)
BOT_TOKEN = os.getenv("BOT_TOKEN")
MAIN = -1004295034675
SCREENSHOT = -1004352241439
WITHDRAW = -1004319888475
cur_main, cur_ss, cur_wd = MAIN, SCREENSHOT, WITHDRAW
def get_main(): return cur_main
def get_ss(): return cur_ss
def get_wd(): return cur_wd
ADMIN = [7256515560, 8544307598]
def is_admin(uid): return uid in ADMIN
users = {}
OPTS = [200,300,500,1000]
FEE = 7
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"V65 Perfect Live {now_ist()} Main:{get_main()} SS Private:{get_ss()} WD:{get_wd()}"
@flask_app.route('/health')
def h(): return "OK",200
def run_flask(): flask_app.run(host='0.0.0.0', port=int(os.getenv("PORT",10000)), debug=False)
def get_user(uid):
    if uid not in users: users[uid] = {"balance":765,"upi":None,"referrals":[],"total":0,"history":[]}
    return users[uid]
def main_kb(): return InlineKeyboardMarkup([
        [InlineKeyboardButton("My Referrals", callback_data="my_ref"), InlineKeyboardButton("Wallet", callback_data="wallet")],
        [InlineKeyboardButton("Daily Task", callback_data="daily"), InlineKeyboardButton("Withdraw", callback_data="wd_menu")],
        [InlineKeyboardButton("Promo Tasks", callback_data="promo"), InlineKeyboardButton("Promote My Shop", callback_data="shop")],
        [InlineKeyboardButton("Scheduled Tasks", callback_data="sched"), InlineKeyboardButton("Support Plans", callback_data="support")],
        [InlineKeyboardButton("Contact Us", callback_data="contact"), InlineKeyboardButton("Admin", callback_data="admin")],
    ])
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)
    if context.args and context.args[0].isdigit():
        rid = int(context.args[0])
        if rid != uid and rid in users and uid not in users[rid]["referrals"]:
            users[rid]["referrals"].append(uid)
            users[rid]["balance"] += 10
    await update.message.reply_text(f"S2E V65 Perfect\nBalance: {get_user(uid)['balance']}\nSS Private {get_ss()} ONLY - Not public {get_main()}\n7% + 200/300/500/1000", reply_markup=main_kb())
async def cb_my_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    uid = update.effective_user.id
    u = get_user(uid)
    link = f"https://t.me/{context.bot.username}?start={uid}"
    await update.callback_query.edit_message_text(f"Referrals: {len(u['referrals'])}\nLink: {link}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    u = get_user(update.effective_user.id)
    await update.callback_query.edit_message_text(f"Wallet\nBalance: {u['balance']}\nUPI: {u['upi']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    txt = f"Today's Task:\nTitle: Join Channel @s2edayincome\nReward: Rs5\nLink: https://t.me/S2E_Daily_Earning\nClick Upload after completing!\nProof goes ONLY to private {get_ss()} not public {get_main()}"
    await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("VIEW CHANNEL", url="https://t.me/S2E_Daily_Earning")],[InlineKeyboardButton("Upload Screenshot", callback_data="upload")],[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    context.user_data['wait_ss'] = True
    await update.callback_query.edit_message_text(f"Upload Here\nONLY to TASK Private {get_ss()} NOT to S2E Public {get_main()}\nSend photo now")
async def cb_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text("Promo Tasks - Rs10 extra", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text("Promote My Shop - Contact admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_sched(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text("Scheduled Tasks - No tasks now", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text("Support Plans - Basic 99, Pro 199", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text("Contact Us - @S2E_Admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def ss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('wait_ss'): return
    uid = update.effective_user.id
    fid = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Approve", callback_data=f"appr_{uid}"), InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]])
    cap = f"NEW PROOF V65\nUser: {uid} (@{update.effective_user.username or 'no'})\nTask: 1 Join @s2edayincome\nReward: 5\nTime: {now_ist().strftime('%d-%m %H:%M')} IST\nChannel: TASK Private {get_ss()} ONLY NOT S2E Public {get_main()}"
    try:
        await context.bot.send_photo(chat_id=get_ss(), photo=fid, caption=cap, reply_markup=kb)
        await update.message.reply_text(f"Sent ONLY to TASK Private {get_ss()} NOT to S2E Public {get_main()} - FIXED", reply_markup=main_kb())
        context.user_data.pop('wait_ss', None)
    except Exception as e:
        await update.message.reply_text(f"Bot not admin in private {get_ss()} Error: {e}")
async def cb_wd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    u = get_user(update.effective_user.id)
    kb = []
    for amt in OPTS:
        if u["balance"] >= amt:
            fee = int(amt*FEE/100); get_amt = amt - fee
            kb.append([InlineKeyboardButton(f"Rs{amt} Fee Rs{fee} Get Rs{get_amt}", callback_data=f"wd_{amt}")])
    kb.append([InlineKeyboardButton("Set/Edit UPI", callback_data="wd_upi")])
    kb.append([InlineKeyboardButton("Back", callback_data="back")])
    await update.callback_query.edit_message_text(f"Withdraw 7% Logic\nBalance: {u['balance']}\nUPI: {u['upi']}\n200->Get 186, 300->279, 500->465, 1000->930\nRemaining shown", reply_markup=InlineKeyboardMarkup(kb))
async def cb_wd_sel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    amt = int(update.callback_query.data.replace("wd_",""))
    u = get_user(update.effective_user.id)
    if not u["upi"]:
        await update.callback_query.edit_message_text("UPI not set", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Set UPI", callback_data="wd_upi")]]))
        return
    fee = int(amt*FEE/100); get_amt = amt - fee; rem = u["balance"] - amt
    await update.callback_query.edit_message_text(f"Confirm?\nAmount: {amt}\nFee: {fee}\nYou get: {get_amt}\nCurrent: {u['balance']}\nRemaining: {rem}\nUPI: {u['upi']}\nOnly to Withdraw {get_wd()}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Confirm Rs{amt} Get Rs{get_amt}", callback_data=f"wdc_{amt}")],[InlineKeyboardButton("Back", callback_data="wd_menu")]]))
async def cb_wd_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    context.user_data['wait_upi'] = True
    await update.callback_query.edit_message_text("Send UPI ID now\nEx: 8709635130@ybl")
async def upi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('wait_upi'): return
    upi = update.message.text.strip()
    if "@" not in upi: await update.message.reply_text("Invalid UPI"); return
    get_user(update.effective_user.id)["upi"] = upi
    context.user_data.pop('wait_upi', None)
    await update.message.reply_text(f"UPI Saved: {upi}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Withdraw", callback_data="wd_menu")]]))
async def cb_wdc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    amt = int(update.callback_query.data.replace("wdc_",""))
    uid = update.effective_user.id
    u = get_user(uid)
    if u["balance"] < amt: await update.callback_query.edit_message_text(f"Low bal {u['balance']}"); return
    fee = int(amt*FEE/100); get_amt = amt - fee; rem = u["balance"] - amt
    u["balance"] = rem
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Approve", callback_data=f"wda_{uid}_{amt}"), InlineKeyboardButton("Reject Refund", callback_data=f"wdr_{uid}_{amt}")]])
    msg = f"NEW WITHDRAW V65\nUser: {uid} (@{update.effective_user.username or 'no'})\nAmount: {amt}\nFee 7%: {fee}\nGets: {get_amt}\nRemaining: {rem}\nUPI: {u['upi']}\nTime: {now_ist().strftime('%d-%m %H:%M')} IST\nWithdraw ONLY {get_wd()}"
    try:
        await context.bot.send_message(chat_id=get_wd(), text=msg, reply_markup=kb)
        await update.callback_query.edit_message_text(f"Withdraw Sent!\nAmount: {amt}\nFee: {fee}\nYou get: {get_amt}\nRemaining: {rem}\nUPI: {u['upi']}\nOnly to {get_wd()}", reply_markup=main_kb())
    except Exception as e:
        u["balance"] += amt
        await update.callback_query.edit_message_text(f"Bot not admin in withdraw {get_wd()} {e}")
async def cb_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    await update.callback_query.edit_message_text(f"Admin V65\nMain S2E Public 5subs: {get_main()}\nScreenshot TASK Private 2subs: {get_ss()} ONLY - members WONT see FIXED\nWithdraw: {get_wd()}\n200/300/500/1000 +7% +Remaining", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back")]]))
async def cb_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    await update.callback_query.edit_message_text(f"S2E V65\nBalance: {get_user(update.effective_user.id)['balance']}", reply_markup=main_kb())
async def cb_appr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    uid = int(update.callback_query.data.split("_")[1])
    get_user(uid)["balance"] += 5
    try: await update.callback_query.edit_message_caption(caption=update.callback_query.message.caption + "\n\nAPPROVED +5")
    except: await update.callback_query.edit_message_text(text=update.callback_query.message.text + "\n\nAPPROVED")
    try: await context.bot.send_message(chat_id=uid, text="Approved +5", reply_markup=main_kb())
    except: pass
async def cb_rej(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    try: await update.callback_query.edit_message_caption(caption=update.callback_query.message.caption + "\n\nREJECTED")
    except: await update.callback_query.edit_message_text(text=update.callback_query.message.text + "\n\nREJECTED")
async def cb_wda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    await update.callback_query.edit_message_text(text=update.callback_query.message.text + "\n\nAPPROVED PAID")
async def cb_wdr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await update.callback_query.answer()
    except: pass
    if not is_admin(update.effective_user.id): return
    uid = int(update.callback_query.data.split("_")[1]); amt = int(update.callback_query.data.split("_")[2])
    get_user(uid)["balance"] += amt
    await update.callback_query.edit_message_text(text=update.callback_query.message.text + "\n\nREJECTED REFUNDED")
async def cmd_set_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cur_main
    if not is_admin(update.effective_user.id): return
    try: cur_main = int(context.args[0]); await update.message.reply_text(f"Main S2E Set: {cur_main}")
    except: await update.message.reply_text("Usage: /set_join_channel -1004295034675")
async def cmd_set_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cur_ss
    if not is_admin(update.effective_user.id): return
    try: cur_ss = int(context.args[0]); await update.message.reply_text(f"Screenshot TASK Private Set: {cur_ss} - members WONT see FIXED")
    except: await update.message.reply_text("Usage: /set_screenshot_channel -1004352241439")
async def cmd_set_wd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cur_wd
    if not is_admin(update.effective_user.id): return
    try: cur_wd = int(context.args[0]); await update.message.reply_text(f"Withdraw Set: {cur_wd}")
    except: await update.message.reply_text("Usage: /set_withdraw_channel -1004319888475")
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(f"V65 PERFECT STATUS\nMain S2E Public 5subs: {get_main()}\nScreenshot TASK Private 2subs: {get_ss()} ONLY members WONT see FIXED\nWithdraw: {get_wd()}\n200/300/500/1000 +7% +Remaining\nPort+Conflict+/start+Withdraw Fixed No Duplicates")
async def cmd_add_bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try: uid = int(context.args[0]); amt = int(context.args[1]); get_user(uid)["balance"] += amt; await update.message.reply_text(f"Added {amt} to {uid}")
    except: await update.message.reply_text("Usage: /add_balance 8709635130 765")
async def post_init(app): await app.bot.delete_webhook(drop_pending_updates=True)
async def err_h(u,c):
    if "Conflict" in str(c.error): return
def main():
    if not BOT_TOKEN: return
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_error_handler(err_h)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("set_join_channel", cmd_set_main))
    app.add_handler(CommandHandler("set_screenshot_channel", cmd_set_ss))
    app.add_handler(CommandHandler("set_withdraw_channel", cmd_set_wd))
    app.add_handler(CommandHandler("channels_status", cmd_status))
    app.add_handler(CommandHandler("add_balance", cmd_add_bal))
    app.add_handler(CallbackQueryHandler(cb_my_ref, pattern=r"^my_ref$"))
    app.add_handler(CallbackQueryHandler(cb_wallet, pattern=r"^wallet$"))
    app.add_handler(CallbackQueryHandler(cb_daily, pattern=r"^daily$"))
    app.add_handler(CallbackQueryHandler(cb_upload, pattern=r"^upload$"))
    app.add_handler(CallbackQueryHandler(cb_promo, pattern=r"^promo$"))
    app.add_handler(CallbackQueryHandler(cb_shop, pattern=r"^shop$"))
    app.add_handler(CallbackQueryHandler(cb_sched, pattern=r"^sched$"))
    app.add_handler(CallbackQueryHandler(cb_support, pattern=r"^support$"))
    app.add_handler(CallbackQueryHandler(cb_contact, pattern=r"^contact$"))
    app.add_handler(CallbackQueryHandler(cb_wd_menu, pattern=r"^wd_menu$"))
    app.add_handler(CallbackQueryHandler(cb_wd_sel, pattern=r"^wd_"))
    app.add_handler(CallbackQueryHandler(cb_wd_upi, pattern=r"^wd_upi$"))
    app.add_handler(CallbackQueryHandler(cb_wdc, pattern=r"^wdc_"))
    app.add_handler(CallbackQueryHandler(cb_admin, pattern=r"^admin$"))
    app.add_handler(CallbackQueryHandler(cb_back, pattern=r"^back$"))
    app.add_handler(CallbackQueryHandler(cb_appr, pattern=r"^appr_"))
    app.add_handler(CallbackQueryHandler(cb_rej, pattern=r"^rej_"))
    app.add_handler(CallbackQueryHandler(cb_wda, pattern=r"^wda_"))
    app.add_handler(CallbackQueryHandler(cb_wdr, pattern=r"^wdr_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, upi_handler), group=0)
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, ss_handler), group=1)
    print(f"V65 PERFECT STARTING Main:{get_main()} SS Private:{get_ss()} WD:{get_wd()}")
    app.run_polling(drop_pending_updates=True)
if __name__ == "__main__":
    main()
