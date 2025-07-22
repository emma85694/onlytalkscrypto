import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackContext
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
TASKS, TWITTER, WALLET = range(3)

# Only Talks Crypto specific links
TELEGRAM_GROUP = "https://t.me/onlytalkscrypto_group"
TELEGRAM_CHANNEL = "https://t.me/onlytalkscrpto"
TIKTOK_PROFILE = "https://tiktok.com/@onlytalkscrypto"
TWITTER_PROFILE = "https://x.com/onlytalkscrypto"
ADMIN_CHAT_ID = 6726965810  # Your Telegram Chat ID
TOKEN_RECEIVE_ACCOUNT = "@onlytalkscrypto"  # Account to send wallet address

# Store completed users (in-memory)
completed_users = set()
twitter_verifications = {}  # {user_id: twitter_handle}

def create_task_keyboard():
    """Create inline keyboard for tasks with formatted links"""
    keyboard = [
        [InlineKeyboardButton("💬 Join Telegram Group", url=TELEGRAM_GROUP)],
        [InlineKeyboardButton("📢 Join Telegram Channel", url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton("🎥 Follow TikTok", url=TIKTOK_PROFILE)],
        [InlineKeyboardButton("🐦 Follow Twitter", url=TWITTER_PROFILE)],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send instructions and set initial state"""
    user = update.effective_user
    
    # Check if user already completed
    if user.id in completed_users:
        await update.message.reply_text(
            "🎉 You have completed the Only Talks Crypto token giveaway!\n\n"
            "💬 Stay active in our community for the latest memecoin updates, "
            "market analysis, and exclusive opportunities as we navigate the "
            "crypto landscape together.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Create formatted welcome message
    welcome_msg = (
        f"🚀 Welcome {user.first_name} to the Only Talks Crypto Token Giveaway! 🚀\n\n"
        "💰 **To receive your free tokens, please complete these essential tasks:**\n"
        "1. Join our Telegram Group\n"
        "2. Join our Telegram Channel\n"
        "3. Follow us on TikTok\n"
        "4. Follow us on Twitter\n\n"
        "✅ **Send 'done' when you've completed all tasks.**\n\n"
        "🔍 Note: Our team verifies all participation to ensure fairness "
        "across our growing community."
    )
    
    # Send message with inline buttons
    await update.message.reply_text(
        welcome_msg,
        parse_mode="Markdown",
        reply_markup=create_task_keyboard()
    )
    return TASKS

async def tasks_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process task completion and request Twitter handle"""
    user = update.effective_user
    user_input = update.message.text.lower()
    
    # Only respond to "done" command
    if "done" not in user_input:
        await update.message.reply_text(
            "Please complete all tasks and send 'done' when finished.",
            reply_markup=create_task_keyboard()
        )
        return TASKS
    
    # Request Twitter handle for verification
    await update.message.reply_text(
        "👍 Excellent! We appreciate you joining our crypto community.\n\n"
        "🔒 To verify your Twitter follow, please provide your **Twitter username** "
        "(without the '@' symbol).\n\n"
        "Example: If your Twitter is `x.com/crypto_trader`, send `crypto_trader`",
        parse_mode="Markdown"
    )
    return TWITTER

async def receive_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process Twitter handle and notify admin"""
    user = update.effective_user
    twitter_handle = update.message.text.strip()
    
    # Validate Twitter handle format
    if not re.match(r"^[a-zA-Z0-9_]{1,15}$", twitter_handle):
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid Twitter handle. "
            "Please enter just your username (without '@').\n\n"
            "Example: For `x.com/onlytalkscrypto`, send `onlytalkscrypto`"
        )
        return TWITTER
    
    # Store for reference
    twitter_verifications[user.id] = twitter_handle
    
    try:
        # Create admin notification message
        admin_message = (
            f"🆕 Only Talks Crypto Verification Needed\n\n"
            f"👤 User: {user.full_name} (@{user.username or 'N/A'})\n"
            f"🆔 Telegram ID: {user.id}\n"
            f"🐦 Twitter: https://x.com/{twitter_handle}\n\n"
            f"🔗 Verify Twitter follow: {TWITTER_PROFILE}/following\n"
            f"📨 Contact user: https://t.me/{user.username}" if user.username else ""
        )
        
        # Send directly to admin's chat ID
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        logger.info(f"Sent Twitter verification to admin: {twitter_handle}")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
    
    # Proceed to wallet collection
    await update.message.reply_text(
        f"📬 Thank you! Our team will verify your Twitter follow.\n\n"
        f"➡️ **Final Step:** Send your **wallet address** to {TOKEN_RECEIVE_ACCOUNT} to receive your tokens.\n\n"
        "🔐 Always verify you're messaging our official account for security.",
        parse_mode="Markdown"
    )
    return WALLET

async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process wallet address and complete the flow"""
    user = update.effective_user
    wallet = update.message.text
    
    # Add user to completed set
    completed_users.add(user.id)
    
    # Send success messages
    await update.message.reply_text(
        f"🎉 **Congratulations!** You've successfully completed the Only Talks Crypto token giveaway!\n\n"
        f"📍 Your wallet address: `{wallet}`\n\n"
        "⏱️ **Distribution Timeline:**\n"
        "Due to high demand and our thorough verification process to ensure authenticity, "
        "token distribution typically takes 7-14 days. As experienced crypto community builders, "
        "we prioritize security and fairness for all participants.",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        "💎 **What to Expect:**\n"
        "1. Your submission will be verified by our team\n"
        "2. Tokens will be distributed within 14 days\n"
        "3. Stay active in our group for crypto market updates\n\n"
        "💬 Join the conversation in our Telegram group for real-time crypto discussions!",
        parse_mode="Markdown"
    )
    
    try:
        # Notify admin about wallet submission
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"💰 Wallet Submitted by @{user.username or user.id}:\n{wallet}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send wallet to admin: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allow users to exit the flow"""
    await update.message.reply_text(
        "Process canceled. Type /start to begin when you're ready.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def handle_completed_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from users who already completed the giveaway"""
    user = update.effective_user
    if user.id in completed_users:
        await update.message.reply_text(
            "🎉 You've completed the Only Talks Crypto token giveaway!\n\n"
            "💬 Stay active in our Telegram group for the latest memecoin updates, "
            "market analysis, and trading opportunities. Our team of crypto enthusiasts "
            "regularly shares valuable insights to help community members navigate "
            "the volatile crypto market.\n\n"
            "⏳ **Note:** Token distribution may take 7-14 days due to our thorough "
            "verification process, ensuring fairness for all community members.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    return None

def main() -> None:
    """Run the bot."""
    # Get token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN", "7599633766:AAFZeMhW4k_DDbEDUhR62hCKQ7cF4PpQanE")
    
    # Create Application
    application = Application.builder().token(token).build()

    # Conversation handler for new users
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TASKS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    tasks_completed
                )
            ],
            TWITTER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    receive_twitter
                )
            ],
            WALLET: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    receive_wallet
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Handler for completed users
    completed_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_completed_user
    )

    application.add_handler(conv_handler)
    application.add_handler(completed_handler)

    # Check if running on Render
    if os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_HOSTNAME"):
        try:
            PORT = int(os.environ.get("PORT", 8443))
            service_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
            
            if service_url:
                # Auto-configure webhook URL
                WEBHOOK_URL = f"https://{service_url}/webhook"
                logger.info(f"Starting webhook on {WEBHOOK_URL}")
                
                # Start webhook server
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    webhook_url=WEBHOOK_URL,
                    url_path="/webhook",
                    drop_pending_updates=True
                )
                return
        except Exception as e:
            logger.error(f"Webhook setup error: {e}")

    # Fallback to polling
    logger.info("Starting in polling mode...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
