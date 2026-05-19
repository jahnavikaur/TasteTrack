# chatbot.py
import os
from groq import Groq
from datetime import date
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def build_system_prompt(pantry_items: list) -> str:
    today = date.today().strftime("%B %d, %Y")

    if pantry_items:
        pantry_lines = []
        for item in pantry_items:
            line = f"  - {item['item_name']}: {item['quantity']} {item['unit']}"
            if item.get('expiry_date'):
                days_left = (item['expiry_date'] - date.today()).days
                if days_left <= 0:
                    line += " (EXPIRED — do not use)"
                elif days_left <= 3:
                    line += f" (expires in {days_left} day{'s' if days_left != 1 else ''} — use urgently)"
                elif days_left <= 7:
                    line += f" (expires in {days_left} days — use soon)"
        pantry_text = "\n".join(pantry_lines)
    else:
        pantry_text = "  (pantry is empty)"

    return f"""You are KitchenMind AI, a warm and smart Indian kitchen assistant chatbot.
Today's date is {today}.

The user's current pantry contains:
{pantry_text}

Your behaviour rules:
- Suggest recipes using ONLY ingredients the user actually has in their pantry
- Always prioritize ingredients that are expiring soon
- Understand both Hindi and English ingredient names:
  aata/atta/aatta = wheat flour
  pyaaz/piaz = onion
  tamatar = tomato
  dahi = curd/yogurt
  tel = oil
  namak = salt
  haldi = turmeric
  adrak = ginger
  lahsun = garlic
  dhaniya = coriander
  jeera = cumin
  mirch = chili
  chawal = rice
  dal = lentils
  paneer = cottage cheese
  ghee = clarified butter
  doodh = milk
  anda = egg
  aloo = potato
  gobhi = cauliflower
  palak = spinach
  matar = peas
  baingan = eggplant
- Understand typos and spelling variations naturally
- When suggesting a recipe always mention: dish name, main ingredients used, approx cooking time
- If user asks for a full recipe, give proper step by step instructions
- If user mentions an ingredient not in pantry, tell them it's missing and suggest alternatives from their pantry
- Be conversational, friendly and encouraging like a helpful family member
- Keep responses concise — 4 to 6 lines max unless user asks for full recipe
- If pantry is empty, kindly ask them to add ingredients to their pantry first
- Never make up ingredients the user does not have
- You can suggest what to buy if user asks what is missing for a specific dish"""


def chat_with_ai(user_message: str, pantry_items: list, conversation_history: list) -> str:
    system_prompt = build_system_prompt(pantry_items)

    # Keep only last 20 messages to stay within token limits
    recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history

    messages = [
        {"role": "system", "content": system_prompt},
        *recent_history,
        {"role": "user", "content": user_message}
    ]

    try:
        response = client.chat.completions.create(
           model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        error = str(e)
        if "invalid_api_key" in error.lower():
            return "API key error — please check your GROQ_API_KEY in the .env file."
        elif "rate_limit" in error.lower():
            return "Too many requests right now. Please wait a moment and try again."
        elif "connection" in error.lower():
            return "Connection error. Please check your internet and try again."
        else:
            return f"Something went wrong: {error}"
        