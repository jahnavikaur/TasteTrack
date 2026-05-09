import pandas as pd
from datetime import date
import os

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

def recommend_recipes(pantry_items, top_n=10, meal_type=None):
    df = load_recipes()
    results = []

    for _, row in df.iterrows():
        score, matched, missing = score_recipe(row["ingredients"], pantry_items)
        results.append({
            "recipe_id": row["recipe_id"],
            "name": row["name"],
            "meal_type": row["meal_type"],
            "cuisine": row["cuisine"],
            "time": row["cooking_time"],
            "matched": matched,
            "missing": missing,
            "score": score,
            "ingredients": row["ingredients"],
            "instructions": row["instructions"]
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    if meal_type:
        results = [r for r in results if r["meal_type"].lower() == meal_type.lower()]
    return results[:top_n]
