import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import RecipePreference, db, User, PantryItem, WeeklyPlan
from recommender import recommend_recipes, load_recipes
from planner import generate_weekly_plan
from shopping import generate_shopping_list
from datetime import datetime, date
import json
from chatbot import chat_with_ai
from preferences import get_preference_profile, get_top_preferences
from models import db, User, PantryItem, WeeklyPlan, RecipePreference
import json
from collections import Counter

app = Flask(__name__)

# Keep the database in the Flask instance folder for a stable local path.
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'kitchen.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path.replace('\\', '/') }"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kitchenmind-super-secret-2024'

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'          # redirect here if not logged in
login_manager.login_message = 'Please log in to access your kitchen.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ── helper ────────────────────────────────────────────────────────────────────
def get_pantry_list():
    items = PantryItem.query.filter_by(user_id=current_user.id).all()
    return [{"item_name": p.item_name, "quantity": p.quantity,
             "unit": p.unit, "expiry_date": p.expiry_date} for p in items]

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username  = request.form['username'].strip()
        email     = request.form['email'].strip().lower()
        password  = request.form['password']
        password2 = request.form['password2']

        # Validation
        if password != password2:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Welcome to KitchenMind, {username}! 🍳', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        remember = 'remember' in request.form

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}! 🍳', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    pantry_count    = PantryItem.query.filter_by(user_id=current_user.id).count()
    plan_count      = WeeklyPlan.query.filter_by(user_id=current_user.id).count()
    return render_template('profile.html',
                           pantry_count=pantry_count,
                           plan_count=plan_count)


# ── Home ──────────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    pantry_count   = PantryItem.query.filter_by(user_id=current_user.id).count()
    expiring_items = PantryItem.query.filter(
        PantryItem.user_id == current_user.id,
        PantryItem.expiry_date != None
    ).all()
    expiring_count = sum(1 for i in expiring_items
                         if i.expiry_date and (i.expiry_date - date.today()).days <= 5)
    last_plan = WeeklyPlan.query.filter_by(user_id=current_user.id)\
                                .order_by(WeeklyPlan.created_on.desc()).first()
    recipe_count = len(load_recipes())
    return render_template('index.html',
                           pantry_count=pantry_count,
                           expiring_count=expiring_count,
                           last_plan=last_plan,
                           recipe_count=recipe_count)


# ── Pantry ────────────────────────────────────────────────────────────────────
@app.route('/pantry', methods=['GET', 'POST'])
@login_required
def pantry():
    if request.method == 'POST':
        from recommender import fuzzy_canonicalize
        item_name   = fuzzy_canonicalize(request.form['item_name'].strip())
        quantity    = float(request.form['quantity'])
        unit        = request.form['unit']
        expiry_str  = request.form.get('expiry_date')
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date() if expiry_str else None

        existing = PantryItem.query.filter_by(
            user_id=current_user.id
        ).filter(PantryItem.item_name.ilike(item_name)).first()

        if existing:
            existing.quantity += quantity
            if expiry_date:
                existing.expiry_date = expiry_date
        else:
            item = PantryItem(user_id=current_user.id, item_name=item_name,
                              quantity=quantity, unit=unit, expiry_date=expiry_date)
            db.session.add(item)

        db.session.commit()
        return redirect(url_for('pantry'))

    sort_by = request.args.get('sort', 'name')
    search  = request.args.get('search', '')
    query   = PantryItem.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(PantryItem.item_name.ilike(f'%{search}%'))
    if sort_by == 'expiry':
        query = query.order_by(PantryItem.expiry_date.asc())
    elif sort_by == 'quantity':
        query = query.order_by(PantryItem.quantity.desc())
    else:
        query = query.order_by(PantryItem.item_name.asc())

    items = query.all()
    return render_template('pantry.html', items=items,
                           today=date.today(), sort_by=sort_by, search=search)


@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = PantryItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('pantry'))


@app.route('/update_item/<int:item_id>', methods=['POST'])
@login_required
def update_item(item_id):
    item = PantryItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    item.quantity   = float(request.form['quantity'])
    item.unit       = request.form['unit']
    expiry_str      = request.form.get('expiry_date')
    item.expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date() if expiry_str else None
    db.session.commit()
    return redirect(url_for('pantry'))


# ── Recommendations ───────────────────────────────────────────────────────────
@app.route('/recommend')
@login_required
def recommend():
    meal_type = request.args.get('meal_type', '')
    veg_only  = request.args.get('veg_only', '') == '1'   # ADD THIS
    recipes   = recommend_recipes(
        get_pantry_list(), top_n=20,
        meal_type=meal_type if meal_type else None,
        user_id=current_user.id,
        veg_only=veg_only,        # ADD THIS
    )
    liked    = {p.recipe_id for p in current_user.preferences if p.action == 'like'}
    disliked = {p.recipe_id for p in current_user.preferences if p.action == 'dislike'}
    return render_template('recommend.html', recipes=recipes,
                           meal_type=meal_type, liked=liked, disliked=disliked,
                           veg_only=veg_only)    # ADD THIS


# ── Weekly Plan ───────────────────────────────────────────────────────────────
@app.route('/weekly_plan')
@login_required
def weekly_plan():
    plan = generate_weekly_plan(get_pantry_list())
    return render_template('weekly_plan.html', plan=plan)


@app.route('/save_weekly_plan', methods=['POST'])
@login_required
def save_weekly_plan():
    plan_json = request.form['plan_data']
    plan      = json.loads(plan_json)

    new_plan = WeeklyPlan(user_id=current_user.id,
                          week_start=date.today(), plan_data=plan_json)
    db.session.add(new_plan)

    # Deduct ingredients from THIS user's pantry only
    ingredient_usage = {}
    for day in plan:
        for meal in plan[day]:
            for ing in plan[day][meal].get('ingredients', []):
                ingredient_usage[ing.lower()] = ingredient_usage.get(ing.lower(), 0) + 1

    for item in PantryItem.query.filter_by(user_id=current_user.id).all():
        name = item.item_name.lower()
        if name in ingredient_usage:
            item.quantity -= ingredient_usage[name]
            if item.quantity <= 0:
                db.session.delete(item)

    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Weekly plan saved and pantry updated!'})


@app.route('/plan_history')
@login_required
def plan_history():
    plans  = WeeklyPlan.query.filter_by(user_id=current_user.id)\
                             .order_by(WeeklyPlan.created_on.desc()).limit(5).all()
    parsed = [{'id': p.id, 'week_start': p.week_start,
               'created_on': p.created_on, 'plan': json.loads(p.plan_data)}
              for p in plans]
    return render_template('plan_history.html', plans=parsed)


@app.route('/clear_pantry', methods=['POST'])
@login_required
def clear_pantry():
    PantryItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Pantry cleared.', 'success')
    return redirect(url_for('profile'))


# ── Shopping List ─────────────────────────────────────────────────────────────
@app.route('/shopping_list', methods=['POST'])
@login_required
def shopping_list():
    plan_json = request.form.get('plan_data')
    if not plan_json:
        return redirect(url_for('weekly_plan'))
    plan     = json.loads(plan_json)
    shopping = generate_shopping_list(plan, get_pantry_list())
    total    = sum(len(items) for items in shopping.values())
    return render_template('shopping.html',
                           shopping=shopping, total=total, plan_json=plan_json)
@app.route('/chat')
@login_required
def chat():
    pantry_items = PantryItem.query.filter_by(user_id=current_user.id).all()
    expiring = [p for p in pantry_items
                if p.expiry_date and (p.expiry_date - date.today()).days <= 5]
    return render_template('chat.html',
                           pantry_items=pantry_items,
                           expiring=expiring,
                           today=date.today())


@app.route('/chat/send', methods=['POST'])
@login_required
def chat_send():
    data         = request.get_json()
    user_message = data.get('message', '').strip()
    history      = data.get('history', [])

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    if len(user_message) > 500:
        return jsonify({'error': 'Message too long'}), 400

    pantry_items = PantryItem.query.filter_by(user_id=current_user.id).all()
    pantry_list  = [{
        "item_name":   p.item_name,
        "quantity":    p.quantity,
        "unit":        p.unit,
        "expiry_date": p.expiry_date
    } for p in pantry_items]

    reply = chat_with_ai(user_message, pantry_list, history)
    return jsonify({'reply': reply})


@app.route('/pantry/add_from_shopping', methods=['POST'])
@login_required
def add_from_shopping():
    data      = request.get_json()
    item_name = data.get('item_name', '').strip()
    quantity  = float(data.get('quantity', 1))
    unit      = data.get('unit', 'unit')

    if not item_name:
        return jsonify({'status': 'error', 'message': 'No item name'}), 400

    from recommender import fuzzy_canonicalize
    canonical = fuzzy_canonicalize(item_name)

    existing = PantryItem.query.filter_by(user_id=current_user.id)\
                               .filter(PantryItem.item_name.ilike(canonical)).first()
    if existing:
        existing.quantity += quantity
    else:
        new_item = PantryItem(
            user_id=current_user.id,
            item_name=canonical,
            quantity=quantity,
            unit=unit
        )
        db.session.add(new_item)

    db.session.commit()
    return jsonify({'status': 'ok', 'message': f'{canonical} added to pantry!'})

#---------------- like/dislike route:------------------
@app.route('/recipe/preference', methods=['POST'])
@login_required
def recipe_preference():
    data       = request.get_json()
    recipe_id  = int(data.get('recipe_id'))
    action     = data.get('action')   # 'like' or 'dislike'
    name       = data.get('name', '')
    cuisine    = data.get('cuisine', '')
    meal_type  = data.get('meal_type', '')
    ingredients= data.get('ingredients', [])

    if action not in ('like', 'dislike'):
        return jsonify({'status': 'error'}), 400

    # Remove existing preference for this recipe first
    existing = RecipePreference.query.filter_by(
        user_id=current_user.id, recipe_id=recipe_id
    ).first()
    if existing:
        if existing.action == action:
            # Toggle off — remove it
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'status': 'removed', 'action': action})
        else:
            existing.action     = action
            existing.created_on = datetime.utcnow()
            db.session.commit()
            return jsonify({'status': 'updated', 'action': action})

    # New preference
    pref = RecipePreference(
        user_id    = current_user.id,
        recipe_id  = recipe_id,
        recipe_name= name,
        action     = action,
        cuisine    = cuisine,
        meal_type  = meal_type,
        ingredients= json.dumps(ingredients)
    )
    db.session.add(pref)
    db.session.commit()
    return jsonify({'status': 'saved', 'action': action})

#---------------- dashboard route:------------------

@app.route('/dashboard')
@login_required
def dashboard():
    from recommender import recommend_recipes
    today = date.today()

    # Pantry stats
    pantry_items   = PantryItem.query.filter_by(user_id=current_user.id).all()
    pantry_count   = len(pantry_items)

    # Expiring items
    expiring = sorted(
        [p for p in pantry_items if p.expiry_date and (p.expiry_date - today).days <= 7],
        key=lambda x: x.expiry_date
    )

    # Most used ingredient (from all weekly plans)
    all_plans = WeeklyPlan.query.filter_by(user_id=current_user.id).all()
    ing_counter = Counter()
    for plan in all_plans:
        plan_data = json.loads(plan.plan_data)
        for day in plan_data:
            for meal in plan_data[day].values():
                for ing in meal.get('ingredients', []):
                    ing_counter[ing.lower()] += 1
    most_used = ing_counter.most_common(5)

    # Recipe of the day — top recommended
    pantry_list = get_pantry_list()
    top_recipes = recommend_recipes(pantry_list, top_n=5, user_id=current_user.id)
    recipe_of_day = top_recipes[0] if top_recipes else None

    # Latest weekly plan summary
    last_plan = WeeklyPlan.query.filter_by(user_id=current_user.id)\
                                .order_by(WeeklyPlan.created_on.desc()).first()
    plan_summary = None
    if last_plan:
        plan_data = json.loads(last_plan.plan_data)
        plan_summary = {
            "week_start": last_plan.week_start,
            "days":       list(plan_data.keys()),
            "total_meals":sum(len(v) for v in plan_data.values()),
            "preview":    {day: list(meals.keys()) for day, meals in plan_data.items()}
        }

    # Preference profile
    prefs = get_top_preferences(current_user.id)

    # Recent activity
    recent_likes = RecipePreference.query.filter_by(
        user_id=current_user.id, action='like'
    ).order_by(RecipePreference.created_on.desc()).limit(5).all()

    recent_dislikes = RecipePreference.query.filter_by(
        user_id=current_user.id, action='dislike'
    ).order_by(RecipePreference.created_on.desc()).limit(3).all()

    return render_template('dashboard.html',
        pantry_count   = pantry_count,
        expiring       = expiring,
        most_used      = most_used,
        recipe_of_day  = recipe_of_day,
        plan_summary   = plan_summary,
        prefs          = prefs,
        recent_likes   = recent_likes,
        recent_dislikes= recent_dislikes,
        today          = today,
        all_plans_count= len(all_plans),
    )

if __name__ == '__main__':
    app.run(debug=True)