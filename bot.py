# bot.py  →  Super Clean & Guaranteed Working (2025)
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
print("Bot is starting...")  # এটা দেখলে বুঝবে কোড রান হচ্ছে

# তোমার ডাটা এখানে বসাও
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"        # BotFather থেকে নাও
ADMIN_ID = 1651695602                  # তোমার Telegram ID

# Price
P = {
    "hotmail": {"bkash": 2,   "binance": 0.016},
    "edu":     {"bkash": 1.6,  "binance": 0.013}
}

BKASH = "01815243007"
BINANCE = "38017799"

# States
CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)

orders = {}
waiting = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    txt = f"*{context.user_data['cat']}*\n"
    txt += f"Payment: {method} → {curr}{price}/acc\n\n"
    if method == "bKash":
        txt += f"Send to: `{BKASH}`\n"
    else:
        txt += f"Binance ID: `{BINANCE}`\n"
    txt += "\nEnter quantity:"

    await q.edit_message_text(txt, parse_mode="Markdown")
    return QTY

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

# Admin approve
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        oid = context.args[0].upper()
        waiting[ADMIN_ID] = oid
        await update.message.reply_text(f"Send .xlsx file for {oid}")
    except:
        await update.message.reply_text("Use: /approve ABC123")

async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting:
        return
    
    oid = waiting.pop(ADMIN_ID)
    
    # ←←← এই লাইনটাই বদলেছি (এখন .xlsx আর .csv দুটোই গ্রহণ করবে) ←←←
    if not update.message.document or not update.message.document.file_name.lower().endswith(('.xlsx', '.csv')):
        await update.message.reply_text("Only .xlsx or .csv file allowed!")
        waiting[ADMIN_ID] = oid
        return
    
    # বায়ারকে পাঠানোর সময় ফাইলের নাম দেখিয়ে দেবে
    file_ext = ".CSV" if update.message.document.file_name.lower().endswith('.csv') else ".XLSX"
    
    await context.bot.send_document(
        orders[oid]["uid"],
        update.message.document.file_id,
        caption=f"Approved!\n"
                f"{orders[oid]['cat']}\n"
                f"Order {oid} × {orders[oid]['qty']} accounts\n\n"
                f"File attached ({file_ext})"
    )
    await update.message.reply_text(f"Sent → {oid} ({file_ext})")
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
            SCREENSHOT:  [MessageHandler(filters.PHOTO, screenshot)],
            TXID:       [MessageHandler(filters.TEXT & ~filters.COMMAND, txid)],
        },
        fallbacks=[],
    allow_reentry=True)

    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, excel))

    print("Bot is ONLINE & ready!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
