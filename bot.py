# bot.py → তোমার পুরানো কোডের ফাইনাল ফিক্সড ভার্সন (2025)
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

# ←←← শুধু এই লাইনগুলো বদলাবে ←←←
TOKEN      "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"       # ← তোমার টোকেন
ADMIN_ID = 1651695602                     # তোমার আইডি

# QR file_id (না থাকলে None রাখো)
BKASH_QR_FILE_ID   = AgACAgUAAxkBAAEZYCZpNOTLIbUSloBZxDaXKjCU3cL53QACcQtrG-QSqFVIuPQ_B-XJLAEAAwIAA3gAAzYE    # ← bKash QR এর file_id বসাও (থাকলে)
BINANCE_QR_FILE_ID = None    # ← Binance QR এর file_id বসাও (থাকলে)

BKASH   = "01815243007"
BINANCE = "38017799"
# ←←← এখানেই শেষ ←←←

# তোমার পুরানো প্রাইস
P = {
    "hotmail": {"bkash": 2.5,  "binance": 0.02},
    "edu":     {"bkash": 2,    "binance": 0.016}
}

CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)
orders = {}
waiting = {}

# মূল ফিক্স: যেকোনো সময় /start দিলে নতুন করে শুরু হবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()   # ← এটাই ম্যাজিক! পুরানো অর্ডার ক্লিয়ার
    kb = [
        [InlineKeyboardButton("Hotmail/Outlook Accounts", callback_data="cat_hotmail")],
        [InlineKeyboardButton(".EDU Mail Accounts",       callback_data="cat_edu")],
    ]
    await update.message.reply_text("Welcome to Mail Shop!\n\nChoose category:", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_CAT

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cat = "hotmail" if q.data == "cat_hotmail" else "edu"
    context.user_data["cat"] = "Hotmail/Outlook Accounts" if cat == "hotmail" else ".EDU Mail Accounts"
    context.user_data["key"] = cat

    kb = [
        [InlineKeyboardButton(f"bKash ৳{P[cat]['bkash']}/acc", callback_data="pay_bkash")],
        [InlineKeyboardButton(f"Binance ${P[cat]['binance']}/acc", callback_data="pay_binance")],
    ]
    await q.edit_message_text(f"*{context.user_data['cat']}*\n\nSelect payment method:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAYMENT

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = "bKash" if q.data == "pay_bkash" else "Binance Pay"
    price = P[context.user_data["key"]]["bkash" if method=="bKash" else "binance"]
    curr = "৳" if method=="bKash" else "$"
    context.user_data.update({"method": method, "price": price, "curr": curr})

    # ====== QR কোড যোগ করা হলো ======
    if method == "bKash" and BKASH_QR_FILE_ID:
        await q.message.reply_photo(
            photo=BKASH_QR_FILE_ID,
            caption=f"*{context.user_data['cat']}*\n\n"
                    f"Payment: *{method}*\n"
                    f"Price: {curr}{price} per account\n\n"
                    f"Scan QR or send to:\n`{BKASH}`\n\n"
                    f"Enter quantity:",
            parse_mode="Markdown"
        )
        await q.message.delete()
    elif method == "Binance Pay" and BINANCE_QR_FILE_ID:
        await q.message.reply_photo(
            photo=BINANCE_QR_FILE_ID,
            caption=f"*{context.user_data['cat']}*\n\n"
                    f"Payment: *{method}*\n"
                    f"Price: {curr}{price} per account\n\n"
                    f"Scan QR with Binance App\n"
                    f"Binance Pay ID: `{BINANCE}`\n\n"
                    f"Enter quantity:",
            parse_mode="Markdown"
        )
        await q.message.delete()
    else:
        txt = f"*{context.user_data['cat']}*\n\n"
        txt += f"Payment: *{method}*\n"
        txt += f"Price: {curr}{price} per account\n\n"
        txt += f"Send to: `{BKASH if method=='bKash' else BINANCE}`\n\n"
        txt += "Enter quantity:"
        await q.edit_message_text(txt, parse_mode="Markdown")
    return QTY

# বাকি সব ফাংশন তোমার পুরানো কোডের মতোই (কোনো বদল নাই)
async def qty(update: ...          # তোমার আগের মতো
async def confirm: ...          # তোমার আগের মতো
async def screenshot: ...       # তোমার আগের মতো
async def txid: ...             # তোমার আগের মতো
async def approve: ...          # তোমার আগের মতো
async def excel: ...            # তোমার আগের মতো

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start, CommandHandler("order", start)],
        states={
            CHOOSE_CAT: [CallbackQueryHandler(cat, pattern="^cat_")],
            PAYMENT:    [CallbackQueryHandler(payment, pattern="^pay_")],
            QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
            CONFIRM:    [CallbackQueryHandler(confirm, pattern="^(ok|no)$")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot)],
            TXID:       [MessageHandler(filters.TEXT & ~filters.COMMAND, txid)],
        },
        fallbacks=[],
        allow_reentry=True,   # ← এটাই গ্যারান্টি দেয় যে /start সবসময় কাজ করবে
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, excel))

    print("Bot is ONLINE! /start দিয়ে চেক করো")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
