"""
TaskNova Official Bot - FINAL DEPLOYMENT READY
Bot: @tasknovaofficial_bot
Main Channel: @task_nova_official (Public)
Support Inbox: Task Nova Support Inbox - Private -1003873380192
Admin: 7256515560 (S2E Day income - will show as TaskNova Team)
- 100% Private & Anonymous Support
- Sign Messages OFF so only channel name shows
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= CONFIG - FINAL =================
BOT_TOKEN = "8882746334:AAEYbsWR1xE1A3HmNYZmTc_6S5rlKG9ceKQ"
MAIN_CHANNEL = "task_nova_official"
SUPPORT_CHANNEL_ID = -1003873380192
ADMIN_ID = 7256515560

TASKS = {
    "task1": "https://t.me/task_nova_official/1",
    "task2": "https://t.me/task_nova_official/2", 
    "task3": "https://t.me/task_nova_official/3",
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def is_user_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(f"@{MAIN_CHANNEL}", user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.error(f"Join check error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    joined = await is_user_joined(user.id, context)
    
    if not joined:
        keyboard = [
            [InlineKeyboardButton("📢 Join Main Channel", url=f"https://t.me/{MAIN_CHANNEL}")],
            [InlineKeyboardButton("✅ I Joined - Verify", callback_data="verify_join")]
        ]
        await update.message.reply_text(
            f"👋 Welcome to *TaskNova Official*!\n\n"
            f"To use this bot, you must join our main channel first:\n"
            f"👉 @{MAIN_CHANNEL}\n\n"
            f"After joining, click Verify below.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton("📋 View Tasks", callback_data="tasks")],
        [InlineKeyboardButton("💰 My Earnings", callback_data="earnings")],
        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton("📢 Main Channel", url=f"https://t.me/{MAIN_CHANNEL}")]
    ]
    
    await update.message.reply_text(
        f"🚀 *Welcome {user.first_name} to TaskNova!*\n\n"
        f"Complete tasks, earn daily rewards!\n"
        f"Official Bot - 100% Safe & Anonymous\n\n"
        f"Choose an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "verify_join":
        joined = await is_user_joined(user.id, context)
        if joined:
            keyboard = [
                [InlineKeyboardButton("📋 View Tasks", callback_data="tasks")],
                [InlineKeyboardButton("💰 My Earnings", callback_data="earnings")],
                [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
            ]
            await query.edit_message_text(
                "✅ Verified! You joined the channel.\n\nWelcome to TaskNova!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.answer("❌ You haven't joined yet! Please join @task_nova_official first", show_alert=True)

    elif query.data == "tasks":
        keyboard = [
            [InlineKeyboardButton("Task 1 - ₹10", url=TASKS["task1"])],
            [InlineKeyboardButton("Task 2 - ₹20", url=TASKS["task2"])],
            [InlineKeyboardButton("Task 3 - ₹30", url=TASKS["task3"])],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_home")]
        ]
        await query.edit_message_text(
            "📋 *Available Tasks Today:*\n\nComplete tasks from our channel and earn!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "earnings":
        await query.edit_message_text(
            "💰 *Your Earnings:*\n\nToday: ₹0\nTotal: ₹0\n\nComplete tasks to start earning!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_home")]])
        )

    elif query.data == "contact_support":
        context.user_data["awaiting_support"] = True
        await query.edit_message_text(
            "📞 *TaskNova Support*\n\n"
            "Meeku em help kavali? Please type your question below:\n\n"
            "Example: Payment eppudu vastundi? Task work avvatledu etc.\n\n"
            "Your details are 100% private - only TaskNova Team will see it.\n"
            "Type your message now:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="back_home")]])
        )

    elif query.data == "back_home":
        context.user_data["awaiting_support"] = False
        keyboard = [
            [InlineKeyboardButton("📋 View Tasks", callback_data="tasks")],
            [InlineKeyboardButton("💰 My Earnings", callback_data="earnings")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
        ]
        await query.edit_message_text(
            f"🚀 *TaskNova Official*\n\nChoose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def support_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_support"):
        return

    user = update.effective_user
    text = update.message.text

    try:
        support_text = (
            f"📩 *New Support Ticket*\n\n"
            f"👤 User: {user.first_name} (ID: {user.id})\n"
            f"🔗 Username: @{user.username if user.username else 'No username'}\n\n"
            f"💬 Message:\n{text}\n\n"
            f"Reply: /reply {user.id} your_message"
        )
        
        await context.bot.send_message(chat_id=SUPPORT_CHANNEL_ID, text=support_text, parse_mode="Markdown")
        
        await update.message.reply_text(
            "✅ *Your message sent to TaskNova Support!*\n\n"
            "Memu 24 hours lo reply isthamu. Please wait.\n\n"
            "Inkoka question unte malli Contact Support click cheyyandi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="back_home")]])
        )
        context.user_data["awaiting_support"] = False

    except Exception as e:
        logger.error(f"Support forward error: {e}")
        await update.message.reply_text(
            f"❌ Error: {e}\nPlease ensure bot is admin in private support channel",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="back_home")]])
        )
        context.user_data["awaiting_support"] = False

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can use this command")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reply <user_id> <message>\nExample: /reply 123456789 Your payment is processing")
        return
    
    try:
        user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📞 *Reply from TaskNova Support:*\n\n{reply_text}\n\n- Team TaskNova",
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ Reply sent to {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_message_handler))
    
    print(f"TaskNova Bot running...")
    print(f"Main Channel: @{MAIN_CHANNEL}")
    print(f"Support Inbox: {SUPPORT_CHANNEL_ID}")
    print(f"Admin ID: {ADMIN_ID}")
    app.run_polling()

if __name__ == "__main__":
    main()
