#!/usr/bin/env python3
"""
TeraBox Leech Bot - Startup Script
Run this file to start the bot directly
"""

import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bot import TeraBoxLeechBot

def main():
    """Main function to start the bot"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🤖 Starting TeraBox Leech Bot...")
    print("📍 Make sure you have set BOT_TOKEN in config.py")
    
    try:
        bot = TeraBoxLeechBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
