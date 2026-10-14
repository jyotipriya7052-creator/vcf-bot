import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# --- Dummy Web Server for Render Port Binding ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- Configuration ---
TOKEN = "8905713910:AAE8_pmgtD8Z8IJwUsOXFnotMkwu0BLHLV8"

# Optional Force Subscription Channels (Leave empty [] if not needed)
REQUIRED_CHANNELS = [https://t.me/whatsappworkfile22] 

# Conversation States
GET_FILE, GET_BATCH_SIZE, GET_START_NUM, GET_PREFIX, GET_FILENAME = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Force Subscription Check
    if REQUIRED_CHANNELS:
        keyboard = []
        not_joined = False
        for channel in REQUIRED_CHANNELS:
            try:
                member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ['left', 'kicked']:
                    not_joined = True
                    keyboard.append([InlineKeyboardButton(f"📢 Join {channel}", url=f"https://t.me/{channel.replace('@', '')}")])
            except Exception:
                pass
        
        if not_joined:
            keyboard.append([InlineKeyboardButton("🔄 Check Membership", callback_data="check_sub")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ **You must join our channels/groups before using this bot!**\n\n"
                "Click the buttons below to join, then click 'Check Membership':",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return ConversationHandler.END

    await update.message.reply_text(
        "👋 Welcome to Advanced VCF Maker Bot!\n\n"
        "📁 Please upload your contacts `.txt` file or send the list as text:",
        parse_mode="Markdown"
    )
    return GET_FILE

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "check_sub":
        joined = True
        for channel in REQUIRED_CHANNELS:
            try:
                member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ['left', 'kicked']:
                    joined = False
            except Exception:
                pass
        
        if joined:
            await query.message.edit_text(
                "✅ Verification successful!\n\n"
                "📁 Please upload your contacts `.txt` file or send the list as text:",
                parse_mode="Markdown"
            )
            return GET_FILE
        else:
            await query.answer("❌ You haven't joined all required channels yet!", show_alert=True)

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    if update.message.document:
        doc = update.message.document
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            text = file_bytes.decode('latin-1', errors='ignore')
    elif update.message.text:
        text = update.message.text

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        await update.message.reply_text("❌ No contacts found. Please upload a valid `.txt` file or text list.")
        return GET_FILE

    context.user_data['contacts'] = lines
    await update.message.reply_text(
        f"✅ Received **{len(lines)}** contacts successfully!\n\n"
        "2️⃣ How many contacts do you want in each VCF file? (Example: `20` or `50`):",
        parse_mode="Markdown"
    )
    return GET_BATCH_SIZE

async def get_batch_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        batch_size = int(update.message.text.strip())
        if batch_size <= 0:
            raise ValueError()
        context.user_data['batch_size'] = batch_size
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number greater than 0 (Example: 50):")
        return GET_BATCH_SIZE

    await update.message.reply_text(
        "3️⃣ From which number do you want to start the sequence? (Example: `1` or `51`):",
        parse_mode="Markdown"
    )
    return GET_START_NUM

async def get_start_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_num = int(update.message.text.strip())
        context.user_data['start_num'] = start_num
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid starting number (Example: 1):")
        return GET_START_NUM

    await update.message.reply_text(
        "4️⃣ What name prefix do you want inside the contacts? (Example: `VV`):",
        parse_mode="Markdown"
    )
    return GET_PREFIX

async def get_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prefix'] = update.message.text.strip()
    await update.message.reply_text(
        "5️⃣ What do you want to name the output VCF file(s)? (Example: `MyContacts` or `ClientList`):",
        parse_mode="Markdown"
    )
    return GET_FILENAME

async def get_filename_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base_filename = update.message.text.strip()
    contacts = context.user_data.get('contacts', [])
    batch_size = context.user_data.get('batch_size', 50)
    current_num = context.user_data.get('start_num', 1)
    prefix = context.user_data.get('prefix', 'Contact')

    await update.message.reply_text("⏳ Generating your customized VCF files, please wait...")

    file_count = 1
    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        vcf_content = ""
        
        for line in batch:
            parts = line.split(',')
            if len(parts) >= 2:
                phone = parts[1].strip()
            else:
                phone = parts[0].strip()
            
            contact_name = f"{prefix} {current_num}"
            vcf_content += f"BEGIN:VCARD\nVERSION:3.0\nN:{contact_name};;;;\nFN:{contact_name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n"
            current_num += 1

        file_name = f"{base_filename}_part{file_count}.vcf"
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(vcf_content)

        with open(file_name, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file_name,
                caption=f"📁 File {file_count}: {file_name}"
            )
        
        if os.path.exists(file_name):
            os.remove(file_name)
        
        file_count += 1

    await update.message.reply_text("✨ All VCF files have been generated successfully according to your instructions!\nSend /start to begin a new task.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled. Send /start to begin again.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_FILE: [MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), get_file)],
            GET_BATCH_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_batch_size)],
            GET_START_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_num)],
            GET_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prefix)],
            GET_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_filename_and_generate)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()
