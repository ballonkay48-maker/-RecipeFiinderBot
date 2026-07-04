import re
import random

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return text
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

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

# ========================
# MOCK RECIPE DATABASE (FALLBACK)
# ========================

MOCK_RECIPES = {
    'pasta': [
        {
            'title': 'Classic Spaghetti Carbonara',
            'readyInMinutes': 30,
            'servings': 4,
            'extendedIngredients': [
                {'original': '400g spaghetti'},
                {'original': '100g pancetta or bacon'},
                {'original': '2 large eggs'},
                {'original': '50g Parmesan cheese'},
                {'original': '2 cloves garlic'}
            ],
            'instructions': '1. Cook pasta in salted water until al dente.\n2. In a bowl, whisk eggs and Parmesan cheese.\n3. Cook pancetta until crispy.\n4. Combine everything and serve hot!'
        },
        {
            'title': 'Pasta with Tomato Basil Sauce',
            'readyInMinutes': 25,
            'servings': 4,
            'extendedIngredients': [
                {'original': '400g pasta'},
                {'original': '800g canned tomatoes'},
                {'original': 'Fresh basil leaves'},
                {'original': '3 cloves garlic'},
                {'original': 'Olive oil'}
            ],
            'instructions': '1. Cook pasta.\n2. Sauté garlic in olive oil.\n3. Add tomatoes and simmer.\n4. Mix with pasta and top with basil.'
        },
        {
            'title': 'Creamy Pasta Alfredo',
            'readyInMinutes': 20,
            'servings': 4,
            'extendedIngredients': [
                {'original': '400g fettuccine'},
                {'original': '200ml heavy cream'},
                {'original': '50g butter'},
                {'original': '100g Parmesan cheese'},
                {'original': 'Salt and pepper'}
            ],
            'instructions': '1. Cook pasta.\n2. Melt butter and add cream.\n3. Add Parmesan and stir until smooth.\n4. Combine with pasta and serve!'
        }
    ],
    'chicken': [
        {
            'title': 'Grilled Lemon Chicken Breast',
            'readyInMinutes': 45,
            'servings': 4,
            'extendedIngredients': [
                {'original': '4 chicken breasts'},
                {'original': 'Olive oil'},
                {'original': 'Lemon juice'},
                {'original': 'Garlic powder'},
                {'original': 'Paprika'}
            ],
            'instructions': '1. Marinate chicken with oil, lemon, and spices.\n2. Grill for 6-8 minutes per side.\n3. Let rest before serving.'
        },
        {
            'title': 'Chicken Stir Fry',
            'readyInMinutes': 30,
            'servings': 4,
            'extendedIngredients': [
                {'original': '500g chicken breast'},
                {'original': 'Mixed vegetables'},
                {'original': 'Soy sauce'},
                {'original': 'Garlic'},
                {'original': 'Ginger'}
            ],
            'instructions': '1. Cut chicken into strips.\n2. Stir-fry in hot oil.\n3. Add vegetables and sauce.\n4. Cook until done and serve with rice.'
        }
    ],
    'salad': [
        {
            'title': 'Fresh Garden Salad',
            'readyInMinutes': 15,
            'servings': 4,
            'extendedIngredients': [
                {'original': 'Mixed greens'},
                {'original': 'Cherry tomatoes'},
                {'original': 'Cucumber'},
                {'original': 'Olive oil'},
                {'original': 'Balsamic vinegar'}
            ],
            'instructions': '1. Wash and dry greens.\n2. Chop vegetables.\n3. Mix with dressing and serve.'
        },
        {
            'title': 'Caesar Salad',
            'readyInMinutes': 20,
            'servings': 4,
            'extendedIngredients': [
                {'original': 'Romaine lettuce'},
                {'original': 'Croutons'},
                {'original': 'Parmesan cheese'},
                {'original': 'Caesar dressing'},
                {'original': 'Chicken (optional)'}
            ],
            'instructions': '1. Chop lettuce.\n2. Add croutons and cheese.\n3. Toss with dressing.\n4. Top with chicken if desired.'
        }
    ],
    'pizza': [
        {
            'title': 'Margherita Pizza',
            'readyInMinutes': 45,
            'servings': 4,
            'extendedIngredients': [
                {'original': 'Pizza dough'},
                {'original': 'Tomato sauce'},
                {'original': 'Mozzarella cheese'},
                {'original': 'Fresh basil'},
                {'original': 'Olive oil'}
            ],
            'instructions': '1. Roll out dough.\n2. Spread sauce.\n3. Top with cheese and basil.\n4. Bake until golden.'
        }
    ],
    'soup': [
        {
            'title': 'Tomato Soup',
            'readyInMinutes': 30,
            'servings': 4,
            'extendedIngredients': [
                {'original': '800g tomatoes'},
                {'original': 'Onion'},
                {'original': 'Garlic'},
                {'original': 'Vegetable broth'},
                {'original': 'Cream (optional)'}
            ],
            'instructions': '1. Sauté onion and garlic.\n2. Add tomatoes and broth.\n3. Simmer and blend.\n4. Add cream and serve.'
        }
    ]
}

def get_mock_recipe(query):
    """Get a mock recipe based on the search query"""
    query_lower = query.lower()
    
    # Check each category
    for key, recipes in MOCK_RECIPES.items():
        if key in query_lower:
            return random.choice(recipes)
    
    # Return a default recipe
    return {
        'title': f'{query.title()} Delight',
        'readyInMinutes': random.randint(25, 50),
        'servings': random.choice([2, 4, 6]),
        'extendedIngredients': [
            {'original': f'2 cups {query}'},
            {'original': 'Olive oil'},
            {'original': 'Salt and pepper'},
            {'original': 'Fresh herbs'},
            {'original': 'Garlic'}
        ],
        'instructions': f'1. Prepare the {query}.\n2. Season with herbs and spices.\n3. Cook until tender.\n4. Serve and enjoy!'
    }
