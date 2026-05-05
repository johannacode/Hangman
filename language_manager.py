import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TRANSLATIONS_FILE = os.path.join(DATA_DIR, "translations.json")
CONFIG_FILE       = os.path.join(DATA_DIR, "config.json")

SUPPORTED_LANGUAGES = ["fr", "en"]
DEFAULT_LANGUAGE    = "fr"


class LanguageManager:
    """
    Gère la langue active du jeu.

    Usage :
        lang = LanguageManager()          # charge la langue sauvegardée
        lang.set("en")                    # change la langue
        lang.t("menu.play")               # → "Play"
        lang.t("result.attempts_label", n=3)  # → "in 3 attempt(s)"
    """

    def __init__(self):
        self._translations: dict = {}
        self._current: str = DEFAULT_LANGUAGE
        self._load_translations()
        self._load_saved_language()

    # ──────────────────────────────────────────
    #  Chargement
    # ──────────────────────────────────────────

    def _load_translations(self) -> None:
        """Charge le fichier translations.json."""
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
        except FileNotFoundError:
            print(f"[ERREUR] Fichier de traductions introuvable : {TRANSLATIONS_FILE}")
            self._translations = {}
        except json.JSONDecodeError as e:
            print(f"[ERREUR] JSON invalide dans translations.json : {e}")
            self._translations = {}

    def _load_saved_language(self) -> None:
        """Lit la langue enregistrée dans config.json."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            saved = config.get("game", {}).get("language", DEFAULT_LANGUAGE)
            if saved in SUPPORTED_LANGUAGES:
                self._current = saved
        except (FileNotFoundError, json.JSONDecodeError):
            self._current = DEFAULT_LANGUAGE

    def _save_language(self) -> None:
        """Persiste la langue choisie dans config.json."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            config.setdefault("game", {})["language"] = self._current
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass  # On ne bloque pas le jeu si la sauvegarde échoue

    # ──────────────────────────────────────────
    #  API publique
    # ──────────────────────────────────────────

    @property
    def current(self) -> str:
        """Code de la langue active ("fr" ou "en")."""
        return self._current

    @property
    def available(self) -> list[str]:
        """Liste des codes de langues disponibles."""
        return SUPPORTED_LANGUAGES

    def set(self, code: str) -> bool:
        """
        Change la langue active.
        Retourne True si le changement a réussi, False sinon.
        """
        code = code.strip().lower()
        if code not in SUPPORTED_LANGUAGES:
            print(f"[AVERTISSEMENT] Langue '{code}' non supportée. Choix : {SUPPORTED_LANGUAGES}")
            return False
        self._current = code
        self._save_language()
        return True

    def toggle(self) -> str:
        """Bascule entre les langues disponibles et retourne le nouveau code."""
        idx = SUPPORTED_LANGUAGES.index(self._current)
        next_idx = (idx + 1) % len(SUPPORTED_LANGUAGES)
        self.set(SUPPORTED_LANGUAGES[next_idx])
        return self._current

    def t(self, key: str, **kwargs) -> str:
        """
        Retourne le texte traduit pour la clé donnée (notation pointée).

        Exemples :
            t("menu.play")                    → "Jouer"  /  "Play"
            t("result.attempts_label", n=4)   → "en 4 tentative(s)"
            t("difficulty.easy")              → "Facile"  /  "Easy"

        Si la clé est introuvable, retourne la clé elle-même
        (le jeu continue sans planter).
        """
        lang_data = self._translations.get(self._current, {})
        parts = key.split(".")
        value = lang_data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
            if value is None:
                # Fallback : essaye la langue par défaut
                fallback = self._translations.get(DEFAULT_LANGUAGE, {})
                for p in parts:
                    fallback = fallback.get(p) if isinstance(fallback, dict) else None
                    if fallback is None:
                        break
                return str(fallback) if fallback else key

        # Remplace les variables {n}, {word}, etc.
        if isinstance(value, str) and kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError:
                pass  # Renvoie la chaîne avec les placeholders intacts si ça plante

        return str(value) if value is not None else key

    def category_name(self, category_key: str) -> str:
        """Retourne le nom affiché d'une catégorie dans la langue active."""
        return self.t(f"categories.{category_key}")

    def flag(self) -> str:
        """Retourne l'emoji drapeau de la langue active."""
        return self._translations.get(self._current, {}).get("meta", {}).get("flag", "🌐")

    def language_name(self) -> str:
        """Retourne le nom de la langue active dans cette même langue."""
        return self._translations.get(self._current, {}).get("meta", {}).get("name", self._current)


# ──────────────────────────────────────────
#  Singleton global — importé par les autres modules
# ──────────────────────────────────────────
lang = LanguageManager()


# ──────────────────────────────────────────
#  Test rapide
# ──────────────────────────────────────────
if __name__ == "__main__":
    print("=== Test language_manager.py ===\n")

    lm = LanguageManager()

    for code in ["fr", "en"]:
        lm.set(code)
        print(f"── {lm.flag()}  {lm.language_name()} ──")
        print(f"  menu.title         : {lm.t('menu.title')}")
        print(f"  menu.play          : {lm.t('menu.play')}")
        print(f"  difficulty.hard    : {lm.t('difficulty.hard')}")
        print(f"  result.win_title   : {lm.t('result.win_title')}")
        print(f"  result.attempts    : {lm.t('result.attempts_label', n=4)}")
        print(f"  result.new_record  : {lm.t('result.new_record')}")
        print(f"  clé inexistante    : {lm.t('menu.nonexistent')}")
        print()

    print("── Toggle ──")
    lm.set("fr")
    print(f"  Avant  : {lm.current}")
    lm.toggle()
    print(f"  Après  : {lm.current}")

    print("\n✅ Tout fonctionne !")