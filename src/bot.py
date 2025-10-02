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
    
    async def safe_polling(self):
        """Start polling with conflict handling and retries."""
        max_retries = 5
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Clear any existing webhook first
                await self.app.bot.delete_webhook(drop_pending_updates=True)
                print("✅ Webhook deleted, starting polling...")
                
                # Start polling - this will run until stopped
                await self.app.run_polling()
                break  # Exit loop if polling completes successfully

            except Exception as e:
                if "Conflict" in str(e):
                    print(f"❌ Conflict detected (attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"❌ Unexpected error during polling: {e}")
                    raise e
        else:
            print("❌ Failed to start polling after multiple retries due to conflicts.")
            print("💡 Check if another bot instance is running elsewhere")

    async def start_bot(self):
        """Start the bot with proper async context"""
        logger.info("Starting TeraBox Leech Bot...")
        print("✅ Bot started successfully!")
        print("📍 Press Ctrl+C to stop the bot")
        print("🌐 Health checks available on http://localhost:8000")
        
        # Start the bot with safe polling
        await self.safe_polling()

    # ... keep all your existing handler methods unchanged ...
    # start_handler, help_handler, ping_handler, leech_handler, 
    # message_handler, _process_terabox_request, error_handler

def main():
    """Main function to start the bot"""
    print("🚀 Starting TeraBox Leech Bot...")
    try:
        bot = TeraBoxLeechBot()
        # Use asyncio.run() to properly manage the event loop
        asyncio.run(bot.start_bot())
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        print("💡 Check that:")
        print("  1. config.py exists in the project root")
        print("  2. BOT_TOKEN is set in config.py")
        print("  3. All dependencies are installed")

if __name__ == "__main__":
    main()
