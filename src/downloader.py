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
        
        # Download the file with progress tracking
        response = requests.get(file_info["direct_link"], stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Update progress every 5MB
                    if total_size > 0 and downloaded_size % (5 * 1024 * 1024) == 0:
                        progress = (downloaded_size / total_size) * 100
                        await status_msg.edit_text(
                            f"⬇️ Downloading **{file_info['filename']}**...\n"
                            f"📊 Progress: `{progress:.1f}%`"
                        )
        
        file_size = os.path.getsize(download_path)
        file_size_mb = file_size / (1024 * 1024)
        
        await status_msg.edit_text(
            f"✅ Download completed!\n"
            f"📦 File size: `{file_size_mb:.2f} MB`\n"
            f"📤 Uploading to Telegram..."
        )
        
        # Send file to user
        with open(download_path, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=file_info["filename"],
                caption=f"**{file_info['filename']}**\n📦 Size: `{file_size_mb:.2f} MB`"
            )
        
        await status_msg.edit_text("✅ File sent successfully!")
        
        # Cleanup
        try:
            os.remove(download_path)
            logger.info(f"Cleaned up temporary file: {download_path}")
        except Exception as e:
            logger.warning(f"Could not delete temporary file: {str(e)}")
            
    except Exception as e:
        logger.error(f"Download/Upload error: {str(e)}")
        await status_msg.edit_text(f"❌ Error during download/upload:\n`{str(e)}`")
        
        # Cleanup on error
        try:
            if os.path.exists(download_path):
                os.remove(download_path)
        except:
            pass
