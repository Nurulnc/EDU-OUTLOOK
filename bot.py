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
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"
ADMIN_ID = 1651695602
BKASH = "01815243007"
BINANCE = "38017799"

# আপনার সাপোর্ট লিংকগুলো এখানে দিন
SUPPORT_BOT = "https://t.me/mailmarketplaceSupport_bot"
UPDATE_CHANNEL = "https://t.me/mailmarketplace"

PRODUCTS = {
    "hotmail_trust": {"name": "📬 Hotmail Trust", "bkash": 2, "binance": 0.016},
    "edu":           {"name": "🎓 .EDU Mail (US)", "bkash": 1, "binance": 0.008},
    "android":       {"name": "📩 Android Studio Mail", "bkash": 5, "binance": 0.04},
    "outlook_trust": {"name": "📧 Outlook Trust", "bkash": 2, "binance": 0.016},
    "hma_vpn":       {"name": "🔒 HMA VPN (7 দিন)", "bkash": 30, "binance": 0.24},
    "nord_vpn":      {"name": "🔒 Nord VPN (7 দিন)", "bkash": 30, "binance": 0.24},
    "express_vpn":   {"name": "🔒 Express VPN (7 দিন)", "bkash": 30, "binance": 0.24},
    "abc_1gb":       {"name": "🚀 ABCProxy 1GB", "bkash": 200, "binance": 1.70, "is_proxy": True},
    "abc_2gb":       {"name": "🚀 ABCProxy 2GB", "bkash": 380, "binance": 3.20, "is_proxy": True},
}

# States
CHOOSE_CAT, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(6)
orders = {}
waiting = {}

# --- ইউটিলিটি ফাংশন ---
def get_main_menu():
    buttons = []
    for key, info in PRODUCTS.items():
        if "is_proxy" not in info:
            buttons.append([InlineKeyboardButton(info["name"], callback_data=f"cat_{key}")])
    buttons.append([InlineKeyboardButton("📦 ABCProxy (Residential)", callback_data="main_abc")])
    return InlineKeyboardMarkup(buttons)

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *স্বাগতম আমাদের শপে!*\n\n"
        "প্রিমিয়াম মেইল, ভিপিএন এবং প্রক্সি পাবেন সাশ্রয়ী মূল্যে।\n\n"
        "🛒 *সার্ভিস বেছে নিন:* "
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    else:
        await update.callback_query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    return CHOOSE_CAT

async def cat_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "main_abc":
        buttons = [
            [InlineKeyboardButton("🚀 1GB Proxy - 200 TK", callback_data="cat_abc_1gb")],
            [InlineKeyboardButton("🚀 2GB Proxy - 380 TK", callback_data="cat_abc_2gb")],
            [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_start")]
        ]
        await query.edit_message_text("📂 *ABCProxy সাব-ক্যাটাগরি:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return CHOOSE_CAT
    cat_key = query.data.replace("cat_", "")
    product = PRODUCTS[cat_key]
    context.user_data.update({"key": cat_key, "name": product["name"]})
    kb = [[InlineKeyboardButton("💳 বিকাশ", callback_data="pay_bkash")],
          [InlineKeyboardButton("💳 বিনান্স", callback_data="pay_binance")],
          [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_start")]]
    await query.edit_message_text(f"✨ *সার্ভিস:* {product['name']}\n💰 বিকাশ: {product['bkash']} BDT\n💰 বিনান্স: ${product['binance']}\n\n💳 পেমেন্ট মেথড বেছে নিন:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return PAYMENT

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_start": return await start(update, context)
    method = "বিকাশ" if query.data == "pay_bkash" else "বিনান্স পে"
    key = context.user_data["key"]
    price = PRODUCTS[key]["bkash" if "bkash" in query.data else "binance"]
    currency = "৳" if "bkash" in query.data else "$"
    context.user_data.update({"method": method, "price": price, "curr": currency})
    instr = f"📍 *পেমেন্ট ডিটেইলস ({method})*\n━━━━━━━━━━━━━━━━━━\n"
    instr += f"📞 নম্বর/আইডি: `{BKASH if method=='বিকাশ' else BINANCE}`\n"
    instr += f"💵 রেট: {currency}{price}/পিস\n\n✍️ *কয়টি লাগবে?* (সংখ্যা লিখুন)"
    await query.edit_message_text(instr, parse_mode="Markdown")
    return QTY

async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text); context.user_data["qty"] = qty
        total = round(qty * context.user_data["price"], 3); context.user_data["total"] = total
        summary = (f"📝 *অর্ডারের বিবরণ*\n📦 পণ্য: {context.user_data['name']}\n🔢 পরিমাণ: {qty} টি\n💰 মোট: {context.user_data['curr']}{total}\n\n✅ নিশ্চিত করতে চান?")
        kb = [[InlineKeyboardButton("✅ হ্যাঁ", callback_data="confirm_ok")],[InlineKeyboardButton("❌ বাতিল", callback_data="back_to_start")]]
        await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return CONFIRM
    except: return QTY

async def process_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    oid = str(uuid4())[:8].upper(); context.user_data["oid"] = oid
    await query.edit_message_text(f"🚀 *ID:* `{oid}`\nএখন পেমেন্ট স্ক্রিনশট পাঠান।", parse_mode="Markdown")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return SCREENSHOT
    photo_id = update.message.photo[-1].file_id; oid = context.user_data["oid"]
    orders[oid] = {**context.user_data, "uid": update.effective_user.id, "username": update.effective_user.username}
    await update.message.reply_text("✅ এখন পেমেন্টের *TrxID* লিখে পাঠান:")
    admin_msg = f"🔔 *নতুন অর্ডার!* ({oid})\n👤 ইউজার: @{orders[oid]['username']}\n📦 পণ্য: {orders[oid]['name']}\n💰 মোট: {orders[oid]['curr']}{orders[oid]['total']}"
    await context.bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, parse_mode="Markdown")
    return TXID

# --- এখানে ইউজার ওয়েটিং মেসেজে সাপোর্ট বাটন যোগ করা হয়েছে ---
async def get_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    oid = context.user_data["oid"]
    
    # ইউজারকে সাপোর্ট এবং চ্যানেলের বাটন দেখানো
    kb = [
        [InlineKeyboardButton("👨‍💻 Contact Support", url=SUPPORT_BOT)],
        [InlineKeyboardButton("📢 Join Update Channel", url=UPDATE_CHANNEL)]
    ]
    
    await update.message.reply_text(
        f"✅ *অর্ডার জমা হয়েছে!*\n\n"
        f"🆔 অর্ডার আইডি: `{oid}`\n"
        f"⏳ স্ট্যাটাস: ভেরিফিকেশন চলছে...\n\n"
        f"অ্যাডমিন আপনার পেমেন্ট চেক করে কিছুক্ষণের মধ্যে ডেলিভারি দিবে। কোনো প্রশ্ন থাকলে সাপোর্ট বাটনে ক্লিক করুন।",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    
    await context.bot.send_message(ADMIN_ID, f"💸 *TrxID জমা পড়েছে!*\nID: `{oid}`\nTrxID: `{txid}`\n\n✅ Approve (Key): `/approve {oid} KEY` \n📁 Approve (File): `/approve {oid}`")
    return ConversationHandler.END

# --- অ্যাডমিন অ্যাপ্রুভ (বাকি সব আগের মতই) ---
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    oid = context.args[0].upper()
    if oid not in orders: return
    order_info = orders.get(oid)

    if len(context.args) > 1:
        cd_key = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=order_info["uid"], text=f"🎉 *ডেলিভারি!*\n📦 পণ্য: {order_info['name']}\n🔑 *Key:* `{cd_key}`", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Key delivered: {oid}"); del orders[oid]
    else:
        waiting[ADMIN_ID] = oid; await update.message.reply_text(f"📁 ফাইল পাঠান: {oid}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting: return
    oid = waiting.pop(ADMIN_ID); order_info = orders.get(oid)
    await context.bot.send_document(chat_id=order_info["uid"], document=update.message.document.file_id, caption=f"✅ *ডেলিভারি!*\n📦 পণ্য: {order_info['name']}")
    await update.message.reply_text(f"✅ ফাইল ডেলিভারি সফল: {oid}"); del orders[oid]

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_CAT: [CallbackQueryHandler(cat_selection, pattern="^cat_"), CallbackQueryHandler(cat_selection, pattern="main_abc"), CallbackQueryHandler(start, pattern="back_to_start")],
            PAYMENT:    [CallbackQueryHandler(payment_method, pattern="^pay_"), CallbackQueryHandler(start, pattern="back_to_start")],
            QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            CONFIRM:    [CallbackQueryHandler(process_confirm, pattern="confirm_ok"), CallbackQueryHandler(start, pattern="back_to_start")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            TXID:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_txid)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve_order))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == "__main__":
    main()
