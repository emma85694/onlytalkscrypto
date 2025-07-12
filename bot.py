import logging
import re
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.system_program import Transfer
from solana.keypair import Keypair

# Telegram Bot Token (from @BotFather)
BOT_TOKEN = "8099231547:AAGRSZJu1T9tbPwaSq2G9GfbSTAPvCBtJcQ"

# Solana Configuration
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
FUNDING_WALLET = Keypair.from_secret_key(bytes.fromhex(os.getenv("SOL_PRIVATE_KEY")))  # Hex-encoded private key
REWARD_AMOUNT = 10_000_000_000  # 10 SOL in lamports (1 SOL = 1,000,000,000 lamports)

# Social Media Links
SOCIAL_LINKS = {
    "telegram_group": "https://t.me/+GT79579A9hM5ZjY0",
    "telegram_channel": "https://t.me/onlytalkscrpto",
    "twitter": "https://x.com/onlytalkscrypto",
    "tiktok": "https://www.tiktok.com/@onlytalkscrypto",
    "website": "https://comfy-youtiao-930681.netlify.app/"
}

# In-memory storage (consider using a database for production)
user_data = {}
completed_users = set()

# Conversation states
VERIFYING, WALLET = range(2)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    welcome_text = (
        "🌟 Welcome to OnlyTalksCrypto ($OTC) Airdrop! 🌟\n\n"
        "Complete these simple tasks to earn 10 SOL:\n"
        f"1. Join our Telegram Group: {SOCIAL_LINKS['telegram_group']}\n"
        f"2. Join our Telegram Channel: {SOCIAL_LINKS['telegram_channel']}\n"
        f"3. Follow us on Twitter (X): {SOCIAL_LINKS['twitter']}\n"
        f"4. Follow us on TikTok: {SOCIAL_LINKS['tiktok']}\n"
        f"5. Visit our Website: {SOCIAL_LINKS['website']}\n\n"
        "Click ✅ VERIFY below when you've completed all tasks!"
    )
    
    keyboard = [[InlineKeyboardButton("✅ VERIFY TASKS", callback_data="verify_tasks")]]
    update.message.reply_text(
        welcome_text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def verify_tasks(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    
    # Prevent multiple submissions
    if user_id in completed_users:
        query.edit_message_text("⚠️ You've already completed the airdrop!")
        return ConversationHandler.END
    
    query.edit_message_text(
        "🎉 Well done! Hope you didn't cheat the system!\n"
        "Please enter your Twitter username (e.g., @yourhandle):"
    )
    return VERIFYING

def store_twitter(update: Update, context: CallbackContext) -> int:
    twitter_handle = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Simple validation and formatting
    if not twitter_handle:
        update.message.reply_text("❌ Please enter a valid Twitter handle:")
        return VERIFYING
    
    if not twitter_handle.startswith('@'):
        twitter_handle = '@' + twitter_handle
    
    # Store user data
    user_data[user_id] = {
        "twitter": twitter_handle,
        "username": update.effective_user.username or "N/A",
        "full_name": update.effective_user.full_name
    }
    
    update.message.reply_text(
        "📝 Now send your SOL wallet address where we should send your 10 SOL reward:"
    )
    return WALLET

def process_wallet(update: Update, context: CallbackContext) -> int:
    wallet_address = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Validate SOL address format
    if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", wallet_address):
        update.message.reply_text("❌ Invalid SOL address format. Please check and resend:")
        return WALLET
    
    # Save wallet to user data
    user_data[user_id]["wallet"] = wallet_address
    
    # Create success message
    success_message = (
        f"🎉 Congratulations! You passed the $OTC (OnlyTalksCrypto) Airdrop call!\n\n"
        f"✅ 10 SOL is on its way to your wallet:\n`{wallet_address}`\n\n"
        "Please allow a few minutes for blockchain confirmation."
    )
    
    # Attempt to send SOL
    try:
        txn = Transaction().add(
            Transfer(
                from_pubkey=FUNDING_WALLET.public_key,
                to_pubkey=wallet_address,
                lamports=REWARD_AMOUNT
            )
        )
        result = Client(SOLANA_RPC_URL).send_transaction(txn, FUNDING_WALLET)
        tx_id = result['result']
        
        success_message += f"\n🔗 Transaction ID: `{tx_id}`"
        logging.info(f"SOL sent to {wallet_address}. TX ID: {tx_id}")
        
    except Exception as e:
        logging.error(f"Transaction failed: {str(e)}")
        success_message = (
            f"✅ Airdrop submission received!\n\n"
            f"We encountered an issue sending SOL: {str(e)}\n"
            "Your wallet has been saved and we'll process your reward manually.\n"
            "Contact @OTC_Support for assistance."
        )
    
    update.message.reply_text(success_message, parse_mode="Markdown")
    
    # Mark user as completed
    completed_users.add(user_id)
    
    # Save user data to file (for your records)
    with open("airdrops.log", "a") as f:
        f.write(f"User ID: {user_id}, Wallet: {wallet_address}, Twitter: {user_data[user_id]['twitter']}\n")
    
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Airdrop process cancelled.')
    return ConversationHandler.END

def main() -> None:
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    logger = logging.getLogger(__name__)
    
    # Initialize Telegram Updater
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(verify_tasks, pattern='^verify_tasks$')],
        states={
            VERIFYING: [MessageHandler(Filters.text & ~Filters.command, store_twitter)],
            WALLET: [MessageHandler(Filters.text & ~Filters.command, process_wallet)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    logger.info("Bot is now running...")
    updater.idle()

if __name__ == "__main__":
    main()
