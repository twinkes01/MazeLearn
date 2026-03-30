import random
from collections import deque
# Инициализация Pygame .venv\Scripts\activate        python main.py
def generate_unicursal_maze(width, height, min_path_ratio, max_attempts=100000):
    
    # Корректировка до нечетных размеров (для работы DFS)
    if width % 2 == 0:
        width += 1
    if height % 2 == 0:
        height += 1

    total_cells = width * height
    min_path_length = int(total_cells * min_path_ratio)

    # Список граничных клеток (периметр)
    border_cells = []
    # Верхняя и нижняя границы
    for x in range(width):
        border_cells.append((x, 0))
        border_cells.append((x, height-1))
    # Левая и правая границы (исключаем углы, чтобы не дублировать)
    for y in range(1, height-1):
        border_cells.append((0, y))
        border_cells.append((width-1, y))

    # Исключаем возможность совпадения точек старта и финиша в дальнейшем (избавляемся от дубликатов)
    border_cells = list(set(border_cells))

    for attempt in range(max_attempts):
        # 1. Генерируем идеальный лабиринт (DFS)
        maze = [[0 for _ in range(width)] for _ in range(height)]

        def get_unvisited_neighbors(x, y):
            neighbors = []
            for dx, dy in [(2,0), (-2,0), (0,2), (0,-2)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0:
                    neighbors.append((nx, ny))
            return neighbors

        def remove_wall(x1, y1, x2, y2):
            mx = (x1 + x2) // 2
            my = (y1 + y2) // 2
            maze[my][mx] = 1

        # Выбираем случайную стартовую клетку для генерации (внутреннюю)
        start_x = random.randrange(0, width, 2)
        start_y = random.randrange(0, height, 2)
        maze[start_y][start_x] = 1
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]
            neighbors = get_unvisited_neighbors(x, y)
            if neighbors:
                nx, ny = random.choice(neighbors)
                remove_wall(x, y, nx, ny)
                maze[ny][nx] = 1
                stack.append((nx, ny))
            else:
                stack.pop()

        # 2. Выбираем случайные старт и финиш из граничных клеток
        # При этом они должны быть разными
        start, finish = random.sample(border_cells, 2)

        # 3. Делаем стартовую и финишную клетки проходимыми
        maze[start[1]][start[0]] = 1
        maze[finish[1]][finish[0]] = 1

        # 4. Соединяем старт с основной сетью лабиринта (если он изолирован)
        # Используем BFS от старта, чтобы найти ближайшую проходимую клетку
        def connect_point(point):
            x0, y0 = point
            if maze[y0][x0] == 1:
                # Уже проходимо, но может быть не связано? Проверим связность позже.
                # Для надёжности всё равно попытаемся найти путь к существующему лабиринту
                pass
            visited = {point: None}
            queue = deque([point])
            found = None
            while queue:
                x, y = queue.popleft()
                if maze[y][x] == 1 and (x, y) != point:
                    found = (x, y)
                    break
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                        visited[(nx, ny)] = (x, y)
                        queue.append((nx, ny))
            if found is None:
                return False  # не удалось соединить
            # Прорубаем путь от point к found
            cx, cy = found
            while (cx, cy) != point:
                px, py = visited[(cx, cy)]
                # Если между клетками стена (расстояние 2), убираем её
                if abs(cx - px) == 2 or abs(cy - py) == 2:
                    mx = (cx + px) // 2
                    my = (cy + py) // 2
                    maze[my][mx] = 1
                cx, cy = px, py
            return True

        if not connect_point(start):
            continue
        if not connect_point(finish):
            continue

        # 5. Находим путь от старта до финиша (BFS)
        queue = deque([start])
        visited = {start: None}
        path_found = False
        while queue:
            x, y = queue.popleft()
            if (x, y) == finish:
                path_found = True
                break
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 1 and (nx, ny) not in visited:
                    visited[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        if not path_found:
            continue

        # Восстанавливаем путь
        path = []
        cell = finish
        while cell:
            path.append(cell)
            cell = visited[cell]
        path.reverse()

        # 6. Проверяем длину пути
        if len(path) < min_path_length:
            continue

        # 7. Создаём уникурсальный лабиринт, оставляя только клетки пути
        new_maze = [[0 for _ in range(width)] for _ in range(height)]
        for x, y in path:
            new_maze[y][x] = 1

        return new_maze, start, finish, path