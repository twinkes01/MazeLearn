import pygame, random, sys, json
from maze_generation import generate_unicursal_maze

pygame.init()
FPS, CELL_SIZE, UI_W = 60, 40, 250
WHITE, BLACK, GRAY, GREEN, RED, BLUE, YELLOW, LBLUE = (255,255,255), (0,0,0), (100,100,100), (0,255,0), (255,0,0), (0,0,255), (255,255,0), (100,150,255)
ORANGE = (255, 140, 0)

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
    def __init__(self, x, y, w, h, text, color=LBLUE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text, self.color = text, color
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        text_surf = FONT_BUTTON.render(self.text, True, WHITE)
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

def generate_question_from_template(template):
    a_range = template.get('a_range', [1, 10])
    b_range = template.get('b_range', [1, 10])
    a = random.randint(a_range[0], a_range[1]) if a_range[1] > 0 else 0
    b = random.randint(b_range[0], b_range[1]) if b_range[1] > 0 else 0
    try:
        answer = eval(template.get('answer', '0'))
        correct = str(answer)
    except:
        correct = template.get('answer', '0')
        if isinstance(correct, int):
            correct = str(correct)
    question = template.get('q', '?').format(a=a, b=b)
    if 'options' in template:
        options = template['options'].copy()
        if correct not in options:
            options[0] = correct
        random.shuffle(options)
    else:
        options = generate_options(correct, template.get('type', 'number'))
    return {'q': question, 'options': options, 'a': correct}

def generate_options(correct, q_type='number'):
    try:
        if q_type == 'binary':
            options = {correct}
            while len(options) < 4:
                wrong = list(correct)
                if len(wrong) > 1:
                    idx = random.randint(0, len(wrong)-1)
                    wrong[idx] = '1' if wrong[idx] == '0' else '0'
                wrong = ''.join(wrong)
                if wrong != correct and (len(wrong) == 1 or wrong[0] != '0'):
                    options.add(wrong)
            return list(options)
        else:
            correct_num = int(correct)
            options = {correct}
            while len(options) < 4:
                offset = random.randint(-5, 5)
                wrong = correct_num + offset
                if wrong != correct_num and wrong > 0:
                    options.add(str(wrong))
            return list(options)
    except:
        return [correct, "Вариант1", "Вариант2", "Вариант3"]

def draw_question_screen(screen, question_data, answer_buttons, feedback=None):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    box_w, box_h = 550, 400
    box_x = (screen.get_width() - box_w) // 2
    box_y = (screen.get_height() - box_h) // 2
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), border_radius=15)
    pygame.draw.rect(screen, BLUE, (box_x, box_y, box_w, box_h), 4, border_radius=15)
    title = FONT.render("Вопрос!", True, RED)
    screen.blit(title, (box_x + 20, box_y + 20))
    q_text = FONT.render(question_data.get('q', '?'), True, BLACK)
    screen.blit(q_text, (box_x + 20, box_y + 70))
    for btn in answer_buttons:
        btn.draw(screen)
    if feedback:
        fb_text = FONT.render(feedback, True, GREEN if feedback == "Верно!" else RED)
        screen.blit(fb_text, (box_x + 160, box_y + 330))

def draw_centered_text(screen, text, font, color, y):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(text_surf, text_rect)

def draw_ui_panel(screen, player, path, ui_x, offset_y, maze_height, dice, roll_button):
    """Отрисовка UI панели справа от лабиринта"""
    # ✅ Сдвиг вправо на 15 пикселей
    ui_offset = ui_x + 23
    
    # Сердца на одной линии с верхом лабиринта
    draw_hearts(screen, player.lives, ui_offset, offset_y)
    
    # Прогресс - надпись
    progress_label = FONT.render("Прогресс:", True, BLACK)
    screen.blit(progress_label, (ui_offset, offset_y + 45))
    
    # Процент - по центру под надписью
    progress = int(player.idx / max(len(path)-1, 1) * 100)
    progress_text = FONT.render(f"{progress}%", True, BLACK)
    label_width = progress_label.get_width()
    percent_width = progress_text.get_width()
    center_offset = (label_width - percent_width) // 2
    screen.blit(progress_text, (ui_offset + center_offset, offset_y + 90))
    
    # ✅ Вычисляем низ лабиринта и позиционируем кубик с кнопкой
    maze_bottom_y = offset_y + maze_height * CELL_SIZE
    dice.rect.x = ui_offset + 26  # ✅ Кубик сдвинут вправо (было ui_x + 20)
    dice.rect.y = maze_bottom_y - 250
    roll_button.rect.x = ui_offset + 26  # ✅ Кнопка сдвинута вправо (было ui_x + 20)
    roll_button.rect.y = maze_bottom_y - 55
    
    # Рисуем
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
    roll_button = None
    ui_x, offset_x, offset_y = 0, 0, 0
    gen_params = {}
    current_question = None
    answer_buttons = []
    feedback = None
    feedback_timer = 0
    
    question_templates = load_question_templates()

    btns = {
        'menu': [Button(350, 250, 200, 55, "Начать"), Button(350, 350, 200, 55, "Выход")],
        'topic': [Button(250, 250, 220, 55, "Математика", GREEN), Button(470, 250, 220, 55, "Информатика", BLUE)],
        'diff': [Button(200, 250, 160, 55, "Легкая", GREEN), Button(375, 250, 160, 55, "Средняя", YELLOW), Button(550, 250, 160, 55, "Сложная", RED)],
        'back': Button(50, 500, 120, 55, "Назад", GRAY)
    }

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if state == 'menu':
                if btns['menu'][0].clicked(event):
                    state = 'topic'
                elif btns['menu'][1].clicked(event):
                    running = False
            elif state == 'topic':
                for i, b in enumerate(btns['topic']):
                    if b.clicked(event):
                        topic = 'math' if i==0 else 'info'
                        state = 'diff'
                if btns['back'].clicked(event):
                    state = 'menu'
            elif state == 'diff':
                for i, b in enumerate(btns['diff']):
                    if b.clicked(event):
                        diff = ['easy','medium','hard'][i]
                        size, mine_pct, ratio = [13, 17, 21][i], [0.4, 0.55, 0.7][i], [0.5, 0.5, 0.4][i]
                        gen_params = {'size': size, 'mine_pct': mine_pct, 'ratio': ratio}
                        state = 'loading'
                if btns['back'].clicked(event):
                    state = 'topic'
            elif state == 'loading':
                size = gen_params['size']
                w, h = size * CELL_SIZE + UI_W, max(size * CELL_SIZE + 100, 700)
                screen = pygame.display.set_mode((w, h))
                offset_x, offset_y = 10, 10
                ui_x = w - UI_W + 10
                maze, start, finish, path = generate_unicursal_maze(size, size, gen_params['ratio'])
                player = Player(start)
                
                # ✅ Точное выравнивание по нижней границе лабиринта
                maze_bottom_y = offset_y + size * CELL_SIZE
                dice = Dice(ui_x + 20, maze_bottom_y - 250)
                roll_button = Button(ui_x + 20, maze_bottom_y - 55, 140, 55, "Бросить", color=ORANGE)
                
                candidates = [p for p in path if p not in (start, finish)]
                active_mines = set(random.sample(candidates, min(int(len(path)*gen_params['mine_pct']), len(candidates))))
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
                            feedback = "Верно!"
                        else:
                            feedback = "Неверно!"
                            if player.lose_health():
                                state = 'game_over'
                                break
                        feedback_timer = pygame.time.get_ticks()
                        active_mines.discard(path[player.idx])
                        if player.idx >= len(path)-1 and not active_mines:
                            state = 'victory'
                        elif player.lives <= 0:
                            state = 'game_over'
                        else:
                            state = 'game'
                        break
        
        if dice and dice.rolling:
            res = dice.update()
            if res and state == 'game':
                player.move(res, path)
                if path[player.idx] in active_mines:
                    templates = question_templates.get(topic, {}).get(diff, {}).get('templates', [])
                    if templates:
                        template = random.choice(templates)
                        current_question = generate_question_from_template(template)
                        options = current_question.get('options', [])
                        answer_buttons = []
                        box_w, box_h = 550, 400
                        box_x = (screen.get_width() - box_w) // 2
                        box_y = (screen.get_height() - box_h) // 2
                        for i, opt in enumerate(options):
                            btn = Button(box_x + 50, box_y + 130 + i * 60, 450, 50, opt, color=BLUE)
                            answer_buttons.append(btn)
                        state = 'question'
                    else:
                        active_mines.discard(path[player.idx])
        
        if state == 'question' and feedback and pygame.time.get_ticks() - feedback_timer > 1000:
            if player.lives <= 0:
                state = 'game_over'
            elif player.idx >= len(path)-1 and not active_mines:
                state = 'victory'
            else:
                state = 'game'
            feedback = None

        screen.fill(WHITE)
        
        if state == 'menu':
            draw_centered_text(screen, "MazeLearn", FONT_TITLE, BLUE, 140)
            for b in btns['menu']:
                b.draw(screen)
        elif state == 'topic':
            draw_centered_text(screen, "Выберите тему:", FONT, BLACK, 140)
            for b in btns['topic']:
                b.draw(screen)
            btns['back'].draw(screen)
        elif state == 'diff':
            draw_centered_text(screen, "Выберите сложность:", FONT, BLACK, 140)
            for b in btns['diff']:
                b.draw(screen)
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
            draw_ui_panel(screen, player, path, ui_x, offset_y, len(maze), dice, roll_button)
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
            draw_question_screen(screen, current_question, answer_buttons, feedback)
        elif state == 'game_over':
            draw_centered_text(screen, "Игра окончена!", FONT_TITLE, RED, 240)
            retry_btn = Button(350, 350, 200, 55, "Заново", color=GREEN)
            retry_btn.draw(screen)
            if event.type == pygame.MOUSEBUTTONDOWN and retry_btn.clicked(event):
                state = 'menu'
        elif state == 'victory':
            draw_centered_text(screen, "Победа!", FONT_TITLE, GREEN, 240)
            retry_btn = Button(350, 350, 200, 55, "Заново", color=BLUE)
            retry_btn.draw(screen)
            if event.type == pygame.MOUSEBUTTONDOWN and retry_btn.clicked(event):
                state = 'menu'

        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()