import json
import random
import os

# Chemin vers le fichier de mots
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WORDS_FILE = os.path.join(DATA_DIR, "words.json")
SCORES_FILE = os.path.join(DATA_DIR, "best_scores.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def load_json(filepath: str) -> dict:
    """Charge un fichier JSON de façon sécurisée."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable : {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERREUR] JSON invalide dans {filepath} : {e}")
        return {}


def save_json(filepath: str, data: dict) -> bool:
    """Sauvegarde des données dans un fichier JSON de façon sécurisée."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (OSError, IOError) as e:
        print(f"[ERREUR] Impossible d'écrire dans {filepath} : {e}")
        return False


def get_random_word(difficulty: str = "medium", category: str = None,
                    language: str = "fr") -> tuple[str, str, str]:
    """
    Retourne un mot aléatoire selon la langue, difficulté et catégorie.
    Retourne un tuple (mot, difficulte, categorie).
    """
    words_data = load_json(WORDS_FILE)

    # Sélectionne la langue (fallback "fr")
    lang_data = words_data.get(language) or words_data.get("fr", {})

    # Vérifie que la difficulté existe
    if difficulty not in lang_data:
        print(f"[AVERTISSEMENT] Difficulté '{difficulty}' inconnue, utilisation de 'medium'")
        difficulty = "medium"

    difficulty_data = lang_data[difficulty]

    # Choisit la catégorie
    if category and category in difficulty_data:
        chosen_category = category
    else:
        chosen_category = random.choice(list(difficulty_data.keys()))

    word = random.choice(difficulty_data[chosen_category])
    return word.upper(), difficulty, chosen_category


def get_all_categories(difficulty: str = None, language: str = "fr") -> list[str]:
    """Retourne toutes les catégories disponibles pour une langue donnée."""
    words_data = load_json(WORDS_FILE)
    lang_data = words_data.get(language) or words_data.get("fr", {})
    if difficulty:
        return list(lang_data.get(difficulty, {}).keys())
    categories = set()
    for diff_data in lang_data.values():
        if isinstance(diff_data, dict):
            categories.update(diff_data.keys())
    return sorted(list(categories))


def load_scores() -> dict:
    """Charge les meilleurs scores."""
    scores_data = load_json(SCORES_FILE)
    if not scores_data:
        return {"record": None, "scores": []}
    return scores_data


def save_score(word: str, difficulty: str, category: str,
               attempts: int, errors: int, duration: int) -> bool:
    """
    Sauvegarde un score et retourne True si c'est un nouveau record.
    """
    from datetime import datetime

    scores_data = load_scores()
    current_record = scores_data.get("record")

    # Crée l'entrée du nouveau score
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "word": word.lower(),
        "difficulty": difficulty,
        "category": category,
        "attempts": attempts,
        "errors": errors,
        "duration_seconds": duration
    }

    # Ajoute en tête de liste
    scores_data["scores"].insert(0, new_entry)

    # Limite à 50 entrées max pour ne pas gonfler le fichier
    scores_data["scores"] = scores_data["scores"][:50]

    # Vérifie si c'est un nouveau record (moins de tentatives = meilleur score)
    is_new_record = False
    if current_record is None or attempts < current_record:
        scores_data["record"] = attempts
        is_new_record = True

    save_json(SCORES_FILE, scores_data)
    return is_new_record


def load_config() -> dict:
    """Charge la configuration du jeu."""
    config = load_json(CONFIG_FILE)
    if not config:
        # Valeurs par défaut si le fichier config est absent
        return {
            "window": {"width": 600, "height": 600, "title": "Le Pendu", "fps": 60},
            "game": {"max_errors": 6, "default_difficulty": "medium"},
            "colors": {
                "background": [30, 30, 46],
                "text_primary": [205, 214, 244],
                "text_secondary": [166, 173, 200],
                "accent": [137, 180, 250],
                "success": [166, 227, 161],
                "error": [243, 139, 168],
                "hangman": [205, 214, 244],
                "gallows": [127, 132, 156]
            }
        }
    return config


# ──────────────────────────────────────────
#  Test rapide (lance ce fichier directement)
# ──────────────────────────────────────────
if __name__ == "__main__":
    print("=== Test word_manager.py ===\n")

    word, diff, cat = get_random_word("easy")
    print(f"Mot facile     : {word} ({cat})")

    word, diff, cat = get_random_word("medium")
    print(f"Mot moyen      : {word} ({cat})")

    word, diff, cat = get_random_word("hard")
    print(f"Mot difficile  : {word} ({cat})")

    print(f"\nCatégories dispo : {get_all_categories()}")

    print("\n--- Test sauvegarde score ---")
    is_record = save_score("PYTHON", "medium", "informatique", 3, 1, 60)
    print(f"Nouveau record ? {is_record}")

    scores = load_scores()
    print(f"Meilleur score  : {scores['record']} tentatives")
    print(f"Nb de scores    : {len(scores['scores'])}")

    config = load_config()
    print(f"\nFenêtre : {config['window']['width']}x{config['window']['height']}")
    print(f"FPS     : {config['window']['fps']}")