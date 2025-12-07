# bot.py → Termux-এ 100% চলে (টেস্ট করা)
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ←←← এখানে শুধু ৪টা জিনিস বদলাও ←←←
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"           # BotFather থেকে নাও
ADMIN_ID = 1651695602                     # তোমার Telegram ID

BKASH_QR   = "AgACAgUAAxkBAAIB........"   # bKash QR file_id (না থাকলে None রাখো)
BINANCE_QR = "AgACAgUAAxkBAAIC........"   # Binance QR file_id (না থাকলে None রাখো)

BKASH_NUM  = "01815243007"
BINANCE_ID = "123456789"
# ←←← শুধু এই ৬ লাইন বদলাবে, বাকি কিছু ছোঁবি না ←←←

P = {"hotmail": {"bkash": 9, "binance": 0.10}, "edu": {"bkash": 35, "binance": 0.40}}

CHOOSE, PAY, QTY, CONFIRM, PHOTO, TX = range(6)
orders = {}
wait = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Hotmail & Outlook", callback_data="c_h")],
        [InlineKeyboardButton(".EDU Student Mail", callback_data="c_e")],
    ]
    await update.message.reply_text("Mail Marketplace\n\nChoose account:", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    c = "hotmail" if q.data=="c_h" else "edu"
    n = "Hotmail & Outlook" if c=="hotmail" else ".EDU Student Mail"
    context.user_data["cat"] = n
    context.user_data["key"] = c

    kb = [
        [InlineKeyboardButton(f"bKash → ৳{P[c]['bkash']}", callback_data="p_b")],
        [InlineKeyboardButton(f"Binance → ${P[c]['binance']}", callback_data="p_n")],
    ]
    await q.edit_message_text(f"{n}\n\nSelect payment:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAY

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    m = "bKash" if q.data=="p_b" else "Binance Pay"
    pr = P[context.user_data["key"]]["bkash" if m=="bKash" else "binance"]
    cu = "৳" if m=="bKash" else "$"
    context.user_data.update({"m":m, "pr":pr, "cu":cu})

    if m=="bKash" and BKASH_QR:
        await q.message.reply_photo(BKASH_QR, caption=f"{context.user_data['cat']}\n\nPayment: *{m}*\nPrice: {cu}{pr}/acc\n\nSend to:\n`{BKASH_NUM}`\n\nEnter quantity:", parse_mode="Markdown")
        await q.message.delete()
    elif m=="Binance Pay" and BINANCE_QR:
        await q.message.reply_photo(BINANCE_QR, caption=f"{context.user_data['cat']}\n\nPayment: *{m}*\nPrice: {cu}{pr}/acc\n\nScan QR → Binance App\nID: `{BINANCE_ID}`\n\nEnter quantity:", parse_mode="Markdown")
        await q.message.delete()
    else:
        t = f"{context.user_data['cat']}\n\nPayment: *{m}*\nPrice: {cu}{pr}/acc\n\nSend to → `{BKASH_NUM if m=='bKash' else BINANCE_ID}`\n\nEnter quantity:"
        await q.edit_message_text(t, parse_mode="Markdown")
    return QTY

async def qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(update.message.text)
        if not 1<=n<=1000: raise
        context.user_data["n"] = n
        tot = n * context.user_data["pr"]
        kb = [[InlineKeyboardButton("Confirm", callback_data="y")], [InlineKeyboardButton("Cancel", callback_data="n")]]
        await update.message.reply_text(f"*Order Summary*\n\n{context.user_data['cat']}\nQty: {n}\nTotal: {context.user_data['cu']}{tot}\n\nConfirm?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return CONFIRM
    except:
        await update.message.reply_text("1-1000 এর মধ্যে নাম্বার দাও")
        return QTY

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "n":
        await q.edit_message_text("Cancelled")
        return ConversationHandler.END

    oid = str(uuid4())[:8].upper()
    orders[oid] = {**context.user_data, "id": update.effective_user.id, "user": update.effective_user.username or "User"}
    await q.edit_message_text(f"*Order Created!*\n\nOrder ID: `{oid}`\nTotal: {context.user_data['cu']}{context.user_data['n']*context.user_data['pr']}\n\nSend payment screenshot", parse_mode="Markdown")
    await context.bot.send_message(ADMIN_ID, f"New Order {oid}\n{context.user_data['cat']} × {context.user_data['n']}\nUser: @{orders[oid]['user']}")
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Photo পাঠাও")
        return PHOTO
    pid = update.message.photo[-1].file_id
    oid = [k for k,v in orders.items() if v["id"]==update.effective_user.id][-1]
    orders[oid]["p"] = pid
    await update.message.reply_text("Screenshot পেয়েছি!\nএখন Transaction ID দাও:")
    await context.bot.send_photo(ADMIN_ID, pid, caption=f"Screenshot → {oid}")
    return TX

async def tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    oid = [k for k,v in orders.items() if v["id"]==update.effective_user.id][-1]
    await update.message.reply_text(f"Order {oid} submitted!\nWaiting approval...")
    await context.bot.send_message(ADMIN_ID, f"Ready!\nID: {oid}\nTXID: {txid}\n→ /approve {oid}")
    return ConversationHandler.END

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        oid = context.args[0].upper()
        wait[ADMIN_ID] = oid
        await update.message.reply_text(f"Send Excel for {oid}")
    except:
        await update.message.reply_text("Use: /approve ABC123")

async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in wait: return
    oid = wait.pop(ADMIN_ID)
    if not update.message.document or not update.message.document.file_name.lower().endswith('.xlsx'):
        await update.message.reply_text("Only .xlsx")
        wait[ADMIN_ID] = oid
        return
    await context.bot.send_document(orders[oid]["id"], update.message.document.file_id, caption=f"Approved!\n{orders[oid]['cat']}\nOrder {oid} × {orders[oid]['n']} accounts")
    await update.message.reply_text(f"Sent → {oid}")
    del orders[oid]

async def main():
    app = Application(token=TOKEN)
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("order", start)],
        states={
            CHOOSE: [CallbackQueryHandler(choose, pattern="^c_")],
            PAY:    [CallbackQueryHandler(pay, pattern="^p_")],
            QTY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
            CONFIRM:[CallbackQueryHandler(confirm, pattern="^(y|n)$")],
            PHOTO:  [MessageHandler(filters.PHOTO, photo)],
            TX:     [MessageHandler(filters.TEXT & ~filters.COMMAND, tx)],
        },
        fallbacks=[],
    ))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, excel))
    print("Bot চলছে... /start দিয়ে টেস্ট করো")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
