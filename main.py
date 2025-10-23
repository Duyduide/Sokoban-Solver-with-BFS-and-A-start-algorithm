"""
Sokoban Game với BFS và A* Search Algorithms
CO3061 Nhập môn AI - Trường Đại học Bách Khoa TP.HCM
"""
from openpyxl import Workbook, load_workbook


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
        self.auto_play = False
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
        new_matrix = [row[:] for row in matrix]
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
    
    # =======================
    # DEADLOCK DETECTION
    # =======================
    def is_deadlock(self, matrix):
        """
        Kiểm tra xem trạng thái hiện tại có bị deadlock không
        Returns True nếu bị deadlock (không thể giải được)
        """
        boxes = self.get_boxes(matrix)
        
        for box_pos in boxes:
            if self.is_box_deadlock(matrix, box_pos):
                return True
        
        return False
    
    def get_boxes(self, matrix):
        """Lấy danh sách vị trí của tất cả các box chưa vào dock"""
        boxes = []
        for y, row in enumerate(matrix):
            for x, cell in enumerate(row):
                if cell == '$':  # Box chưa vào dock
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
        
        # Corner Deadlock - Box bị kẹt ở góc
        if self.is_corner_deadlock(matrix, box_pos):
            return True
        
        # Có thể thêm các loại deadlock khác ở đây (ví dụ: wall deadlock, room deadlock, ...)
        
        return False
    
    def is_corner_deadlock(self, matrix, box_pos):
        """
        Kiểm tra Corner Deadlock
        Box bị kẹt ở góc tường và không phải là dock
        """
        x, y = box_pos
        
        # Nếu box đã ở dock thì không phải deadlock
        if matrix[y][x] == '*':
            return False
        
        # Kiểm tra 4 góc có thể
        corners = [
            # Top-left corner
            (matrix[y-1][x] == '#' and matrix[y][x-1] == '#'),
            # Top-right corner  
            (matrix[y-1][x] == '#' and matrix[y][x+1] == '#'),
            # Bottom-left corner
            (matrix[y+1][x] == '#' and matrix[y][x-1] == '#'),
            # Bottom-right corner
            (matrix[y+1][x] == '#' and matrix[y][x+1] == '#')
        ]
        
        return any(corners)

    
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
    # BFS ALGORITHM TEMPLATE
    # =======================
    def solve_bfs(self):
        """
        Template cho thuật toán Breadth-First Search
        TODO: Hiện thực giải thuật BFS
        """
        # phần chuẩn bị thông số để đo thời gian và bộ nhớ 
        print("🔍 Start Solver using BFS...")
        start_time = time.time() # thời điểm bắt đầu
        #lấy thông tin tiến trình hiện tại  
        process = psutil.Process(os.getpid()) 
        #chuyển đổi sang MB
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # TODO: Implement BFS logic here
        # Hint: Sử dụng queue (deque) để lưu trữ các trạng thái giống hồi học DSA á =))))
        # Cần track: current_matrix, player_position, path_to_reach_this_state

        # Placeholder implementation
        nodes_explored = 0
        solution_found = False
        solution_path = []

        visited = set()
        queue = deque()
        player_pos = self.player_pos #lấy thông tin vị trí người chơi hiện tại
        matrix = deepcopy(self.game_matrix) #bản đồ hiện tại
        matrix_key = self.matrix_to_string(matrix) # biến ma trận thành chuỗi 
        queue.append((matrix, player_pos, []))
        visited.add((matrix_key, player_pos))

        while queue:
            nodes_explored += 1 # tăng bộ đếm
            current_matrix, current_player_pos, path = queue.popleft() # lấy phần tử đầu tiên của queue
            if self.is_level_completed(current_matrix): # nếu level đã hoàn thành thì break
                solution_found = True
                solution_path = path
                break
            #kiểm tra deadlock
            deadlock = self.detect_all_deadlocks(current_matrix)
            if not deadlock:                
                # danh sách các hướng đi khả thi của player
                valid_move = self.get_valid_moves(current_matrix, current_player_pos) 
                #lặp qua từng hướng để thử mở rộng
                for direction in valid_move:
                    #Áp dụng bước đi
                    new_current_matrix, new_current_player_pos = self.apply_move(current_matrix, current_player_pos, direction)
                    new_matrix_key = self.matrix_to_string(new_current_matrix)
                    # tránh lặp trạng thái đã visited nếu chưa có thì thêm vào visited
                    if (new_matrix_key, new_current_player_pos) not in visited:
                        visited.add((new_matrix_key, new_current_player_pos))
                        new_path = path + [direction]
                        queue.append((new_current_matrix, new_current_player_pos, new_path))
                    
        # Tính toán thống kê
        # ghi lại thời gian kết thúc và bộ nhớ chiếm dụng (MB)
        end_time = time.time() 
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        self.bfs_stats = {
            "time": end_time - start_time,
            "memory": end_memory - start_memory,
            "nodes": nodes_explored,
            "solution_length": len(solution_path)
        }
        # phần ghi lại thông số về thời gian, bộ nhớ sử dụng, độ dài các bước,...
        print(f"✅ BFS Completed in {self.bfs_stats['time']:.3f}s")
        print(f"📊 Nodes explored: {self.bfs_stats['nodes']}")
        print(f"💾 Memory used: {self.bfs_stats['memory']:.4f} MB")
        print(f"📏 Solution length: {self.bfs_stats['solution_length']}")
        if solution_found:
            print("🧭 Solution Path:")
            for step in solution_path:
                print(step)
        else:
            print("❌ No solution found.")


        return solution_path if solution_found else None
    
    # =======================
    # A* ALGORITHM TEMPLATE
    # =======================
    def heuristic(self, matrix, player_pos):
        """
        Hàm heuristic cho A*
        TODO: Implement heuristic function
        """
        # Placeholder heuristic
        return 0
    
    def solve_astar(self):
        """
        Template cho thuật toán A*
        TODO: Implement A* algorithm here
        """
        print("🌟 Start Solver using A*...")
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # TODO: Implement A* logic here
        # Hint: Sử dụng heapq để implement priority queue
        # Cần track: f_score, g_score, current_matrix, player_position, path
        
        # Placeholder implementation
        nodes_explored = 0
        solution_found = False
        solution_path = []
        
        # Tính toán thống kê
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        self.astar_stats = {
            "time": end_time - start_time,
            "memory": end_memory - start_memory,
            "nodes": nodes_explored,
            "solution_length": len(solution_path)
        }
        
        print(f"✅ A* completed in {self.astar_stats['time']:.3f}s")
        print(f"📊 Nodes explored: {self.astar_stats['nodes']}")
        print(f"💾 Memory used: {self.astar_stats['memory']:.2f} MB")
        print(f"📏 Solution length: {self.astar_stats['solution_length']}")
        
        return solution_path if solution_found else None
    
    def display_statistics(self):
        """Hiển thị thống kê so sánh giữa BFS và A*"""
        y_offset = 10
        stats_surface = pygame.Surface((350, 350))
        stats_surface.fill(WHITE)
        stats_surface.set_alpha(230)
        
        # Tiêu đề
        title = self.font.render("ALGORITHM COMPARISON", True, BLACK)
        stats_surface.blit(title, (10, y_offset))
        y_offset += 30
        
        # BFS Stats
        bfs_title = self.font.render("BFS:", True, BLUE)
        stats_surface.blit(bfs_title, (10, y_offset))
        y_offset += 20
        
        bfs_time = self.font.render(f"Time: {self.bfs_stats['time']:.3f}s", True, BLACK)
        stats_surface.blit(bfs_time, (20, y_offset))
        y_offset += 15
        
        bfs_memory = self.font.render(f"Memory: {self.bfs_stats['memory']:.4f}MB", True, BLACK)
        stats_surface.blit(bfs_memory, (20, y_offset))
        y_offset += 15
        
        bfs_nodes = self.font.render(f"Nodes: {self.bfs_stats['nodes']}", True, BLACK)
        stats_surface.blit(bfs_nodes, (20, y_offset))
        y_offset += 15
        
        bfs_length = self.font.render(f"Solution: {self.bfs_stats['solution_length']}", True, BLACK)
        stats_surface.blit(bfs_length, (20, y_offset))
        y_offset += 25
        
        # A* Stats
        astar_title = self.font.render("A*:", True, RED)
        stats_surface.blit(astar_title, (10, y_offset))
        y_offset += 20
        
        astar_time = self.font.render(f"Time: {self.astar_stats['time']:.3f}s", True, BLACK)
        stats_surface.blit(astar_time, (20, y_offset))
        y_offset += 15
        
        astar_memory = self.font.render(f"Memory: {self.astar_stats['memory']:.2f}MB", True, BLACK)
        stats_surface.blit(astar_memory, (20, y_offset))
        y_offset += 15
        
        astar_nodes = self.font.render(f"Nodes: {self.astar_stats['nodes']}", True, BLACK)
        stats_surface.blit(astar_nodes, (20, y_offset))
        y_offset += 15
        
        astar_length = self.font.render(f"Solution: {self.astar_stats['solution_length']}", True, BLACK)
        stats_surface.blit(astar_length, (20, y_offset))
        
        self.screen.blit(stats_surface, (WINDOW_WIDTH - 360, 10))
    
    def display_ui_info(self):
        """Hiển thị thông tin điều khiển và level"""
        info_texts = [
            f"Level: {self.current_level + 1}/{len(self.levels)}",
            "Controls:",
            "Arrow Keys/WASD: Move",
            "R: Reset Level",
            "N: Next Level",
            "P: Previous Level",
            "1: Run BFS",
            "2: Run A*",
            "D: Check Deadlocks",
            "ESC: Quit"
        ]
        
        y_offset = WINDOW_HEIGHT - 240
        for text in info_texts:
            text_surface = self.font.render(text, True, WHITE)
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
                    self.auto_play = True
                    
            elif event.key == pygame.K_2:
                # Run A*
                solution = self.solve_astar()
                if solution:
                    self.solution_path = solution
                    self.solution_index = 0
            
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
            
            # Movement keys (for manual play)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self.try_move((0, -1))
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.try_move((0, 1))
            elif event.key in [pygame.K_LEFT, pygame.K_a]:
                self.try_move((-1, 0))
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
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
            if self.auto_play and self.solution_index < len(self.solution_path):
                direction = self.solution_path[self.solution_index]
                self.game_matrix, self.player_pos = self.apply_move(
                self.game_matrix, self.player_pos, direction
             )
                self.solution_index += 1
                time.sleep(0.2)
            elif self.solution_index >= len(self.solution_path):
                self.auto_play = False
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