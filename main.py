"""
Sokoban Game với BFS và A* Search Algorithms
CO3061 Nhập môn AI - Trường Đại học Bách Khoa TP.HCM
"""

import pygame
import sys
import time
import psutil
import os
from collections import deque
from memory_profiler import profile
import heapq
from copy import deepcopy

# Khởi tạo Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TILE_SIZE = 48
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class SokobanGame:
    def __init__(self):
        """Khởi tạo game Sokoban"""
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Sokoban - BFS vs A* Algorithm Visualization")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        
        # Load assets
        self.load_assets()
        
        # Game state
        self.current_level = 0
        self.levels = []
        self.original_level = None
        self.game_matrix = []
        self.player_pos = (0, 0)
        self.algorithm_running = False
        self.solution_path = []
        self.solution_index = 0
        
        # Auto-play solution variables
        self.auto_playing = False
        self.auto_play_speed = 500  # milliseconds between moves
        self.last_move_time = 0
        self.solution_matrix_history = []  # Lưu trữ lịch sử các state
        
        # Statistics
        self.bfs_stats = {"time": 0, "memory": 0, "nodes": 0, "solution_length": 0}
        self.astar_stats = {"time": 0, "memory": 0, "nodes": 0, "solution_length": 0}
        
        # Load levels from files
        self.load_levels_from_file("MicroCosmos.txt")
        self.load_levels_from_file("MiniCosmos.txt")
        
        if self.levels:
            self.load_level(0)
    
    def load_assets(self):
        """Load game assets (hình ảnh)"""
        try:
            # Đường dẫn đến thư mục assets
            assets_path = "assets"
            
            # Load player sprites
            self.worker = pygame.image.load(os.path.join(assets_path, "Player", "player_01.png"))
            self.worker_docked = pygame.image.load(os.path.join(assets_path, "Player", "player_03.png"))
            
            # Load environment sprites
            self.floor = pygame.image.load(os.path.join(assets_path, "Ground", "ground_01.png"))
            self.wall = pygame.image.load(os.path.join(assets_path, "Blocks", "block_01.png"))
            self.docker = pygame.image.load(os.path.join(assets_path, "Environment", "environment_01.png"))
            
            # Load box sprites
            self.box = pygame.image.load(os.path.join(assets_path, "Crates", "crate_01.png"))
            self.box_docked = pygame.image.load(os.path.join(assets_path, "Crates", "crate_05.png"))
            
            # Scale images to tile size
            self.worker = pygame.transform.scale(self.worker, (TILE_SIZE, TILE_SIZE))
            self.worker_docked = pygame.transform.scale(self.worker_docked, (TILE_SIZE, TILE_SIZE))
            self.floor = pygame.transform.scale(self.floor, (TILE_SIZE, TILE_SIZE))
            self.wall = pygame.transform.scale(self.wall, (TILE_SIZE, TILE_SIZE))
            self.docker = pygame.transform.scale(self.docker, (TILE_SIZE, TILE_SIZE))
            self.box = pygame.transform.scale(self.box, (TILE_SIZE, TILE_SIZE))
            self.box_docked = pygame.transform.scale(self.box_docked, (TILE_SIZE, TILE_SIZE))
            
        except pygame.error as e:
            print(f"Không thể load assets: {e}")
            # Tạo các hình vuông màu thay thế
            self.create_placeholder_assets()
    
    def create_placeholder_assets(self):
        """Tạo các hình ảnh thay thế nếu không load được assets"""
        self.floor = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.floor.fill(WHITE)
        
        self.wall = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.wall.fill(BLACK)
        
        self.worker = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.worker.fill(RED)
        
        self.worker_docked = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.worker_docked.fill((255, 100, 100))
        
        self.docker = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.docker.fill(GREEN)
        
        self.box = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.box.fill(BLUE)
        
        self.box_docked = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.box_docked.fill((0, 100, 255))
    
    def load_levels_from_file(self, filename):
        """Đọc levels từ file"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                levels_text = content.split('Level ')
                
                for level_text in levels_text[1:]:  # Bỏ qua phần đầu trống
                    lines = level_text.strip().split('\n')
                    if len(lines) > 1:
                        level_matrix = []
                        for line in lines[1:]:  # Bỏ qua dòng số level
                            if line.strip():  # Chỉ thêm dòng không rỗng
                                level_matrix.append(list(line))
                        
                        if level_matrix:  # Chỉ thêm level không rỗng
                            self.levels.append(level_matrix)
                            
        except FileNotFoundError:
            print(f"Không tìm thấy file: {filename}")
        except Exception as e:
            print(f"Lỗi khi đọc file {filename}: {e}")
    
    def load_level(self, level_index):
        """Load một level cụ thể"""
        if 0 <= level_index < len(self.levels):
            self.current_level = level_index
            self.game_matrix = deepcopy(self.levels[level_index])
            self.original_level = deepcopy(self.levels[level_index])
            self.find_player_position()
            self.solution_path = []
            self.solution_index = 0
    
    def find_player_position(self):
        """Tìm vị trí người chơi trong level"""
        for y, row in enumerate(self.game_matrix):
            for x, cell in enumerate(row):
                if cell in ['@', '+']:  # @ = player on floor, + = player on dock
                    self.player_pos = (x, y)
                    return
    
    def print_game(self, matrix):
        """Hiển thị game theo matrix được truyền vào"""
        self.screen.fill(GRAY)
        x = 0
        y = 0
        
        for row in matrix:
            for char in row:
                if char == ' ':  # floor
                    self.screen.blit(self.floor, (x, y))
                elif char == '#':  # wall
                    self.screen.blit(self.wall, (x, y))
                elif char == '@':  # worker on floor
                    self.screen.blit(self.floor, (x, y))
                    self.screen.blit(self.worker, (x, y))
                elif char == '.':  # dock
                    self.screen.blit(self.docker, (x, y))
                elif char == '*':  # box on dock
                    self.screen.blit(self.box_docked, (x, y))
                elif char == '$':  # box
                    self.screen.blit(self.floor, (x, y))
                    self.screen.blit(self.box, (x, y))
                elif char == '+':  # worker on dock
                    self.screen.blit(self.docker, (x, y))
                    self.screen.blit(self.worker_docked, (x, y))
                x += TILE_SIZE
            x = 0
            y += TILE_SIZE
    
    def is_level_completed(self, matrix):
        """Kiểm tra xem level đã hoàn thành chưa"""
        for row in matrix:
            for cell in row:
                if cell == '$':  # Còn box chưa đặt vào dock
                    return False
        return True
    
    def get_valid_moves(self, matrix, player_pos):
        """Lấy danh sách các nước đi hợp lệ từ vị trí hiện tại"""
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # left, right, up, down
        px, py = player_pos
        
        for dx, dy in directions:
            new_x, new_y = px + dx, py + dy
            
            # Kiểm tra biên
            if 0 <= new_y < len(matrix) and 0 <= new_x < len(matrix[new_y]):
                target_cell = matrix[new_y][new_x]
                
                # Nếu ô đích là tường thì không thể di chuyển
                if target_cell == '#':
                    continue
                
                # Nếu ô đích là box
                if target_cell in ['$', '*']:
                    # Kiểm tra ô phía sau box
                    box_new_x, box_new_y = new_x + dx, new_y + dy
                    if (0 <= box_new_y < len(matrix) and 
                        0 <= box_new_x < len(matrix[box_new_y])):
                        behind_box = matrix[box_new_y][box_new_x]
                        # Box chỉ có thể đẩy nếu ô phía sau trống hoặc là dock
                        if behind_box in [' ', '.']:
                            moves.append((dx, dy))
                else:
                    # Di chuyển bình thường (không có box)
                    moves.append((dx, dy))
        
        return moves
    
    def apply_move(self, matrix, player_pos, move):
        """Áp dụng một nước đi và trả về matrix mới cùng vị trí player mới"""
        new_matrix = deepcopy(matrix)
        px, py = player_pos
        dx, dy = move
        new_x, new_y = px + dx, py + dy
        
        target_cell = new_matrix[new_y][new_x]
        
        # Xử lý vị trí cũ của player
        if new_matrix[py][px] == '@':
            new_matrix[py][px] = ' '
        elif new_matrix[py][px] == '+':
            new_matrix[py][px] = '.'
        
        # Nếu đẩy box
        if target_cell in ['$', '*']:
            box_new_x, box_new_y = new_x + dx, new_y + dy
            behind_box = new_matrix[box_new_y][box_new_x]
            
            # Di chuyển box
            if behind_box == ' ':
                new_matrix[box_new_y][box_new_x] = '$'
            elif behind_box == '.':
                new_matrix[box_new_y][box_new_x] = '*'
            
            # Đặt player vào vị trí box cũ
            if target_cell == '$':
                new_matrix[new_y][new_x] = '@'
            elif target_cell == '*':
                new_matrix[new_y][new_x] = '+'
        else:
            # Di chuyển bình thường
            if target_cell == ' ':
                new_matrix[new_y][new_x] = '@'
            elif target_cell == '.':
                new_matrix[new_y][new_x] = '+'
        
        return new_matrix, (new_x, new_y)
    
    def matrix_to_string(self, matrix):
        """Chuyển matrix thành string để hash"""
        return ''.join(''.join(row) for row in matrix)
    
    # -------------------------
    # Helper: tách bản đồ tĩnh (1 lần / level)
    # -------------------------
    def extract_static_maps(self, matrix):
        """
        Trả về:
        - walls: set of (x,y)
        - docks: set of (x,y)
        - floors: set of (x,y)
        """
        walls = set()
        docks = set()
        floors = set()
        for y, row in enumerate(matrix):
            for x, c in enumerate(row):
                if c == '#':
                    walls.add((x, y))
                else:
                    floors.add((x, y))
                if c in ['.', '+', '*']:
                    docks.add((x, y))
        return walls, docks, floors
    
    # =======================
    # DEADLOCK DETECTION
    # =======================

    # -------------------------
    # Deadlock detection với memoization (theo boxes set)
    # -------------------------
    def is_deadlock(self, matrix):
        """
        Quick deadlock detection using boxes positions as key.
        Memo hóa các kết quả để tránh tính nhiều lần.
        """
        boxes = self.get_boxes(matrix)
        key = frozenset(boxes)
        if not hasattr(self, "_deadlock_memo"):
            self._deadlock_memo = {}
        if key in self._deadlock_memo:
            return self._deadlock_memo[key]
        for b in boxes:
            if self.is_corner_deadlock(matrix, b):
                self._deadlock_memo[key] = True
                return True
        self._deadlock_memo[key] = False
        return False
    
    def get_boxes(self, matrix):
        boxes = []
        for y, row in enumerate(matrix):
            for x, cell in enumerate(row):
                if cell == '$':  # box not on dock
                    boxes.append((x, y))
        return boxes
    
    def get_docks(self, matrix):
        """Lấy danh sách vị trí của tất cả các dock"""
        docks = []
        for y, row in enumerate(matrix):
            for x, cell in enumerate(row):
                if cell in ['.', '+', '*']:  # Dock (trống, có player, có box)
                    docks.append((x, y))
        return docks
    
    def is_box_deadlock(self, matrix, box_pos):
        """Kiểm tra một box cụ thể có bị deadlock không"""
        x, y = box_pos
        
        # 1. Corner Deadlock - Box bị kẹt ở góc
        if self.is_corner_deadlock(matrix, box_pos):
            return True
        
        
        
        return False
    
    def is_deadlock_matrix(self, boxes, docks, walls):
        """
        Kiểm tra deadlock đơn giản: box kẹt góc mà không ở trên dock.
        """
        for (bx, by) in boxes:
            if (bx, by) in docks:
                continue  # Box đã đúng vị trí
            # 4 trường hợp kẹt góc
            if ((bx-1, by) in walls and (bx, by-1) in walls) or \
            ((bx+1, by) in walls and (bx, by-1) in walls) or \
            ((bx-1, by) in walls and (bx, by+1) in walls) or \
            ((bx+1, by) in walls and (bx, by+1) in walls):
                return True
        return False

    # -------------------------
    # Safe corner deadlock check (không OOB)
    # -------------------------
    def is_corner_deadlock(self, matrix, box_pos):
        """
        Kiểm tra corner deadlock an toàn (không truy cập ngoài chỉ số).
        Nếu box ở dock thì không coi là deadlock.
        """
        x, y = box_pos
        # Nếu box đã ở dock thì không deadlock
        if matrix[y][x] == '*':
            return False

        max_y = len(matrix) - 1
        max_x = max(len(row) for row in matrix) - 1

        def is_wall(nx, ny):
            # treat out-of-range as wall (outer boundary)
            if ny < 0 or ny > max_y:
                return True
            if nx < 0 or nx > (len(matrix[ny]) - 1):
                return True
            return matrix[ny][nx] == '#'

        # top-left
        if is_wall(x-1, y) and is_wall(x, y-1):
            return True
        # top-right
        if is_wall(x+1, y) and is_wall(x, y-1):
            return True
        # bottom-left
        if is_wall(x-1, y) and is_wall(x, y+1):
            return True
        # bottom-right
        if is_wall(x+1, y) and is_wall(x, y+1):
            return True

        return False

    
    def detect_all_deadlocks(self, matrix):
        """
        Phát hiện tất cả các deadlock trong trạng thái hiện tại
        Trả về danh sách các deadlock được tìm thấy
        """
        deadlocks = []
        boxes = self.get_boxes(matrix)
        
        for box_pos in boxes:
            x, y = box_pos
            
            if self.is_corner_deadlock(matrix, box_pos):
                deadlocks.append(f"Corner deadlock at ({x}, {y})")
            
            
        
        return deadlocks
    
    # =======================
    # AUTO-PLAY SOLUTION
    # =======================
    def start_auto_play(self, solution_path):
        """Bắt đầu auto-play solution"""
        if not solution_path:
            print("❌ No solution to play!")
            return
            
        print(f"🎬 Starting auto-play with {len(solution_path)} moves...")
        
        # Lưu solution trước khi reset level (vì load_level sẽ clear solution_path)
        temp_solution = solution_path.copy()
        
        # Reset về trạng thái ban đầu
        self.load_level(self.current_level)
        
        # Gán lại solution sau khi reset
        self.solution_path = temp_solution
        self.solution_index = 0
        self.auto_playing = True
        self.last_move_time = pygame.time.get_ticks()
        
        # Tạo lịch sử các state để có thể step backward
        self.generate_solution_history()
        
        print(f"✅ Auto-play initialized:")
        print(f"   • Solution length: {len(self.solution_path)}")
        print(f"   • Auto-playing: {self.auto_playing}")
        print(f"   • Speed: {self.auto_play_speed}ms per move")
        print(f"   • History states: {len(self.solution_matrix_history)}")
        print("▶️ Auto-play will start in 1 second...")
    
    def generate_solution_history(self):
        """Tạo lịch sử tất cả states trong solution"""
        self.solution_matrix_history = []
        current_matrix = deepcopy(self.original_level)
        
        # Tìm player position trong original level
        current_player_pos = None
        for y, row in enumerate(current_matrix):
            for x, cell in enumerate(row):
                if cell in ['@', '+']:  # @ = player on floor, + = player on dock
                    current_player_pos = (x, y)
                    break
            if current_player_pos:
                break
        
        if not current_player_pos:
            print("❌ Cannot find player position in original level!")
            return
        
        # Lưu state ban đầu
        self.solution_matrix_history.append((deepcopy(current_matrix), current_player_pos))
        
        # Apply từng move và lưu state
        for move in self.solution_path:
            current_matrix, current_player_pos = self.apply_move(current_matrix, current_player_pos, move)
            self.solution_matrix_history.append((deepcopy(current_matrix), current_player_pos))
    
    def update_auto_play(self):
        """Update auto-play logic"""
        if not self.auto_playing or not self.solution_path:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Kiểm tra nếu đã đến lúc move tiếp theo
        if current_time - self.last_move_time >= self.auto_play_speed:
            if self.solution_index < len(self.solution_path):
                self.step_solution_forward()
                self.last_move_time = current_time
            else:
                # Kết thúc auto-play
                self.auto_playing = False
                print("🎉 Auto-play completed!")
    
    def step_solution_forward(self):
        """Thực hiện một bước tiếp theo trong solution"""
        if self.solution_index < len(self.solution_path):
            # Apply move from solution
            move = self.solution_path[self.solution_index]
            
            # Print current matrix state
            print(f"\n🎮 Current matrix state (Step {self.solution_index + 1}/{len(self.solution_path)}):")
            for row in self.game_matrix:
                print(''.join(row))
            
            # Debug info
            print(f"📍 Executing step {self.solution_index + 1}/{len(self.solution_path)}: {move}")
            print(f"   Current pos: {self.player_pos}")
            
            # Apply the move
            self.game_matrix, self.player_pos = self.apply_move(self.game_matrix, self.player_pos, move)
            self.solution_index += 1
            
            print(f"   New pos: {self.player_pos}")
            
            # Kiểm tra nếu hoàn thành
            if self.solution_index >= len(self.solution_path):
                self.auto_playing = False
                if self.is_level_completed(self.game_matrix):
                    print("🎉 Solution completed! Level solved!")
                else:
                    print("⚠️ Solution finished but level not completed")
        else:
            print("⚠️ No more moves in solution!")
            self.auto_playing = False
    
    def step_solution_backward(self):
        """Lùi lại một bước trong solution"""
        if self.solution_index > 0:
            self.solution_index -= 1
            # Restore state từ history
            if self.solution_index < len(self.solution_matrix_history):
                self.game_matrix, self.player_pos = deepcopy(self.solution_matrix_history[self.solution_index])
                print(f"📍 Step {self.solution_index}/{len(self.solution_path)} (backward)")
    
    def toggle_auto_play(self):
        """Toggle auto-play on/off"""
        if self.solution_path:
            self.auto_playing = not self.auto_playing
            if self.auto_playing:
                self.last_move_time = pygame.time.get_ticks()
                print(f"▶️ Auto-play resumed (speed: {self.auto_play_speed}ms)")
            else:
                print("⏸️ Auto-play paused")
        else:
            print("❌ No solution to play!")
    
    def adjust_speed(self, faster=True):
        """Điều chỉnh tốc độ auto-play"""
        if faster:
            self.auto_play_speed = max(100, self.auto_play_speed - 100)  # Tối thiểu 100ms
            print(f"⚡ Speed increased: {self.auto_play_speed}ms per move")
        else:
            self.auto_play_speed = min(2000, self.auto_play_speed + 100)  # Tối đa 2000ms
            print(f"🐌 Speed decreased: {self.auto_play_speed}ms per move")
    
    # -------------------------
    # Apply move trên state nhẹ (player_pos, boxes_set) — nhanh, không deepcopy whole matrix
    # -------------------------
    def apply_move_state(self, player_pos, boxes_set, move, walls):
        """
        Áp dụng một bước di chuyển trong A*.
        Trả về (player_pos_mới, boxes_set_mới) hoặc (None, None) nếu move không hợp lệ.
        """
        px, py = player_pos
        dx, dy = move
        nx, ny = px + dx, py + dy

        # Nếu đi vào tường thì không hợp lệ
        if (nx, ny) in walls:
            return None, None

        boxes = set(boxes_set)

        # Nếu ô kế tiếp có box
        if (nx, ny) in boxes:
            bx, by = nx + dx, ny + dy
            # Nếu box bị chặn (bởi tường hoặc box khác)
            if (bx, by) in walls or (bx, by) in boxes:
                return None, None

            # Di chuyển box
            boxes.remove((nx, ny))
            if (bx, by) in boxes:  # Ngăn trường hợp 2 box nhập làm 1
                return None, None
            boxes.add((bx, by))
            return (nx, ny), frozenset(boxes)

        # Nếu ô trống — player chỉ di chuyển
        return (nx, ny), frozenset(boxes)

    # =======================
    # BFS ALGORITHM TEMPLATE
    # =======================
    def solve_bfs(self):
        """
        BFS Algorithm - Not implemented in this version
        Focus on A* algorithm implementation
        """
        print("🔍 BFS Algorithm")
        print("❌ BFS is not implemented in this version")
        print("🌟 Please use A* algorithm (Press '2') for solving")
        print("💡 A* provides optimal solutions with heuristic guidance")
        
        # Reset stats
        self.bfs_stats = {
            "time": 0,
            "memory": 0,
            "nodes": 0,
            "solution_length": 0
        }
        
        return None
    
    # =======================
    # A* ALGORITHM TEMPLATE
    # =======================
    
    # -------------------------
    # Heuristic: tổng min manhattan của mỗi box tới dock gần nhất (admissible)
    # -------------------------
    def heuristic(self, boxes_frozen, docks):
        if not docks or not boxes_frozen:
            return 0
        docks_list = list(docks)
        total = 0
        for bx, by in boxes_frozen:
            md = min(abs(bx - dx) + abs(by - dy) for dx, dy in docks_list)
            total += md
        return total
    
    # -------------------------
    # Optimized A* (state = (player_pos, frozenset(boxes)))
    # -------------------------
    def solve_astar(self):
        """
        A* Solver cải tiến cho Sokoban
        - Ngăn 2 box nhập làm 1
        - Deadlock pruning
        - Giảm bộ nhớ và thời gian
        """
        print("🌟 Running A* Solver (improved)...")
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / (1024 * 1024)

        # Parse map
        walls, docks, boxes = set(), set(), set()
        player = None
        for y, row in enumerate(self.game_matrix):
            for x, cell in enumerate(row):
                pos = (x, y)
                if cell == '#':
                    walls.add(pos)
                elif cell == '.':
                    docks.add(pos)
                elif cell == '$':
                    boxes.add(pos)
                elif cell == '*':
                    boxes.add(pos)
                    docks.add(pos)
                elif cell in ['@', '+']:
                    player = pos
                    if cell == '+':
                        docks.add(pos)

        if player is None:
            print("❌ Player not found!")
            return None

        # Trạng thái khởi tạo
        start_state = (player, frozenset(boxes))
        frontier = []
        heapq.heappush(frontier, (self.heuristic(frozenset(boxes), docks), 0, start_state, []))

        visited = set()
        nodes_explored = 0

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while frontier:
            f, g, (player_pos, boxes_frozen), path = heapq.heappop(frontier)

            if (player_pos, boxes_frozen) in visited:
                continue
            visited.add((player_pos, boxes_frozen))
            nodes_explored += 1

            # Goal state
            if all(b in docks for b in boxes_frozen):
                end_time = time.time()
                end_memory = process.memory_info().rss / (1024 * 1024)
                self.astar_stats = {
                    "time": end_time - start_time,
                    "memory": end_memory - start_memory,
                    "nodes": nodes_explored,
                    "solution_length": len(path)
                }
                print(f"🎯 Solution found! Length = {len(path)}, Nodes = {nodes_explored}")
                return path

            # Mở rộng successor
            for dx, dy in directions:
                new_player, new_boxes = self.apply_move_state(player_pos, boxes_frozen, (dx, dy), walls)
                if new_player is None:
                    continue

                # Prune deadlock
                if self.is_deadlock_matrix(new_boxes, docks, walls):
                    continue

                new_state = (new_player, new_boxes)
                if new_state in visited:
                    continue

                new_g = g + 1
                h = self.heuristic(new_boxes, docks)
                heapq.heappush(frontier, (new_g + h, new_g, new_state, path + [(dx, dy)]))

        # Không tìm được lời giải
        print("❌ No solution found.")
        end_time = time.time()
        end_memory = process.memory_info().rss / (1024 * 1024)
        self.astar_stats = {
            "time": end_time - start_time,
            "memory": end_memory - start_memory,
            "nodes": nodes_explored,
            "solution_length": 0
        }
        return None

    
    def display_statistics(self):
        """Hiển thị thống kê A* Algorithm với Deadlock Detection"""
        y_offset = 10
        stats_surface = pygame.Surface((380, 280))
        stats_surface.fill(WHITE)
        stats_surface.set_alpha(230)
        
        # Tiêu đề
        title = self.font.render("A* ALGORITHM STATS", True, BLACK)
        stats_surface.blit(title, (10, y_offset))
        y_offset += 30
        
        # A* Stats với highlighting
        astar_title = self.font.render("A* Solver with Deadlock Detection:", True, (220, 0, 0))
        stats_surface.blit(astar_title, (10, y_offset))
        y_offset += 25
        
        # Performance metrics
        astar_time = self.font.render(f"Execution Time: {self.astar_stats['time']:.3f}s", True, BLACK)
        stats_surface.blit(astar_time, (15, y_offset))
        y_offset += 20
        
        astar_memory = self.font.render(f"Memory Usage: {self.astar_stats['memory']:.2f}MB", True, BLACK)
        stats_surface.blit(astar_memory, (15, y_offset))
        y_offset += 20
        
        astar_nodes = self.font.render(f"Nodes Explored: {self.astar_stats['nodes']}", True, BLACK)
        stats_surface.blit(astar_nodes, (15, y_offset))
        y_offset += 20
        
        astar_length = self.font.render(f"Solution Length: {self.astar_stats['solution_length']}", True, BLACK)
        stats_surface.blit(astar_length, (15, y_offset))
        y_offset += 25
        
        # Deadlock info
        deadlocks = self.detect_all_deadlocks(self.game_matrix)
        deadlock_count = len(deadlocks)
        deadlock_color = (255, 0, 0) if deadlock_count > 0 else (0, 150, 0)
        deadlock_text = self.font.render(f"Deadlocks: {deadlock_count}", True, deadlock_color)
        stats_surface.blit(deadlock_text, (15, y_offset))
        y_offset += 20
        
        # Status
        if self.astar_stats['solution_length'] > 0:
            status_text = self.font.render("Solution Found!", True, (0, 150, 0))
        elif self.astar_stats['nodes'] > 0:
            status_text = self.font.render("No Solution", True, (200, 0, 0))
        else:
            status_text = self.font.render("Ready to solve", True, (0, 0, 200))
        
        stats_surface.blit(status_text, (15, y_offset))
        
        self.screen.blit(stats_surface, (WINDOW_WIDTH - 390, 10))
    
    def display_ui_info(self):
        """Hiển thị thông tin điều khiển và level"""
        if not self.solution_path:
            # Normal game controls
            info_texts = [
                f"Level: {self.current_level + 1}/{len(self.levels)}",
                "Controls:",
                "Arrow Keys: Move",
                "R: Reset Level",
                "N: Next Level", 
                "P: Previous Level",
                "1: BFS (Not implemented)",
                "2: Run A* Solver ⭐",
                "D: Check Deadlocks",
                "ESC: Quit"
            ]
        else:
            # Solution mode controls
            auto_status = "Playing" if self.auto_playing else "Paused"
            info_texts = [
                f"Level: {self.current_level + 1}/{len(self.levels)}",
                f"Solution: {self.solution_index}/{len(self.solution_path)} {auto_status}",
                "",
                "Solution Controls:",
                "SPACE: Play/Pause auto-play",
                "Z/X: Step backward/forward",
                "+/-: Speed control",
                f"Speed: {self.auto_play_speed}ms/move",
                "",
                "R: Reset Level",
                "D: Check Deadlocks",
                "ESC: Quit"
            ]
        
        y_offset = WINDOW_HEIGHT - 240
        for text in info_texts:
            # Highlight A* option
            color = (255, 255, 0) if "A* Solver" in text else WHITE  # Yellow for A*
            color = (128, 128, 128) if "Not implemented" in text else color  # Gray for not implemented
            
            text_surface = self.font.render(text, True, color)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 20
    
    def display_deadlock_info(self):
        """Hiển thị thông tin deadlock nếu có"""
        deadlocks = self.detect_all_deadlocks(self.game_matrix)
        
        if deadlocks:
            # Tạo surface cho deadlock warning
            warning_surface = pygame.Surface((450, min(180, 35 + len(deadlocks) * 25)))
            warning_surface.fill((255, 200, 200))  # Light red background
            warning_surface.set_alpha(230)
            
            # Tiêu đề warning
            warning_title = self.font.render("⚠️ DEADLOCK DETECTED!", True, (150, 0, 0))
            warning_surface.blit(warning_title, (10, 5))
            
            # Liệt kê các deadlock
            y_offset = 30
            for deadlock in deadlocks[:5]:  # Chỉ hiển thị tối đa 5 deadlock
                deadlock_text = self.font.render(f"• {deadlock}", True, (100, 0, 0))
                warning_surface.blit(deadlock_text, (15, y_offset))
                y_offset += 25
            
            # Hiển thị ở góc trên bên trái
            self.screen.blit(warning_surface, (10, 10))
    
    def handle_input(self, event):
        """Xử lý input từ người dùng"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            
            elif event.key == pygame.K_r:
                # Reset level
                self.load_level(self.current_level)
            
            elif event.key == pygame.K_n:
                # Next level
                if self.current_level < len(self.levels) - 1:
                    self.load_level(self.current_level + 1)
            
            elif event.key == pygame.K_p:
                # Previous level
                if self.current_level > 0:
                    self.load_level(self.current_level - 1)
            
            elif event.key == pygame.K_1:
                # Run BFS
                solution = self.solve_bfs()
                if solution:
                    self.solution_path = solution
                    self.solution_index = 0
            
            elif event.key == pygame.K_2:
                # Run A*
                solution = self.solve_astar()
                if solution:
                    self.start_auto_play(solution)
            
            elif event.key == pygame.K_d:
                # Check deadlocks
                deadlocks = self.detect_all_deadlocks(self.game_matrix)
                if deadlocks:
                    print("🚫 DEADLOCK DETECTED:")
                    for deadlock in deadlocks:
                        print(f"  • {deadlock}")
                    print(f"Total deadlocks found: {len(deadlocks)}")
                else:
                    print("✅ No deadlocks detected in current state")
                    
                # Check if current state is completely deadlocked
                if self.is_deadlock(self.game_matrix):
                    print("💀 This state is UNSOLVABLE!")
                else:
                    print("🎯 State is still solvable")
            
            # Auto-play controls
            elif event.key == pygame.K_SPACE:
                # Toggle auto-play
                self.toggle_auto_play()
            
            elif event.key == pygame.K_z:
                # Step backward in solution (Z key)
                if self.solution_path:
                    self.auto_playing = False  # Pause auto-play
                    self.step_solution_backward()
            
            elif event.key == pygame.K_x:
                # Step forward in solution (X key)
                if self.solution_path:
                    self.auto_playing = False  # Pause auto-play
                    self.step_solution_forward()
            
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                # Increase speed
                self.adjust_speed(faster=True)
            
            elif event.key == pygame.K_MINUS:
                # Decrease speed
                self.adjust_speed(faster=False)
            
            # Movement keys (for manual play) - only if not auto-playing
            elif not self.auto_playing:
                if event.key == pygame.K_UP:
                    self.try_move((0, -1))
                elif event.key == pygame.K_DOWN:
                    self.try_move((0, 1))
                elif event.key == pygame.K_LEFT:
                    self.try_move((-1, 0))
                elif event.key == pygame.K_RIGHT:
                    self.try_move((1, 0))
        
        return True
    
    def try_move(self, direction):
        """Thử thực hiện một nước đi thủ công"""
        valid_moves = self.get_valid_moves(self.game_matrix, self.player_pos)
        if direction in valid_moves:
            self.game_matrix, self.player_pos = self.apply_move(
                self.game_matrix, self.player_pos, direction
            )
            
            if self.is_level_completed(self.game_matrix):
                print("🎉 Level completed!")
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    running = self.handle_input(event)
            
            # Update auto-play if running
            self.update_auto_play()
            
            # Clear screen
            self.screen.fill(GRAY)
            
            # Draw game
            self.print_game(self.game_matrix)
            
            # Draw UI
            self.display_ui_info()
            self.display_statistics()
            self.display_deadlock_info()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


def main():
    """Entry point của chương trình"""
    print("Sokoban solver with Breadth First Search and A* Algorithms")
    print("=" * 60)
    print("CO3061 Introduction to AI - Ho Chi Minh City University of Technology")
    print("=" * 60)
    
    try:
        game = SokobanGame()
        game.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()