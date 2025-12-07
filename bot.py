# bot.py → তোমার পুরানো কোডের ফাইনাল + QR + Always /start works
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

# ←←← শুধু এই লাইনগুলো চেক করো ←←←
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"
ADMIN_ID = 1651695602

# ←←← QR চাইলে এখানে file_id বসাও (না থাকলে None রাখো) ←←←
BKASH_QR_FILE_ID   = AgACAgUAAxkBAAEZYCZpNOTLIbUSloBZxDaXKjCU3cL53QACcQtrG-QSqFVIuPQ_B-XJLAEAAwIAA3gAAzYE   # উদা: "AgACAgUAAxkBAAIB9WcAAf..."
BINANCE_QR_FILE_ID = AgACAgUAAxkBAAEZYD5pNPTN-OxDfgLAYhcyp4b6X3qJkAACRQtrG3d3qVXctWMRQ9uzrQEAAwIAA3gAAzYE   # উদা: "AgACAgUAAxkBAAIB9mcAAf..."

BKASH   = "01815243007"
BINANCE = "38017799"

# তোমার পুরানো প্রাইস
P = {
    "hotmail": {"bkash": 2.5,  "binance": 0.02},
    "edu":     {"bkash": 2,    "binance": 0.016}
}

CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)
orders = {}
waiting = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # এটাই ম্যাজিক → যেকোনো সময় /start কাজ করবে
    kb = [
        [InlineKeyboardButton("Hotmail/Outlook", callback_data="cat_hotmail")],
        [InlineKeyboardButton(".EDU Mail",       callback_data="cat_edu")],
    ]
    await update.message.reply_text("Welcome!\nChoose category:", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_CAT

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cat = "hotmail" if q.data == "cat_hotmail" else "edu"
    context.user_data["cat"] = "Hotmail/Outlook" if cat == "hotmail" else ".EDU Mail"
    context.user_data["key"] = cat

    kb = [
        [InlineKeyboardButton(f"bKash ৳{P[cat]['bkash']}", callback_data="pay_bkash")],
        [InlineKeyboardButton(f"Binance ${P[cat]['binance']}", callback_data="pay_binance")],
    ]
    await q.edit_message_text(f"*{context.user_data['cat']}*\nSelect payment:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAYMENT

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = "bKash" if q.data == "pay_bkash" else "Binance Pay"
    price = P[context.user_data["key"]]["bkash" if method=="bKash" else "binance"]
    curr = "৳" if method=="bKash" else "$"
    context.user_data.update({"method": method, "price": price, "curr": curr})

    # ============ QR কোড যোগ করা হয়েছে ============
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
        txt = f"*{context.user_data['cat']}*\n"
        txt += f"Payment: {method} → {curr}{price}/acc\n\n"
        txt += f"Send to: `{BKASH if method=='bKash' else BINANCE}`\n\n"
        txt += "Enter quantity:"
        await q.edit_message_text(txt, parse_mode="Markdown")
    # =================================================
    return QTY

# বাকি সব ফাংশন তোমার পুরানো মতোই (কোনো বদল নাই)
async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = int(update.message.text)
        if not 1 <= q <= 2000:
            raise ValueError
        context.user_data["qty"] = q
        total = q * context.user_data["price"]
        kb = [[InlineKeyboardButton("Confirm", callback_data="ok")], [InlineKeyboardButton("Cancel", callback_data="no")]]
        await update.message.reply_text(
            f"*Summary*\n\n{context.user_data['cat']}\nQty: {q}\nTotal: {context.user_data['curr']}{total}\n\nConfirm?",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
        )
        return CONFIRM
    except:
        await update.message.reply_text("1-2000 এর মধ্যে নাম্বার দাও")
        return QTY

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "no":
        await q.edit_message_text("Cancelled")
        return ConversationHandler.END

    oid = str(uuid4())[:8].upper()
    orders[oid] = {**context.user_data, "uid": update.effective_user.id, "user": update.effective_user.username or "User"}
    await q.edit_message_text(f"Order ID: `{oid}`\nSend payment screenshot", parse_mode="Markdown")
    await context.bot.send_message(ADMIN_ID, f"New Order {oid}\n{context.user_data['cat']} × {context.user_data['qty']} = {context.user_data['curr']}{context.user_data['qty']*context.user_data['price']}\nUser: @{orders[oid]['user']}")
    return SCREENSHOT

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Photo পাঠাও")
        return SCREENSHOT
    pid = update.message.photo[-1].file_id
    oid = [k for k,v in orders.items() if v["uid"]==update.effective_user.id][-1]
    orders[oid]["shot"] = pid
    await update.message.reply_text("Send Transaction ID:")
    await context.bot.send_photo(ADMIN_ID, pid, caption=f"Screenshot → {oid}")
    return TXID

async def txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.message.text.strip()
    oid = [k for k,v in orders.items() if v["uid"]==update.effective_user.id][-1]
    orders[oid]["tx"] = tid
    await update.message.reply_text(f"Order {oid} submitted!\nWaiting approval...")
    await context.bot.send_message(ADMIN_ID, f"Ready!\nID: {oid}\nTXID: {tid}\n→ /approve {oid}")
    return ConversationHandler.END

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        oid = context.args[0].upper()
        waiting[ADMIN_ID] = oid
        await update.message.reply_text(f"Send .xlsx file for {oid}")
    except:
        await update.message.reply_text("Use: /approve ABC123")

async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting: return
    oid = waiting.pop(ADMIN_ID)
    if not update.message.document or not update.message.document.file_name.endswith(".xlsx"):
        await update.message.reply_text("Only .xlsx")
        waiting[ADMIN_ID] = oid
        return
    await context.bot.send_document(orders[oid]["uid"], update.message.document.file_id,
        f"Approved!\n{orders[oid]['cat']}\n{oid} × {orders[oid]['qty']} accounts")
    await update.message.reply_text(f"Sent → {oid}")
    del orders[oid]

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("order", start)],
        states={
            CHOOSE_CAT: [CallbackQueryHandler(cat, pattern="^cat_")],
            PAYMENT:    [CallbackQueryHandler(payment, pattern="^pay_")],
            QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
            CONFIRM:    [CallbackQueryHandler(confirm, pattern="^(ok|no)$")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot)],
            TXID:       [MessageHandler(filters.TEXT & ~filters.COMMAND, txid)],
        },
        fallbacks=[],
        allow_reentry=True   # ← এটাই গ্যারান্টি যে /start সবসময় কাজ করবে
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, excel))

    print("Bot is ONLINE & ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
