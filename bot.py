import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
TOKEN = "8905713910:AAE8jkQeXYyudYUlQurMAQ_PihFCEJqh0Cc"

# Force Subscription Channels (Add your channels here or leave [] if not needed)
REQUIRED_CHANNELS = ["https://t.me/whatsappworkfile22"] 

# Main Menu Keyboard (Neeche dikhne wale buttons jaise screenshot me hain)
MAIN_MENU = [
    ["Text to VCF", "VCF to Text"],
    ["Admin/Navy VCF", "VCF Editor"],
    ["Merge File", "Split File"],
    ["Rename File", "Get VCF Details"]
]

# States
CHOOSING, TEXT_TO_VCF_INPUT, ADMIN_VCF_INPUT = range(3)

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

    # Welcome Message & Main Menu
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    
    welcome_text = (
        f"🌟 **WELCOME TO VCF TOOL BOT** 🌟\n\n"
        f"👤 **User:** {user.first_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"⭐ **Status:** (Premium Unlocked 🔓)\n\n"
        f"🛠️ Select a service from the menu below:"
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
                text=f"🌟 **WELCOME TO VCF TOOL BOT** 🌟\n\n👤 **User:** {user.first_name}\n🛠️ Select a service from the menu below:",
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
            "📥 **Text to VCF Selected**\n\n"
            "Send your contacts list (Format: `Name, Phone` or just numbers, one per line):",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return TEXT_TO_VCF_INPUT
        
    elif text == "Admin/Navy VCF":
        await update.message.reply_text(
            "👑 **Admin/Navy VCF Selected**\n\n"
            "Send contacts numbers or text for Admin contacts:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return ADMIN_VCF_INPUT
        
    else:
        await update.message.reply_text(
            f"🛠️ **{text}** feature is selected. (You can customize this section as needed!)"
            "\n\nSend /start to go back to the main menu."
        )
        return CHOOSING

async def process_text_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = update.message.text
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    if not lines:
        await update.message.reply_text("❌ No contacts found. Please try again or send /start.")
        return CHOOSING

    vcf_content = ""
    for idx, line in enumerate(lines, start=1):
        parts = line.split(',')
        phone = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
        name = parts[0].strip() if len(parts) >= 2 else f"Contact {idx}"
        vcf_content += f"BEGIN:VCARD\nVERSION:3.0\nN:{name};;;;\nFN:{name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n"

    file_name = "Converted_Contacts.vcf"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(vcf_content)

    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    with open(file_name, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=file_name,
            caption="✨ **Generation Completed!** Here is your VCF file.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    if os.path.exists(file_name):
        os.remove(file_name)
        
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    await update.message.reply_text("❌ Operation cancelled.", reply_markup=reply_markup)
    return CHOOSING

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_choice)],
            TEXT_TO_VCF_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_to_vcf)],
            ADMIN_VCF_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_to_vcf)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()
