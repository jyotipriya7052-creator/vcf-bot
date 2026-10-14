import os
import time
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
TOKEN = "8905713910:AAEUC4tcLaKsuzWW38u2-wRypCu1u2AvujU"

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
    
    welcome_text = (
        f"🎉 **WELCOME TO VCF TOOL BOT**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User:** {user.first_name}\n"
        f"⚡ **Status:** (Premium Unlocked 🔓)\n"
        f"👨‍💻 **Developed By:** `@Rule_Breakerz`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Need help? Send /help\n"
        f"⬇️ Select a service from the menu below:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    return CHOOSING

# --- Extra Commands (As seen in screenshot) ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ **HOW TO USE THIS BOT**\n\n"
        "1️⃣ Click **Text to VCF** from the menu.\n"
        "2️⃣ Upload your `.txt` file (Unlimited contacts supported).\n"
        "3️⃣ Enter batch size (e.g., 50 or 100).\n"
        "4️⃣ Enter sequence starting number (e.g., 1).\n"
        "5️⃣ Enter contact name prefix (e.g., VV).\n"
        "6️⃣ Enter output filename (e.g., MyList).\n\n"
        "Bot will instantly generate your VCF files!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    ping = round((end_time - start_time) * 1000, 2)
    await msg.edit_text(f"🏓 **Pong!** Bot Speed: `{ping}ms`", parse_mode="Markdown")

async def caption_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_status = context.user_data.get('caption', True)
    context.user_data['caption'] = not caption_status
    status_str = "ON 🟢" if not caption_status else "OFF 🔴"
    await update.message.reply_text(f"⚠️ Caption setting turned: **{status_str}**", parse_mode="Markdown")

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 Default Language is set to **English**.")

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Text to VCF":
        await update.message.reply_text(
            "📁 **Text to VCF Selected**\n\n"
            "Please upload your `.txt` file containing numbers (Unlimited numbers supported):",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return GET_FILE
    else:
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
        await update.message.reply_text(
            f"🛠️ **{text}** feature selected!\n\nChoose an option from the menu:",
            reply_markup=reply_markup
        )
        return CHOOSING

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    try:
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
    except Exception as e:
        await update.message.reply_text(f"❌ Error reading file: {str(e)}\nPlease upload the `.txt` file again.")
        return GET_FILE

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        await update.message.reply_text("❌ No contacts found in the file! Please upload a valid `.txt` file.")
        return GET_FILE

    context.user_data['contacts'] = lines
    await update.message.reply_text(
        f"✅ Successfully received **{len(lines)}** contacts!\n\n"
        "2️⃣ How many contacts do you want in each VCF file? (Example: `50`, `100`, `500`):",
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
        await update.message.reply_text("❌ Please enter a valid number greater than 0:")
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
        "4️⃣ What name prefix do you want inside the contacts? (Example: `Admin` or `VV`):",
        parse_mode="Markdown"
    )
    return GET_PREFIX

async def get_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prefix'] = update.message.text.strip()
    await update.message.reply_text(
        "5️⃣ What do you want to name the output VCF file? (Example: `Admin_File`):",
        parse_mode="Markdown"
    )
    return GET_FILENAME

async def get_filename_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base_filename = update.message.text.strip().replace(" ", "_")
    contacts = context.user_data.get('contacts', [])
    batch_size = context.user_data.get('batch_size', 50)
    current_num = context.user_data.get('start_num', 1)
    prefix = context.user_data.get('prefix', 'Contact')
    show_caption = context.user_data.get('caption', True)

    await update.message.reply_text("⚡ Generating your customized VCF files at superfast speed, please wait...")

    file_count = 1
    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        vcf_lines = []
        
        for line in batch:
            parts = line.split(',')
            phone = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
            contact_name = f"{prefix} {current_num}"
            vcf_lines.append(f"BEGIN:VCARD\nVERSION:3.0\nN:{contact_name};;;;\nFN:{contact_name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n")
            current_num += 1

        vcf_content = "".join(vcf_lines)
        file_name = f"{base_filename}_part{file_count}.vcf"
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(vcf_content)

        caption_msg = f"📁 File {file_count}: {file_name}" if show_caption else None

        with open(file_name, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file_name,
                caption=caption_msg
            )
        
        if os.path.exists(file_name):
            os.remove(file_name)
        
        file_count += 1

    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        "✨ All VCF files generated successfully!\nChoose an option from the menu:",
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
                MessageHandler(filters.Document.ALL, get_file)
            ],
            GET_FILE: [MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), get_file)],
            GET_BATCH_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_batch_size)],
            GET_START_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_num)],
            GET_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prefix)],
            GET_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_filename_and_generate)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ],
    )

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("caption", caption_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(conv_handler)

    app.run_polling()
