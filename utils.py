import re

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return text
    # Remove HTML tags
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def truncate_text(text, max_length=300):
    """Truncate text to a maximum length"""
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def format_ingredients(ingredients):
    """Format a list of ingredients"""
    if not ingredients:
        return "No ingredients listed."
    
    formatted = []
    for ing in ingredients:
        original = ing.get('original', '')
        if original:
            formatted.append(f"• {original}")
    
    return '\n'.join(formatted)

def get_emoji_for_cuisine(cuisine):
    """Get emoji for different cuisine types"""
    emoji_map = {
        'italian': '🇮🇹',
        'mexican': '🇲🇽',
        'chinese': '🇨🇳',
        'indian': '🇮🇳',
        'french': '🇫🇷',
        'japanese': '🇯🇵',
        'thai': '🇹🇭',
        'mediterranean': '🌊',
        'american': '🇺🇸',
        'spanish': '🇪🇸'
    }
    return emoji_map.get(cuisine.lower(), '🍽️')
