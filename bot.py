import os
import sys
import logging
import json
import requests
import re
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils import clean_html, format_recipe_message

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

# Store active sessions (for tracking searches)
user_sessions = {}

# ========================
# TELEGRAM BOT HANDLERS
# ========================

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    """Handle /start and /hello commands"""
    user_name = message.from_user.first_name or "there"
    welcome_text = f"""
👋 *Welcome to RecipeFiinderBot, {user_name}!*

I'm your AI-powered recipe assistant that helps you find delicious recipes based on ingredients you have.

🔍 *How to use:*
• Type any dish name or ingredient (e.g., "pasta", "chicken")
• Use commands for specific searches
• Get detailed recipes with cooking instructions

📌 *Quick Commands:*
/recipe [dish] - Search for specific recipes
/random - Get a random recipe surprise
/cuisine [type] - Search by cuisine (Italian, Mexican, etc.)
/ingredients [list] - Find recipes with ingredients you have
/help - Show all available commands

🎯 *Example:* Try typing "chocolate cake" or "pasta with chicken"

Let's start cooking! 🍳
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    """Handle /help command"""
    help_text = """
📖 *Help Menu - RecipeFiinderBot*

*Basic Commands:*
🔹 /start - Welcome message and introduction
🔹 /help - Show this help menu
🔹 /recipe [dish] - Search for specific recipes
🔹 /random - Get a random recipe
🔹 /cuisine [type] - Search by cuisine type
🔹 /ingredients [list] - Find recipes using ingredients you have

*How to Search:*
• Simply type any food name (e.g., "pizza", "salad")
• Be specific for better results (e.g., "chicken parmesan")
• You'll get top 5 matching recipes

*Cuisine Types:* Italian, Mexican, Chinese, Indian, French, Japanese, Thai, Mediterranean, American, Spanish

*Tips:* 
💡 Use the "View Full Recipe" button for complete instructions
💡 Bookmark your favorite recipes
💡 Share recipes with friends

Need more help? Just ask me anything about cooking! 🍳
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['recipe'])
def search_recipe_command(message):
    """Handle /recipe command"""
    query = message.text.replace('/recipe', '').strip()
    
    if not query:
        bot.reply_to(
            message,
            "❌ Please specify what you want to search!\n"
            "Example: `/recipe pasta carbonara`",
            parse_mode='Markdown'
        )
        return
    
    # Store the query in session
    user_sessions[message.chat.id] = {'query': query}
    
    search_recipes(message, query)

@bot.message_handler(commands=['random'])
def random_recipe(message):
    """Handle /random command"""
    bot.reply_to(message, "🎲 Searching for a random recipe...", parse_mode='Markdown')
    
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('recipes'):
                recipe = data['recipes'][0]
                send_recipe_details(message, recipe)
            else:
                bot.reply_to(
                    message,
                    "😅 No random recipe found. Please try again!",
                    parse_mode='Markdown'
                )
        else:
            bot.reply_to(
                message,
                f"⚠️ API Error (Status {response.status_code}). Please try again later.",
                parse_mode='Markdown'
            )
    except requests.exceptions.Timeout:
        bot.reply_to(
            message,
            "⏰ API request timed out. Please try again in a moment.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Random recipe error: {str(e)}")
        bot.reply_to(
            message,
            f"❌ An error occurred: {str(e)}",
            parse_mode='Markdown'
        )

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
            "Italian, Mexican, Chinese, Indian, French, Japanese, Thai, Mediterranean, American, Spanish",
            parse_mode='Markdown'
        )
        return
    
    bot.reply_to(
        message,
        f"🔍 Searching for {cuisine_type} recipes...",
        parse_mode='Markdown'
    )
    
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "cuisine": cuisine_type,
        "number": 5,
        "addRecipeInformation": True
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                results = data['results'][:5]
                
                # Send each recipe
                for recipe in results:
                    send_recipe_preview(message, recipe)
                
                # Send summary
                bot.send_message(
                    message.chat.id,
                    f"✅ Found {len(results)} {cuisine_type} recipes!",
                    parse_mode='Markdown'
                )
            else:
                bot.reply_to(
                    message,
                    f"😅 No {cuisine_type} recipes found. Try another cuisine!",
                    parse_mode='Markdown'
                )
        else:
            bot.reply_to(
                message,
                f"⚠️ API Error (Status {response.status_code}). Please try again.",
                parse_mode='Markdown'
            )
    except requests.exceptions.Timeout:
        bot.reply_to(
            message,
            "⏰ API request timed out. Please try again.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Cuisine search error: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Error: {str(e)}",
            parse_mode='Markdown'
        )

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
    
    bot.reply_to(
        message,
        f"🛒 Searching recipes with: *{ingredients}*...",
        parse_mode='Markdown'
    )
    
    # Convert comma-separated list to URL-friendly format
    ingredients_list = [i.strip() for i in ingredients.split(',')]
    ingredients_query = ','.join(ingredients_list)
    
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ingredients_query,
        "number": 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                results = data[:5]
                
                for recipe in results:
                    title = recipe.get('title', 'Untitled Recipe')
                    image_url = recipe.get('image', '')
                    missed = len(recipe.get('missedIngredients', []))
                    used = len(recipe.get('usedIngredients', []))
                    
                    caption = f"🍽️ *{title}*\n"
                    caption += f"✅ {used} ingredients you have\n"
                    caption += f"❌ {missed} ingredients missing"
                    
                    keyboard = InlineKeyboardMarkup()
                    button = InlineKeyboardButton(
                        "🔍 View Details",
                        callback_data=f"details_{recipe.get('id', '')}"
                    )
                    keyboard.add(button)
                    
                    if image_url:
                        bot.send_photo(
                            message.chat.id,
                            image_url,
                            caption=caption,
                            parse_mode='Markdown',
                            reply_markup=keyboard
                        )
                    else:
                        bot.send_message(
                            message.chat.id,
                            caption,
                            parse_mode='Markdown',
                            reply_markup=keyboard
                        )
                
                bot.send_message(
                    message.chat.id,
                    f"✅ Found {len(results)} recipes you can make!",
                    parse_mode='Markdown'
                )
            else:
                bot.reply_to(
                    message,
                    "😅 No recipes found with those ingredients. Try different combinations!",
                    parse_mode='Markdown'
                )
        else:
            bot.reply_to(
                message,
                f"⚠️ API Error (Status {response.status_code}). Please try again.",
                parse_mode='Markdown'
            )
    except requests.exceptions.Timeout:
        bot.reply_to(
            message,
            "⏰ API request timed out. Please try again.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ingredients search error: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Error: {str(e)}",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle all other text messages"""
    query = message.text.strip()
    
    if not query:
        bot.reply_to(
            message,
            "Please type a dish name, ingredient, or use a command!\n"
            "Type /help to see all available commands.",
            parse_mode='Markdown'
        )
        return
    
    # Store query in session
    user_sessions[message.chat.id] = {'query': query}
    
    search_recipes(message, query)

def search_recipes(message, query):
    """Search recipes using Spoonacular API"""
    bot.reply_to(
        message,
        f"🔍 Searching for: *{query}*...",
        parse_mode='Markdown'
    )
    
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": query,
        "number": 5,
        "addRecipeInformation": True
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('results'):
                results = data['results'][:5]
                
                # Send each recipe
                for recipe in results:
                    send_recipe_preview(message, recipe)
                
                # Add "Load More" button
                keyboard = InlineKeyboardMarkup()
                button = InlineKeyboardButton(
                    "🔍 Search More",
                    callback_data=f"more_{query}"
                )
                keyboard.add(button)
                
                bot.send_message(
                    message.chat.id,
                    f"✅ Found {len(results)} recipes for '{query}'!",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                bot.reply_to(
                    message,
                    f"😅 No recipes found for '{query}'.\n\n"
                    "Try:\n"
                    "• Using different keywords\n"
                    "• Searching for ingredients\n"
                    "• Using the /cuisine command\n"
                    "• Being more specific (e.g., 'chicken parmesan')",
                    parse_mode='Markdown'
                )
        else:
            bot.reply_to(
                message,
                f"⚠️ API Error (Status {response.status_code}).\n"
                "Please try again in a few moments.",
                parse_mode='Markdown'
            )
            
    except requests.exceptions.Timeout:
        bot.reply_to(
            message,
            "⏰ The search is taking too long. Please try again.",
            parse_mode='Markdown'
        )
    except requests.exceptions.ConnectionError:
        bot.reply_to(
            message,
            "🌐 Connection error. Please check your internet connection and try again.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Search error for '{query}': {str(e)}")
        
        # Fallback response when API fails
        fallback_message = f"""
🍳 *{query.title()} Recipe - Quick Guide*

I couldn't connect to the recipe database right now, but here's a simple approach:

1️⃣ *Gather Ingredients:*
   • Main ingredient: {query}
   • Olive oil
   • Salt and pepper to taste
   • Any other ingredients you like

2️⃣ *Basic Method:*
   • Prepare your {query}
   • Season to taste
   • Cook until done
   • Serve and enjoy!

💡 *Tips:*
• Get creative with your cooking
• Adjust seasoning as needed
• Try different cooking methods

*Search again later for detailed recipes!* 🔄
"""
        bot.reply_to(message, fallback_message, parse_mode='Markdown')

def send_recipe_preview(message, recipe):
    """Send a preview of a recipe"""
    recipe_id = recipe.get('id')
    title = recipe.get('title', 'Untitled Recipe')
    image_url = recipe.get('image', '')
    ready_in = recipe.get('readyInMinutes', 'N/A')
    servings = recipe.get('servings', 'N/A')
    source_url = recipe.get('sourceUrl', '')
    
    # Get ingredients if available
    ingredients = []
    if recipe.get('extendedIngredients'):
        for ing in recipe['extendedIngredients'][:3]:
            ingredients.append(ing.get('original', ''))
    
    # Build message
    caption = f"🍽️ *{title}*\n"
    caption += f"⏱️ Time: {ready_in} mins\n"
    caption += f"👥 Servings: {servings}\n"
    
    if ingredients:
        caption += f"\n📋 *Key Ingredients:*\n"
        for ing in ingredients:
            caption += f"• {ing}\n"
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup()
    view_button = InlineKeyboardButton(
        "👀 View Details",
        callback_data=f"details_{recipe_id}"
    )
    
    if source_url:
        full_button = InlineKeyboardButton(
            "📖 Full Recipe",
            url=source_url
        )
        keyboard.add(view_button, full_button)
    else:
        keyboard.add(view_button)
    
    # Send message with image if available
    try:
        if image_url:
            bot.send_photo(
                message.chat.id,
                image_url,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                caption,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error sending recipe preview: {str(e)}")
        # Fallback: Send without image
        bot.send_message(
            message.chat.id,
            caption,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

def send_recipe_details(message, recipe):
    """Send detailed recipe information"""
    recipe_id = recipe.get('id')
    title = recipe.get('title', 'Untitled Recipe')
    image_url = recipe.get('image', '')
    source_url = recipe.get('sourceUrl', '')
    ready_in = recipe.get('readyInMinutes', 'N/A')
    servings = recipe.get('servings', 'N/A')
    
    # Build detailed message
    caption = f"🍳 *{title}*\n"
    caption += f"⏱️ Ready in: {ready_in} mins\n"
    caption += f"👥 Servings: {servings}\n"
    
    # Add summary if available
    if recipe.get('summary'):
        summary = clean_html(recipe['summary'])[:300]
        caption += f"\n📝 *Description:*\n{summary}...\n"
    
    # Add ingredients
    if recipe.get('extendedIngredients'):
        caption += f"\n📋 *Ingredients:*\n"
        for ing in recipe['extendedIngredients']:
            caption += f"• {ing.get('original', '')}\n"
    
    # Add instructions if available
    if recipe.get('instructions'):
        instructions = clean_html(recipe['instructions'])[:500]
        caption += f"\n📝 *Instructions:*\n{instructions}..."
    
    # Create buttons
    keyboard = InlineKeyboardMarkup()
    
    if source_url:
        full_button = InlineKeyboardButton(
            "🔗 View Full Recipe",
            url=source_url
        )
        keyboard.add(full_button)
    
    # Add recipe ID to allow fetching more info
    save_button = InlineKeyboardButton(
        f"⭐ Save Recipe #{recipe_id if recipe_id else 'N/A'}",
        callback_data="save_recipe"
    )
    keyboard.add(save_button)
    
    # Send message
    try:
        if image_url:
            bot.send_photo(
                message.chat.id,
                image_url,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                caption,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error sending recipe details: {str(e)}")
        # Fallback
        bot.send_message(
            message.chat.id,
            caption[:1000],
            parse_mode='Markdown',
            reply_markup=keyboard
        )

# ========================
# CALLBACK HANDLERS
# ========================

@bot.callback_query_handler(func=lambda call: call.data.startswith('details_'))
def handle_details_callback(call):
    """Handle 'View Details' button clicks"""
    recipe_id = call.data.replace('details_', '')
    bot.answer_callback_query(call.id, "Loading recipe details...")
    
    # Fetch full recipe details
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        "apiKey": SPOONACULAR_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            recipe = response.json()
            
            # Create a message object to send details
            class MockMessage:
                def __init__(self, chat_id):
                    self.chat = type('obj', (object,), {'id': chat_id})()
            
            msg = MockMessage(call.message.chat.id)
            send_recipe_details(msg, recipe)
        else:
            bot.send_message(
                call.message.chat.id,
                "❌ Could not load recipe details. Please try again.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Details callback error: {str(e)}")
        bot.send_message(
            call.message.chat.id,
            f"❌ Error loading details: {str(e)}",
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('more_'))
def handle_more_callback(call):
    """Handle 'Search More' button clicks"""
    query = call.data.replace('more_', '')
    bot.answer_callback_query(call.id, f"Searching more for '{query}'...")
    
    # Update the search query
    search_recipes(call.message, query)

@bot.callback_query_handler(func=lambda call: call.data == 'save_recipe')
def handle_save_callback(call):
    """Handle 'Save Recipe' button clicks"""
    bot.answer_callback_query(
        call.id,
        "⭐ Recipe saved to favorites! (Feature coming soon)",
        show_alert=True
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
        'version': '1.0.0'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check for Railway"""
    return jsonify({'status': 'healthy'}), 200

# ========================
# SETUP WEBHOOK
# ========================

def setup_webhook():
    """Set up Telegram webhook"""
    if not WEBHOOK_URL:
        logger.warning("No WEBHOOK_URL set. Using polling mode.")
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
            else:
                logger.error(f"❌ Webhook setup failed: {data.get('description')}")
                return False
        else:
            logger.error(f"❌ Webhook HTTP error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Webhook setup exception: {str(e)}")
        return False

# ========================
# APPLICATION ENTRY POINT
# ========================

if __name__ == '__main__':
    # Set up webhook or use polling
    if Config.USE_WEBHOOK:
        setup_webhook()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Use polling mode (for development)
        logger.info("Starting bot in polling mode...")
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"Bot polling error: {str(e)}")
            sys.exit(1)
