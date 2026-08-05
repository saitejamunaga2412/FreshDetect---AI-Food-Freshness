import difflib

names = ["apples", "bananas", "carrots", "potatoes", "tomatoes", "mangoes", "oranges", "strawberries", "bell peppers"]

def run_fuzzy_test(word):
    # exact
    if word.lower() in names:
        return word.lower(), 1.0
        
    matches = difflib.get_close_matches(word.lower(), names, n=1, cutoff=0.6)
    if matches:
        match = matches[0]
        # Calculate ratio
        ratio = difflib.SequenceMatcher(None, word.lower(), match).ratio()
        return match, ratio
    return None, 0.0

for w in ['Carrot', 'Potato', 'Tomato', 'Bellpepper', 'Orange', 'Strawberry', 'Mango', 'Jujube']:
    m, c = run_fuzzy_test(w)
    print(f"{w} -> {m} (conf {c:.2f})")
