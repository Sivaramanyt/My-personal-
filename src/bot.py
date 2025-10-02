import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config
from src.terabox_api import TeraBoxAPI
from src.downloader import download_and_send_file

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TeraBoxLeechBot:
    def __init__(self):
        self.token = Config.BOT_TOKEN
        self.app = Application.builder().token(self.token).build()
        self.terabox_api = TeraBoxAPI()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.start_handler))
        self.app.add_handler(CommandHandler("leech", self.leech_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = (
            "🤖 **TeraBox Leech Bot**\n\n"
            "Send me a TeraBox link and I'll download it for you!\n"
            "You can also use /leech [url] command."
        )
        await update.message.reply_text(welcome_text)
    
    async def leech_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leech command"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a TeraBox link.\nUsage: `/leech [your_terabox_link]`")
            return
        
        terabox_url = context.args[0]
        await self.process_terabox_link(update, terabox_url)
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages containing TeraBox links"""
        message_text = update.message.text
        
        # Simple TeraBox link detection
        if "terabox" in message_text.lower() or "1024tera" in message_text.lower():
            await self.process_terabox_link(update, message_text)
    
    async def process_terabox_link(self, update: Update, terabox_url: str):
        """Process TeraBox link and initiate download"""
        status_msg = await update.message.reply_text("🔄 Processing your TeraBox link...")
        
        # Get direct link from API
        file_info = self.terabox_api.get_direct_link(terabox_url)
        
        if not file_info["success"]:
            await status_msg.edit_text(f"❌ Failed to get direct link:\n`{file_info['error']}`")
            return
        
        # Update status with file info
        info_text = (
            f"**File Name:** `{file_info['filename']}`\n"
            f"**Status:** Starting download..."
        )
        await status_msg.edit_text(info_text)
        
        # Start download process
        await download_and_send_file(update, status_msg, file_info)
    
    def run(self):
        """Start the bot"""
        logger.info("Starting TeraBox Leech Bot...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = TeraBoxLeechBot()
    bot.run()
