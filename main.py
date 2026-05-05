import pygame
import sys

from word_manager import get_random_word, save_score, load_config
from language_manager import lang

SCREEN_MENU = "menu"
SCREEN_DIFFICULTY = "difficulty"
SCREEN_GAME = "game"

# INIT # 
pygame.init()
pygame.font.init()

config  = load_config()
WIN_W   = config["window"]["width"]
WIN_H   = config["window"]["height"]
FPS     = config["window"]["fps"]
MAX_ERR = config["game"]["max_errors"]

C = config["colors"]
COL_BG      = tuple(C["background"])
COL_TEXT    = tuple(C["text_primary"])
COL_MUTED   = tuple(C["text_secondary"])
COL_ACCENT  = tuple(C["accent"])
COL_SUCCESS = tuple(C["success"])
COL_ERROR   = tuple(C["error"])
COL_HANGMAN = tuple(C["hangman"])
COL_GALLOWS = tuple(C["gallows"])

screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption(lang.t("menu.title"))
clock  = pygame.time.Clock()


# POLICES #   
def font(size, bold=False):
    for name in ("Segoe UI", "Arial", "DejaVu Sans", ""):
        f = pygame.font.SysFont(name, size, bold=bold)
        if f:
            return f
    return pygame.font.Font(None, size)

F_HUGE   = font(72, bold=True)
F_TITLE  = font(48, bold=True)
F_LARGE  = font(34, bold=True)
F_MEDIUM = font(24)
F_SMALL  = font(19)
F_TINY   = font(15)


# UTILITAIRES DE RENDU #   
def draw_text(surf, text, fnt, color, cx, cy):
    s = fnt.render(text, True, color)
    surf.blit(s, (cx - s.get_width() // 2, cy - s.get_height() // 2))
    return s.get_width(), s.get_height()


def draw_button(surf, text, fnt, cx, cy, w, h, color, hover=False):
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    bg   = (color[0]//3, color[1]//3, color[2]//3) if not hover else \
           (min(color[0]+40, 255), min(color[1]+40, 255), min(color[2]+40, 255))
    pygame.draw.rect(surf, bg, rect, border_radius=10)
    pygame.draw.rect(surf, color, rect, 2, border_radius=10)
    draw_text(surf, text, fnt, color, cx, cy)
    return rect


# DESSIN DU PENDU #   
def draw_hangman(surf, errors):
    gx = WIN_W // 5
    gy = 60
    lw = 4

    if errors >= 1:
        pygame.draw.line(surf, COL_GALLOWS, (gx-55, gy+340), (gx+55, gy+340), lw+1)
    if errors >= 2:
        pygame.draw.line(surf, COL_GALLOWS, (gx,    gy+340), (gx,    gy),      lw)
    if errors >= 3:
        pygame.draw.line(surf, COL_GALLOWS, (gx,    gy),     (gx+140, gy),     lw)
    if errors >= 4:
        pygame.draw.line(surf, COL_GALLOWS, (gx+140, gy),    (gx+140, gy+60),  lw)
    
    cx     = gx + 140
    head_y = gy + 60

    if errors >= 5:
        pygame.draw.circle(surf, COL_HANGMAN, (cx, head_y+24), 24, lw)
    if errors >= 6:
        pygame.draw.line(surf, COL_HANGMAN, (cx, head_y+48),  (cx, head_y+130),      lw)
    if errors >= 7:
        pygame.draw.line(surf, COL_HANGMAN, (cx, head_y+68),  (cx-40, head_y+105),   lw)
    if errors >= 8:
        pygame.draw.line(surf, COL_HANGMAN, (cx, head_y+68),  (cx+40, head_y+105),   lw)
    if errors >= 9:
        pygame.draw.line(surf, COL_HANGMAN, (cx, head_y+130), (cx-36, head_y+178),   lw)
    if errors >= 10:
        pygame.draw.line(surf, COL_HANGMAN, (cx, head_y+130), (cx+36, head_y+178),   lw)


# ÉTAT DU JEU #   
class GameState:
    def __init__(self, difficulty="medium"):
        self.reset(difficulty)

    def reset(self, difficulty="medium"):
        word, diff, cat = get_random_word(difficulty, language=lang.current)
        self.word       = word
        self.difficulty = diff
        self.category   = cat
        self.guessed    = set()
        self.errors     = 0
        self.status     = "playing"
        self.message    = ""
        self.msg_timer  = 0
        self.is_record  = False
        self.start_tick = pygame.time.get_ticks()
        self.duration   = 0

    @property
    def attempts(self):
        return len(self.guessed)

    def masked_word(self):
        return "  ".join(c if c in self.guessed else "_" for c in self.word)

    def try_letter(self, letter):
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
                self._finish("win")
        else:
            self.errors   += 1
            self.message   = lang.t("game.wrong_guess")
            self.msg_timer = 60
            if self.errors >= MAX_ERR:
                self._finish("lose")

    def _finish(self, result):
        self.status   = result
        self.duration = (pygame.time.get_ticks() - self.start_tick) // 1000
        if result == "win":
            self.is_record = save_score(
                self.word, self.difficulty, self.category,
                self.attempts, self.errors, self.duration)


# ÉCRAN : MENU PRINCIPAL #   
class MenuScreen:
    def __init__(self):
        self._btn_play = None
        self._btn_lang = None
        self._btn_quit = None
        self.difficulty = "medium"

    def handle(self, event):
        # ✔️ On ne touche à event.pos QUE si c’est un clic souris
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self._btn_play and self._btn_play.collidepoint(mx, my):
                return "play"

            if self._btn_lang and self._btn_lang.collidepoint(mx, my):
                lang.toggle()
                pygame.display.set_caption(lang.t("menu.title"))

            if self._btn_quit and self._btn_quit.collidepoint(mx, my):
                return "quit"

        # ✔️ clavier séparé (sans event.pos)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "play"
            if event.key == pygame.K_ESCAPE:
                return "quit"

        return None

    def draw(self, surf):
        surf.fill(COL_BG)
        mx, my = pygame.mouse.get_pos()
        bcx    = WIN_W // 2
        bw, bh = 300, 62

        # Titre
        draw_text(surf, lang.t("menu.title"), F_HUGE, COL_ACCENT, bcx, WIN_H // 4)

        # Sous-titre
        draw_text(surf, "— " + lang.t("menu.choose_difficulty") + " —",
                  F_SMALL, COL_MUTED, bcx, WIN_H // 4 + 75)

        # Bouton Jouer
        y1 = WIN_H // 2 + 10
        h1 = pygame.Rect(bcx-bw//2, y1-bh//2, bw, bh).collidepoint(mx, my)
        self._btn_play = draw_button(surf, lang.t("menu.play"),
                                     F_LARGE, bcx, y1, bw, bh, COL_ACCENT, h1)

        # Bouton Langue
        y2 = y1 + 90
        label = lang.flag() + "  " + lang.language_name()
        h2 = pygame.Rect(bcx-bw//2, y2-bh//2, bw, bh).collidepoint(mx, my)
        self._btn_lang = draw_button(surf, label,
                                     F_MEDIUM, bcx, y2, bw, bh, COL_MUTED, h2)

        # Bouton Quitter
        y3 = y2 + 82
        h3 = pygame.Rect(bcx-bw//2, y3-bh//2, bw, bh).collidepoint(mx, my)
        self._btn_quit = draw_button(surf, lang.t("menu.quit"),
                                     F_MEDIUM, bcx, y3, bw, bh, COL_ERROR, h3)

        # Astuce bas de page
        draw_text(surf, "Entrée · Jouer    Échap · Quitter",
                  F_TINY, COL_MUTED, bcx, WIN_H - 22)

        pygame.display.flip()


#   
#  ÉCRAN : JEU
#   
class GameScreen:
    def __init__(self, difficulty="medium"):
        self.gs          = GameState(difficulty)
        self._btn_replay = None
        self._btn_menu   = None
        self._btn_quit   = None

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            if self.gs.status != "playing":
                if event.key == pygame.K_r:
                    self.gs.reset(self.gs.difficulty)
                elif event.key == pygame.K_m:
                    return "menu"
                elif event.key == pygame.K_q:
                    return "quit"
            elif event.unicode and event.unicode.isalpha():
                self.gs.try_letter(event.unicode)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.gs.status != "playing":
                if self._btn_replay and self._btn_replay.collidepoint(mx, my):
                    self.gs.reset(self.gs.difficulty)
                elif self._btn_menu and self._btn_menu.collidepoint(mx, my):
                    return "menu"
                elif self._btn_quit and self._btn_quit.collidepoint(mx, my):
                    return "quit"
        return None

    def draw(self, surf):
        surf.fill(COL_BG)
        gs     = self.gs
        mx, my = pygame.mouse.get_pos()

        # Pendu (moitié gauche)
        draw_hangman(surf, gs.errors)

        # Zone droite
        rx  = WIN_W // 2 + 30
        rw  = WIN_W - rx - 30
        rcx = rx + rw // 2

        draw_text(surf, f"{lang.t('game.errors')} : {gs.errors} / {MAX_ERR}",
                  F_SMALL,
                  COL_ERROR if gs.errors >= MAX_ERR - 1 else COL_MUTED,
                  rcx, 38)

        draw_text(surf,
                  f"{lang.t('game.hint')} : {lang.category_name(gs.category)}",
                  F_SMALL, COL_MUTED, rcx, 70)

        # Mot masqué
        word_col = COL_SUCCESS if gs.status == "win" else \
                   COL_ERROR   if gs.status == "lose" else COL_TEXT
        draw_text(surf, gs.masked_word(), F_LARGE, word_col, rcx, WIN_H // 2 - 30)

        # Lettres jouées
        draw_text(surf, "  ".join(sorted(gs.guessed)),
                  F_MEDIUM, COL_MUTED, rcx, WIN_H // 2 + 30)

        # Feedback
        if gs.msg_timer > 0:
            msg_col = COL_SUCCESS if lang.t("game.good_guess") in gs.message else COL_ERROR
            msg_s   = F_MEDIUM.render(gs.message, True, msg_col)
            msg_s.set_alpha(min(255, gs.msg_timer * 5))
            surf.blit(msg_s, (rcx - msg_s.get_width()//2, WIN_H//2 - 90))
            gs.msg_timer -= 1

        # Langue + aide
        draw_text(surf, lang.flag() + " " + lang.language_name(),
                  F_TINY, COL_MUTED, 55, WIN_H - 18)
        draw_text(surf, "Échap → Menu", F_TINY, COL_MUTED, WIN_W - 65, WIN_H - 18)

        # Résultat
        if gs.status != "playing":
            self._draw_result(surf, gs, mx, my)

        pygame.display.flip()

    def _draw_result(self, surf, gs, mx, my):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surf.blit(overlay, (0, 0))

        cy  = WIN_H // 2 - 130
        bcx = WIN_W // 2
        bw, bh = 250, 54

        if gs.status == "win":
            draw_text(surf, lang.t("result.win_title"),  F_TITLE, COL_SUCCESS, bcx, cy)
            draw_text(surf, f"{lang.t('result.win_message')} : {gs.word}",
                      F_MEDIUM, COL_TEXT, bcx, cy + 68)
        else:
            draw_text(surf, lang.t("result.lose_title"), F_TITLE, COL_ERROR,   bcx, cy)
            draw_text(surf, f"{lang.t('result.lose_message')} : {gs.word}",
                      F_MEDIUM, COL_TEXT, bcx, cy + 68)

        draw_text(surf, lang.t("result.attempts_label", n=gs.attempts),
                  F_SMALL, COL_MUTED, bcx, cy + 106)

        if gs.is_record:
            draw_text(surf, lang.t("result.new_record"),
                      F_MEDIUM, COL_ACCENT, bcx, cy + 138)

        y_r = cy + 200
        h1  = pygame.Rect(bcx-bw//2, y_r-bh//2, bw, bh).collidepoint(mx, my)
        self._btn_replay = draw_button(surf, lang.t("result.play_again"),
                                       F_MEDIUM, bcx, y_r, bw, bh, COL_ACCENT, h1)

        y_m = y_r + 70
        h2  = pygame.Rect(bcx-bw//2, y_m-bh//2, bw, bh).collidepoint(mx, my)
        self._btn_menu = draw_button(surf, lang.t("result.main_menu"),
                                     F_MEDIUM, bcx, y_m, bw, bh, COL_MUTED, h2)

        y_q = y_m + 64
        h3  = pygame.Rect(bcx-bw//2, y_q-bh//2, bw, bh).collidepoint(mx, my)
        self._btn_quit = draw_button(surf, lang.t("result.quit"),
                                     F_MEDIUM, bcx, y_q, bw, bh, COL_ERROR, h3)

        draw_text(surf, "R · Rejouer    M · Menu    Q · Quitter",
                  F_TINY, COL_MUTED, bcx, WIN_H - 22)


# BOUCLE PRINCIPALE #   
def main():
    screen_state = SCREEN_MENU
    menu = MenuScreen()
    difficulty = "medium"
    game = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            #  MENU PRINCIPAL  
            if screen_state == SCREEN_MENU:
                result = menu.handle(event)

                if result == "play":
                    screen_state = SCREEN_DIFFICULTY

                elif result == "quit":
                    pygame.quit()
                    sys.exit()

            #   DIFFICULTÉ  
            elif screen_state == SCREEN_DIFFICULTY:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    if menu._btn_easy and menu._btn_easy.collidepoint(mx, my):
                        difficulty = "easy"
                        game = GameScreen(difficulty)
                        screen_state = SCREEN_GAME

                    elif menu._btn_medium and menu._btn_medium.collidepoint(mx, my):
                        difficulty = "medium"
                        game = GameScreen(difficulty)
                        screen_state = SCREEN_GAME

                    elif menu._btn_hard and menu._btn_hard.collidepoint(mx, my):
                        difficulty = "hard"
                        game = GameScreen(difficulty)
                        screen_state = SCREEN_GAME

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    screen_state = SCREEN_MENU

            #   JEU  
            elif screen_state == SCREEN_GAME:
                result = game.handle(event)

                if result == "menu":
                    screen_state = SCREEN_MENU

                elif result == "quit":
                    pygame.quit()
                    sys.exit()

        #   DRAW  
        if screen_state == SCREEN_MENU:
            menu.draw(screen)

        elif screen_state == SCREEN_DIFFICULTY:
            draw_difficulty_screen(menu, screen)

        elif screen_state == SCREEN_GAME:
            game.draw(screen)

        clock.tick(FPS)

def draw_difficulty_screen(menu, surf):
    surf.fill(COL_BG)
    mx, my = pygame.mouse.get_pos()
    bcx = WIN_W // 2

    draw_text(surf, lang.t("menu.choose_difficulty"),
              F_HUGE, COL_ACCENT, bcx, WIN_H // 4)

    # bouton faciles 
    bw, bh = 220, 70
    y = WIN_H // 2 - 60

    menu._btn_easy = draw_button(
        surf,
        lang.t("menu.easy"),
        F_MEDIUM,
        bcx,
        y,
        bw,
        bh,
        COL_SUCCESS,
        False
    )

    menu._btn_medium = draw_button(
        surf,
        lang.t("menu.medium"),
        F_MEDIUM,
        bcx,
        y + 100,
        bw,
        bh,
        COL_ACCENT,
        False
    )

    menu._btn_hard = draw_button(
        surf,
        lang.t("menu.hard"),
        F_MEDIUM,
        bcx,
        y + 200,
        bw,
        bh,
        COL_ERROR,
        False
    )

    draw_text(surf, "ESC → Menu",
              F_TINY, COL_MUTED, bcx, WIN_H - 30)

    pygame.display.flip()

if __name__ == "__main__":
    main()