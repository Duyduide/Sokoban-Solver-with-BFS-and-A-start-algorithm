# Sokoban Game với BFS và A* Algorithms

## Mô tả dự án
Dự án này hiện thực game Sokoban sử dụng PyGame và minh họa việc giải bài toán bằng hai thuật toán:
- Breadth-First Search (BFS)
- A* Search Algorithm

## Yêu cầu hệ thống
- Python 3.7+
- Windows/Linux/MacOS

## Cài đặt

### 1. Tạo môi trường ảo
```bash
python -m venv sokoban-venv
```

### 2. Kích hoạt môi trường ảo
**Windows:**
```bash
sokoban-venv\Scripts\activate
```

**Linux/MacOS:**
```bash
source sokoban-venv/bin/activate
```

### 3. Cài đặt các package cần thiết
```bash
pip install pygame
pip install psutil
pip install memory-profiler
```

## Chạy chương trình
```bash
python main.py
```

## Cấu trúc dự án
- `main.py`: File chính chứa toàn bộ source code
- `MicroCosmos.txt`: File chứa các level test nhỏ
- `MiniCosmos.txt`: File chứa các level test lớn hơn
- `assets/`: Thư mục chứa hình ảnh cho game
- `README.md`: File hướng dẫn này

## Điều khiển game
- Arrow Keys hoặc WASD: Di chuyển nhân vật
- R: Reset level hiện tại
- ESC: Thoát game
- 1: Chạy thuật toán BFS
- 2: Chạy thuật toán A*

## Game State
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