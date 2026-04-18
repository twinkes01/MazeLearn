import pygame, random, sys, json, os
from maze_generation import generate_unicursal_maze

pygame.init()
FPS, CELL_SIZE, UI_W = 60, 40, 250
WHITE, BLACK, GRAY, GREEN, RED, BLUE, YELLOW, LBLUE = (255,255,255), (0,0,0), (100,100,100), (0,255,0), (255,0,0), (0,0,255), (255,255,0), (100,150,255)
ORANGE = (255, 140, 0)

font_path = "DejaVuSans.ttf"
try:
    FONT = pygame.font.Font(font_path, 38)
    FONT_SMALL = pygame.font.Font(font_path, 30)
    FONT_TITLE = pygame.font.Font(font_path, 52)
    FONT_BUTTON = pygame.font.Font(font_path, 34)
except FileNotFoundError:
    try:
        FONT = pygame.font.SysFont('dejavusans', 38)
        FONT_SMALL = pygame.font.SysFont('dejavusans', 30)
        FONT_TITLE = pygame.font.SysFont('dejavusans', 52)
        FONT_BUTTON = pygame.font.SysFont('dejavusans', 34)
    except:
        FONT = pygame.font.SysFont('arial', 38)
        FONT_SMALL = pygame.font.SysFont('arial', 30)
        FONT_TITLE = pygame.font.SysFont('arial', 52)
        FONT_BUTTON = pygame.font.SysFont('arial', 34)

DICE_FACES = {
    1: [(0, 0)],
    2: [(-1, -1), (1, 1)],
    3: [(-1, -1), (0, 0), (1, 1)],
    4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
    6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]
}

class Button:
    def __init__(self, x, y, w, h, text, color=LBLUE, font_size=34):
        self.rect = pygame.Rect(x, y, w, h)
        self.text, self.color = text, color
        self.font_size = font_size
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        font = pygame.font.SysFont('dejavusans', self.font_size)
        text_surf = font.render(self.text, True, WHITE)
        if text_surf.get_width() > self.rect.width - 20:
            small_font = pygame.font.SysFont('dejavusans', 28)
            text_surf = small_font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class Dice:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 140, 180)
        self.result = 1
        self.rolling = False
        self.start_time = 0
        self.highlight = 1
        self.roll_duration = 1200
        self.last_switch = 0
        self.switch_interval = 150

    def roll(self):
        self.rolling = True
        self.start_time = pygame.time.get_ticks()
        self.result = random.randint(1, 6)
        self.highlight = 1
        self.last_switch = self.start_time

    def update(self):
        if not self.rolling:
            return None
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        if elapsed >= self.roll_duration:
            self.rolling = False
            self.highlight = self.result
            return self.result
        if now - self.last_switch >= self.switch_interval:
            self.highlight = random.randint(1, 6)
            self.last_switch = now
        return None

    def draw_face(self, screen, num, x, y, size, is_highlighted):
        if is_highlighted:
            color = GREEN if not self.rolling else YELLOW
        else:
            color = WHITE
        pygame.draw.rect(screen, color, (x, y, size, size), border_radius=8)
        pygame.draw.rect(screen, BLACK, (x, y, size, size), 3, border_radius=8)
        for dx, dy in DICE_FACES[num]:
            dot_x = int(x + size/2 + dx * size/4)
            dot_y = int(y + size/2 + dy * size/4)
            pygame.draw.circle(screen, BLACK, (dot_x, dot_y), 7)
            pygame.draw.circle(screen, WHITE, (dot_x, dot_y), 7, 2)

    def draw(self, screen):
        cols, rows = 2, 3
        gap = 6
        face_w = (self.rect.width - gap * (cols + 1)) // cols
        face_h = (self.rect.height - gap * (rows + 1)) // rows
        for i in range(6):
            row, col = divmod(i, 2)
            num = i + 1
            x = self.rect.x + gap + col * (face_w + gap)
            y = self.rect.y + gap + row * (face_h + gap)
            is_highlighted = (num == self.highlight)
            self.draw_face(screen, num, x, y, face_w, is_highlighted)

class Player:
    def __init__(self, pos):
        self.pos, self.lives, self.idx, self.visited = pos, 5, 0, {pos}
    def lose_health(self):
        self.lives -= 1
        return self.lives <= 0
    def move(self, steps, path):
        for _ in range(steps):
            if self.idx < len(path) - 1:
                self.idx += 1
                self.visited.add(path[self.idx])
                self.pos = path[self.idx]

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    return lines if lines else [""]

def draw_heart(screen, x, y, size, color):
    heart_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    half = size // 4
    pygame.draw.circle(heart_surface, color, (half, half), half)
    pygame.draw.circle(heart_surface, color, (half * 3, half), half)
    pygame.draw.polygon(heart_surface, color, [(0, half), (size, half), (size // 2, size - 2)])
    screen.blit(heart_surface, (x, y))

def draw_hearts(screen, lives, x, y):
    for i in range(5):
        color = RED if i < lives else GRAY
        draw_heart(screen, x + i * 40, y, 30, color)

def load_question_templates(filepath='questions.json'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def load_about_author():
    try:
        with open('autor.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Информация об авторе не найдена"

def load_about_program():
    try:
        with open('help.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Информация о программе не найдена"

def generate_question_from_template(template):
    a_range = template.get('a_range', [1, 10])
    b_range = template.get('b_range', [1, 10])
    c_range = template.get('c_range', [1, 10])
    d_range = template.get('d_range', [1, 10])
    a = random.randint(a_range[0], a_range[1]) if a_range[1] > 0 else 0
    b = random.randint(b_range[0], b_range[1]) if b_range[1] > 0 else 0
    c = random.randint(c_range[0], c_range[1]) if c_range[1] > 0 else 0
    d = random.randint(d_range[0], d_range[1]) if d_range[1] > 0 else 0
    try:
        answer = eval(template.get('answer', '0'), {'a':a, 'b':b, 'c':c, 'd':d})
        correct = str(answer)
    except:
        correct = template.get('answer', '0')
        if isinstance(correct, int):
            correct = str(correct)
    question = template.get('q', '?').format(a=a, b=b, c=c, d=d)
    if 'options' in template:
        options = template['options'].copy()
        if correct not in options:
            options[0] = correct
        random.shuffle(options)
    else:
        options = generate_options(correct, template.get('type', 'number'))
    return {'q': question, 'options': options, 'a': correct}

def draw_mine_stats(screen, mines_hit, mines_defused, x, y):
    stat_font = pygame.font.SysFont('dejavusans', 24)
    total_text = stat_font.render(f"Найдено мин: {mines_hit}", True, BLACK)
    screen.blit(total_text, (x - 8, y - 45))
    defused_text = stat_font.render(f"Обезврежено: {mines_defused}", True, GREEN)
    screen.blit(defused_text, (x - 8, y - 15))
    defused_text = stat_font.render(f"Взорвались: {mines_hit - mines_defused}", True, RED)
    screen.blit(defused_text, (x - 8, y + 15))

def generate_options(correct, q_type='number'):
    try:
        if q_type == 'binary':
            options = {correct}
            iterations = 0
            while len(options) < 4 and iterations < 100:
                wrong = list(correct)
                if len(wrong) > 1:
                    idx = random.randint(0, len(wrong)-1)
                    wrong[idx] = '1' if wrong[idx] == '0' else '0'
                wrong = ''.join(wrong)
                if wrong != correct and (len(wrong) == 1 or wrong[0] != '0'):
                    options.add(wrong)
                iterations += 1
            while len(options) < 4:
                options.add("0" if random.random() > 0.5 else "1")
            return list(options)
        else:
            correct_num = int(correct)
            options = {correct}
            iterations = 0
            while len(options) < 4 and iterations < 100:
                offset = random.randint(-5, 5)
                wrong = correct_num + offset
                if wrong != correct_num and wrong > 0:
                    options.add(str(wrong))
                iterations += 1
            while len(options) < 4:
                options.add(str(correct_num + len(options) + 1))
            return list(options)
    except:
        return [correct, "Вариант1", "Вариант2", "Вариант3"]
    
def draw_mine_indicator(screen, pos, state, offset_x, offset_y, cell_size):
    x = offset_x + pos[0] * cell_size
    y = offset_y + pos[1] * cell_size
    cx, cy = x + cell_size // 2, y + cell_size // 2
    
    if state == 'active':
        import math
        for i in range(8):
            angle = i * 45
            rad = math.radians(angle)
            start_x = cx + int(8 * math.cos(rad))
            start_y = cy + int(8 * math.sin(rad))
            end_x = cx + int(10 * math.cos(rad))
            end_y = cy + int(10 * math.sin(rad))
            pygame.draw.line(screen, BLACK, (start_x, start_y), (end_x, end_y), 3)
        pygame.draw.circle(screen, BLACK, (cx, cy), 6)
        pygame.draw.circle(screen, (50, 50, 50), (cx, cy), 8)
    
    elif state == 'defused':
        pygame.draw.line(screen, GREEN, (cx - 12, cy - 8), (cx - 3, cy + 5), 4)
        pygame.draw.line(screen, GREEN, (cx -3, cy + 5), (cx + 12, cy - 12), 4)
    
    elif state == 'exploded':
        for i in range(8):
            angle = i * 45
            import math
            rad = math.radians(angle)
            end_x = cx + int(12 * math.cos(rad))
            end_y = cy + int(12 * math.sin(rad))
            pygame.draw.line(screen, RED, (cx, cy), (end_x, end_y), 2)
        pygame.draw.circle(screen, RED, (cx, cy), 6)
        pygame.draw.circle(screen, (255, 100, 100), (cx, cy), 4)
        pygame.draw.circle(screen, ORANGE, (cx, cy), 10, 2)

def draw_question_screen(screen, question_data, answer_buttons, feedback=None):
    question = question_data.get('q', '?')
    max_text_width = 490
    lines = wrap_text(question, FONT, max_text_width)
    
    line_height = 38
    question_height = len(lines) * line_height
    num_buttons = len(answer_buttons)
    button_height = num_buttons * 60
    button_spacing = 20
    title_height = 50
    bottom_margin = 50
    box_h = title_height + question_height + button_spacing + button_height + bottom_margin
    
    box_w = 550
    box_x = (screen.get_width() - box_w) // 2
    box_y = (screen.get_height() - box_h) // 2
    
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), border_radius=15)
    pygame.draw.rect(screen, BLUE, (box_x, box_y, box_w, box_h), 4, border_radius=15)

    title = FONT.render("Вопрос!", True, RED)
    screen.blit(title, (box_x + 20, box_y + 20))

    y_pos = box_y + 60
    for line in lines:
        text_surf = FONT.render(line, True, BLACK)
        screen.blit(text_surf, (box_x + 20, y_pos))
        y_pos += line_height
    
    button_start_y = y_pos + 20
    for i, btn in enumerate(answer_buttons):
        btn.rect.y = button_start_y + i * 60
        btn.rect.x = box_x + 50
        btn.draw(screen)
    
    if feedback:
        fb_text = FONT.render(feedback, True, GREEN if feedback == "Верно!" else RED)
        screen.blit(fb_text, (box_x + 160, box_y + box_h - 45))

def draw_answer_feedback_screen(screen, feedback_text):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    color = GREEN if "Верно" in feedback_text else RED
    lines = feedback_text.split('\n')
    font_large = pygame.font.SysFont('dejavusans', 64)
    font_small = pygame.font.SysFont('dejavusans', 42)
    y_start = screen.get_height() // 2 - 30
    for i, line in enumerate(lines):
        font = font_large if i == 0 else font_small
        text_surf = font.render(line, True, color)
        text_rect = text_surf.get_rect(center=(screen.get_width() // 2, y_start + i * 50))
        screen.blit(text_surf, text_rect)

def draw_centered_text(screen, text, font, color, y):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(text_surf, text_rect)

def draw_about_author_screen(screen, back_btn, text):
    screen.fill(WHITE)
    draw_centered_text(screen, "Об авторе", FONT_TITLE, BLUE, 40)
    y = 150
    for line in text.split('\n'):
        text_surf = FONT.render(line, True, BLACK)
        screen.blit(text_surf, ((screen.get_width() - text_surf.get_width()) // 2, y))
        y += 40
    back_btn.draw(screen)

def draw_about_program_screen(screen, back_btn, text):
    screen.fill(WHITE)
    draw_centered_text(screen, "О программе", FONT_TITLE, BLUE, 40)
    y = 150
    for line in text.split('\n'):
        text_surf = FONT.render(line, True, BLACK)
        screen.blit(text_surf, ((screen.get_width() - text_surf.get_width()) // 2, y))
        y += 40
    back_btn.draw(screen)

class Dropdown:
    def __init__(self, x, y, w, h, options, color=LBLUE):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected = None
        self.color = color
        self.expanded = False
        self.option_rects = []
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        display_text = self.selected if self.selected else f"Выберите"
        font = pygame.font.SysFont('dejavusans', 28)
        text_surf = font.render(display_text, True, WHITE)
        text_rect = text_surf.get_rect(center=(self.rect.centerx - 11, self.rect.centery))
        screen.blit(text_surf, text_rect)
        arrow_x = self.rect.right - 23
        arrow_y = self.rect.centery
        pygame.draw.polygon(screen, WHITE, [
            (arrow_x - 8, arrow_y - 5),
            (arrow_x + 8, arrow_y - 5),
            (arrow_x, arrow_y + 5)
        ])
        if self.expanded:
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height + i * 40, self.rect.width, 40)
                self.option_rects.append(opt_rect)
                pygame.draw.rect(screen, LBLUE, opt_rect, border_radius=5)
                pygame.draw.rect(screen, BLACK, opt_rect, 2, border_radius=5)
                text_surf = font.render(opt, True, WHITE)
                text_rect = text_surf.get_rect(center=opt_rect.center)
                screen.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return False
            elif self.expanded:
                for i, opt_rect in enumerate(self.option_rects):
                    if opt_rect.collidepoint(event.pos):
                        self.selected = self.options[i]
                        self.expanded = False
                        self.option_rects = []
                        return True
                self.expanded = False
                self.option_rects = []
        return False
    
    def is_valid(self):
        return self.selected is not None

def draw_ui_panel(screen, player, path, ui_x, offset_y, maze_height, dice, roll_button):
    ui_offset = ui_x + 23
    draw_hearts(screen, player.lives, ui_offset, offset_y)
    progress_label = FONT.render("Прогресс:", True, BLACK)
    screen.blit(progress_label, (ui_offset, offset_y + 45))
    progress = int(player.idx / max(len(path)-1, 1) * 100)
    progress_text = FONT.render(f"{progress}%", True, BLACK)
    label_width = progress_label.get_width()
    percent_width = progress_text.get_width()
    center_offset = (label_width - percent_width) // 2
    screen.blit(progress_text, (ui_offset + center_offset, offset_y + 90))
    maze_bottom_y = offset_y + maze_height * CELL_SIZE
    dice.rect.x = ui_offset + 26
    dice.rect.y = maze_bottom_y - 250
    roll_button.rect.x = ui_offset + 26
    roll_button.rect.y = maze_bottom_y - 55
    dice.draw(screen)
    if roll_button:
        roll_button.color = GRAY if dice.rolling else ORANGE
        roll_button.draw(screen)

def main():
    global screen
    screen = pygame.display.set_mode((900, 700))
    pygame.display.set_caption("MazeLearn")
    clock = pygame.time.Clock()
    
    state, topic, diff = 'menu', None, None
    maze, path, player, dice, active_mines = None, None, None, None, set()
    mine_states = {}
    roll_button = None
    ui_x, offset_x, offset_y = 0, 0, 0
    gen_params = {}

    topic_dropdown = None
    diff_dropdown = None
    settings_valid = False
    
    current_question = None
    answer_buttons = []
    feedback = None
    feedback_timer = 0
    answer_feedback = None
    answer_feedback_timer = 0
    show_answer_feedback = False
    used_questions = set()
    
    about_author_text = load_about_author()
    about_program_text = load_about_program()
    
    show_info_menu = False
    info_menu_buttons = []
    
    window_reset = False
    prev_state = None
    question_templates = load_question_templates()

    mines_hit = 0
    mines_defused = 0

    btns = {
        'menu': [
            Button(350, 240, 200, 55, "Настроить", font_size=32),
            Button(350, 320, 200, 55, "Выход") 
        ],
        'back': Button(45, 620, 120, 55, "Назад", GRAY),
        'play': Button(350, 450, 200, 55, "Играть", GREEN)
    }

    running = True
    while running:
        btn_info_icon = Button(20, 20, 40, 40, "?", color=GRAY, font_size=28)
        btn_about_author = Button(70, 20, 150, 40, "Об авторе", color=LBLUE, font_size=30)
        btn_about_program = Button(70, 70, 197, 40, "О программе", color=LBLUE, font_size=29)
        info_menu_buttons = [btn_about_author, btn_about_program]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if state == 'menu':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_info_icon.rect.collidepoint(event.pos):
                        show_info_menu = not show_info_menu
                    elif show_info_menu:
                        if btn_about_author.rect.collidepoint(event.pos):
                            state = 'about_author'
                            show_info_menu = False
                        elif btn_about_program.rect.collidepoint(event.pos):
                            state = 'about_program'
                            show_info_menu = False
                        else:
                            show_info_menu = False
            
            if state in ('about_author', 'about_program', 'settings'):
                if btns['back'].clicked(event):
                    if state == 'settings':
                        topic_dropdown = None
                        diff_dropdown = None
                        settings_valid = False
                    state = 'menu'
            
            if state == 'menu':
                if not window_reset or prev_state != 'menu':
                    screen = pygame.display.set_mode((900, 700))
                    window_reset = True
                    prev_state = 'menu'
                if btns['menu'][0].clicked(event):
                    state = 'settings' 
                    topic_dropdown = None
                    diff_dropdown = None
                    settings_valid = False
                elif btns['menu'][1].clicked(event):
                    running = False
            
            elif state == 'settings':
                if topic_dropdown is None:
                    topic_dropdown = Dropdown(210, 200, 200, 50, ["Математика", "Информатика"])
                if diff_dropdown is None:
                    diff_dropdown = Dropdown(495, 200, 200, 50, ["Лёгкая", "Средняя", "Сложная"])
                
                if topic_dropdown:
                    if topic_dropdown.handle_event(event):
                        settings_valid = topic_dropdown.is_valid() and diff_dropdown.is_valid()
                if diff_dropdown:
                    if diff_dropdown.handle_event(event):
                        settings_valid = topic_dropdown.is_valid() and diff_dropdown.is_valid()
                
                if settings_valid and btns['play'].clicked(event):
                    topic = 'math' if topic_dropdown.selected == "Математика" else 'info'
                    diff_selected = diff_dropdown.selected.lower().replace('ё', 'е')
                    diff_map = {'легкая': 'easy', 'средняя': 'medium', 'сложная': 'hard'}
                    diff = diff_map.get(diff_selected, 'easy')
                    size, mine_pct, ratio = [13, 17, 21][['easy','medium','hard'].index(diff)], [0.4, 0.55, 0.7][['easy','medium','hard'].index(diff)], [0.5, 0.5, 0.4][['easy','medium','hard'].index(diff)]
                    gen_params = {'size': size, 'mine_pct': mine_pct, 'ratio': ratio}
                    state = 'loading'
            
            elif state == 'loading':
                size = gen_params['size']
                w, h = size * CELL_SIZE + UI_W, max(size * CELL_SIZE + 100, 700)
                screen = pygame.display.set_mode((w, h))
                offset_x, offset_y = 10, 10
                ui_x = w - UI_W + 10
                maze, start, finish, path = generate_unicursal_maze(size, size, gen_params['ratio'])
                player = Player(start)
                maze_bottom_y = offset_y + size * CELL_SIZE
                dice = Dice(ui_x + 20, maze_bottom_y - 250)
                roll_button = Button(ui_x + 20, maze_bottom_y - 55, 140, 55, "Бросить", color=ORANGE)
                candidates = [p for p in path if p not in (start, finish)]
                mine_list = random.sample(candidates, min(int(len(path)*gen_params['mine_pct']), len(candidates)))
                active_mines = set(mine_list)
                mine_states = {pos: 'active' for pos in mine_list}
                used_questions = set()
                mines_hit = 0
                mines_defused = 0
                state = 'game'
                
            elif state == 'game':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if roll_button and roll_button.clicked(event) and not dice.rolling:
                        dice.roll()
        
            elif state == 'question':
                for i, btn in enumerate(answer_buttons):
                    if btn.clicked(event):
                        selected_answer = btn.text
                        correct_answer = current_question.get('a', '')
                        if selected_answer == correct_answer:
                            answer_feedback = "Верно!\nМина обезврежена."
                        else:
                            answer_feedback = "Неверно!\nМина взорвалась."
                            player.lose_health()
                        mines_hit += 1
                        if "Верно" in answer_feedback:
                            mines_defused += 1
                        show_answer_feedback = True
                        answer_feedback_timer = pygame.time.get_ticks()
                        pos = path[player.idx]
                        if pos in mine_states:
                            if "Верно" in answer_feedback:
                                mine_states[pos] = 'defused'
                            else:
                                mine_states[pos] = 'exploded'
                        active_mines.discard(pos)
                        break
        
        if dice and dice.rolling:
            res = dice.update()
            if res is not None and state == 'game':
                player.move(res, path)
                if player.idx >= len(path) - 1:
                    state = 'victory'
                elif path[player.idx] in active_mines:
                    templates = question_templates.get(topic, {}).get(diff, {}).get('templates', [])
                    if templates:
                        available_templates = [t for i, t in enumerate(templates) if i not in used_questions]
                        if not available_templates:
                            used_questions = set()
                            available_templates = templates
                        template = random.choice(available_templates)
                        template_index = templates.index(template)
                        used_questions.add(template_index)
                        current_question = generate_question_from_template(template)
                        options = current_question.get('options', [])
                        answer_buttons = []
                        for i, opt in enumerate(options):
                            btn = Button(0, 0, 450, 50, opt, color=BLUE)
                            answer_buttons.append(btn)
                        state = 'question'
                    else:
                        active_mines.discard(path[player.idx])
        
        if show_answer_feedback:
            if pygame.time.get_ticks() - answer_feedback_timer >= 1500:
                show_answer_feedback = False
                if player.lives <= 0:
                    state = 'game_over'
                elif player.idx >= len(path)-1 and not active_mines:
                    state = 'victory'
                else:
                    state = 'game'

        screen.fill(WHITE)
        
        if state == 'menu':
            draw_centered_text(screen, "Тропа Знаний", FONT_TITLE, BLUE, 100)
            for b in btns['menu']:
                b.draw(screen)
            btn_info_icon.draw(screen)
            if show_info_menu:
                for btn in info_menu_buttons:
                    btn.draw(screen)
                
        elif state == 'settings':
            draw_centered_text(screen, "Настройка лабиринта", FONT_TITLE, BLUE, 80)
            
            topic_label = FONT_SMALL.render("Тема:", True, BLACK)
            screen.blit(topic_label, (265, 165))
            diff_label = FONT_SMALL.render("Сложность:", True, BLACK)
            screen.blit(diff_label, (503, 165))
            
            if topic_dropdown:
                topic_dropdown.option_rects = []
                topic_dropdown.draw(screen)
            if diff_dropdown:
                diff_dropdown.option_rects = []
                diff_dropdown.draw(screen)
            
            if settings_valid:
                btns['play'].color = GREEN
            else:
                btns['play'].color = GRAY
            btns['play'].draw(screen)
            
            btns['back'].draw(screen)
            
        elif state == 'loading':
            draw_centered_text(screen, "Генерация лабиринта...", FONT, BLACK, 300)
            
        elif state == 'game':
            for y, row in enumerate(maze):
                for x, cell in enumerate(row):
                    r = pygame.Rect(offset_x + x*CELL_SIZE, offset_y + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    if cell == 0:
                        col = GRAY
                    elif (x, y) == player.pos:
                        col = BLUE
                    elif (x, y) == path[0]:
                        col = GREEN
                    elif (x, y) == path[-1]:
                        col = RED
                    elif (x, y) in player.visited and (x, y) != player.pos:
                        col = LBLUE
                    else:
                        col = WHITE
                    pygame.draw.rect(screen, col, r)
                    pygame.draw.rect(screen, BLACK, r, 1)
                    if (x, y) in mine_states and (x, y) != player.pos:
                        draw_mine_indicator(screen, (x, y), mine_states[(x, y)], offset_x, offset_y, CELL_SIZE)
            
            player_x = offset_x + player.pos[0] * CELL_SIZE
            player_y = offset_y + player.pos[1] * CELL_SIZE
            player_rect = pygame.Rect(player_x + 5, player_y + 5, CELL_SIZE - 10, CELL_SIZE - 10)
            pygame.draw.rect(screen, BLUE, player_rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, player_rect, 2, border_radius=5)
            
            draw_ui_panel(screen, player, path, ui_x, offset_y, len(maze), dice, roll_button)
            draw_mine_stats(screen, mines_hit, mines_defused, ui_x + 20, offset_y + 200)
            
        elif state == 'about_author':
            draw_about_author_screen(screen, btns['back'], about_author_text)
        
        elif state == 'about_program':
            draw_about_program_screen(screen, btns['back'], about_program_text)
            
        elif state == 'question':
            for y, row in enumerate(maze):
                for x, cell in enumerate(row):
                    r = pygame.Rect(offset_x + x*CELL_SIZE, offset_y + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    if cell == 0:
                        col = GRAY
                    elif (x, y) == player.pos:
                        col = BLUE
                    elif (x, y) == path[0]:
                        col = GREEN
                    elif (x, y) == path[-1]:
                        col = RED
                    elif (x, y) in player.visited and (x, y) != player.pos:
                        col = LBLUE
                    else:
                        col = WHITE
                    pygame.draw.rect(screen, col, r)
                    pygame.draw.rect(screen, BLACK, r, 1)
                    if (x, y) in mine_states and (x, y) != player.pos:
                        draw_mine_indicator(screen, (x, y), mine_states[(x, y)], offset_x, offset_y, CELL_SIZE)
            draw_question_screen(screen, current_question, answer_buttons, feedback)
            
        elif state == 'game_over':
            if not window_reset or prev_state != 'game_over':
                screen = pygame.display.set_mode((900, 700))
                window_reset = True
                prev_state = 'game_over'
            draw_centered_text(screen, "Игра окончена!", FONT_TITLE, RED, 240)
            retry_btn = Button(350, 350, 200, 55, "Меню")
            retry_btn.draw(screen)
            if event.type == pygame.MOUSEBUTTONDOWN and retry_btn.clicked(event):
                state = 'menu'
                window_reset = False
                
        elif state == 'victory':
            if not window_reset or prev_state != 'victory':
                screen = pygame.display.set_mode((900, 700))
                window_reset = True
                prev_state = 'victory'
            draw_centered_text(screen, "Поздравляем! Победа!", FONT_TITLE, GREEN, 240)
            retry_btn = Button(350, 350, 200, 55, "Меню")
            retry_btn.draw(screen)
            if event.type == pygame.MOUSEBUTTONDOWN and retry_btn.clicked(event):
                state = 'menu'
                window_reset = False
    
        if show_answer_feedback:
            draw_answer_feedback_screen(screen, answer_feedback)
            
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()