import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
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
TOKEN = "8905713910:AAFLrVYHcD9LBiUw2YZvStpYMFRghS4j8rk"

# Main Menu Buttons
MAIN_MENU = [
    ["Text to VCF", "VCF to Text"],
    ["Admin/Navy VCF", "VCF Editor"],
    ["Merge File", "Split File"],
    ["Rename File", "Get VCF Details"]
]

# Conversation States
CHOOSING, GET_FILE, GET_BATCH_SIZE, GET_START_NUM, GET_PREFIX, GET_FILENAME = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        f"🌟 **WELCOME TO VCF TOOL BOT** 🌟\n\n"
        f"👤 **User:** {user.first_name}\n"
        f"⭐ **Status:** (Premium Unlocked 🔓)\n\n"
        f"🛠️ Select a service from the menu below or directly upload your `.txt` file:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CHOOSING

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Text to VCF":
        await update.message.reply_text(
            "📁 **Text to VCF Selected**\n\n"
            "Please upload your `.txt` file containing numbers (1000+ numbers supported) or send them as text:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return GET_FILE
    else:
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        await update.message.reply_text(
            f"🛠️ **{text}** feature is selected.\n\nChoose an option from the menu:",
            reply_markup=reply_markup
        )
        return CHOOSING

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
        await update.message.reply_text("❌ No contacts found! Please upload a valid `.txt` file.")
        return GET_FILE

    context.user_data['contacts'] = lines
    await update.message.reply_text(
        f"✅ Successfully received **{len(lines)}** contacts!\n\n"
        "2️⃣ How many contacts do you want in each VCF file? (Example: `50` or `100`):"
    )
    return GET_BATCH_SIZE

async def get_batch_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        batch_size = int(update.message.text.strip())
        if batch_size <= 0:
            raise ValueError()
        context.user_data['batch_size'] = batch_size
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number greater than 0:")
        return GET_BATCH_SIZE

    await update.message.reply_text(
        "3️⃣ From which number do you want to start the sequence? (Example: `1` or `51`):"
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
        "4️⃣ What name prefix do you want inside the contacts? (Example: `Admin` or `VV`):"
    )
    return GET_PREFIX

async def get_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prefix'] = update.message.text.strip()
    await update.message.reply_text(
        "5️⃣ What do you want to name the output VCF file? (Example: `Admin_File`):"
    )
    return GET_FILENAME

async def get_filename_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base_filename = update.message.text.strip().replace(" ", "_")
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
            phone = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
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

    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        "✨ All VCF files have been generated successfully according to your instructions!\nChoose an option from the menu:",
        reply_markup=reply_markup
    )
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("❌ Process cancelled.", reply_markup=reply_markup)
    return CHOOSING

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_choice),
                MessageHandler(filters.Document.ALL, get_file)  # Direct file upload support at any time!
            ],
            GET_FILE: [MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), get_file)],
            GET_BATCH_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_batch_size)],
            GET_START_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_num)],
            GET_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prefix)],
            GET_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_filename_and_generate)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
