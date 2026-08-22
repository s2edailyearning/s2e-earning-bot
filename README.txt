S2E Daily Earning Bot - Render Upload Package

Files:
- main.py
- requirements.txt
- render.yaml
- .python-version

Render:
Build Command: pip install -r requirements.txt
Start Command: python main.py
Runtime: Python
Plan: Free

Required Environment Variable:
BOT_TOKEN = your Telegram bot token

Optional:
ADMIN_UPI
SUPPORT_USERNAME

Important:
The Telegram Bot API cannot programmatically open a user's Gallery/Camera picker from an inline bot button.
The Upload Screenshot button now puts the user into an upload-ready state and clearly instructs:
Telegram -> paperclip (📎) -> Gallery/Camera -> select screenshot -> Send.

After the photo is sent:
1. The bot records it as the selected task screenshot.
2. The user gets a pending-verification message.
3. The screenshot is sent to the configured Task Screenshots channel.
4. Admin gets Approve / Reject controls.
5. Pending Tasks shows the user's current pending submission.

Support Plans:
- Basic / Premium buttons work.
- Payment screenshot upload is routed to admins.
- Admin approval activates the selected plan ID.

The service is intentionally kept in polling mode to match the previously working deployment and avoid the webhook/polling conflict shown in the logs.
