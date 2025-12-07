# bot.py → FINAL PRO VERSION 2025 (bKash + Binance QR Both Working)
import logging
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

# ═══════════════════ তোমার তথ্য এখানে বসাও ═══════════════════
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"                    # BotFather থেকে
ADMIN_ID = 1651695602                              # তোমার টেলিগ্রাম আইডি

# QR file_id দুটো (নিচে বলছি কিভাবে নিবে)
BKASH_QR_FILE_ID   = "AgACAgUAAxkBAAEZYCZpNOTLIbUSloBZxDaXKjCU3cL53QACcQtrG-QSqFVIuPQ_B-XJLAEAAwIAA3kAAzYE"    # ← বসাও
BINANCE_QR_FILE_ID = "AgACAgUAAxkBAAIC...তোমার_binance_qr_file_id_এখানে"  # ← বসাও

BKASH_NUMBER = "01815243007"      # তোমার bKash নাম্বার
BINANCE_ID   = "38017799"        # তোমার Binance Pay ID
# ═══════════════════════════════════════════════════════════════

# Price
P = {
    "hotmail": {"bkash": 2.5,    "binance": 0.02},
    "edu":     {"bkash": 2,   "binance":0.016}
}

CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)
orders = {}
waiting = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Hotmail & Outlook Accounts", callback_data="cat_hotmail")],
        [InlineKeyboardButton(".EDU Student Mail Accounts", callback_data="cat_edu")],
    ]
    await update.message.reply_text(
        "Mail Marketplace\n\n"
        "Choose account type:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CHOOSE_CAT

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cat = "hotmail" if q.data == "cat_hotmail" else "edu"
    name = "Hotmail & Outlook Accounts" if cat == "hotmail" else ".EDU Student Mail Accounts"
    context.user_data["cat"] = name
    context.user_data["key"] = cat

    kb = [
        [InlineKeyboardButton(f"bKash → ৳{P[cat]['bkash']}/acc", callback_data="pay_bkash")],
        [InlineKeyboardButton(f"Binance → ${P[cat]['binance']}/acc", callback_data="pay_binance")],
    ]
    await q.edit_message_text(f"{name}\n\nSelect payment method:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAYMENT

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    method = "bKash" if q.data == "pay_bkash" else "Binance Pay"
    price = P[context.user_data["key"]]["bkash" if method=="bKash" else "binance"]
    curr = "৳" if method=="bKash" else "$"
    context.user_data.update({"method": method, "price": price, "curr": curr})

    # bKash QR
    if method == "bKash" and BKASH_QR_FILE_ID:
        await q.message.reply_photo(
            photo=BKASH_QR_FILE_ID,
            caption=f"{context.user_data['cat']}\n\n"
                    f"Payment: *{method}*\n"
                    f"Price: {curr}{price} per account\n\n"
                    f"Scan QR or send to:\n"
                    f"`{BKASH_NUMBER}` (Personal)\n\n"
                    f"Enter quantity:",
            parse_mode="Markdown"
        )
        await q.message.delete()

    # Binance QR
    elif method == "Binance Pay" and BINANCE_QR_FILE_ID:
        await q.message.reply_photo(
            photo=BINANCE_QR_FILE_ID,
            caption=f"{context.user_data['cat']}\n\n"
                    f"Payment: *{method}*\n"
                    f"Price: {curr}{price} per account\n\n"
                    f"Scan QR with Binance App\n"
                    f"Binance Pay ID: `{BINANCE_ID}`\n\n"
                    f"Enter quantity:",
            parse_mode="Markdown"
        )
        await q.message.delete()

    # যদি কোনো QR না থাকে
    else:
        txt = f"{context.user_data['cat']}\n\nPayment: *{method}*\nPrice: {curr}{price}/acc\n\n"
        txt += f"Send to → `{BKASH_NUMBER if method=='bKash' else BINANCE_ID}`\n\nEnter quantity:"
        await q.edit_message_text(txt, parse_mode="Markdown")

    return QTY

# বাকি ফাংশন (qty → confirm → screenshot → txid → approve) আগের মতোই রাখো
# শুধু main() এর শেষে এই লাইনটা রাখো যাতে সবসময় রেসপন্স করে:
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("order", start)],
        states={
            CHOOSE_CAT: [CallbackQueryHandler(cat, pattern="^cat_")],
            PAYMENT:    [CallbackQueryHandler(payment, pattern="^pay_")],
            QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
            CONFIRM:    [CallbackHandler(confirm, pattern="^(ok|no)$")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot)],
            TXID:       [MessageHandler(filters.TEXT & ~filters.COMMAND, txid)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, excel))

    print("ULTRA PRO BOT WITH QR CODES IS ONLINE!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
