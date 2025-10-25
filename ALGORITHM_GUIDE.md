# Hướng dẫn implement BFS và A* cho Sokoban

## Tổng quan
File `main.py` đã được khởi tạo với đầy đủ framework cần thiết. Bạn cần implement 2 thuật toán trong các hàm template đã được chuẩn bị sẵn.

## Cấu trúc dữ liệu chính

### Game State
- `matrix`: Ma trận 2D biểu diễn trạng thái game
- `player_pos`: Tuple (x, y) vị trí người chơi
- Các ký tự trong matrix:
  - `' '`: Sàn trống
  - `'#'`: Tường
  - `'@'`: Người chơi trên sàn
  - `'+'`: Người chơi trên dock
  - `'$'`: Hộp trên sàn
  - `'*'`: Hộp trên dock
  - `'.'`: Dock (vị trí đích)

### Các hàm utility đã có sẵn
- `get_valid_moves(matrix, player_pos)`: Trả về list các direction hợp lệ
- `apply_move(matrix, player_pos, move)`: Áp dụng nước đi, trả về (new_matrix, new_player_pos)
- `is_level_completed(matrix)`: Kiểm tra level hoàn thành
- `matrix_to_string(matrix)`: Chuyển matrix thành string để hash

## 1. Implement BFS (Breadth-First Search)

### Location: Hàm `solve_bfs()` tại dòng 517

### Pseudocode:
```python
def solve_bfs(self):
    # 1. Khởi tạo
    queue = deque([(initial_matrix, initial_player_pos, [])])
    visited = set()
    nodes_explored = 0
    
    # 2. BFS loop
    while queue:
        current_matrix, player_pos, path = queue.popleft()
        nodes_explored += 1
        
        # 3. Kiểm tra đích
        if self.is_level_completed(current_matrix):
            return path
        
        # 4. Tránh trạng thái đã thăm
        state_key = self.matrix_to_string(current_matrix) + str(player_pos)
        if state_key in visited:
            continue
        visited.add(state_key)
        
        # 5. Expand các trạng thái kế tiếp
        valid_moves = self.get_valid_moves(current_matrix, player_pos)
        for move in valid_moves:
            new_matrix, new_player_pos = self.apply_move(current_matrix, player_pos, move)
            new_path = path + [move]
            queue.append((new_matrix, new_player_pos, new_path))
    
    return None  # Không tìm thấy solution
```

### Những điều cần lưu ý:
- Sử dụng `deque` từ `collections` cho queue
- State representation: `(matrix_string, player_pos)` để tránh lặp vô hạn
- Path chứa danh sách các moves để đến trạng thái hiện tại
- Deadlock detection để tối ưu performance
- Performance tracking: thời gian, memory, nodes explored
- Cập nhật `self.bfs_stats` để hiển thị UI
- Return `solution_path` khi tìm thấy hoặc `None` nếu không có solution

## 2. Implement A* Algorithm

### Location: Hàm `solve_astar()` tại dòng 622

### Trước tiên, implement heuristic function:
```python
def heuristic(self, matrix, player_pos):
    """
    Hàm heuristic cho A* - Manhattan distance từ các box đến dock gần nhất
    """
    total_distance = 0
    boxes = []
    docks = []
    
    # Tìm tất cả boxes và docks
    for y, row in enumerate(matrix):
        for x, cell in enumerate(row):
            if cell == '$':  # Box chưa đặt đúng chỗ
                boxes.append((x, y))
            elif cell in ['.', '+', '*']:  # Dock hoặc có đối tượng trên dock
                docks.append((x, y))
    
    # Tính Manhattan distance từ mỗi box đến dock gần nhất
    for box in boxes:
        if docks:  # Nếu có dock
            min_dist = float('inf')
            for dock in docks:
                dist = abs(box[0] - dock[0]) + abs(box[1] - dock[1])
                min_dist = min(min_dist, dist)
            total_distance += min_dist
    
    return total_distance
```

### Pseudocode cho A*:
```python
def solve_astar(self):
    # 1. Khởi tạo và đo performance
    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / (1024 * 1024)  # MB
    
    initial_state = (self.matrix_to_string(self.game_matrix), self.player_pos)
    visited = set()  # Set of visited vertices
    open_list = []  # Priority queue (heap)
    
    # Dictionary để lưu trữ g_score và predecessor
    g_scores = {initial_state: 0}
    predecessors = {initial_state: None}
    
    # Tính f_score cho trạng thái đầu
    h_score = self.heuristic(self.game_matrix, self.player_pos)
    f_score = 0 + h_score
    
    # Push start node vào open_list
    heapq.heappush(open_list, (f_score, 0, self.game_matrix, self.player_pos, []))
    nodes_explored = 0
    
    # 2. A* loop
    while open_list:
        current_f, current_g, current_matrix, current_player_pos, current_path = heapq.heappop(open_list)
        current_state = (self.matrix_to_string(current_matrix), current_player_pos)
        
        # Skip nếu đã visited
        if current_state in visited:
            continue
            
        visited.add(current_state)
        nodes_explored += 1
        
        # 3. Kiểm tra goal state
        if self.is_level_completed(current_matrix):
            # Tính toán thống kê và return solution
            end_time = time.time()
            end_memory = process.memory_info().rss / (1024 * 1024)
            
            self.astar_stats = {
                "time": end_time - start_time,
                "memory": end_memory - start_memory,
                "nodes": nodes_explored,
                "solution_length": len(current_path)
            }
            return current_path
        
        # 4. Skip deadlock states (early pruning)
        if self.is_deadlock(current_matrix):
            continue
        
        # 5. Expand successors
        valid_moves = self.get_valid_moves(current_matrix, current_player_pos)
        for move in valid_moves:
            succ_matrix, succ_player_pos = self.apply_move(current_matrix, current_player_pos, move)
            succ_state = (self.matrix_to_string(succ_matrix), succ_player_pos)
            succ_path = current_path + [move]
            
            if succ_state in visited:
                continue
                
            # Skip deadlock successor states
            if self.is_deadlock(succ_matrix):
                continue
            
            # Tính scores
            new_g_score = current_g + 1
            h_score = self.heuristic(succ_matrix, succ_player_pos)
            f_score = new_g_score + h_score
            
            # Update nếu tìm được đường tốt hơn
            if succ_state in g_scores:
                if new_g_score < g_scores[succ_state]:
                    g_scores[succ_state] = new_g_score
                    predecessors[succ_state] = current_state
                    heapq.heappush(open_list, (f_score, new_g_score, succ_matrix, succ_player_pos, succ_path))
            else:
                g_scores[succ_state] = new_g_score
                predecessors[succ_state] = current_state
                heapq.heappush(open_list, (f_score, new_g_score, succ_matrix, succ_player_pos, succ_path))
    
    return None  # Không tìm thấy solution
```

### Những điều cần lưu ý cho A*:
- Sử dụng `heapq` cho priority queue
- f_score = g_score + h_score
- g_score là cost thực tế từ start
- h_score là heuristic estimate đến goal
- State representation: `(matrix_string, player_pos)`
- Deadlock detection để early pruning
- Performance tracking: thời gian, memory, nodes explored
- Cập nhật stats vào `self.astar_stats` để hiển thị UI
- Return `current_path` (list of moves) khi tìm thấy solution

## 3. Testing và Debug

### Cách test:
1. Chạy game: `python main.py`
2. Nhấn `1` để test BFS
3. Nhấn `2` để test A*
4. So sánh kết quả thống kê

### Debug tips:
- In ra số nodes explored
- Kiểm tra visited states có hoạt động đúng không
- Test với level đơn giản trước
- Đảm bảo heuristic admissible (không overestimate)

## 4. Tối ưu hóa

### Cải thiện hiệu suất:
- Sử dụng set thay vì list cho visited
- Cache kết quả heuristic nếu có thể
- Implement deadlock detection (box bị kẹt góc)
- Sử dụng better heuristics (Hungarian algorithm cho assignment)

### Memory optimization:
- Chỉ lưu trữ essential state information
- Use generators thay vì lists khi có thể
- Clear unused references

## 5. Visualization (Optional)

Nếu muốn visualize quá trình giải:
- Thêm biến để track intermediate steps
- Hiển thị solution path step by step
- Add animation cho solution playback