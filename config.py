import os

class Config:
    # Get bot token from environment variable or use default
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # TeraBox API configuration
    TERABOX_API_URL = "https://wdzone-terabox-api.vercel.app/api"
    
    # Download settings
    DOWNLOAD_DIR = "downloads"
    MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB in bytes
    
    # Bot settings
    OWNER_ID = os.environ.get("OWNER_ID", "123456789")

# Quick validation
if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("⚠️  WARNING: Please set your BOT_TOKEN in config.py")
