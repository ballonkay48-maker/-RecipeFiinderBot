import re
import random

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return text
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
        original = ing.get('original', '') if isinstance(ing, dict) else str(ing)
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

# ========================
# MOCK RECIPE DATABASE (FALLBACK)
# ========================

MOCK_RECIPES = {
    'pasta': [
        {
            'title': 'Classic Spaghetti Carbonara',
            'image': '',
            'readyInMinutes': 30,
            'servings': 4,
            'extendedIngredients': [
                {'original': '400g spaghetti'},
                {'original': '100g pancetta or bacon'},
                {'original': '2 large eggs'},
                {'original': '50g Parmesan cheese'},
                {'original': '2 cloves garlic'}
            ],
            'summary': 'A classic Italian pasta dish made with eggs, cheese, pancetta, and pepper.',
            'instructions': '1. Cook pasta in salted water until al dente.\n2. In a bowl, whisk eggs and Parmesan cheese.\n3. Cook pancetta until crispy.\n4. Combine everything and serve hot!'
        },
        {
            'title': 'Pasta with Tomato Basil Sauce',
            'image': '',
            'readyInMinutes': 25,
            'servings': 4,
            'extendedIngredients': [
                {'original': '400g pasta'},
                {'original': '800g canned tomatoes'},
                {'original': 'Fresh basil leaves'},
                {'original': '3 cloves garlic'},
                {'original': 'Olive oil'}
            ],
            'summary': 'A simple and delicious pasta dish with fresh tomato and basil sauce.',
            'instructions': '1. Cook pasta.\n2. Sauté garlic in olive oil.\n3. Add tomatoes and simmer.\n4. Mix with pasta and top with basil.'
        }
    ],
    'chicken': [
        {
            'title': 'Grilled Chicken Breast',
            'image': '',
            'readyInMinutes': 45,
            'servings': 4,
            'extendedIngredients': [
                {'original': '4 chicken breasts'},
                {'original': 'Olive oil'},
                {'original': 'Lemon juice'},
                {'original': 'Garlic powder'},
                {'original': 'Paprika'}
            ],
            'summary': 'Juicy grilled chicken breast with Mediterranean spices.',
            'instructions': '1. Marinate chicken with oil, lemon, and spices.\n2. Grill for 6-8 minutes per side.\n3. Let rest before serving.'
        }
    ],
    'salad': [
        {
            'title': 'Fresh Garden Salad',
            'image': '',
            'readyInMinutes': 15,
            'servings': 4,
            'extendedIngredients': [
                {'original': 'Mixed greens'},
                {'original': 'Cherry tomatoes'},
                {'original': 'Cucumber'},
                {'original': 'Olive oil'},
                {'original': 'Balsamic vinegar'}
            ],
            'summary': 'A refreshing salad with seasonal vegetables.',
            'instructions': '1. Wash and dry greens.\n2. Chop vegetables.\n3. Mix with dressing and serve.'
        }
    ]
}

def get_mock_recipe(query):
    """Get a mock recipe based on the search query"""
    query_lower = query.lower()
    
    # Search through mock recipes
    for key, recipes in MOCK_RECIPES.items():
        if key in query_lower:
            return random.choice(recipes)
    
    # Default mock recipe if no match found
    return {
        'title': f'{query.title()} Recipe',
        'image': '',
        'readyInMinutes': random.randint(20, 60),
        'servings': random.randint(2, 6),
        'extendedIngredients': [
            {'original': f'2 cups {query}'},
            {'original': 'Olive oil'},
            {'original': 'Salt and pepper'},
            {'original': 'Your favorite spices'},
            {'original': 'Fresh herbs'}
        ],
        'summary': f'A delicious recipe featuring {query}. Perfect for any occasion!',
        'instructions': f'1. Prepare the {query}.\n2. Season to taste.\n3. Cook until done.\n4. Serve and enjoy!'
    }
