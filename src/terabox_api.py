import requests
import logging
import re
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
            
            # Debug: Print the actual API response structure
            print(f"🔍 DEBUG: Full API Response: {data}")
            
            # Parse the actual API response structure with emoji keys
            if data.get("✅ Status") == "Success":
                # Access the first file in the "📚 Extracted Info" list
                extracted_info = data["📚 Extracted Info"][0]
                
                filename = extracted_info.get("📁 Title", "Unnamed_File")
                size_str = extracted_info.get("📊 Size", "0 MB")
                direct_link = extracted_info.get("🔗 Direct Download Link", "")
                
                # Convert size string (like "20.29 MB") to bytes
                size_bytes = self._convert_size_to_bytes(size_str)
                
                logger.info(f"Successfully retrieved link for: {filename}")
                return {
                    "success": True,
                    "filename": filename,
                    "direct_link": direct_link,
                    "size": size_bytes,
                    "size_str": size_str  # Keep original string for display
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

    def _convert_size_to_bytes(self, size_str: str) -> int:
        """
        Convert size string like "20.29 MB" to bytes
        """
        try:
            # Extract number and unit
            match = re.match(r"([\d.]+)\s*([KMGTP]?B)", size_str.upper())
            if not match:
                return 0
                
            size_value = float(match.group(1))
            unit = match.group(2)
            
            # Convert to bytes
            units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
            return int(size_value * units.get(unit, 1))
            
        except Exception as e:
            logger.warning(f"Could not parse size string '{size_str}': {e}")
            return 0
