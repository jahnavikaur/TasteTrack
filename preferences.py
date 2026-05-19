# preferences.py
import json
from collections import Counter
from models import RecipePreference, db

def get_preference_profile(user_id: int) -> dict:
    """
    Build a taste profile from all likes/dislikes.
    Returns scores for cuisines, meal types, ingredients.
    """
    likes    = RecipePreference.query.filter_by(user_id=user_id, action='like').all()
    dislikes = RecipePreference.query.filter_by(user_id=user_id, action='dislike').all()

    liked_cuisines    = Counter()
    liked_meal_types  = Counter()
    liked_ingredients = Counter()
    disliked_recipes  = set()
    disliked_cuisines = Counter()

    for p in likes:
        if p.cuisine:    liked_cuisines[p.cuisine] += 1
        if p.meal_type:  liked_meal_types[p.meal_type] += 1
        if p.ingredients:
            for ing in json.loads(p.ingredients):
                liked_ingredients[ing.strip().lower()] += 1

    for p in dislikes:
        disliked_recipes.add(p.recipe_id)
        if p.cuisine: disliked_cuisines[p.cuisine] += 1

    return {
        "liked_cuisines":    dict(liked_cuisines),
        "liked_meal_types":  dict(liked_meal_types),
        "liked_ingredients": dict(liked_ingredients),
        "disliked_recipes":  list(disliked_recipes),
        "disliked_cuisines": dict(disliked_cuisines),
        "total_likes":       len(likes),
        "total_dislikes":    len(dislikes),
    }


def preference_score(recipe: dict, profile: dict) -> float:
    """
    Returns a bonus/penalty score based on family preferences.
    Called on top of the existing pantry match score.
    """
    if not profile or profile['total_likes'] == 0:
        return 0.0

    score = 0.0

    # Hard dislike — skip this recipe entirely (caller handles this)
    if recipe.get('recipe_id') in profile['disliked_recipes']:
        return -999

    # Cuisine bonus/penalty
    cuisine = recipe.get('cuisine', '')
    if cuisine in profile['liked_cuisines']:
        score += profile['liked_cuisines'][cuisine] * 1.5
    if cuisine in profile['disliked_cuisines']:
        score -= profile['disliked_cuisines'][cuisine] * 1.0

    # Meal type bonus
    meal_type = recipe.get('meal_type', '')
    if meal_type in profile['liked_meal_types']:
        score += profile['liked_meal_types'][meal_type] * 1.0

    # Ingredient overlap bonus
    recipe_ings = [i.lower() for i in recipe.get('ingredients', [])]
    for ing in recipe_ings:
        if ing in profile['liked_ingredients']:
            score += profile['liked_ingredients'][ing] * 0.5

    return score


def get_top_preferences(user_id: int) -> dict:
    """Return human-readable top preferences for dashboard."""
    profile = get_preference_profile(user_id)

    top_cuisine = max(profile['liked_cuisines'], key=profile['liked_cuisines'].get) \
                  if profile['liked_cuisines'] else None
    top_meal    = max(profile['liked_meal_types'], key=profile['liked_meal_types'].get) \
                  if profile['liked_meal_types'] else None
    top_ings    = sorted(profile['liked_ingredients'].items(),
                         key=lambda x: x[1], reverse=True)[:5]

    return {
        "top_cuisine":    top_cuisine,
        "top_meal_type":  top_meal,
        "top_ingredients":top_ings,
        "total_likes":    profile['total_likes'],
        "total_dislikes": profile['total_dislikes'],
    }