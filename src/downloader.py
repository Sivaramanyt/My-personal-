import requests
import os
import logging
from config import Config
from telegram import Update
from telegram.types import Message

logger = logging.getLogger(__name__)

async def download_and_send_file(update: Update, status_msg: Message, file_info: dict):
    """
    Download file from direct link and send to Telegram
    """
    download_path = os.path.join(Config.DOWNLOAD_DIR, file_info["filename"])
    
    try:
        # Create download directory
        os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
        
        await status_msg.edit_text(f"⬇️ Downloading **{file_info['filename']}**...")
        
        # Download the file
        response = requests.get(file_info["direct_link"], stream=True)
        response.raise_for_status()
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        await status_msg.edit_text(f"📤 Uploading **{file_info['filename']}** to Telegram...")
        
        # Send file to user
        with open(download_path, 'rb') as file:
            await update.message.reply_document(
                document=file,
                caption=f"**{file_info['filename']}**"
            )
        
        await status_msg.edit_text("✅ Download completed successfully!")
        
        # Cleanup
        try:
            os.remove(download_path)
        except Exception as e:
            logger.warning(f"Could not delete temporary file: {str(e)}")
            
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        await status_msg.edit_text(f"❌ Download failed:\n`{str(e)}`")
        
        # Cleanup on error
        try:
            if os.path.exists(download_path):
                os.remove(download_path)
        except:
            pass
