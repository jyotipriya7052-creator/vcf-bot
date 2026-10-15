import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
TOKEN = "8482835334:AAGbdNUDsq1aCyRl6aZkgrQEAXPgABKjk1I"

# Force Subscription Channels (Add your channels here or leave [] if not needed)
REQUIRED_CHANNELS = ["https://t.me/whatsappworkfile22"] 

# Main Menu Buttons (As seen in video)
MAIN_MENU = [
    ["Text to VCF", "VCF to Text"],
    ["Admin/Navy VCF", "VCF Editor"],
    ["Merge File", "Split File"],
    ["Rename File", "Get VCF Details"]
]

# Conversation States for the 5-Step Wizard
(
    CHOOSING, 
    GET_FILE, 
    GET_VCF_FILENAME, 
    GET_PREFIX, 
    GET_FILE_START_NUM, 
    GET_CONTACT_START_NUM, 
    GET_BATCH_SIZE
) = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
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
            keyboard.append([InlineKeyboardButton("✅ Verify Joined", callback_data="check_sub")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🚨 **Join our official channels to use the bot!**\n\n"
                "Please join the channels below and click 'Verify Joined':",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return ConversationHandler.END

    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    welcome_text = (
        f"🌟 **WELCOME TO VCF TOOL BOT** 🌟\n\n"
        f"👤 **User:** {user.first_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"⚡ **Status:** (Premium Unlocked 🔓)\n"
        f"👨‍💻 **Developed By:** `@Rule_Breakerz`\n\n"
        f"💡 Need help? Send /help\n"
        f"⬇️ Select a service from the menu below:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    return CHOOSING

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
            user = query.from_user
            reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
            await query.message.edit_text("✅ **Verification Successful!** Welcome aboard.")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🌟 **WELCOME TO VCF TOOL BOT** 🌟\n\n👤 **User:** {user.first_name}\n⚡ **Status:** (Premium Unlocked 🔓)\n\n⬇️ Select a service from the menu below:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return CHOOSING
        else:
            await query.answer("❌ You haven't joined all required channels yet!", show_alert=True)

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Text to VCF":
        await update.message.reply_text(
            "📥 **Text to VCF Module**\n\n"
            "📂 Send Numbers, .txt, or Excel files...",
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
        await update.message.reply_text(f"❌ Error reading file: {str(e)}\nPlease upload the file again.")
        return GET_FILE

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        await update.message.reply_text("❌ No contacts found! Please upload a valid `.txt` file.")
        return GET_FILE

    context.user_data['contacts'] = lines
    
    # Step 0: Initial Config message as seen in video
    await update.message.reply_text(
        f"⚙️ **Configuring VCF**\n\n"
        f"📊 **Total Contacts:** {len(lines)}\n"
        f"🔄 **Status:** Processing...\n\n"
        f"1️⃣ **Send VCF File Name:**\n*(Example: Target_Audience)*",
        parse_mode="Markdown"
    )
    return GET_VCF_FILENAME

async def get_vcf_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['vcf_filename'] = update.message.text.strip()
    await update.message.reply_text(
        "2️⃣ **Contact Name Prefix?:**\n*(Example: Rule Test)*",
        parse_mode="Markdown"
    )
    return GET_PREFIX

async def get_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prefix'] = update.message.text.strip()
    await update.message.reply_text(
        "3️⃣ **VCF File Starting Number?:**\n*(Example: 1)*",
        parse_mode="Markdown"
    )
    return GET_FILE_START_NUM

async def get_file_start_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['file_start_num'] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (Example: 1):")
        return GET_FILE_START_NUM

    await update.message.reply_text(
        "4️⃣ **Contact Starting Number?:**\n*(Example: 1)*",
        parse_mode="Markdown"
    )
    return GET_CONTACT_START_NUM

async def get_contact_start_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['contact_start_num'] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (Example: 1):")
        return GET_CONTACT_START_NUM

    await update.message.reply_text(
        "5️⃣ **Contacts per vcf file?:**\n*(Example: 50)*",
        parse_mode="Markdown"
    )
    return GET_BATCH_SIZE

async def get_batch_size_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        batch_size = int(update.message.text.strip())
        if batch_size <= 0:
            raise ValueError()
        context.user_data['batch_size'] = batch_size
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number greater than 0:")
        return GET_BATCH_SIZE

    # Retrieve all inputs
    contacts = context.user_data.get('contacts', [])
    vcf_name = context.user_data.get('vcf_filename', 'Contact')
    prefix = context.user_data.get('prefix', 'User')
    file_num = context.user_data.get('file_start_num', 1)
    contact_num = context.user_data.get('contact_start_num', 1)

    await update.message.reply_text(
        f"🚀 **Generating VCF Files**\n"
        f"📊 **Total Contacts:** {len(contacts)}\n"
        f"🔄 **Status:** Processing...",
        parse_mode="Markdown"
    )

    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        vcf_lines = []
        
        for line in batch:
            parts = line.split(',')
            phone = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
            contact_name = f"{prefix} {contact_num}"
            vcf_lines.append(f"BEGIN:VCARD\nVERSION:3.0\nN:{contact_name};;;;\nFN:{contact_name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n")
            contact_num += 1

        vcf_content = "".join(vcf_lines)
        file_name = f"{vcf_name}{file_num}.vcf"
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(vcf_content)

        with open(file_name, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file_name,
                caption=f"📁 {file_name}"
            )
        
        if os.path.exists(file_name):
            os.remove(file_name)
        
        file_num += 1

    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text(
        "✅ **Generation Completed!**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
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
            GET_VCF_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vcf_filename)],
            GET_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prefix)],
            GET_FILE_START_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_file_start_num)],
            GET_CONTACT_START_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact_start_num)],
            GET_BATCH_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_batch_size_and_generate)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()
