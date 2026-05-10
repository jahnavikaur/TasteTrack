from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from models import db, PantryItem, WeeklyPlan
from recommender import recommend_recipes
from planner import generate_weekly_plan
from datetime import datetime, date
import json
from synonyms import fuzzy_canonicalize

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kitchen.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "kitchenmind-secret"

db.init_app(app)

with app.app_context():
    db.create_all()

# ─── Home ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    pantry_count = PantryItem.query.count()
    expiring_soon = PantryItem.query.filter(PantryItem.expiry_date.isnot(None)).all()
    expiring_count = sum(1 for i in expiring_soon if i.expiry_date and (i.expiry_date - date.today()).days <= 5)
    last_plan = WeeklyPlan.query.order_by(WeeklyPlan.created_on.desc()).first()
    return render_template("index.html", pantry_count=pantry_count, expiring_count=expiring_count, last_plan=last_plan)

# ─── Pantry ─────────────────────────────────────────────────────────────────
@app.route("/pantry", methods=["GET", "POST"])
def pantry():
    if request.method == "POST":
        from synonyms import fuzzy_canonicalize
        item_name = fuzzy_canonicalize(request.form["item_name"].strip())
        quantity = float(request.form["quantity"])
        unit = request.form["unit"]
        expiry_date_str = request.form.get("expiry_date")
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date() if expiry_date_str else None

        # Check if item exists → update quantity
        existing = PantryItem.query.filter(PantryItem.item_name.ilike(item_name)).first()
        if existing:
            existing.quantity += quantity
            if expiry_date:
                existing.expiry_date = expiry_date
        else:
            item = PantryItem(item_name=item_name, quantity=quantity, unit=unit, expiry_date=expiry_date)
            db.session.add(item)

        db.session.commit()
        return redirect(url_for("pantry"))

    sort_by = request.args.get("sort", "name")
    search = request.args.get("search", "")

    query = PantryItem.query
    if search:
        query = query.filter(PantryItem.item_name.ilike(f"%{search}%"))
    if sort_by == "expiry":
        query = query.order_by(PantryItem.expiry_date.asc())
    elif sort_by == "quantity":
        query = query.order_by(PantryItem.quantity.desc())
    else:
        query = query.order_by(PantryItem.item_name.asc())

    items = query.all()
    today = date.today()
    return render_template("pantry.html", items=items, today=today, sort_by=sort_by, search=search)

@app.route("/delete_item/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("pantry"))

@app.route("/update_item/<int:item_id>", methods=["POST"])
def update_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    item.quantity = float(request.form["quantity"])
    item.unit = request.form["unit"]
    expiry_date_str = request.form.get("expiry_date")
    item.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date() if expiry_date_str else None
    db.session.commit()
    return redirect(url_for("pantry"))

# ─── Recommendations ─────────────────────────────────────────────────────────
@app.route("/recommend")
def recommend():
    meal_type = request.args.get("meal_type", "")
    pantry_items = PantryItem.query.all()
    pantry_list = [{"item_name": p.item_name, "quantity": p.quantity, "unit": p.unit, "expiry_date": p.expiry_date} for p in pantry_items]
    pantry_names = [p.item_name.lower() for p in pantry_items]
    recipes = recommend_recipes(pantry_list, top_n=20, meal_type=meal_type if meal_type else None)
    return render_template("recommend.html", recipes=recipes, meal_type=meal_type, pantry_names=pantry_names)

# ─── Weekly Plan ─────────────────────────────────────────────────────────────
@app.route("/weekly_plan")
def weekly_plan():
    pantry_items = PantryItem.query.all()
    pantry_list = [{"item_name": p.item_name, "quantity": p.quantity, "unit": p.unit, "expiry_date": p.expiry_date} for p in pantry_items]
    plan = generate_weekly_plan(pantry_list)
    return render_template("weekly_plan.html", plan=plan)

@app.route("/save_weekly_plan", methods=["POST"])
def save_weekly_plan():
    plan_json = request.form["plan_data"]
    plan = json.loads(plan_json)

    new_plan = WeeklyPlan(week_start=date.today(), plan_data=plan_json)
    db.session.add(new_plan)

    ingredient_usage = {}
    for day in plan:
        for meal in plan[day]:
            for ing in plan[day][meal].get("ingredients", []):
                ing = ing.lower()
                ingredient_usage[ing] = ingredient_usage.get(ing, 0) + 1

    pantry_items = PantryItem.query.all()
    for item in pantry_items:
        name = item.item_name.lower()
        if name in ingredient_usage:
            item.quantity -= ingredient_usage[name]
            if item.quantity <= 0:
                db.session.delete(item)

    db.session.commit()
    return jsonify({"status": "ok", "message": "Weekly plan saved and pantry updated!"})

@app.route("/plan_history")
def plan_history():
    plans = WeeklyPlan.query.order_by(WeeklyPlan.created_on.desc()).limit(5).all()
    parsed = []
    for p in plans:
        parsed.append({"id": p.id, "week_start": p.week_start, "created_on": p.created_on, "plan": json.loads(p.plan_data)})
    return render_template("plan_history.html", plans=parsed)

if __name__ == "__main__":
    app.run(debug=True)
