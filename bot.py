from uuid import uuid4
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton as B
from telegram.ext import Application, CommandHandler, CallbackQueryHandler as Q, MessageHandler as M, filters, ContextTypes, ConversationHandler

TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"          # ← এটা বদলাও
ADMIN = 1651695602                       # ← তোমার ID
BKASH_NUM = "01815243007"
BINANCE_ID = "123456789"
BKASH_QR = AgACAgUAAxkBAAEZYCZpNOTLIbUSloBZxDaXKjCU3cL53QACcQtrG-QSqFVIuPQ_B-XJLAEAAwIAA3gAAzYE   # QR থাকলে file_id দাও, না থাকলে None
BINANCE_QR = None

P = {"h":{"b":9,"n":0.10},"e":{"b":35,"n":0.40}}
(CAT,PAY,QTY,CFM,PH,TX) = range(6)
orders,wait={},{}

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # যেকোনো সময় /start দিলে পুরানো সেশন ক্লিয়ার
    c.user_data.clear()
    await u.message.reply_text("Mail Marketplace\n\nChoose account:",
        reply_markup=InlineKeyboardMarkup([
            [B("Hotmail & Outlook", callback_data="h")],
            [B(".EDU Student Mail", callback_data="e")]
        ]))
    return CAT

async def cat(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    k = q.data
    name = "Hotmail & Outlook" if k=="h" else ".EDU Student Mail"
    c.user_data["name"] = name
    c.user_data["key"] = k
    await q.edit_message_text(f"{name}\n\nPayment method:",
        reply_markup=InlineKeyboardMarkup([
            [B(f"bKash → ৳{P[k]['b']}", callback_data="b")],
            [B(f"Binance → ${P[k]['n']}", callback_data="n")]
        ]))
    return PAY

async def pay(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    m = "bKash" if q.data=="b" else "Binance Pay"
    pr = P[c.user_data["key"]][q.data]
    cu = "৳" if q.data=="b" else "$"
    c.user_data.update({"m":m, "pr":pr, "cu":cu})

    if q.data=="b" and BKASH_QR:
        await q.message.reply_photo(BKASH_QR, caption=f"{c.user_data['name']}\n\n*{m}*\n{cu}{pr}/acc\n\nSend to: `{BKASH_NUM}`\n\nQuantity:", parse_mode="Markdown")
        await q.message.delete()
    elif q.data=="n" and BINANCE_QR:
        await q.message.reply_photo(BINANCE_QR, caption=f"{c.user_data['name']}\n\n*{m}*\n{cu}{pr}/acc\n\nScan QR\nID: `{BINANCE_ID}`\n\nQuantity:", parse_mode="Markdown")
        await q.message.delete()
    else:
        await q.edit_message_text(f"{c.user_data['name']}\n\n*{m}*\n{cu}{pr}/acc\n\nSend to → `{BKASH_NUM if q.data=='b' else BINANCE_ID}`\n\nQuantity:", parse_mode="Markdown")
    return QTY

async def qty(u: Update, c: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(u.message.text)
        if not 1<=n<=1000: raise ValueError
        c.user_data["qty"] = n
        total = n * c.user_data["pr"]
        await u.message.reply_text(f"*Order Summary*\n\n{c.user_data['name']}\nQty: {n}\nTotal: {c.user_data['cu']}{total}\n\nConfirm?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[B("Confirm",callback_data="y")],[B("Cancel",callback_data="n")]]))
        return CFM
    except:
        await u.message.reply_text("1-1000 এর মধ্যে দাও")
        return QTY

async def cfm(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    if q.data == "n":
        c.user_data.clear()
        await q.edit_message_text("Order cancelled")
        return ConversationHandler.END

    oid = str(uuid4())[:8].upper()
    orders[oid] = {"data":c.user_data.copy(), "uid":u.effective_user.id}
    await q.edit_message_text(f"*Order Created!*\n\nOrder ID: `{oid}`\nTotal: {c.user_data['cu']}{c.user_data['qty']*c.user_data['pr']}\n\nSend payment screenshot", parse_mode="Markdown")
    await c.bot.send_message(ADMIN, f"New Order {oid}\n{c.user_data['name']} × {c.user_data['qty']}")
    return PH

async def ph(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message.photo:
        await u.message.reply_text("Screenshot পাঠাও")
        return PH
    pid = u.message.photo[-1].file_id
    oid = [k for k,v in orders.items() if v["uid"]==u.effective_user.id][-1]
    await u.message.reply_text("Transaction ID দাও")
    await c.bot.send_photo(ADMIN, pid, caption=f"Screenshot → {oid}")
    return TX

async def tx(u: Update, c: ContextTypes.DEFAULT_TYPE):
    txid = u.message.text.strip()
    oid = [k for k,v in orders.items() if v["uid"]==u.effective_user.id][-1]
    await u.message.reply_text(f"Order `{oid}` submitted!\nWaiting for approval...")
    await c.bot.send_message(ADMIN, f"Ready!\nID: {oid}\nTXID: {txid}\n→ /approve {oid}")
    return ConversationHandler.END

async def approve(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN: return
    try:
        oid = c.args[0].upper()
        wait[ADMIN] = oid
        await u.message.reply_text(f"Send .xlsx file for {oid}")
    except:
        await u.message.reply_text("Use: /approve ABC123")

async def excel(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != ADMIN or ADMIN not in wait: return
    oid = wait.pop(ADMIN)
    if not u.message.document or not u.message.document.file_name.lower().endswith('.xlsx'):
        await u.message.reply_text("Only .xlsx file")
        wait[ADMIN] = oid
        return
    await c.bot.send_document(orders[oid]["uid"], u.message.document.file_id, caption=f"Approved!\nOrder {oid}\n{orders[oid]['data']['name']}")
    await u.message.reply_text(f"Delivered → {oid}")
    del orders[oid]

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start",start), CommandHandler("order",start)],
        states={
            CAT: [Q(cat, pattern="^[he]$")],
            PAY: [Q(pay, pattern="^[bn]$")],
            QTY: [M(filters.TEXT & ~filters.COMMAND, qty)],
            CFM: [Q(cfm, pattern="^[yn]$")],
            PH:  [M(filters.PHOTO, ph)],
            TX:  [M(filters.TEXT & ~filters.COMMAND, tx)],
        },
        fallbacks=[],
        allow_reentry=True,   # ← এটাই ম্যাজিক! যেকোনো সময় /start কাজ করবে
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(M(filters.Document.ALL, excel))
    app.run_polling(drop_pending_updates=True)

if __name__name__ == "__main__":
    main()
