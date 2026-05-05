import pygame
import sys
import os

# ── Modules du projet ──────────────────────────────────────────
from word_manager import get_random_word, save_score, load_config
from language_manager import lang

# ── Initialisation pygame ──────────────────────────────────────
pygame.init()
pygame.font.init()

# ── Chargement de la config ────────────────────────────────────
config  = load_config()
WIN_W   = config["window"]["width"]       # 600
WIN_H   = config["window"]["height"]      # 600
TITLE   = config["window"]["title"]       # "Le Pendu"
FPS     = config["window"]["fps"]         # 60
MAX_ERR = config["game"]["max_errors"]    # 6

C = config["colors"]
COL_BG       = tuple(C["background"])    # (30, 30, 46)
COL_TEXT      = tuple(C["text_primary"]) # (205, 214, 244)
COL_MUTED     = tuple(C["text_secondary"])
COL_ACCENT    = tuple(C["accent"])
COL_SUCCESS   = tuple(C["success"])
COL_ERROR     = tuple(C["error"])
COL_HANGMAN   = tuple(C["hangman"])
COL_GALLOWS   = tuple(C["gallows"])

# ── Fenêtre ────────────────────────────────────────────────────
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption(lang.t("menu.title"))
clock  = pygame.time.Clock()

# ── Polices ────────────────────────────────────────────────────
FONT_TITLE  = pygame.font.SysFont("segoeui",  42, bold=True)
FONT_WORD   = pygame.font.SysFont("segoeui",  38, bold=True)
FONT_HINT   = pygame.font.SysFont("segoeui",  20)
FONT_SMALL  = pygame.font.SysFont("segoeui",  17)
FONT_MSG    = pygame.font.SysFont("segoeui",  26, bold=True)
FONT_BTN    = pygame.font.SysFont("segoeui",  19)


# ══════════════════════════════════════════════════════════════
#  DESSIN DU PENDU
# ══════════════════════════════════════════════════════════════
def draw_hangman(surface: pygame.Surface, errors: int) -> None:
    """Dessine la potence et le bonhomme selon le nb d'erreurs (0-6)."""
    gx, gy = 90, 80   # origine de la potence
    lw = 3             # épaisseur trait

    # ── Potence (toujours visible) ──────────────────────────────
    # socle
    pygame.draw.line(surface, COL_GALLOWS, (gx - 40, gy + 290), (gx + 40, gy + 290), lw + 1)
    # montant vertical
    pygame.draw.line(surface, COL_GALLOWS, (gx, gy + 290), (gx, gy), lw)
    # bras horizontal
    pygame.draw.line(surface, COL_GALLOWS, (gx, gy), (gx + 120, gy), lw)
    # corde
    pygame.draw.line(surface, COL_GALLOWS, (gx + 120, gy), (gx + 120, gy + 50), lw)

    cx = gx + 120   # centre horizontal du bonhomme
    head_y = gy + 50

    if errors >= 1:   # tête
        pygame.draw.circle(surface, COL_HANGMAN, (cx, head_y + 18), 18, lw)
    if errors >= 2:   # corps
        pygame.draw.line(surface, COL_HANGMAN, (cx, head_y + 36), (cx, head_y + 100), lw)
    if errors >= 3:   # bras gauche
        pygame.draw.line(surface, COL_HANGMAN, (cx, head_y + 52), (cx - 30, head_y + 80), lw)
    if errors >= 4:   # bras droit
        pygame.draw.line(surface, COL_HANGMAN, (cx, head_y + 52), (cx + 30, head_y + 80), lw)
    if errors >= 5:   # jambe gauche
        pygame.draw.line(surface, COL_HANGMAN, (cx, head_y + 100), (cx - 28, head_y + 138), lw)
    if errors >= 6:   # jambe droite — game over
        pygame.draw.line(surface, COL_HANGMAN, (cx, head_y + 100), (cx + 28, head_y + 138), lw)


# ══════════════════════════════════════════════════════════════
#  ÉTAT DU JEU
# ══════════════════════════════════════════════════════════════
class GameState:
    def __init__(self):
        self.reset()

    def reset(self, difficulty: str = "medium"):
        word, diff, cat        = get_random_word(difficulty, language=lang.current)
        self.word:       str   = word           # "PYTHON"
        self.difficulty: str   = diff
        self.category:   str   = cat
        self.guessed:    set   = set()          # lettres déjà jouées
        self.errors:     int   = 0
        self.status:     str   = "playing"      # "playing" | "win" | "lose"
        self.message:    str   = ""             # feedback rapide
        self.msg_timer:  int   = 0              # frames restantes pour afficher msg
        self.start_tick: int   = pygame.time.get_ticks()
        self.duration:   int   = 0              # secondes à la fin

    @property
    def attempts(self) -> int:
        return len(self.guessed)

    def masked_word(self) -> str:
        """Retourne le mot avec _ pour les lettres non trouvées."""
        return "  ".join(c if c in self.guessed else "_" for c in self.word)

    def try_letter(self, letter: str) -> None:
        letter = letter.upper()
        if not letter.isalpha() or letter in self.guessed:
            self.message   = lang.t("game.already_tried")
            self.msg_timer = 90
            return

        self.guessed.add(letter)

        if letter in self.word:
            self.message   = lang.t("game.good_guess")
            self.msg_timer = 60
            if all(c in self.guessed for c in self.word):
                self._end("win")
        else:
            self.errors   += 1
            self.message   = lang.t("game.wrong_guess")
            self.msg_timer = 60
            if self.errors >= MAX_ERR:
                self._end("lose")

    def _end(self, result: str) -> None:
        self.status   = result
        elapsed       = pygame.time.get_ticks() - self.start_tick
        self.duration = elapsed // 1000
        if result == "win":
            save_score(self.word, self.difficulty, self.category,
                       self.attempts, self.errors, self.duration)


# ══════════════════════════════════════════════════════════════
#  RENDU
# ══════════════════════════════════════════════════════════════
def render(surface: pygame.Surface, gs: GameState) -> None:
    surface.fill(COL_BG)

    # ── Pendu ──────────────────────────────────────────────────
    draw_hangman(surface, gs.errors)

    # ── Infos en haut à droite ─────────────────────────────────
    err_color = COL_ERROR if gs.errors >= MAX_ERR - 1 else COL_MUTED
    err_text  = FONT_SMALL.render(
        f"{lang.t('game.errors')} : {gs.errors} / {MAX_ERR}", True, err_color)
    surface.blit(err_text, (WIN_W - err_text.get_width() - 20, 20))

    hint_text = FONT_SMALL.render(
        f"{lang.t('game.hint')} : {lang.category_name(gs.category)}", True, COL_MUTED)
    surface.blit(hint_text, (WIN_W - hint_text.get_width() - 20, 46))

    lang_text = FONT_SMALL.render(lang.flag() + " " + lang.language_name(), True, COL_MUTED)
    surface.blit(lang_text, (WIN_W - lang_text.get_width() - 20, WIN_H - 36))

    # ── Mot masqué ─────────────────────────────────────────────
    word_color = COL_SUCCESS if gs.status == "win" else (
                 COL_ERROR   if gs.status == "lose" else COL_TEXT)
    word_surf  = FONT_WORD.render(gs.masked_word(), True, word_color)
    wx = (WIN_W - word_surf.get_width()) // 2
    surface.blit(word_surf, (wx, WIN_H - 180))

    # ── Lettres déjà jouées ────────────────────────────────────
    played = "  ".join(sorted(gs.guessed))
    played_surf = FONT_HINT.render(played, True, COL_MUTED)
    surface.blit(played_surf, ((WIN_W - played_surf.get_width()) // 2, WIN_H - 130))

    # ── Feedback rapide ────────────────────────────────────────
    if gs.msg_timer > 0:
        alpha    = min(255, gs.msg_timer * 5)
        msg_col  = COL_SUCCESS if lang.t("game.good_guess") in gs.message else COL_ERROR
        msg_surf = FONT_MSG.render(gs.message, True, msg_col)
        msg_surf.set_alpha(alpha)
        surface.blit(msg_surf, ((WIN_W - msg_surf.get_width()) // 2, WIN_H - 230))
        gs.msg_timer -= 1

    # ── Écran fin de partie ────────────────────────────────────
    if gs.status != "playing":
        _render_end_screen(surface, gs)

    pygame.display.flip()


def _render_end_screen(surface: pygame.Surface, gs: GameState) -> None:
    """Superpose un panneau de résultat transparent."""
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    if gs.status == "win":
        title_col = COL_SUCCESS
        title_txt = lang.t("result.win_title")
        sub_txt   = f"{lang.t('result.win_message')} : {gs.word}"
    else:
        title_col = COL_ERROR
        title_txt = lang.t("result.lose_title")
        sub_txt   = f"{lang.t('result.lose_message')} : {gs.word}"

    title_surf = FONT_TITLE.render(title_txt, True, title_col)
    surface.blit(title_surf, ((WIN_W - title_surf.get_width()) // 2, 200))

    sub_surf = FONT_HINT.render(sub_txt, True, COL_TEXT)
    surface.blit(sub_surf, ((WIN_W - sub_surf.get_width()) // 2, 260))

    attempts_surf = FONT_HINT.render(
        lang.t("result.attempts_label", n=gs.attempts), True, COL_MUTED)
    surface.blit(attempts_surf, ((WIN_W - attempts_surf.get_width()) // 2, 292))

    # Boutons [R] Rejouer  [M] Menu  (simulés en texte pour l'instant)
    replay_surf = FONT_BTN.render(lang.t("result.play_again"), True, COL_ACCENT)
    surface.blit(replay_surf, ((WIN_W - replay_surf.get_width()) // 2, 360))

    quit_surf = FONT_BTN.render(lang.t("result.quit"), True, COL_MUTED)
    surface.blit(quit_surf, ((WIN_W - quit_surf.get_width()) // 2, 396))


# ══════════════════════════════════════════════════════════════
#  BOUCLE PRINCIPALE
# ══════════════════════════════════════════════════════════════
def main():
    gs = GameState()

    while True:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # ── Raccourcis globaux ─────────────────────────
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # ── Fin de partie ──────────────────────────────
                if gs.status != "playing":
                    if event.key == pygame.K_r:           # Rejouer
                        gs.reset(gs.difficulty)
                    elif event.key == pygame.K_q:         # Quitter
                        pygame.quit()
                        sys.exit()

                # ── En jeu : saisie d'une lettre ───────────────
                elif event.unicode and event.unicode.isalpha():
                    gs.try_letter(event.unicode)

        render(screen, gs)
        clock.tick(FPS)


if __name__ == "__main__":
    main()