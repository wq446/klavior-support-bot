import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ايدي الأدمن (يُقرأ من متغيرات البيئة في Render)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6880607158"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "**مرحباً بك في الدعم الفني لموقع Klavior! 👋**\n\n"
        "أرسل استفسارك أو مشكلتك هنا مباشرة، وسيقوم فريق الدعم بالرد عليك في أقرب وقت. 💙"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 1. إذا كانت الرسالة قادمة من المستخدم -> توجيهها للأدمن
    if chat_id != ADMIN_ID:
        user_info = f"📩 **رسالة جديدة من:** {user.first_name} (ID: `{user.id}`)\n\n"
        
        # إذا كانت الرسالة نصية
        if update.message.text:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=user_info + update.message.text,
                parse_mode="Markdown"
            )
        # إذا أرسل المستخدم صورة أو ملف
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=user_info, parse_mode="Markdown")
            await update.message.forward(chat_id=ADMIN_ID)

        await update.message.reply_text("تم استلام رسالتك بنجاح، وسيتم الرد عليك قريباً! ✨")

    # 2. إذا كانت الرسالة قادمة منك (الأدمن) كرد (Reply) على رسالة إشعار
    elif chat_id == ADMIN_ID and update.message.reply_to_message:
        try:
            # استخراج ID الطالب من النص الموجه
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
            
            if "ID: `" in reply_text:
                target_user_id = int(reply_text.split("ID: `")[1].split("`")[0])

                # إرسال الرد للطالب
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
            await update.message.reply_text(f"❌ تعذر إرسال الرد. التأكد من الرد على الرسالة الصحيحة.\nالخطأ: {e}")

if __name__ == '__main__':
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # التعامل مع كافة أنواع الرسائل (نصوص، صور، مستندات)
    app.add_handler(MessageHandler(~filters.COMMAND, handle_message))

    app.run_polling()
