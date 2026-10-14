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
TOKEN = "8905713910:AAGZaVP5V4RTeD8IsB4Ccut-iMunqrZfeHA"

# Add your Telegram channels or groups username here for Force Subscription
REQUIRED_CHANNELS = ["https://t.me/whatsappworkfile22"]  # Put your channel username here (Make sure bot is admin in the channel)

# Conversation States
GET_PREFIX, GET_BATCH_SIZE, GET_CONTACTS = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Force Subscription Check
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
        "👋 Welcome to VCF Maker Bot!\n\n"
        "1️⃣ First, what name prefix would you like for your contacts? (Example: `VV`):",
        parse_mode="Markdown"
    )
    return GET_PREFIX

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
                "1️⃣ Now, what name prefix would you like for your contacts? (Example: `VV`):",
                parse_mode="Markdown"
            )
            return GET_PREFIX
        else:
            await query.answer("❌ You haven't joined all required channels yet!", show_alert=True)

async def get_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prefix'] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Prefix set to: **{context.user_data['prefix']}**\n\n"
        "2️⃣ How many contacts do you want in each VCF file? (Example: `50` or `100`):",
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
        f"✅ Batch size set to: **{context.user_data['batch_size']} contacts per file**.\n\n"
        "3️⃣ Now send your contacts (one per line, e.g., `Name, Phone` or just numbers).\n"
        "You can paste 100 or as many contacts as you want!",
        parse_mode="Markdown"
    )
    return GET_CONTACTS

async def process_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        await update.message.reply_text("❌ No contacts found. Please send valid contact entries.")
        return GET_CONTACTS

    prefix = context.user_data.get('prefix', 'Contact')
    batch_size = context.user_data.get('batch_size', 50)

    await update.message.reply_text(f"⏳ Total {len(lines)} contacts received. Processing files...")

    file_count = 1
    for i in range(0, len(lines), batch_size):
        batch = lines[i:i + batch_size]
        vcf_content = ""
        
        for idx, line in enumerate(batch, start=i + 1):
            parts = line.split(',')
            if len(parts) >= 2:
                phone = parts[1].strip()
            else:
                phone = parts[0].strip()
            
            contact_name = f"{prefix} {idx}"
            vcf_content += f"BEGIN:VCARD\nVERSION:3.0\nN:{contact_name};;;;\nFN:{contact_name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n"

        start_num = i + 1
        end_num = i + len(batch)
        file_name = f"{prefix}_{start_num}_to_{end_num}.vcf"
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(vcf_content)

        with open(file_name, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file_name,
                caption=f"📁 File {file_count}: Contacts ({start_num} to {end_num})"
            )
        
        if os.path.exists(file_name):
            os.remove(file_name)
        
        file_count += 1

    await update.message.reply_text("✨ All VCF files have been generated and sent successfully!\nSend /start to create a new batch.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled. Send /start to begin again.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prefix)],
            GET_BATCH_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_batch_size)],
            GET_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_contacts)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()
