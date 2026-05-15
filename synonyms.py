# synonyms.py
SYNONYMS = {
    # Flours
    "wheat flour": ["atta", "aata", "aatta", "gehun atta", "gehun ka atta", "whole wheat flour", "chapati flour"],
    "rice flour": ["chawal ka atta", "rice powder"],
    "gram flour": ["besan", "chickpea flour", "chana atta"],
    "maida": ["all purpose flour", "refined flour", "white flour"],
    "semolina": ["suji", "sooji", "rava", "rawa"],
    "cornflour": ["corn starch", "makki atta", "corn flour"],

    # Lentils & legumes
    "moong dal": ["mung dal", "green gram dal", "moong daal", "mung lentil"],
    "masoor dal": ["red lentil", "masur dal", "masoor daal", "lal dal"],
    "chana dal": ["split chickpea", "chana daal", "bengal gram dal"],
    "urad dal": ["black gram dal", "urad daal", "ulundu"],
    "toor dal": ["arhar dal", "pigeon pea dal", "toovar dal", "tuvar dal"],
    "rajma": ["kidney beans", "red kidney beans"],
    "chana": ["chickpea", "chole", "garbanzo", "kabuli chana"],

    # Vegetables
    "potato": ["aloo", "alu", "batata"],
    "tomato": ["tamatar", "tamater"],
    "onion": ["pyaz", "pyaaz", "kanda", "vengayam"],
    "garlic": ["lahsun", "lasan", "garlic cloves"],
    "ginger": ["adrak", "adrakh", "ginger root"],
    "spinach": ["palak", "paalak"],
    "cauliflower": ["gobhi", "gobi", "phool gobhi", "phool gobi"],
    "cabbage": ["patta gobhi", "band gobhi", "patta gobi"],
    "eggplant": ["brinjal", "baingan", "baigan", "aubergine"],
    "green peas": ["matar", "mattar", "peas"],
    "carrot": ["gajar", "gaajar"],
    "radish": ["mooli", "muli"],
    "capsicum": ["bell pepper", "shimla mirch", "shimla mirch"],
    "bitter gourd": ["karela", "karella"],
    "bottle gourd": ["lauki", "ghiya", "doodhi"],
    "fenugreek leaves": ["methi", "methi leaves", "fenugreek"],
    "coriander leaves": ["dhania", "cilantro", "hara dhania", "dhaniya"],
    "mint leaves": ["pudina", "peppermint leaves"],
    "curry leaves": ["kadi patta", "meetha neem"],

    # Spices
    "cumin": ["jeera", "zeera", "jira"],
    "mustard seeds": ["rai", "sarson", "mustard"],
    "turmeric": ["haldi", "haldee", "turmeric powder"],
    "red chili powder": ["lal mirch", "red chilli powder", "lal mirchi"],
    "green chili": ["hari mirch", "green chilli", "hari mirchi"],
    "coriander powder": ["dhania powder", "dhaniya powder"],
    "garam masala": ["garam masala powder", "mixed spices"],
    "black pepper": ["kali mirch", "pepper", "kali mirchi"],
    "cardamom": ["elaichi", "ilaichi", "green cardamom"],
    "cinnamon": ["dalchini", "dal chini"],
    "cloves": ["laung", "lavang"],
    "bay leaf": ["tej patta", "tej patta leaves"],
    "asafoetida": ["hing", "heeng"],
    "carom seeds": ["ajwain", "ajvain", "bishop weed"],
    "fennel seeds": ["saunf", "sonf"],

    # Dairy
    "milk": ["doodh", "dudh"],
    "yogurt": ["curd", "dahi", "dahee", "dadhi"],
    "butter": ["makhan", "makkhan"],
    "ghee": ["clarified butter", "desi ghee"],
    "paneer": ["cottage cheese", "indian cottage cheese"],
    "cream": ["malai", "fresh cream"],

    # Grains & Rice
    "rice": ["chawal", "chaval", "chaawal"],
    "basmati rice": ["basmati", "basmati chawal", "long grain rice"],
    "poha": ["flattened rice", "beaten rice", "aval"],
    "oats": ["jaie", "oat"],

    # Oils & Fats
    "oil": ["tel", "cooking oil", "vegetable oil", "refined oil"],
    "mustard oil": ["sarson ka tel", "mustard tel"],

    # Others
    "sugar": ["cheeni", "chini", "shakkar", "shaker"],
    "salt": ["namak", "noon"],
    "water": ["paani", "pani", "jal"],
    "bread": ["double roti", "pav", "pau"],
    "egg": ["anda", "ande", "eggs"],
    "lemon": ["nimbu", "nimbu juice", "lime"],
    "coconut": ["nariyal", "nariyel", "narial"],
    "coconut milk": ["nariyal ka doodh", "coconut cream"],
    "tamarind": ["imli", "imlee"],
    "jaggery": ["gur", "gud", "gurr"],
}

# Build reverse lookup: every alias → canonical name
_REVERSE = {}
for canonical, aliases in SYNONYMS.items():
    _REVERSE[canonical.lower()] = canonical.lower()
    for alias in aliases:
        _REVERSE[alias.lower()] = canonical.lower()


def canonicalize(name: str) -> str:
    """Return the canonical ingredient name for any alias or misspelling."""
    return _REVERSE.get(name.strip().lower(), name.strip().lower())