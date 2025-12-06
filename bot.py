# bot.py - Dual Category Bot: Hotmail/Outlook + .EDU Mail
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# CHANGE THESE
BOT_TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"
ADMIN_ID = 1651695602

# PRICING (You can change anytime)
PRICE_HOTMAIL_BKASH = 2.5      # Taka per Hotmail/Outlook
PRICE_HOTMAIL_BINANCE = 0.2 # USD

PRICE_EDU_BKASH = 2         # Taka per .EDU mail
PRICE_EDU_BINANCE = 0.016     # USD per .EDU mail

BKASH_NUMBER = "01815243007"
BINANCE_ID = "38017799"

BKASH_QR = None   # Put file_id if you have QR
BINANCE_QR = None

# States
CHOOSE_CATEGORY, SELECT_PAYMENT, QUANTITY, CONFIRM_ORDER, PAYMENT_SCREENSHOT, TRANSACTION_ID = range(6)

orders = {}
waiting_excel = {}

# START & CATEGORY SELECTION
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Hotmail/Outlook Accounts", callback_data="cat_hotmail")],
        [InlineKeyboardButton(".EDU Mail Accounts", callback_data="cat_edu")],
    ]
    await update.message.reply_text(
        "Welcome to Premium Accounts Shop\n\n"
        "Choose category:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cat_hotmail":
        context.user_data["category"] = "Hotmail/Outlook"
        context.user_data["price_bkash"] = PRICE_HOTMAIL_BKASH
        context.user_data["price_binance"] = PRICE_HOTMAIL_BINANCE
        title = "Hotmail/Outlook Accounts"
    else:
        context.user_data["category"] = ".EDU Mail"
        context.user_data["price_bkash"] = PRICE_EDU_BKASH
        context.user_data["price_binance"] = PRICE_EDU_BINANCE
        title = ".EDU Mail Accounts"

    keyboard = [
        [InlineKeyboardButton(f"bKash → ৳{context.user_data['price_bkash']}/acc", callback_data="pay_bkash")],
        [InlineKeyboardButton(f"Binance → ${context.user_data['price_binance']}/acc", callback_data="pay_binance")],
        [InlineKeyboardButton("Back", callback_data="back")],
    ]
    await query.edit_message_text(
        f"*{title}*\n\nChoose payment method:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_PAYMENT

async def select_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        await start(update, context)
        return CHOOSE_CATEGORY

    method = "bKash" if query.data == "pay_bkash" else "Binance Pay"
    context.user_data["method"] = method
    price = context.user_data["price_bkash"] if method == "bKash" else context.user_data["price_binance"]
    curr = "৳" if method == "bKash" else "$"
    context.user_data.update({"price": price, "curr": curr})

    text = f"*{context.user_data['category']}*\n"
    text += f"Payment: *{method}*\n"
    text += f"Price: {curr}{price} per account\n\n"

    if method == "bKash":
        text += f"Send to: `{BKASH_NUMBER}`\n"
        if BKASH_QR:
            await query.message.reply_photo(BKASH_QR, caption=text + "Enter quantity:", parse_mode="Markdown")
        else:
            await query.edit_message_text(text + "Enter quantity:", parse_mode="Markdown")
    else:
        text += f"Binance Pay ID: `{BINANCE_ID}`\n"
        if BINANCE_QR:
            await query.message.reply_photo(BINANCE_QR, caption=text + "Enter quantity:", parse_mode="Markdown")
        else:
            await query.edit_message_text(text + "Enter quantity:", parse_mode="Markdown")
    return QUANTITY

# Rest same as before (quantity → confirm → screenshot → txid)
async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text)
        if not 1 <= qty <= 3000:
            raise ValueError
        context.user_data["qty"] = qty
        total = qty * context.user_data["price"]

        await update.message.reply_text(
            f"*Order Summary*\n\n"
            f"Category: {context.user_data['category']}\n"
            f"Quantity: {qty}\n"
            f"Price: {context.user_data['curr']}{context.user_data['price']}/acc\n"
            f"*Total: {context.user_data['curr']}{total}*\n"
            f"Payment: {context.user_data['method']}\n\n"
            f"Confirm order?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Confirm", callback_data="confirm")],
                [InlineKeyboardButton("Cancel", callback_data="cancel")]
            ])
        )
        return CONFIRM_ORDER
    except:
        await update.message.reply_text("Enter valid number (1-3000)")
        return QUANTITY

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Order cancelled")
        return ConversationHandler.END

    order_id = str(uuid.uuid4())[:8].upper()
    total = context.user_data["qty"] * context.user_data["price"]

    orders[order_id] = {
        "user_id": update.effective_user.id,
        "username": update.effective_user.username or "User",
        "category": context.user_data["category"],
        "qty": context.user_data["qty"],
        "total": total,
        "curr": context.user_data["curr"],
        "method": context.user_data["method"],
        "status": "waiting_payment"
    }

    await query.edit_message_text(
        f"*Order Created!*\n"
        f"ID: `{order_id}`\n"
        f"{context.user_data['category']} × {context.user_data['qty']}\n"
        f"Total: {context.user_data['curr']}{total}\n\n"
        f"Send payment screenshot",
        parse_mode="Markdown"
    )

    await context.bot.send_message(ADMIN_ID,
        f"New {context.user_data['category']} Order!\n"
        f"ID: {order_id} | {context.user_data['qty']} × {context.user_data['curr']}{context.user_data['price']} = {context.user_data['curr']}{total}\n"
        f"@{orders[order_id]['username']}"
    )
    return PAYMENT_SCREENSHOT

# Screenshot & TXID (same logic)
async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("Send photo screenshot")
        return PAYMENT_SCREENSHOT
    file_id = update.message.photo[-1].file_id
    order_id = next((oid for oid, d in orders.items() if d["user_id"] == update.effective_user.id and d["status"] == "waiting_payment"), None)
    if not order_id:
        await update.message.reply_text("No active order")
        return ConversationHandler.END

    orders[order_id]["screenshot"] = file_id
    orders[order_id]["status"] = "waiting_txid"
    await update.message.reply_text("Screenshot saved!\nSend Transaction ID:")
    await context.bot.send_photo(ADMIN_ID, file_id, caption=f"Screenshot\n{order_id} | {orders[order_id]['category']}")
    return TRANSACTION_ID

async def get_txid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    txid = update.message.text.strip()
    order_id = next((oid for oid, d in orders.items() if d["user_id"] == update.effective_user.id and d["status"] == "waiting_txid"), None)
    if not order_id: return ConversationHandler.END

    orders[order_id]["txid"] = txid
    orders[order_id]["status"] = "pending_approval"

    await update.message.reply_text(f"Order `{order_id}` submitted!\nWaiting for approval...", parse_mode="Markdown")
    await context.bot.send_message(ADMIN_ID,
        f"{orders[order_id]['category']} Ready!\n"
        f"ID: {order_id}\nTXID: {txid}\n→ /approve {order_id}"
    )
    return ConversationHandler.END

# EASY APPROVE (Same as before)
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("Use: /approve ORDER_ID")
        return
    order_id = context.args[0].upper()
    if order_id not in orders or orders[order_id]["status"] != "pending_approval":
        await update.message.reply_text("Invalid order")
        return

    waiting_excel[ADMIN_ID] = order_id
    o = orders[order_id]
    await update.message.reply_text(
        f"Send Excel for:\n"
        f"Order: `{order_id}`\n"
        f"{o['category']} × {o['qty']} = {o['curr']}{o['total']}\n"
        f"Buyer: @{o['username']}",
        parse_mode="Markdown"
    )

async def receive_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting_excel:
        return
    order_id = waiting_excel.pop(ADMIN_ID)
    if not update.message.document or not update.message.document.file_name.lower().endswith('.xlsx'):
        await update.message.reply_text("Send .xlsx file")
        waiting_excel[ADMIN_ID] = order_id
        return

    await context.bot.send_document(
        orders[order_id]["user_id"],
        update.message.document.file_id,
        caption=f"Approved!\n{orders[order_id]['category']}\nOrder {order_id} × {orders[order_id]['qty']} accounts"
    )
    await update.message.reply_text(f"Excel sent | Order {order_id} done")
    del orders[order_id]

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = "*Pending*\n\n"
    for oid, o in orders.items():
        if o["status"] == "pending_approval":
            text += f"• `{oid}` | {o['category']} | {o['qty']} | {o['curr']}{o['total']}\n"
    await update.message.reply_text(text or "No pending", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("order", start)],
        states={
            CHOOSE_CATEGORY: [CallbackQueryHandler(choose_category)],
            SELECT_PAYMENT: [CallbackQueryHandler(select_payment)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order)],
            PAYMENT_SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            TRANSACTION_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_txid)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, receive_excel))

    print("Dual Category Bot Running | Hotmail + .EDU")
    app.run_polling()

if __name__ == "__main__":
    main()
