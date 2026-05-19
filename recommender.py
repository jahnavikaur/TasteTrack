import pandas as pd
from datetime import date
from synonyms import canonicalize
from rapidfuzz import process, fuzz
import os

def fuzzy_canonicalize(name: str, threshold: int = 80) -> str:
    """
    First tries exact synonym lookup.
    Falls back to fuzzy match against all known aliases if no exact hit.
    """
    from synonyms import _REVERSE

    exact = canonicalize(name)
    # If it changed, synonym dict handled it
    if exact != name.strip().lower():
        return exact

    # Fuzzy match against all known aliases
    all_keys = list(_REVERSE.keys())
    result = process.extractOne(name.lower(), all_keys, scorer=fuzz.WRatio)
    if result and result[1] >= threshold:
        return _REVERSE[result[0]]

    return name.strip().lower()

def load_recipes(path=None):
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "dataset", "recipes.csv")
    df = pd.read_csv(path)
    df["ingredients"] = df["ingredients"].apply(lambda x: [i.strip().lower() for i in x.split(",")])
    return df

def score_recipe(recipe_ingredients, pantry_items):
    pantry_dict = {p["item_name"].lower(): p for p in pantry_items}
    matched = 0
    missing = 0
    expiry_bonus = 0

    for ing in recipe_ingredients:
        if ing in pantry_dict:
            matched += 1
            expiry_date = pantry_dict[ing].get("expiry_date")
            if expiry_date:
                days_left = (expiry_date - date.today()).days
                if days_left <= 2:
                    expiry_bonus += 5
                elif days_left <= 5:
                    expiry_bonus += 3
                elif days_left <= 10:
                    expiry_bonus += 1
        else:
            missing += 1

    score = matched * 2 - missing * 1 + expiry_bonus
    return score, matched, missing

def recommend_recipes(pantry_items, top_n=10, meal_type=None, user_id=None):
    df = load_recipes()
    results = []

    # Load preference profile if user_id given
    profile = None
    if user_id:
        from preferences import get_preference_profile, preference_score
        profile = get_preference_profile(user_id)

    for _, row in df.iterrows():
        score, matched, missing = score_recipe(row["ingredients"], pantry_items)

        # Add preference bonus on top of pantry score
        pref_bonus = 0
        if profile:
            recipe_dict = {
                "recipe_id":   row["recipe_id"],
                "cuisine":     row["cuisine"],
                "meal_type":   row["meal_type"],
                "ingredients": row["ingredients"],
            }
            from preferences import preference_score as pref_score
            pref_bonus = pref_score(recipe_dict, profile)

        final_score = score + pref_bonus

        # Skip hard disliked recipes
        if pref_bonus == -999:
            continue

        results.append({
            "recipe_id":   row["recipe_id"],
            "name":        row["name"],
            "meal_type":   row["meal_type"],
            "cuisine":     row["cuisine"],
            "time":        row["cooking_time"],
            "matched":     matched,
            "missing":     missing,
            "score":       round(final_score, 2),
            "ingredients": row["ingredients"],
            "instructions":row["instructions"]
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    if meal_type:
        results = [r for r in results if r["meal_type"].lower() == meal_type.lower()]
    return results[:top_n]

   
