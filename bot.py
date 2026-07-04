import os
import sys
import logging
import json
import requests
import random
import time
import threading
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils import clean_html, format_ingredients, get_mock_recipe, MOCK_RECIPES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Bot configuration
BOT_TOKEN = Config.TELEGRAM_BOT_TOKEN
SPOONACULAR_API_KEY = Config.SPOONACULAR_API_KEY

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Track user sessions
user_sessions = {}

# Check if we have Spoonacular API
HAS_API = bool(SPOONACULAR_API_KEY)
if not HAS_API:
    logger.warning("⚠️ SPOONACULAR_API_KEY not set. Using mock recipes only.")

# ========================
# TELEGRAM BOT HANDLERS
# ========================

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    """Handle /start and /hello commands"""
    user_name = message.from_user.first_name or "there"
    
    welcome_text = f"""
👋 *Welcome to RecipeFiinderBot, {user_name}!*

I'm your recipe assistant that helps you find delicious recipes!

🔍 *How to use:*
• Type any dish name (e.g., "pasta", "chicken")
• Use commands for specific searches
• Get detailed recipes with instructions

📌 *Quick Commands:*
/recipe [dish] - Search for recipes
/random - Get a random recipe
/cuisine [type] - Search by cuisine
/ingredients [list] - Find recipes by ingredients
/help - Show all commands

🎯 *Example:* Try typing "pasta" or "chicken"

📚 Using built-in recipe collection
Happy cooking! 🍳
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    """Handle /help command"""
    help_text = """
📖 *Help Menu - RecipeFiinderBot*

*Basic Commands:*
🔹 /start - Welcome message
🔹 /help - Show this menu
🔹 /recipe [dish] - Search for recipes
🔹 /random - Get a random recipe
🔹 /cuisine [type] - Search by cuisine
🔹 /ingredients [list] - Find by ingredients

*How to Search:*
• Type any food name (e.g., "pizza")
• Use specific ingredients (e.g., "chicken rice")
• Try different cuisines

*Cuisine Types:* Italian, Mexican, Chinese, Indian, French, Japanese, Thai, Mediterranean

*Tips:* 
💡 Be specific for better results
💡 Try different search terms
💡 Get creative with ingredients
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['recipe'])
def search_recipe_command(message):
    """Handle /recipe command"""
    query = message.text.replace('/recipe', '').strip()
    
    if not query:
        bot.reply_to(
            message,
            "❌ Please specify what to search!\n"
            "Example: `/recipe pasta carbonara`",
            parse_mode='Markdown'
        )
        return
    
    search_recipes(message, query)

@bot.message_handler(commands=['random'])
def random_recipe(message):
    """Handle /random command"""
    bot.reply_to(message, "🎲 Finding a random recipe for you...", parse_mode='Markdown')
    
    # Use mock recipes
    mock_categories = list(MOCK_RECIPES.keys())
    random_category = random.choice(mock_categories)
    mock_recipes = MOCK_RECIPES[random_category]
    recipe = random.choice(mock_recipes)
    
    send_mock_recipe_details(message, recipe, random_category)

@bot.message_handler(commands=['cuisine'])
def cuisine_search(message):
    """Handle /cuisine command"""
    cuisine_type = message.text.replace('/cuisine', '').strip()
    
    if not cuisine_type:
        bot.reply_to(
            message,
            "🍕 Please specify a cuisine type!\n"
            "Example: `/cuisine Italian` or `/cuisine Mexican`\n\n"
            "*Popular cuisines:*\n"
            "Italian, Mexican, Chinese, Indian, French, Japanese, Thai, Mediterranean",
            parse_mode='Markdown'
        )
        return
    
    # Suggest mock recipes for cuisine
    mock_keywords = {
        'italian': ['pasta', 'spaghetti', 'lasagna'],
        'mexican': ['tacos', 'enchiladas', 'burritos'],
        'chinese': ['stir fry', 'noodles', 'fried rice'],
        'indian': ['curry', 'tikka', 'biryani'],
        'french': ['croissant', 'quiche', 'ratatouille'],
        'japanese': ['sushi', 'ramen', 'teriyaki'],
        'thai': ['pad thai', 'curry', 'noodles'],
        'mediterranean': ['salad', 'hummus', 'falafel']
    }
    
    suggestions = mock_keywords.get(cuisine_type.lower(), ['pasta', 'salad', 'chicken'])
    suggestion_text = f"🍽️ *{cuisine_type.title()} Cuisine Recipes*\n\n"
    suggestion_text += "Try searching for these dishes:\n"
    for suggestion in suggestions[:3]:
        suggestion_text += f"• {suggestion.title()}\n"
    suggestion_text += "\n💡 Just type the dish name to search!"
    
    bot.reply_to(message, suggestion_text, parse_mode='Markdown')

@bot.message_handler(commands=['ingredients'])
def ingredients_search(message):
    """Handle /ingredients command"""
    ingredients = message.text.replace('/ingredients', '').strip()
    
    if not ingredients:
        bot.reply_to(
            message,
            "🛒 Please list the ingredients you have!\n"
            "Example: `/ingredients chicken, rice, vegetables`",
            parse_mode='Markdown'
        )
        return
    
    # Suggest recipes with ingredients
    suggestions = ingredients.split(',')
    main_ingredient = suggestions[0].strip() if suggestions else 'chicken'
    
    suggestion_text = f"🛒 Searching for recipes with: *{ingredients}*\n\n"
    suggestion_text += f"Try searching for:\n"
    suggestion_text += f"• '{main_ingredient} pasta'\n"
    suggestion_text += f"• '{main_ingredient} salad'\n"
    suggestion_text += f"• '{main_ingredient} soup'\n\n"
    suggestion_text += "💡 Or type any dish name to search!"
    
    bot.reply_to(message, suggestion_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle all other text messages"""
    query = message.text.strip()
    
    if not query:
        bot.reply_to(
            message,
            "Please type a dish name or use a command!\n"
            "Type /help to see all available commands.",
            parse_mode='Markdown'
        )
        return
    
    user_sessions[message.chat.id] = {'query': query}
    search_recipes(message, query)

def search_recipes(message, query):
    """Search recipes using mock database"""
    bot.reply_to(message, f"🔍 Searching for: *{query}*...", parse_mode='Markdown')
    
    # Use mock recipes
    recipe = get_mock_recipe(query)
    send_mock_recipe_details(message, recipe, query)

def send_mock_recipe_details(message, recipe, query):
    """Send a mock recipe"""
    title = recipe.get('title', f'{query.title()} Recipe')
    ready_in = recipe.get('readyInMinutes', '30-45')
    servings = recipe.get('servings', '4')
    ingredients = recipe.get('extendedIngredients', [{'original': 'Your favorite ingredients'}])
    instructions = recipe.get('instructions', f'1. Prepare your {query}\n2. Cook to perfection\n3. Enjoy!')
    
    caption = f"🍳 *{title}*\n"
    caption += f"⏱️ Time: {ready_in} mins\n"
    caption += f"👥 Servings: {servings}\n"
    
    caption += f"\n📋 *Ingredients:*\n"
    for ing in ingredients[:5]:
        if isinstance(ing, dict):
            caption += f"• {ing.get('original', '')}\n"
        else:
            caption += f"• {ing}\n"
    
    caption += f"\n📝 *Instructions:*\n{instructions}\n"
    
    caption += "\n💡 *Tips:*\n"
    caption += "• Adjust seasonings to taste\n"
    caption += "• Substitute ingredients as needed\n"
    caption += "• Have fun and get creative!"
    
    caption += "\n\nℹ️ *Note:* Using built-in recipe collection. Get your free Spoonacular API key at spoonacular.com for more recipes!"
    
    bot.send_message(message.chat.id, caption[:1000], parse_mode='Markdown')

# ========================
# FLASK ROUTES (For Railway Health Checks)
# ========================

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'bot': '@RecipeFiinderBot',
        'version': '1.0.0',
        'mode': 'polling',
        'api_connected': HAS_API
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check for Railway"""
    return jsonify({'status': 'healthy', 'api': HAS_API}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint (kept for compatibility)"""
    return jsonify({'status': 'ok'}), 200

# ========================
# START BOT IN BACKGROUND THREAD
# ========================

def start_bot_polling():
    """Start the bot in polling mode"""
    logger.info("🤖 Starting bot polling in background thread...")
    
    # Remove any existing webhook
    try:
        bot.remove_webhook()
        logger.info("✅ Webhook removed")
    except Exception as e:
        logger.warning(f"Could not remove webhook: {e}")
    
    # Start polling with retry
    while True:
        try:
            logger.info("🔄 Bot is listening for messages...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            logger.error(f"❌ Polling error: {str(e)}")
            logger.info("🔄 Restarting polling in 5 seconds...")
            time.sleep(5)

# ========================
# APPLICATION ENTRY POINT
# ========================

# Start bot polling in background thread when app starts
bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
bot_thread.start()
logger.info("✅ Bot polling thread started")

# For local testing
if __name__ == '__main__':
    logger.info("🚀 Starting Flask app with bot polling...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
