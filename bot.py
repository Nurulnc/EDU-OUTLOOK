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

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- কনফিগারেশন ---
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA" # এটি পরে এনভায়রনমেন্ট ভেরিয়েবলে নিয়ে নেবেন
ADMIN_ID = 1651695602
BKASH = "01815243007"
BINANCE = "38017799"

PRODUCTS = {
    "hotmail_trust": {"name": "📬 Hotmail Trust", "bkash": 2, "binance": 0.016, "type": "mail"},
    "edu":           {"name": "🎓 .EDU Mail (US)", "bkash": 1, "binance": 0.008, "type": "mail"},
    "android":       {"name": "📩 Android Studio Mail", "bkash": 5, "binance": 0.04, "type": "mail"},
    "outlook_trust": {"name": "📧 Outlook Trust", "bkash": 2, "binance": 0.016, "type": "mail"},
    "hma_vpn":       {"name": "🔒 HMA VPN (7 দিন)", "bkash": 30, "binance": 0.24, "type": "vpn"},
    "nord_vpn":      {"name": "🔒 Nord VPN (7 দিন)", "bkash": 30, "binance": 0.24, "type": "vpn"},
    "express_vpn":   {"name": "🔒 Express VPN (7 দিন)", "bkash": 30, "binance": 0.24, "type": "vpn"},
}

# States
CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)
orders = {}
waiting = {}

# --- ইউটিলিটি ফাংশন ---
def get_main_menu():
    buttons = [[InlineKeyboardButton(info["name"], callback_data=f"cat_{key}")] for key, info in PRODUCTS.items()]
    return InlineKeyboardMarkup(buttons)

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *স্বাগতম আমাদের শপে!*\n\n"
        "এখানে আপনি প্রিমিয়াম মেইল এবং ভিপিএন পাবেন সবথেকে সাশ্রয়ী মূল্যে।\n\n"
        "🛒 *অর্ডার করতে নিচের যেকোনো একটি সার্ভিস বেছে নিন:* "
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    else:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    return CHOOSE_CAT

async def cat_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    cat_key = query.data.replace("cat_", "")
    product = PRODUCTS[cat_key]
    context.user_data.update({"key": cat_key, "name": product["name"]})

    text = (
        f"✨ *সার্ভিস:* {product['name']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *মূল্য তালিকা:*\n"
        f"🔸 বিকাশ: {product['bkash']} BDT /পিস\n"
        f"🔸 বিনান্স: ${product['binance']} /পিস\n\n"
        f"💳 *পেমেন্ট মেথড বেছে নিন:* "
    )
    
    kb = [
        [InlineKeyboardButton("💳 বিকাশ (Bkash)", callback_data="pay_bkash")],
        [InlineKeyboardButton("💳 বিনান্স (Binance)", callback_data="pay_binance")],
        [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_start")]
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAYMENT

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_start":
        return await start(update, context)

    method = "বিকাশ" if query.data == "pay_bkash" else "বিনান্স পে"
    key = context.user_data["key"]
    price = PRODUCTS[key]["bkash" if "bkash" in query.data else "binance"]
    currency = "৳" if "bkash" in query.data else "$"
    
    context.user_data.update({"method": method, "price": price, "curr": currency})

    instr = f"📍 *পেমেন্ট ডিটেইলস ({method})*\n━━━━━━━━━━━━━━━━━━\n"
    if "bkash" in query.data:
        instr += f"📞 নম্বর: `{BKASH}` (Send Money)\n"
    else:
        instr += f"🆔 বিনান্স আইডি: `{BINANCE}`\n"
    
    instr += f"\n💵 রেট: {currency}{price} প্রতি অ্যাকাউন্ট\n"
    instr += "━━━━━━━━━━━━━━━━━━\n"
    instr += "✍️ *আপনি কয়টি অ্যাকাউন্ট নিতে চান?* (শুধু সংখ্যাটি লিখুন)"

    await query.edit_message_text(instr, parse_mode="Markdown")
    return QTY

async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text)
        if qty < 1: raise ValueError
        
        context.user_data["qty"] = qty
        total = round(qty * context.user_data["price"], 3)
        context.user_data["total"] = total

        summary = (
            f"📝 *অর্ডারের বিবরণ*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 পণ্য: {context.user_data['name']}\n"
            f"🔢 পরিমাণ: {qty} টি\n"
            f"💳 মেথড: {context.user_data['method']}\n"
            f"💰 মোট দেয়: {context.user_data['curr']}{total}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ আপনি কি এই অর্ডারটি নিশ্চিত করতে চান?"
        )
        
        kb = [[InlineKeyboardButton("✅ হ্যাঁ, নিশ্চিত", callback_data="confirm_ok")],
              [InlineKeyboardButton("❌ বাতিল", callback_data="back_to_start")]]
        
        await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return CONFIRM
    except ValueError:
        await update.message.reply_text("❌ ভুল ইনপুট! দয়া করে শুধু সংখ্যা লিখুন (উদা: 5)")
        return QTY

async def process_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    oid = str(uuid4())[:8].upper()
    context.user_data["oid"] = oid
    
    await query.edit_message_text(
        f"🚀 *অর্ডার আইডি:* `{oid}`\n\n"
        f"ধন্যবাদ! এখন পেমেন্ট সম্পন্ন করে তার একটি *স্ক্রিনশট* এখানে পাঠান।",
        parse_mode="Markdown"
    )
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ দয়া করে পেমেন্টের স্ক্রিনশট (ছবি) পাঠান।")
        return SCREENSHOT
    
    photo_id = update.message.photo[-1].file_id
    oid = context.user_data["oid"]
    
    # স্টোর অর্ডার
    orders[oid] = {**context.user_data, "uid": update.effective_user.id, "username": update.effective_user.username}
    
    await update.message.reply_text("✅ স্ক্রিনশট পাওয়া গেছে। এখন পেমেন্টের *Transaction ID (TrxID)* লিখে পাঠান:")
    
    # অ্যাডমিনকে জানানো
    admin_msg = (
        f"🔔 *নতুন অর্ডার এসেছে!* ({oid})\n"
        f"👤 ইউজার: @{orders[oid]['username']}\n"
        f"📦 পণ্য: {orders[oid]['name']}\n"
        f"💰 মোট: {orders[oid]['curr']}{orders[oid]['total']}"
    )
    await context.bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, parse_mode="Markdown")
    return TXID

async def get_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    oid = context.user_data["oid"]
    
    await update.message.reply_text(
        f"✅ *অর্ডার জমা হয়েছে!*\n\n"
        f"আপনার অর্ডার আইডি: `{oid}`\n"
        f"অ্যাডমিন ভেরিফাই করে কিছুক্ষণের মধ্যে ফাইল পাঠিয়ে দেবে। ধৈর্য ধরুন।",
        parse_mode="Markdown"
    )
    
    await context.bot.send_message(
        ADMIN_ID, 
        f"💸 *TrxID জমা পড়েছে!*\nID: `{oid}`\nTrxID: `{txid}`\n\nঅনুমোদন করতে: `/approve {oid}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# --- অ্যাডমিন কমান্ড ---
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: /approve ORDER_ID")
        return

    oid = context.args[0].upper()
    if oid not in orders:
        await update.message.reply_text("❌ এই আইডি দিয়ে কোনো অর্ডার পাওয়া যায়নি।")
        return
    
    waiting[ADMIN_ID] = oid
    await update.message.reply_text(f"📁 অর্ডার `{oid}` এর জন্য এক্সেল/সিএসভি ফাইলটি পাঠান।", parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting:
        return
    
    oid = waiting.pop(ADMIN_ID)
    order_info = orders.get(oid)
    
    if not order_info: return

    try:
        await context.bot.send_document(
            chat_id=order_info["uid"],
            document=update.message.document.file_id,
            caption=(
                f"✅ *আপনার অর্ডার ডেলিভারি করা হয়েছে!*\n\n"
                f"🆔 অর্ডার আইডি: `{oid}`\n"
                f"📦 পণ্য: {order_info['name']}\n"
                f"🙏 আমাদের থেকে কেনার জন্য ধন্যবাদ।"
            ),
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ অর্ডার `{oid}` সফলভাবে ডেলিভারি করা হয়েছে।")
        del orders[oid]
    except Exception as e:
        await update.message.reply_text(f"❌ ভুল হয়েছে: {str(e)}")

# --- মেইন ফাংশন ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_CAT: [CallbackQueryHandler(cat_selection, pattern="^cat_")],
            PAYMENT:    [CallbackQueryHandler(payment_method, pattern="^pay_"), CallbackQueryHandler(start, pattern="back_to_start")],
            QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            CONFIRM:    [CallbackQueryHandler(process_confirm, pattern="confirm_ok"), CallbackQueryHandler(start, pattern="back_to_start")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            TXID:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_txid)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("approve", approve_order))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("🤖 বট সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
