import requests
import logging
from config import Config

logger = logging.getLogger(__name__)

class TeraBoxAPI:
    def __init__(self):
        self.api_url = Config.TERABOX_API_URL

    def get_direct_link(self, terabox_url: str) -> dict:
        """
        Fetches the direct download link from the TeraBox API.
        Returns a dictionary with file info and direct link.
        """
        try:
            payload = {"url": terabox_url}
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"Requesting direct link for: {terabox_url}")
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                file_info = data["data"]
                logger.info(f"Successfully retrieved link for: {file_info.get('filename', 'N/A')}")
                return {
                    "success": True,
                    "filename": file_info.get("filename", "Unnamed_File"),
                    "direct_link": file_info.get("link"),
                    "size": file_info.get("size", 0)
                }
            else:
                error_msg = data.get("message", "Unknown API error")
                logger.error(f"API returned error: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error occurred: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
