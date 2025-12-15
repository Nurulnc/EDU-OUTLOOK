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

# Price (নতুন ক্যাটাগরি যোগ করা হয়েছে)
P = {
    "hotmail_trust": {"bkash": 2,    "binance": 0.016},
    "edu":           {"bkash": 1,  "binance": 0.008},
    "android":       {"bkash": 5,    "binance": 0.04},
    "outlook_trust": {"bkash": 2,    "binance": 0.016},
    "hma_vpn":       {"bkash": 30,   "binance": 0.24},   # নতুন
    "nord_vpn":      {"bkash": 30,   "binance": 0.24},   # নতুন
    "express_vpn":   {"bkash": 30,   "binance": 0.24},   # নতুন
}

BKASH = "01815243007"
BINANCE = "38017799"

# States
CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)

orders = {}
waiting = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📬 Hotmail Trust", callback_data="cat_hotmail_trust")],
        [InlineKeyboardButton("🎓 .EDU Mail (US)",     callback_data="cat_edu")],
        [InlineKeyboardButton("📩 Android Studio Mail", callback_data="cat_android")],
        [InlineKeyboardButton("📧 Outlook Trust", callback_data="cat_outlook_trust")],
        [InlineKeyboardButton("🔒 HMA VPN (7 days)", callback_data="cat_hma_vpn")],         # নতুন
        [InlineKeyboardButton("🔒 Nord VPN (7 days)", callback_data="cat_nord_vpn")],       # নতুন
        [InlineKeyboardButton("🔒 Express VPN (7 days)", callback_data="cat_express_vpn")], # নতুন
    ]
    await update.message.reply_text("Welcome!\nChoose category:", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_CAT

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    category_map = {
        "cat_hotmail_trust": ("hotmail_trust", "Hotmail Trust"),
        "cat_edu": ("edu", ".EDU Mail"),
        "cat_android": ("android", "Android Studio Mail"),
        "cat_outlook_trust": ("outlook_trust", "Outlook Trust"),
        "cat_hma_vpn": ("hma_vpn", "HMA VPN"),
        "cat_nord_vpn": ("nord_vpn", "Nord VPN"),
        "cat_express_vpn": ("express_vpn", "Express VPN"),
    }
    
    if q.data not in category_map:
        return  # invalid
    
    cat_key, cat_name = category_map[q.data]
    
    context.user_data["cat"] = cat_name
    context.user_data["key"] = cat_key
    
    # VPN হলে duration যোগ করি (শুধু display এর জন্য)
    is_vpn = cat_key.endswith("_vpn")
    duration_text = "\nDuration: 7 days" if is_vpn else ""

    kb = [
        [InlineKeyboardButton(f"bKash ৳{P[cat_key]['bkash']}", callback_data="pay_bkash")],
        [InlineKeyboardButton(f"Binance ${P[cat_key]['binance']}", callback_data="pay_binance")],
    ]
    await q.edit_message_text(f"*{cat_name}*{duration_text}\nSelect payment:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAYMENT

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = "bKash" if q.data == "pay_bkash" else "Binance Pay"
    price = P[context.user_data["key"]]["bkash" if method=="bKash" else "binance"]
    curr = "৳" if method=="bKash" else "$"
    context.user_data.update({"method": method, "price": price, "curr": curr})

    is_vpn = context.user_data["key"].endswith("_vpn")
    duration_text = "\nDuration: 7 days" if is_vpn else ""

    txt = f"*{context.user_data['cat']}*{duration_text}\n"
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
        
        is_vpn = context.user_data["key"].endswith("_vpn")
        duration_text = "\nDuration: 7 days" if is_vpn else ""
        
        kb = [[InlineKeyboardButton("Confirm", callback_data="ok")], [InlineKeyboardButton("Cancel", callback_data="no")]]
        await update.message.reply_text(
            f"*Summary*\n\n{context.user_data['cat']}{duration_text}\nQty: {q}\nTotal: {context.user_data['curr']}{total}\n\nConfirm?",
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
    
    is_vpn = context.user_data["key"].endswith("_vpn")
    duration_text = "\nDuration: 7 days" if is_vpn else ""
    
    await q.edit_message_text(f"Order ID: `{oid}`\nSend payment screenshot", parse_mode="Markdown")
    await context.bot.send_message(ADMIN_ID, f"New Order {oid}\n{context.user_data['cat']} × {context.user_data['qty']} = {context.user_data['curr']}{context.user_data['qty']*context.user_data['price']}{duration_text}\nUser: @{orders[oid]['user']}")
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
        await update.message.reply_text(f"Send .xlsx or .csv file for {oid}")
    except:
        await update.message.reply_text("Use: /approve ABC123")

async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting:
        return
    
    oid = waiting.pop(ADMIN_ID)
    
    if not update.message.document or not update.message.document.file_name.lower().endswith(('.xlsx', '.csv')):
        await update.message.reply_text("Only .xlsx or .csv file allowed!")
        waiting[ADMIN_ID] = oid
        return
    
    file_ext = ".CSV" if update.message.document.file_name.lower().endswith('.csv') else ".XLSX"
    
    is_vpn = orders[oid]["key"].endswith("_vpn")
    duration_text = "\nDuration: 7 days" if is_vpn else ""
    
    await context.bot.send_document(
        orders[oid]["uid"],
        update.message.document.file_id,
        caption=f"Approved!{duration_text}\n"
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
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot)],
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
