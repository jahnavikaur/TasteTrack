import random
from recommender import recommend_recipes

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]

def generate_weekly_plan(pantry_items):
    plan = {}
    used_recipes = set()

    all_recs = recommend_recipes(pantry_items, top_n=50)

    for day in DAYS:
        plan[day] = {}
        for meal in MEAL_TYPES:
            meal_filtered = [r for r in all_recs if r["meal_type"].lower() == meal.lower() and r["recipe_id"] not in used_recipes]
            if not meal_filtered:
                meal_filtered = [r for r in all_recs if r["meal_type"].lower() == meal.lower()]
            if not meal_filtered:
                meal_filtered = all_recs

            chosen = meal_filtered[0] if meal_filtered else random.choice(all_recs)
            used_recipes.add(chosen["recipe_id"])

            plan[day][meal] = {
                "recipe_id": chosen["recipe_id"],
                "name": chosen["name"],
                "cuisine": chosen.get("cuisine", ""),
                "time": chosen.get("time", ""),
                "ingredients": chosen["ingredients"],
                "matched": chosen.get("matched", 0),
                "missing": chosen.get("missing", 0),
            }

    return plan
