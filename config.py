import os

class Config:
    """Bot configuration from environment variables"""
    
    # Telegram Bot Token (REQUIRED)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Spoonacular API Key (OPTIONAL - bot works without it)
    SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY', '')
    
    # API settings
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 15))
    MAX_RECIPES = int(os.getenv('MAX_RECIPES', 3))
