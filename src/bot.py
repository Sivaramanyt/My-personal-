import sys
import os
import logging
import asyncio
from aiohttp import web
import threading

# DEBUG: Add the project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

print(f"🔍 DEBUG: Current directory: {current_dir}")
print(f"🔍 DEBUG: Parent directory: {parent_dir}")
print(f"🔍 DEBUG: Python path: {sys.path}")

try:
    from config import Config
    print("✅ SUCCESS: Imported Config from config")
except ImportError as e:
    print(f"❌ ERROR: Failed to import Config: {e}")
    print("💡 TIP: Make sure config.py exists in the project root directory")
    raise

try:
    from src.terabox_api import TeraBoxAPI
    print("✅ SUCCESS: Imported TeraBoxAPI")
except ImportError as e:
    print(f"❌ ERROR: Failed to import TeraBoxAPI: {e}")
    raise

try:
    from src.downloader import download_and_send_file
    print("✅ SUCCESS: Imported download_and_send_file")
except ImportError as e:
    print(f"❌ ERROR: Failed to import download_and_send_file: {e}")
    raise

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

class HealthServer:
    """Simple HTTP server for health checks without signal handlers"""
    def __init__(self, port=8000):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.runner = None
        
    def setup_routes(self):
        """Setup health check routes"""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        
    async def health_check(self, request):
        """Handle health check requests"""
        return web.Response(text="OK", status=200)
    
    def start(self):
        """Start the health server in a separate thread without signal handlers"""
        def run_server():
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create runner manually to avoid signal handlers
                self.runner = web.AppRunner(self.app)
                loop.run_until_complete(self.runner.setup())
                
                site = web.TCPSite(self.runner, '0.0.0.0', self.port)
                loop.run_until_complete(site.start())
                
                print(f"✅ Health check server started on port {self.port}")
                
                # Run the loop forever without signal handling
                loop.run_forever()
                
            except Exception as e:
                print(f"❌ Health server error: {e}")
        
        # Start the server in a daemon thread
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

class TeraBoxLeechBot:
    def __init__(self):
        print("🔧 Initializing TeraBoxLeechBot...")
        
        # Start health check server first
        self.health_server = HealthServer()
        self.health_server.start()
        
        # Check if BOT_TOKEN is set
        if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("❌ Please set your BOT_TOKEN in config.py - get it from @BotFather on Telegram")
        
        print("✅ BOT_TOKEN is configured")
        self.token = Config.BOT_TOKEN
        self.app = Application.builder().token(self.token).build()
        self.terabox_api = TeraBoxAPI()
        self._setup_handlers()
        print("✅ Bot handlers setup completed")
    
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
        print("🌐 Health checks available on http://localhost:8000")
        self.app.run_polling()

if __name__ == "__main__":
    print("🚀 Starting TeraBox Leech Bot...")
    try:
        bot = TeraBoxLeechBot()
        bot.run()
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        print("💡 Check that:")
        print("  1. config.py exists in the project root")
        print("  2. BOT_TOKEN is set in config.py")
        print("  3. All dependencies are installed")
