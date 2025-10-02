import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config
from src.terabox_api import TeraBoxAPI
from src.downloader import download_and_send_file

logger = logging.getLogger(__name__)

class TeraBoxLeechBot:
    def __init__(self):
        self.token = Config.BOT_TOKEN
        if self.token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("❌ Please set your BOT_TOKEN in config.py")
        
        self.app = Application.builder().token(self.token).build()
        self.terabox_api = TeraBoxAPI()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.start_handler))
        self.app.add_handler(CommandHandler("leech", self.leech_handler))
        self.app.add_handler(CommandHandler("help", self.help_handler))
        self.app.add_handler(CommandHandler("ping", self.ping_handler))
        
        # Handle messages containing TeraBox links
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """
🤖 **TeraBox Leech Bot**

I can download files from TeraBox and send them to you on Telegram!

**Commands:**
/leech [url] - Download TeraBox file
/help - Show this help message
/ping - Check if bot is alive

**Usage:**
1. Send me a TeraBox link
2. Or use /leech command
3. I'll download and send you the file

**Supported domains:** terabox.com, terabox.app, 1024tera.com
        """
        await update.message.reply_text(welcome_text)
    
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **Help Guide**

**How to use:**
1. Copy any TeraBox share link
2. Send it to me or use `/leech [link]`
3. Wait for the download to complete

**Example:**
`/leech https://terabox.com/s/your-file-link`

**Note:** Large files may take time to download and upload.
        """
        await update.message.reply_text(help_text)
    
    async def ping_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command"""
        await update.message.reply_text("🏓 Pong! Bot is alive and running!")
    
    async def leech_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leech command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a TeraBox link.\n"
                "**Usage:** `/leech https://terabox.com/s/your-link`"
            )
            return
        
        terabox_url = context.args[0]
        await self._process_terabox_request(update, terabox_url)
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages containing TeraBox links"""
        message_text = update.message.text
        
        # Check if message contains TeraBox link
        terabox_domains = ['terabox.com', 'terabox.app', '1024tera.com']
        if any(domain in message_text for domain in terabox_domains):
            await self._process_terabox_request(update, message_text)
    
    async def _process_terabox_request(self, update: Update, terabox_url: str):
        """Process TeraBox link and initiate download"""
        status_msg = await update.message.reply_text("🔄 Processing your TeraBox link...")
        
        try:
            # Get direct link from API
            file_info = self.terabox_api.get_direct_link(terabox_url)
            
            if not file_info["success"]:
                await status_msg.edit_text(f"❌ Failed to process link:\n`{file_info['error']}`")
                return
            
            # Check file size
            if file_info.get('size', 0) > Config.MAX_FILE_SIZE:
                await status_msg.edit_text("❌ File is too large (max 2GB supported)")
                return
            
            # Update status with file info
            size_mb = file_info.get('size', 0) / (1024 * 1024)
            info_text = (
                f"📄 **File:** `{file_info['filename']}`\n"
                f"📦 **Size:** `{size_mb:.2f} MB`\n"
                f"⏳ **Status:** Starting download..."
            )
            await status_msg.edit_text(info_text)
            
            # Start download process
            await download_and_send_file(update, status_msg, file_info)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            await status_msg.edit_text(f"❌ Error processing request:\n`{str(e)}`")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred while processing your request. Please try again."
            )
        except:
            pass
    
    def run(self):
        """Start the bot"""
        logger.info("Starting TeraBox Leech Bot...")
        print("✅ Bot started successfully!")
        print("📍 Press Ctrl+C to stop the bot")
        self.app.run_polling()
