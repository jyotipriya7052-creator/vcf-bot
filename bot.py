import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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

# --- Telegram Bot Logic ---
TOKEN = "8905713910:AAGUTjG93mFSI6oLhUHCmyHWb8bdb-GZUtY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Names and numbers bhejiyen (format: Name, Number).\nMain VCF file bana dunga.")

async def make_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = text.strip().split('\n')
    
    vcf_content = ""
    for line in lines:
        parts = line.split(',')
        if len(parts) >= 2:
            name = parts[0].strip()
            phone = parts[1].strip()
            vcf_content += f"BEGIN:VCARD\nVERSION:3.0\nN:{name};;;;\nFN:{name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n"
    
    if vcf_content:
        file_path = "contacts.vcf"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(vcf_content)
        
        with open(file_path, "rb") as f:
            await update.message.reply_document(document=f, filename="contacts.vcf")
    else:
        await update.message.reply_text("Kripya sahi format me bhejin (e.g., Name, Number)")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, make_vcf))
    app.run_polling()
