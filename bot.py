import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8905713910"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to VCF Maker Bot! 📇\n\nMujhe Name, Phone Number bhejein (jaise: Rahul, 9876543210) aur mai VCF file bana dunga.")

async def make_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = text.strip().split('\n')
    
    vcf_content = ""
    for idx, line in enumerate(lines, 1):
        parts = line.split(',')
        name = parts[0].strip() if len(parts) > 0 else f"Contact {idx}"
        phone = parts[1].strip() if len(parts) > 1 else line.strip()
        
        vcf_content += f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL:{phone}\nEND:VCARD\n"
    
    file_path = "contacts.vcf"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(vcf_content)
        
    await update.message.reply_document(document=open(file_path, "rb"), filename="contacts.vcf")
    os.remove(file_path)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, make_vcf))
    app.run_polling()
