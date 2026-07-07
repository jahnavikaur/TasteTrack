# 🍳 TasteTrack (KitchenMind)

TasteTrack is a Flask-based smart kitchen assistant that helps you track your pantry, get recipe recommendations based on what you actually have on hand, plan your week of meals, generate a shopping list, and chat with an AI cooking assistant that understands both English and Hindi ingredient names.

## ✨ Features

- **🔐 User Accounts** — Register/login with secure password hashing (Flask-Login + Bcrypt); each user has their own private pantry, plans, and preferences.
- **🧺 Pantry Management** — Add, update, delete, sort, and search pantry items, with quantity, unit, and expiry date tracking.
- **🥘 Smart Recipe Recommendations** — Recipes are scored based on how many pantry ingredients they use, how many are missing, and a bonus for ingredients that are close to expiring (so nothing goes to waste).
- **❤️ Preference Learning** — Like/dislike recipes and TasteTrack builds a taste profile (favorite cuisines, meal types, ingredients) that influences future recommendations.
- **📅 Weekly Meal Planner** — Auto-generates a full week (Breakfast/Lunch/Dinner) of non-repeating recipes based on your pantry and preferences.
- **🛒 Shopping List Generator** — Compares your weekly plan against your pantry and produces a missing-items list grouped by category (grains, vegetables, dairy, spices, etc.).
- **💬 AI Chat Assistant** — A Groq-powered chatbot ("KitchenMind AI") that suggests recipes from your pantry, prioritizes expiring items, and understands common Hindi/English ingredient synonyms and typos (e.g. *aata*, *pyaaz*, *tamatar*, *dahi*).
- **🔎 Fuzzy Ingredient Matching** — A synonym dictionary plus fuzzy string matching (RapidFuzz) canonicalizes ingredient names so "aloo", "alu", and "potato" are all treated as the same item.
- **📊 Dashboard** — At-a-glance view of pantry stats, expiring items, most-used ingredients, recipe of the day, latest plan summary, and recent liked/disliked recipes.
- **🥦 Veg-only Filtering** — Filter recommendations to vegetarian-only recipes.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite via Flask-SQLAlchemy |
| Auth | Flask-Login, Flask-Bcrypt |
| Data | Pandas (recipe dataset), RapidFuzz (fuzzy matching) |
| AI Chat | Groq API (Llama 3) |
| Frontend | Jinja2 templates, HTML/CSS/JS |

## 📁 Project Structure

```
TasteTrack/
├── app.py                # Main Flask app & routes
├── models.py              # SQLAlchemy models (User, PantryItem, WeeklyPlan, RecipePreference)
├── recommender.py          # Recipe scoring & recommendation logic
├── planner.py              # Weekly meal plan generator
├── shopping.py              # Shopping list generation & categorization
├── preferences.py            # Taste profile & preference scoring
├── chatbot.py              # Groq-powered AI chat assistant
├── synonyms.py              # Hindi/English ingredient synonym dictionary
├── dataset/
│   └── recipes.csv            # Recipe dataset (name, ingredients, cuisine, time, instructions)
├── templates/              # Jinja2 HTML templates
├── static/js/              # Frontend JavaScript
├── instance/               # SQLite database (created at runtime)
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/jahnavikaur/TasteTrack.git
   cd TasteTrack
   ```

2. Create a virtual environment and install dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables — create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
   > The app runs without this, but the AI chat feature will be disabled until a valid key is provided. Get a free key at [console.groq.com](https://console.groq.com).

4. Run the app
   ```bash
   python app.py
   ```

5. Open your browser at `http://localhost:5000`

The SQLite database (`instance/kitchen.db`) is created automatically on first run.

## 📖 Usage

1. **Register** an account and log in.
2. **Add pantry items** — enter what's in your kitchen along with quantity and expiry date.
3. Visit **Recommendations** to see recipes ranked by how well they match your pantry (with a boost for using up soon-to-expire ingredients).
4. **Like/dislike** recipes to teach TasteTrack your taste.
5. Generate a **Weekly Plan** for an automatic 7-day, 3-meals-a-day schedule.
6. Convert that plan into a **Shopping List** of exactly what you're missing.
7. Ask the **Chat Assistant** things like *"what can I cook with what's expiring soon?"*

## 🗃️ Recipe Dataset

`dataset/recipes.csv` includes recipes with fields for `recipe_id`, `name`, `meal_type`, `ingredients`, `cuisine`, `cooking_time`, and `instructions` — primarily Indian home-style dishes.

## 🔮 Future Advancements

Ideas for taking TasteTrack further:

- **🖼️ Recipe Images** — Add photos/thumbnails for each recipe in the dataset and display them in the recommendation and plan views.
- **📷 Pantry Input via Receipt/Barcode Scan** — Let users add items by scanning a grocery receipt or product barcode instead of manual entry.
- **🌍 Expanded & Multi-Cuisine Dataset** — Grow beyond the current Indian home-style dataset to include more cuisines, with user-contributed recipes and moderation.
- **🥗 Nutrition & Calorie Tracking** — Add nutritional info (calories, macros) per recipe and daily/weekly nutrition summaries.
- **🔔 Expiry Notifications** — Email/push/SMS reminders when pantry items are about to expire, instead of relying on the user visiting the dashboard.
- **👨‍👩‍👧 Multi-User Households** — Shared pantries and shopping lists for families or roommates, with per-person preference profiles feeding into a combined recommendation.
- **🎙️ Voice Assistant Support** — Extend the chatbot to accept voice input/output (e.g. "Alexa, what can I cook with what's in my fridge?").
- **📱 Mobile App / PWA** — Package the app as a Progressive Web App or native mobile app for offline pantry access and notifications.
- **📈 Analytics Dashboard 2.0** — Deeper insights like monthly food waste saved, cost estimates for shopping lists, and cuisine diversity trends over time.
- **🗄️ Database Migration Support** — Add Flask-Migrate/Alembic for schema migrations and move from SQLite to PostgreSQL for production deployments.
- **♻️ Food Waste Insights** — Track and report how much food was "saved" by prioritizing expiring ingredients, turning it into a shareable sustainability metric.

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

Add your preferred license here (e.g. MIT).
