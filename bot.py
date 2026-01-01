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

# --- CONFIGURATION ---
TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"
ADMIN_ID = 1651695602
BKASH = "01815243007"
BINANCE = "38017799"

SUPPORT_BOT = "https://t.me/mailmarketplaceSupport_bot"
UPDATE_CHANNEL = "https://t.me/mailmarketplace"

# PRODUCTS DATABASE
PRODUCTS = {
    # Mails (Main Category: mail)
    "hotmail_trust": {"name": "📬 Hotmail Trust", "bkash": 2, "binance": 0.016, "cat": "mail"},
    "outlook_trust": {"name": "📧 Outlook Trust", "bkash": 2, "binance": 0.016, "cat": "mail"},
    "android": {"name": "📩 Android Studio Mail", "bkash": 3, "binance": 0.024, "cat": "mail"},
    
    # EDU Mails (Sub Category: mail_edu)
    "edu_24": {"name": "🎓 EDU Mail (24hr Live)", "bkash": 1, "binance": 0.008, "cat": "mail_edu"},
    "edu_72": {"name": "🎓 EDU Mail (72hr Live)", "bkash": 2, "binance": 0.016, "cat": "mail_edu"},
    
    # VPNs (Main Category: vpn)
    "hma_vpn": {"name": "🔒 HMA VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "nord_vpn": {"name": "🔒 Nord VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "express_vpn": {"name": "🔒 Express VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "surfshark": {"name": "🔒 Surfshark VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "cyberghost": {"name": "🔒 Cyberghost VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "avast_vpn": {"name": "🔒 Avast VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "avg_vpn": {"name": "🔒 AVG VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "bitdefender": {"name": "🔒 Bitdefender VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "potato_vpn": {"name": "🔒 Potato VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "vyper_vpn": {"name": "🔒 VyprVPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "pia_vpn": {"name": "🔒 PIA VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "ipvanish": {"name": "🔒 IPVanish VPN", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    "hotspot": {"name": "🔒 Hotspot Shield", "bkash": 30, "binance": 0.24, "cat": "vpn"},
    
    # Proxies (Main Category: proxy)
    "abc_1gb": {"name": "🚀 ABCProxy 1GB", "bkash": 180, "binance": 1.44, "cat": "proxy"},
    "abc_2gb": {"name": "🚀 ABCProxy 2GB", "bkash": 360, "binance": 2.88, "cat": "proxy"},
}

# States
MAIN_MENU, SUB_MENU, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(7)
orders = {}
waiting = {}

# --- KEYBOARDS ---
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Buy Mail", callback_data="cat_mail"), InlineKeyboardButton("🔒 Buy VPN", callback_data="cat_vpn")],
        [InlineKeyboardButton("🚀 Buy Proxy", callback_data="cat_proxy")],
        [InlineKeyboardButton("👨‍💻 সাপোর্ট", url=SUPPORT_BOT), InlineKeyboardButton("📢 চ্যানেল", url=UPDATE_CHANNEL)]
    ])

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "👋 *স্বাগতম আমাদের শপে!*\n\nপ্রিমিয়াম সার্ভিস পেতে নিচের ক্যাটাগরি বেছে নিন।"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu_kb(), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=main_menu_kb(), parse_mode="Markdown")
    return MAIN_MENU

async def handle_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.replace("cat_", "")
    buttons = []

    if choice == "mail":
        buttons.append([InlineKeyboardButton("🎓 .EDU Mails (Sub-cat)", callback_data="cat_mail_edu")])
        for k, v in PRODUCTS.items():
            if v['cat'] == "mail": buttons.append([InlineKeyboardButton(v['name'], callback_data=f"buy_{k}")])
    
    elif choice == "mail_edu":
        for k, v in PRODUCTS.items():
            if v['cat'] == "mail_edu": buttons.append([InlineKeyboardButton(v['name'], callback_data=f"buy_{k}")])

    elif choice == "vpn":
        vpn_items = [InlineKeyboardButton(v['name'], callback_data=f"buy_{k}") for k, v in PRODUCTS.items() if v['cat'] == "vpn"]
        for i in range(0, len(vpn_items), 2):
            buttons.append(vpn_items[i:i+2])

    elif choice == "proxy":
        for k, v in PRODUCTS.items():
            if v['cat'] == "proxy": buttons.append([InlineKeyboardButton(v['name'], callback_data=f"buy_{k}")])

    buttons.append([InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_main")])
    await query.edit_message_text(f"📂 *{choice.replace('_',' ').upper()} সেকশন:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    return SUB_MENU

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_main": return await start(update, context)
    prod_key = query.data.replace("buy_", "")
    product = PRODUCTS[prod_key]
    context.user_data.update({"key": prod_key, "name": product["name"]})
    kb = [[InlineKeyboardButton("💳 বিকাশ", callback_data="pay_bkash"), InlineKeyboardButton("💳 বিনান্স", callback_data="pay_binance")], [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_main")]]
    await query.edit_message_text(f"✨ *সার্ভিস:* {product['name']}\n💰 বিকাশ: {product['bkash']} BDT\n💰 বিনান্স: ${product['binance']}\n\nপেমেন্ট মেথড বেছে নিন:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    return PAYMENT

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = "বিকাশ" if "bkash" in query.data else "বিনান্স পে"
    key = context.user_data["key"]
    price = PRODUCTS[key]["bkash" if "bkash" in query.data else "binance"]
    currency = "৳" if "bkash" in query.data else "$"
    context.user_data.update({"method": method, "price": price, "curr": currency})
    instr = f"📍 *পেমেন্ট ডিটেইলস ({method})*\n━━━━━━━━━━━━━━━━━━\n📞 আইডি: `{BKASH if method=='বিকাশ' else BINANCE}`\n💵 রেট: {currency}{price}/পিস\n\n✍️ *কয়টি লাগবে?* (শুধু সংখ্যা লিখুন)"
    await query.edit_message_text(instr, parse_mode="Markdown")
    return QTY

async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
        return QTY
    qty = int(update.message.text)
    context.user_data["qty"] = qty
    total = round(qty * context.user_data["price"], 3)
    context.user_data["total"] = total
    summary = f"📝 *অর্ডারের বিবরণ*\n📦 পণ্য: {context.user_data['name']}\n🔢 পরিমাণ: {qty} টি\n💰 মোট: {context.user_data['curr']}{total}\n\n✅ নিশ্চিত করতে চান?"
    kb = [[InlineKeyboardButton("✅ হ্যাঁ", callback_data="confirm_ok"), InlineKeyboardButton("❌ বাতিল", callback_data="back_to_main")]]
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRM

async def process_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oid = str(uuid4())[:8].upper()
    context.user_data["oid"] = oid
    await update.callback_query.edit_message_text(f"🚀 *অর্ডার আইডি:* `{oid}`\nএখন পেমেন্ট স্ক্রিনশট পাঠান।", parse_mode="Markdown")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return SCREENSHOT
    photo_id = update.message.photo[-1].file_id
    oid = context.user_data["oid"]
    orders[oid] = {**context.user_data, "uid": update.effective_user.id, "username": update.effective_user.username}
    await update.message.reply_text("✅ এখন পেমেন্টের *TrxID* লিখে পাঠান:")
    admin_msg = f"🔔 *নতুন অর্ডার!*\n🆔 ID: `{oid}`\n👤 @{orders[oid]['username']}\n📦 {orders[oid]['name']}\n💰 {orders[oid]['curr']}{orders[oid]['total']}"
    await context.bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, parse_mode="Markdown")
    return TXID

async def get_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    oid = context.user_data["oid"]
    kb = [[InlineKeyboardButton("👨‍💻 সাপোর্ট", url=SUPPORT_BOT), InlineKeyboardButton("📢 আপডেট", url=UPDATE_CHANNEL)]]
    await update.message.reply_text(f"✅ *অর্ডার জমা হয়েছে!*\n🆔 আইডি: `{oid}`\n⏳ স্ট্যাটাস: ভেরিফিকেশন চলছে...", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    admin_instr = f"💸 *TrxID জমা পড়েছে!*\n🆔 ID: `{oid}`\n🔗 TrxID: `{txid}`\n\n✅ Key: `/approve {oid} key` \n📁 File: `/approve {oid}`"
    await context.bot.send_message(ADMIN_ID, admin_instr, parse_mode="Markdown")
    return ConversationHandler.END

# --- ADMIN SYSTEM (EXACTLY AS REQUESTED) ---
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    oid = context.args[0].upper()
    if oid not in orders: return
    order_info = orders[oid]
    order_more_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 আরও অর্ডার করুন", callback_data="back_to_main")]])

    if len(context.args) > 1:
        # Delivery via Key
        cd_key = " ".join(context.args[1:])
        text = (
            f"🎉 *অর্ডার সফলভাবে ডেলিভারি করা হয়েছে!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 *পণ্য:* {order_info['name']}\n"
            f"🔑 *Key:* `{cd_key}`\n\n"
            f"✨ 𝓣𝓱𝓪𝓷𝓴 𝔂𝓸𝓾 𝓯𝓸𝓻 𝔂𝓸𝓾𝓻 𝓟𝓾𝓻𝓬𝓱𝓪𝓼𝓮! ✨\n"
            f"আমাদের সাথে কেনাকাটা করার জন্য ধন্যবাদ।"
        )
        await context.bot.send_message(chat_id=order_info["uid"], text=text, parse_mode="Markdown", reply_markup=order_more_kb)
        await update.message.reply_text(f"✅ Key delivered: {oid}")
        del orders[oid]
    else:
        # Start File Delivery Process
        waiting[ADMIN_ID] = oid
        await update.message.reply_text(f"📁 ফাইল পাঠান ID: `{oid}`")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID not in waiting: return
    oid = waiting.pop(ADMIN_ID)
    if oid not in orders: return
    order_info = orders[oid]
    order_more_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 আরও অর্ডার করুন", callback_data="back_to_main")]])
    
    caption = (
        f"✅ *অর্ডার সফলভাবে ডেলিভারি করা হয়েছে!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *পণ্য:* {order_info['name']}\n\n"
        f"✨ 𝓣𝓱𝓪𝓷𝓴 𝔂𝓸𝓾 𝓯𝓸𝓻 𝔂𝓸𝓾𝓻 𝓟𝓾𝓻𝓬𝓱𝓪𝓼𝓮! ✨\n"
        f"আপনার অর্ডারটি সংগ্রহ করুন। ধন্যবাদ!"
    )
    await context.bot.send_document(chat_id=order_info["uid"], document=update.message.document.file_id, 
                                    caption=caption, parse_mode="Markdown", reply_markup=order_more_kb)
    await update.message.reply_text(f"✅ ফাইল ডেলিভারি সফল ID: {oid}")
    del orders[oid]

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="^back_to_main$")],
        states={
            MAIN_MENU: [CallbackQueryHandler(handle_categories, pattern="^cat_")],
            SUB_MENU:  [CallbackQueryHandler(handle_selection, pattern="^buy_"), 
                        CallbackQueryHandler(handle_categories, pattern="^cat_"),
                        CallbackQueryHandler(start, pattern="^back_to_main$")],
            PAYMENT:   [CallbackQueryHandler(payment_method, pattern="^pay_"), 
                        CallbackQueryHandler(start, pattern="^back_to_main$")],
            QTY:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            CONFIRM:   [CallbackQueryHandler(process_confirm, pattern="^confirm_ok$"), 
                        CallbackQueryHandler(start, pattern="^back_to_main$")],
            SCREENSHOT:[MessageHandler(filters.PHOTO, get_screenshot)],
            TXID:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_txid)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve_order))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("🤖 বোট রান হচ্ছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
