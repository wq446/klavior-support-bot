import os
import logging
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ADMIN_ID = int(os.environ.get("ADMIN_ID", "6880607158"))

# 1. خادم لإبقاء Render مستيقظاً وتلبية طلبات UptimeRobot (GET & HEAD)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def log_message(self, format, *args):
        return  # لمنع ملء السجلات بطلبات UptimeRobot المكررة

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    logging.info(f"Health check server running on port {port}")
    server.serve_forever()

# 2. منطق البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "**مرحباً بك في الدعم الفني لموقع Klavior! 👋**\n\n"
        "أرسل استفسارك أو مشكلتك هنا مباشرة، وسيقوم فريق الدعم بالرد عليك في أقرب وقت. 💙"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_ID:
        user_info = f"📩 **رسالة جديدة من:** {user.first_name} (ID: `{user.id}`)\n\n"
        
        if update.message.text:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=user_info + update.message.text,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=user_info, parse_mode="Markdown")
            await update.message.forward(chat_id=ADMIN_ID)

        await update.message.reply_text("تم استلام رسالتك بنجاح، وسيتم الرد عليك قريباً! ✨")

    elif chat_id == ADMIN_ID and update.message.reply_to_message:
        try:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
            
            if "ID: `" in reply_text:
                target_user_id = int(reply_text.split("ID: `")[1].split("`")[0])

                if update.message.text:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"💬 **رد الدعم الفني:**\n\n{update.message.text}",
                        parse_mode="Markdown"
                    )
                elif update.message.photo:
                    await context.bot.send_photo(
                        chat_id=target_user_id,
                        photo=update.message.photo[-1].file_id,
                        caption=f"💬 **رد الدعم الفني:**\n\n{update.message.caption or ''}"
                    )
                
                await update.message.reply_text("✅ تم إرسال الرد بنجاح!")
            else:
                await update.message.reply_text("❌ يرجى الرد (Reply) على رسالة الإشعار التي تحتوي على ID الطالب.")

        except Exception as e:
            await update.message.reply_text(f"❌ تعذر إرسال الرد:\n{e}")

if __name__ == '__main__':
    # تشغيل خادم HTTP في الخلفية
    Thread(target=run_dummy_server, daemon=True).start()

    # تشغيل البوت
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(~filters.COMMAND, handle_message))

    app.run_polling()
