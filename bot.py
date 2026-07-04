import os
import sys
import logging
import json
import requests
import random
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
WEBHOOK_URL = Config.WEBHOOK_URL

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
    
    if HAS_API:
        api_status = "✅ Connected to recipe database"
    else:
        api_status = "📚 Using built-in recipe collection"
    
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

{api_status}
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

Need help? Just ask me anything! 🍳
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
    
    # Try API first if available
    if HAS_API:
        try:
            url = "https://api.spoonacular.com/recipes/random"
            params = {
                "apiKey": SPOONACULAR_API_KEY,
                "number": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('recipes'):
                    recipe = data['recipes'][0]
                    send_recipe_details(message, recipe)
                    return
        except Exception as e:
            logger.error(f"Random recipe API error: {str(e)}")
    
    # Fallback: Use mock recipes
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
    
    if HAS_API:
        # Use API
        bot.reply_to(message, f"🔍 Searching for {cuisine_type} recipes...", parse_mode='Markdown')
        
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "cuisine": cuisine_type,
            "number": 3,
            "addRecipeInformation": True
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    results = data['results'][:3]
                    for recipe in results:
                        send_recipe_preview(message, recipe)
                    
                    bot.send_message(
                        message.chat.id,
                        f"✅ Found {len(results)} {cuisine_type} recipes!",
                        parse_mode='Markdown'
                    )
                    return
        except Exception as e:
            logger.error(f"Cuisine search API error: {str(e)}")
    
    # Fallback: Suggest mock recipes
    mock_keywords = {
        'italian': ['pasta', 'spaghetti'],
        'mexican': ['tacos', 'enchiladas'],
        'chinese': ['stir fry', 'noodles'],
        'indian': ['curry', 'tikka']
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
    
    if HAS_API:
        bot.reply_to(message, f"🛒 Searching recipes with: *{ingredients}*...", parse_mode='Markdown')
        
        ingredients_list = [i.strip() for i in ingredients.split(',')]
        ingredients_query = ','.join(ingredients_list)
        
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "ingredients": ingredients_query,
            "number": 3
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    for recipe in data[:3]:
                        title = recipe.get('title', 'Untitled Recipe')
                        image_url = recipe.get('image', '')
                        missed = len(recipe.get('missedIngredients', []))
                        used = len(recipe.get('usedIngredients', []))
                        
                        caption = f"🍽️ *{title}*\n"
                        caption += f"✅ {used} ingredients you have\n"
                        caption += f"❌ {missed} ingredients missing"
                        
                        if image_url:
                            bot.send_photo(message.chat.id, image_url, caption=caption, parse_mode='Markdown')
                        else:
                            bot.send_message(message.chat.id, caption, parse_mode='Markdown')
                    
                    bot.send_message(
                        message.chat.id,
                        f"✅ Found {len(data[:3])} recipes you can make!",
                        parse_mode='Markdown'
                    )
                    return
        except Exception as e:
            logger.error(f"Ingredients search API error: {str(e)}")
    
    # Fallback suggestion
    bot.reply_to(
        message,
        f"🛒 Searching for recipes with: *{ingredients}*\n\n"
        f"Try using one of these in your search:\n"
        f"• 'pasta with {ingredients.split(',')[0]}'\n"
        f"• 'chicken and rice'\n"
        f"• 'simple vegetable soup'\n\n"
        f"Or try searching by dish name! 🍳",
        parse_mode='Markdown'
    )

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
    """Search recipes using Spoonacular API or fallback to mock"""
    bot.reply_to(message, f"🔍 Searching for: *{query}*...", parse_mode='Markdown')
    
    # Try API first if available
    if HAS_API:
        try:
            url = "https://api.spoonacular.com/recipes/complexSearch"
            params = {
                "apiKey": SPOONACULAR_API_KEY,
                "query": query,
                "number": Config.MAX_RECIPES,
                "addRecipeInformation": True
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results'):
                    results = data['results'][:Config.MAX_RECIPES]
                    
                    for recipe in results:
                        send_recipe_preview(message, recipe)
                    
                    bot.send_message(
                        message.chat.id,
                        f"✅ Found {len(results)} recipes for '{query}'!",
                        parse_mode='Markdown'
                    )
                    return
        except Exception as e:
            logger.error(f"API search error for '{query}': {str(e)}")
    
    # Fallback: Use mock recipes
    recipe = get_mock_recipe(query)
    send_mock_recipe_details(message, recipe, query)

def send_recipe_preview(message, recipe):
    """Send a preview of a recipe from API"""
    recipe_id = recipe.get('id')
    title = recipe.get('title', 'Untitled Recipe')
    image_url = recipe.get('image', '')
    ready_in = recipe.get('readyInMinutes', 'N/A')
    servings = recipe.get('servings', 'N/A')
    
    caption = f"🍽️ *{title}*\n"
    caption += f"⏱️ Time: {ready_in} mins\n"
    caption += f"👥 Servings: {servings}\n"
    
    keyboard = InlineKeyboardMarkup()
    view_button = InlineKeyboardButton(
        "👀 View Details",
        callback_data=f"details_{recipe_id}"
    )
    keyboard.add(view_button)
    
    try:
        if image_url:
            bot.send_photo(message.chat.id, image_url, caption=caption, parse_mode='Markdown', reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, caption, parse_mode='Markdown', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error sending recipe preview: {str(e)}")
        bot.send_message(message.chat.id, caption, parse_mode='Markdown', reply_markup=keyboard)

def send_recipe_details(message, recipe):
    """Send detailed recipe information from API"""
    title = recipe.get('title', 'Untitled Recipe')
    image_url = recipe.get('image', '')
    ready_in = recipe.get('readyInMinutes', 'N/A')
    servings = recipe.get('servings', 'N/A')
    
    caption = f"🍳 *{title}*\n"
    caption += f"⏱️ Ready in: {ready_in} mins\n"
    caption += f"👥 Servings: {servings}\n"
    
    if recipe.get('summary'):
        summary = clean_html(recipe['summary'])[:300]
        caption += f"\n📝 *Description:*\n{summary}...\n"
    
    if recipe.get('extendedIngredients'):
        caption += f"\n📋 *Ingredients:*\n"
        for ing in recipe['extendedIngredients'][:5]:
            caption += f"• {ing.get('original', '')}\n"
    
    if recipe.get('instructions'):
        instructions = clean_html(recipe['instructions'])[:400]
        caption += f"\n📝 *Instructions:*\n{instructions}..."
    
    try:
        if image_url:
            bot.send_photo(message.chat.id, image_url, caption=caption[:1000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, caption[:1000], parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending recipe details: {str(e)}")
        bot.send_message(message.chat.id, caption[:1000], parse_mode='Markdown')

def send_mock_recipe_details(message, recipe, query):
    """Send a mock recipe when API is unavailable"""
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
    
    if not HAS_API:
        caption += "\n\nℹ️ *Note:* Using built-in recipe collection. Get your free Spoonacular API key for more recipes!"
    
    bot.send_message(message.chat.id, caption[:1000], parse_mode='Markdown')

# ========================
# CALLBACK HANDLERS
# ========================

@bot.callback_query_handler(func=lambda call: call.data.startswith('details_'))
def handle_details_callback(call):
    """Handle 'View Details' button clicks"""
    recipe_id = call.data.replace('details_', '')
    bot.answer_callback_query(call.id, "Loading recipe details...")
    
    if HAS_API and recipe_id.isdigit():
        try:
            url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            params = {"apiKey": SPOONACULAR_API_KEY}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                recipe = response.json()
                send_recipe_details(call.message, recipe)
                return
        except Exception as e:
            logger.error(f"Details callback error: {str(e)}")
    
    # Fallback
    bot.send_message(
        call.message.chat.id,
        "📚 Recipe details are currently in mock mode.\n"
        "Try searching for a specific dish like 'pasta' or 'chicken'!",
        parse_mode='Markdown'
    )

# ========================
# FLASK WEBHOOK ROUTES
# ========================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook requests from Telegram"""
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'active',
        'bot': '@RecipeFiinderBot',
        'version': '1.0.0',
        'api_connected': HAS_API
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check for Railway"""
    return jsonify({'status': 'healthy', 'api': HAS_API}), 200

# ========================
# SETUP WEBHOOK
# ========================

def setup_webhook():
    """Set up Telegram webhook"""
    if not WEBHOOK_URL:
        logger.info("⚠️ No WEBHOOK_URL set. Using polling mode.")
        return False
    
    webhook_url = f"{WEBHOOK_URL}/webhook"
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={'url': webhook_url}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                logger.info(f"✅ Webhook set successfully: {webhook_url}")
                return True
    except Exception as e:
        logger.error(f"❌ Webhook setup exception: {str(e)}")
    
    return False

# ========================
# APPLICATION ENTRY POINT
# ========================

if __name__ == '__main__':
    logger.info("🤖 RecipeFiinderBot starting...")
    logger.info(f"📊 API Status: {'Connected' if HAS_API else 'Using mock recipes'}")
    
    if Config.USE_WEBHOOK:
        setup_webhook()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        logger.info("Starting bot in polling mode...")
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"Bot polling error: {str(e)}")
            sys.exit(1)
