import os

class Config:
    """Bot configuration from environment variables"""
    
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Spoonacular API Key
    SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')
    if not SPOONACULAR_API_KEY:
        raise ValueError("SPOONACULAR_API_KEY environment variable is required")
    
    # Webhook URL (set this on Railway)
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    
    # Use webhook (True) or polling (False)
    USE_WEBHOOK = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    
    # Flask configuration
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # API settings
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 15))
    MAX_RECIPES = int(os.getenv('MAX_RECIPES', 5))
