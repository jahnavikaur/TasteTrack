# shopping.py

CATEGORIES = {
    "Flours & Grains": ["wheat flour", "atta", "maida", "rice flour", "besan", "gram flour",
                         "semolina", "suji", "rava", "cornflour", "rice", "basmati rice",
                         "poha", "oats", "bread"],
    "Lentils & Legumes": ["moong dal", "masoor dal", "chana dal", "urad dal", "toor dal",
                           "rajma", "chana", "arhar dal"],
    "Vegetables": ["potato", "tomato", "onion", "garlic", "ginger", "spinach", "cauliflower",
                   "cabbage", "eggplant", "green peas", "carrot", "radish", "capsicum",
                   "bitter gourd", "bottle gourd", "fenugreek leaves", "coriander leaves",
                   "mint leaves", "curry leaves", "green chili"],
    "Dairy": ["milk", "yogurt", "curd", "butter", "ghee", "paneer", "cream", "egg"],
    "Spices": ["cumin", "mustard seeds", "turmeric", "red chili powder", "coriander powder",
               "garam masala", "black pepper", "cardamom", "cinnamon", "cloves", "bay leaf",
               "asafoetida", "carom seeds", "fennel seeds", "salt", "sugar"],
    "Oils & Fats": ["oil", "mustard oil", "ghee", "butter"],
    "Others": [],
    # Add to existing CATEGORIES:
"Meat & Poultry": ["chicken", "mutton", "minced meat", "keema", "egg"],
"Dry Fruits & Nuts": ["cashew", "almond", "raisin", "peanut", "walnut", "pistachio"],
"Sweeteners": ["sugar", "jaggery", "honey", "khoya", "mawa"],
}

def categorize(ingredient: str) -> str:
    ing = ingredient.lower()
    for category, items in CATEGORIES.items():
        if any(item in ing or ing in item for item in items):
            return category
    return "Others"

def generate_shopping_list(plan: dict, pantry_items: list) -> dict:
    """
    Compare all ingredients in the weekly plan against pantry.
    Return missing items grouped by category.
    """
    from synonyms import fuzzy_canonicalize

    # Build pantry set with canonicalized names
    pantry_set = {fuzzy_canonicalize(p["item_name"]) for p in pantry_items}

    # Collect all ingredients needed across the full week
    needed = {}  # canonical_name -> count of meals needing it
    for day, meals in plan.items():
        for meal_type, meal in meals.items():
            for ing in meal.get("ingredients", []):
                canonical = fuzzy_canonicalize(ing)
                needed[canonical] = needed.get(canonical, 0) + 1

    # Find missing ones
    missing = {ing: count for ing, count in needed.items() if ing not in pantry_set}

    # Group by category
    grouped = {}
    for ing, count in sorted(missing.items()):
        cat = categorize(ing)
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({"name": ing, "meals": count})

    return grouped