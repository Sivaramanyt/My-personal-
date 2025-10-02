import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    TERABOX_API_URL = "https://wdzone-terabox-api.vercel.app/api"
    DOWNLOAD_DIR = "downloads"
