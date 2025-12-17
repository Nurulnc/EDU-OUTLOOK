import logging
import random
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
print("বোট চালু হচ্ছে...")

TOKEN = "8594094725:AAEtkG2hAgpn7oNxtp8uvrBiFwcaZ2d-oKA"
ADMIN_ID = 1651695602

# প্রাইস (নতুন Edu 24hr ও 72hr যোগ করা)
P = {
    "edu_24hr":      {"bkash": 1,   "binance": 0.008},
    "edu_72hr":      {"bkash": 2,   "binance": 0.016},  # তোমার দাম চেঞ্জ করো
    "android":       {"bkash": 5,   "binance": 0.04},
    "outlook_trust": {"bkash": 2,   "binance": 0.016},
    "hotmail_trust": {"bkash": 2,   "binance": 0.016},
    "hma_vpn":       {"bkash": 30,  "binance": 0.24},
    "nord_vpn":      {"bkash": 30,  "binance": 0.24},
    "express_vpn":   {"bkash": 30,  "binance": 0.24},
}

BKASH = "01815243007"
BINANCE = "38017799"

# States (শপের জন্য)
CHOOSE_MAIN, SHOP_SUB, VPN_SUB, PAYMENT, QTY, CONFIRM, SCREENSHOT, TXID = range(8)

orders = {}
waiting = {}

# ফেক US নাম ও এড্রেস লিস্ট (আরও যোগ করতে পারো)
US_FIRST_NAMES = ["John", "Emma", "Michael", "Sophia", "William", "Olivia", "James", "Ava"]
US_LAST_NAMES = ["Smith", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
US_CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🛒 Shop Now", callback_data="main_shop")],
        [InlineKeyboardButton("🔐 2FA Generator", callback_data="tool_2fa")],
        [InlineKeyboardButton("🇺🇸 US Name Generator", callback_data="tool_name")],
    ]
    await update.message.reply_text(
        "🔒 **স্বাগতম! বাংলাদেশের ট্রাস্টেড প্রিমিয়াম অ্যাকাউন্ট শপে** 🔒\n\n"
        "নিচ থেকে একটি অপশন সিলেক্ট করুন 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CHOOSE_MAIN

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "tool_2fa":
        code = ''.join(random.choices('0123456789', k=6))
        await q.edit_message_text(f"🔐 **তোমার 2FA কোড:** `{code}`\n\nআরেকটা চাইলে আবার ক্লিক করো।", parse_mode="Markdown")
        return CHOOSE_MAIN

    elif q.data == "tool_name":
        name = random.choice(US_FIRST_NAMES) + " " + random.choice(US_LAST_NAMES)
        city = random.choice(US_CITIES)
        await q.edit_message_text(
            f"🇺🇸 **জেনারেটেড US নাম:**\n\n{name}\n{city}, USA\n\nআরেকটা চাইলে আবার ক্লিক করো।",
            parse_mode="Markdown"
        )
        return CHOOSE_MAIN

    elif q.data == "main_shop":
        kb = [
            [InlineKeyboardButton("🎓 Edu Mail 24hr", callback_data="cat_edu_24hr")],
            [InlineKeyboardButton("🎓 Edu Mail 72hr", callback_data="cat_edu_72hr")],
            [InlineKeyboardButton("📩 Android Studio Mail", callback_data="cat_android")],
            [InlineKeyboardButton("📧 Outlook Trust", callback_data="cat_outlook_trust")],
            [InlineKeyboardButton("📬 Hotmail Trust", callback_data="cat_hotmail_trust")],
            [InlineKeyboardButton("🔒 VPN Buy", callback_data="sub_vpn")],
            [InlineKeyboardButton("🔙 মেইন মেনুতে ফিরে যান", callback_data="back_main")],
        ]
        await q.edit_message_text("🛒 **Shop Now** – ক্যাটাগরি সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return SHOP_SUB

    elif q.data == "back_main":
        return await start(update, context)  # মেইন মেনুতে ফিরে যায়

async def shop_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "sub_vpn":
        kb = [
            [InlineKeyboardButton("🔒 HMA VPN (7 দিন)", callback_data="cat_hma_vpn")],
            [InlineKeyboardButton("🔒 Nord VPN (7 দিন)", callback_data="cat_nord_vpn")],
            [InlineKeyboardButton("🔒 Express VPN (7 দিন)", callback_data="cat_express_vpn")],
            [InlineKeyboardButton("🔙 শপ মেনুতে ফিরে যান", callback_data="main_shop")],
        ]
        await q.edit_message_text("🔒 **VPN Buy** – একটি সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return VPN_SUB

    # সরাসরি প্রোডাক্ট সিলেক্ট
    category_map = {
        "cat_edu_24hr": ("edu_24hr", "Edu Mail 24hr"),
        "cat_edu_72hr": ("edu_72hr", "Edu Mail 72hr"),
        "cat_android": ("android", "Android Studio Mail"),
        "cat_outlook_trust": ("outlook_trust", "Outlook Trust"),
        "cat_hotmail_trust": ("hotmail_trust", "Hotmail Trust"),
        "cat_hma_vpn": ("hma_vpn", "HMA VPN"),
        "cat_nord_vpn": ("nord_vpn", "Nord VPN"),
        "cat_express_vpn": ("express_vpn", "Express VPN"),
    }

    if q.data in category_map:
        cat_key, cat_name = category_map[q.data]
        context.user_data["cat"] = cat_name
        context.user_data["key"] = cat_key

        is_vpn = cat_key.endswith("_vpn")
        duration_text = "\nমেয়াদ: ৭ দিন" if is_vpn else ""

        kb = [
            [InlineKeyboardButton(f"বিকাশ ৳{P[cat_key]['bkash']}", callback_data="pay_bkash")],
            [InlineKeyboardButton(f"বিনান্স ${P[cat_key]['binance']}", callback_data="pay_binance")],
            [InlineKeyboardButton("🔙 শপ মেনুতে ফিরে যান", callback_data="main_shop")],
        ]
        await q.edit_message_text(f"*{cat_name}*{duration_text}\nপেমেন্ট মেথড নির্বাচন করুন:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return PAYMENT

# বাকি ফাংশনগুলো (payment, qty, confirm ইত্যাদি) আগের মতোই – শুধু ব্যাক বাটন যোগ করা যায় চাইলে

# ... (payment, qty, confirm, screenshot, txid, approve, excel ফাংশনগুলো আগের কোড থেকে কপি করো – কোনো চেঞ্জ লাগবে না)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MAIN: [CallbackQueryHandler(main_menu, pattern="^(main_shop|tool_2fa|tool_name|back_main)$")],
            SHOP_SUB: [CallbackQueryHandler(shop_sub, pattern="^(sub_vpn|cat_|main_shop)$")],
            VPN_SUB: [CallbackQueryHandler(shop_sub, pattern="^cat_")],
            PAYMENT: [CallbackQueryHandler(payment, pattern="^pay_")],
            QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, qty)],
            CONFIRM: [CallbackQueryHandler(confirm, pattern="^(ok|no)$")],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot)],
            TXID: [MessageHandler(filters.TEXT & ~filters.COMMAND, txid)],
        },
        fallbacks=[],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.Document.ALL, excel))

    print("বোট অনলাইন এবং প্রস্তুত!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
