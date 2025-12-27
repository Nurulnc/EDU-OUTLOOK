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

PRODUCTS = {
    "hotmail_trust": {"name": "📬 Hotmail Trust", "bkash": 2, "binance": 0.016},
    "edu":           {"name": "🎓 .EDU Mail (US)", "bkash": 1, "binance": 0.008},
    "android":       {"name": "📩 Android Studio Mail", "bkash": 5, "binance": 0.04},
    "outlook_trust": {"name": "📧 Outlook Trust", "bkash": 2, "binance": 0.016},
    "hma_vpn":       {"name": "🔒 HMA VPN (7 দিন)", "bkash": 30, "binance": 0.24},
    "nord_vpn":      {"name": "🔒 Nord VPN (7 দিন)", "bkash": 30, "binance": 0.24},
    "express_vpn":   {"name": "🔒 Express VPN (7 দিন)", "bkash": 30, "binance": 0.24},
    # ABCProxy সাব-ক্যাটাগরি
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
    # সাধারণ প্রোডাক্টগুলো যোগ করা
    for key, info in PRODUCTS.items():
        if "is_proxy" not in info:
            buttons.append([InlineKeyboardButton(info["name"], callback_data=f"cat_{key}")])
    
    # ABCProxy এর জন্য মেইন ক্যাটাগরি বাটন
    buttons.append([InlineKeyboardButton("📦 ABCProxy (Residential)", callback_data="main_abc")])
    return InlineKeyboardMarkup(buttons)

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *স্বাগতম আমাদের শপে!*\n\n"
        "এখানে আপনি প্রিমিয়াম মেইল, ভিপিএন এবং প্রক্সি পাবেন সবথেকে সাশ্রয়ী মূল্যে।\n\n"
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
    
    # ABCProxy সাব-ক্যাটাগরি হ্যান্ডলিং
    if query.data == "main_abc":
        buttons = [
            [InlineKeyboardButton("🚀 1GB Proxy - 200 TK", callback_data="cat_abc_1gb")],
            [InlineKeyboardButton("🚀 2GB Proxy - 380 TK", callback_data="cat_abc_2gb")],
            [InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_start")]
        ]
        await query.edit_message_text("📂 *ABCProxy সাব-ক্যাটাগরি বেছে নিন:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return CHOOSE_CAT

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
    instr += "✍️ *আপনি কয়টি অ্যাকাউন্ট নিতে চান?* (সংখ্যা লিখুন)"

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
            f"💰 মোট দেয়: {context.user_data['curr']}{total}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ আপনি কি এই অর্ডারটি নিশ্চিত করতে চান?"
        )
        
        kb = [[InlineKeyboardButton("✅ হ্যাঁ, নিশ্চিত", callback_data="confirm_ok")],
              [InlineKeyboardButton("❌ বাতিল", callback_data="back_to_start")]]
        
        await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return CONFIRM
    except ValueError:
        await update.message.reply_text("❌ ভুল ইনপুট! শুধু সংখ্যা লিখুন।")
        return QTY

async def process_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    oid = str(uuid4())[:8].upper()
    context.user_data["oid"] = oid
    
    await query.edit_message_text(
        f"🚀 *অর্ডার আইডি:* `{oid}`\n\n"
        f"এখন পেমেন্টের *স্ক্রিনশট* পাঠান।",
        parse_mode="Markdown"
    )
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ স্ক্রিনশট পাঠান।")
        return SCREENSHOT
    
    photo_id = update.message.photo[-1].file_id
    oid = context.user_data["oid"]
    orders[oid] = {**context.user_data, "uid": update.effective_user.id, "username": update.effective_user.username}
    
    await update.message.reply_text("✅ এখন পেমেন্টের *TrxID* লিখে পাঠান:")
    
    admin_msg = (
        f"🔔 *নতুন অর্ডার!* ({oid})\n"
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
        f"✅ *অর্ডার জমা হয়েছে!*\n"
        f"আইডি: `{oid}`\nঅ্যাডমিন ভেরিফাই করে ডেলিভারি দিবে।",
        parse_mode="Markdown"
    )
    
    await context.bot.send_message(
        ADMIN_ID, 
        f"💸 *TrxID জমা পড়েছে!*\nID: `{oid}`\nTrxID: `{txid}`\n\n✅ Approve (Key): `/approve {oid} KEY` \n📁 Approve (File): `/approve {oid}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# --- অ্যাডমিন কমান্ড (Hybrid) ---
async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ ব্যবহার: `/approve ORDER_ID` (ফাইলের জন্য) অথবা `/approve ORDER_ID KEY` (টেক্সটের জন্য)")
        return

    oid = context.args[0].upper()
    if oid not in orders:
        await update.message.reply_text("❌ অর্ডার পাওয়া যায়নি।")
        return

    order_info = orders.get(oid)

    # যদি কমান্ডের সাথে CD Key থাকে
    if len(context.args) > 1:
        cd_key = " ".join(context.args[1:])
        try:
            await context.bot.send_message(
                chat_id=order_info["uid"],
                text=(
                    f"🎉 *অর্ডার ডেলিভারি করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📦 পণ্য: {order_info['name']}\n"
                    f"🔑 *CD-Key:* `{cd_key}`\n\n"
                    f"ধন্যবাদ আমাদের সাথে থাকার জন্য।"
                ),
                parse_mode="Markdown"
            )
            await update.message.reply_text(f"✅ Key ডেলিভারি সফল: {oid}")
            del orders[oid]
        except Exception as e:
            await update.message.reply_text(f"❌ এরর: {str(e)}")
    else:
        waiting[ADMIN_ID] = oid
        await update.message.reply_text(f"📁 অর্ডার `{oid}` এর জন্য ফাইল পাঠান।")

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
            caption=f"✅ *অর্ডার ডেলিভারি করা হয়েছে!*\n🆔 আইডি: `{oid}`\n📦 পণ্য: {order_info['name']}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ ফাইল ডেলিভারি সফল: {oid}")
        del orders[oid]
    except Exception as e:
        await update.message.reply_text(f"❌ ভুল হয়েছে: {str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_CAT: [CallbackQueryHandler(cat_selection, pattern="^cat_"), 
                         CallbackQueryHandler(cat_selection, pattern="main_abc"),
                         CallbackQueryHandler(start, pattern="back_to_start")],
            PAYMENT:    [CallbackQueryHandler(payment_method, pattern="^pay_"), 
                         CallbackQueryHandler(start, pattern="back_to_start")],
            QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            CONFIRM:    [CallbackQueryHandler(process_confirm, pattern="confirm_ok"), 
                         CallbackQueryHandler(start, pattern="back_to_start")],
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
