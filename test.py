from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout,
    QLabel, QLineEdit, QMessageBox, QDialog, QHBoxLayout

)
from PyQt6.QtCore import QTimer, QTime
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
import sqlite3
from datetime import datetime
from datetime import timedelta

WHITE = 1
BLACK = 2
flag_highlight_moves = False


# Удобная функция для вычисления цвета противника
def opponent(color):
    if color == WHITE:
        return BLACK
    else:
        return WHITE


def correct_coords(row, col):
    '''Функция проверяет, что координаты (row, col) лежат
    внутри доски'''
    return 0 <= row < 8 and 0 <= col < 8


class Board:
    def __init__(self):
        self.color = WHITE
        self.field = []
        self.castling7w = True
        self.castling0w = True
        self.castling7b = True
        self.castling0b = True

        for row in range(8):
            self.field.append([None] * 8)
        self.field[0] = [
            Rook(WHITE), Knight(WHITE), Bishop(WHITE), Queen(WHITE),
            King(WHITE), Bishop(WHITE), Knight(WHITE), Rook(WHITE)
        ]
        self.field[1] = [
            Pawn(WHITE), Pawn(WHITE), Pawn(WHITE), Pawn(WHITE),
            Pawn(WHITE), Pawn(WHITE), Pawn(WHITE), Pawn(WHITE)
        ]
        self.field[6] = [
            Pawn(BLACK), Pawn(BLACK), Pawn(BLACK), Pawn(BLACK),
            Pawn(BLACK), Pawn(BLACK), Pawn(BLACK), Pawn(BLACK)
        ]
        self.field[7] = [
            Rook(BLACK), Knight(BLACK), Bishop(BLACK), Queen(BLACK),
            King(BLACK), Bishop(BLACK), Knight(BLACK), Rook(BLACK)

        ]

    def castling0(self):
        if (self.color == WHITE and self.castling0w and isinstance(self.field[0][4], King) and isinstance(
                self.field[0][0], Rook) and self.field[0][1] is None and self.field[0][2] is None and self.field[0][3]
                is None):
            self.field[0][0] = None
            self.field[0][4] = None
            self.field[0][2] = King(self.color)
            self.field[0][3] = Rook(self.color)
            self.castling0w = False
            self.color = opponent(self.color)
            return True
        elif (self.color == BLACK and self.castling0b and isinstance(self.field[7][4], King) and isinstance(
                self.field[7][0], Rook) and self.field[7][1] is None and self.field[7][2] is None and self.field[7][3]
              is None):
            self.field[7][0] = None
            self.field[7][4] = None
            self.field[7][2] = King(self.color)
            self.field[7][3] = Rook(self.color)
            self.castling0b = False
            self.color = opponent(self.color)
            return True
        return False

    def castling7(self):
        if (self.color == WHITE and self.castling7w and isinstance(self.field[0][4], King) and isinstance(
                self.field[0][7], Rook) and self.field[0][6] is None and self.field[0][5] is None):
            self.field[0][7] = None
            self.field[0][4] = None
            self.field[0][6] = King(self.color)
            self.field[0][5] = Rook(self.color)
            self.castling7w = False
            self.color = opponent(self.color)
            return True

        elif (self.color == BLACK and self.castling7b and isinstance(self.field[7][4], King) and isinstance(
                self.field[7][7], Rook) and self.field[7][6] is None and self.field[7][5] is None):
            self.field[7][7] = None
            self.field[7][4] = None
            self.field[7][6] = King(self.color)
            self.field[7][5] = Rook(self.color)
            self.castling7b = False
            self.color = opponent(self.color)
            return True
        return False

    def move_and_promote_pawn(self, row, col, row1, col1, char):
        if (isinstance(self.field[row][col], Pawn) and Pawn.can_move(self, self, row, col, row1, col1) or
                Pawn.can_attack(self, self, row, col, row1, col1)):
            color = self.field[row][col].get_color()
            self.field[row][col] = None
            if char == "Q":
                self.field[row1][col1] = Queen(color)
            if char == "R":
                self.field[row1][col1] = Rook(color)
            if char == "N":
                self.field[row1][col1] = Knight(color)
            if char == "B":
                self.field[row1][col1] = Bishop(color)
            self.color = opponent(self.color)
            return True
        return False

    def current_player_color(self):
        return self.color

    def cell(self, row, col):
        '''Возвращает строку из двух символов. Если в клетке (row, col)
        находится фигура, символы цвета и фигуры. Если клетка пуста,
        то два пробела.'''
        piece = self.field[row][col]
        if piece is None:
            return '  '
        color = piece.get_color()
        c = 'w' if color == WHITE else 'b'
        return c + piece.char()

    def get_piece(self, row, col):
        if correct_coords(row, col):
            return self.field[row][col]
        else:
            return None

    def move_piece(self, row, col, row1, col1):
        '''Переместить фигуру из точки (row, col) в точку (row1, col1).
        Если перемещение возможно, метод выполнит его и вернёт True.
        Если нет --- вернёт False'''

        if not correct_coords(row, col) or not correct_coords(row1, col1):
            return False
        if row == row1 and col == col1:
            return False  # нельзя пойти в ту же клетку
        piece = self.field[row][col]
        if piece is None:
            return False
        if self.field[row][col].get_color() != self.color:
            return False
        if self.field[row1][col1] is None:
            if not piece.can_move(self, row, col, row1, col1):
                return False
        elif self.field[row1][col1].get_color() == opponent(piece.get_color()):
            if not piece.can_attack(self, row, col, row1, col1):
                return False
        else:
            return False
        self.field[row][col] = None  # Снять фигуру.
        self.field[row1][col1] = piece  # Поставить на новое место.
        self.color = opponent(self.color)
        return True

    def is_check(self, color):
        """Проверяет, находится ли король данного цвета под шахом."""
        # Найдем короля на доске
        king_position = None
        for row in range(8):
            for col in range(8):
                piece = self.field[row][col]
                if isinstance(piece, King) and piece.get_color() == color:
                    king_position = (row, col)
                    break
            if king_position:
                break

        if not king_position:
            return False  # Король уже съеден, шах невозможен

        # Проверим, может ли какая-либо фигура противника атаковать короля
        opponent_color = opponent(color)
        king_row, king_col = king_position
        for row in range(8):
            for col in range(8):
                piece = self.field[row][col]
                if piece and piece.get_color() == opponent_color:
                    if piece.can_attack(self, row, col, king_row, king_col):
                        return True
        return False

    def is_mate(self, color):
        """Проверяет, есть ли мат у игрока данного цвета."""
        if not self.is_check(color):
            return False  # Мат возможен только в случае шаха

        # Проверить, может ли текущий игрок сделать ход, устраняющий шах
        for row in range(8):
            for col in range(8):
                piece = self.field[row][col]
                if piece and piece.get_color() == color:
                    for target_row in range(8):
                        for target_col in range(8):
                            # Сохранить текущее состояние доски
                            original_piece = self.field[target_row][target_col]
                            if self.move_piece(row, col, target_row, target_col):
                                # Проверить, ушел ли король из-под шаха
                                if not self.is_check(color):
                                    # Вернуть доску в исходное состояние
                                    self.field[row][col] = piece
                                    self.field[target_row][target_col] = original_piece
                                    self.color = opponent(self.color)  # Откат хода
                                    return False
                                # Вернуть доску в исходное состояние
                                self.field[row][col] = piece
                                self.field[target_row][target_col] = original_piece
                                self.color = opponent(self.color)  # Откат хода
        return True


class Rook:

    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color

    def char(self):
        return 'R'

    def can_move(self, board, row, col, row1, col1):
        # Невозможно сделать ход в клетку, которая не лежит в том же ряду
        # или столбце клеток.

        if row != row1 and col != col1 or (row == row1 and col == col1):
            return False

        step = 1 if (row1 >= row) else -1
        for r in range(row + step, row1, step):
            # Если на пути по горизонтали есть фигура
            if not (board.get_piece(r, col) is None):
                return False

        step = 1 if (col1 >= col) else -1
        for c in range(col + step, col1, step):
            # Если на пути по вертикали есть фигура
            if not (board.get_piece(row, c) is None):
                return False

        if board.field[row][col].get_color() == WHITE:
            if col == 0:
                board.castling0w = False
            elif col == 7:
                board.castling7w = False
        else:
            if col == 0:
                board.castling0b = False
            elif col == 7:
                board.castling7b = False
        return True

    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)


class Pawn:

    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color

    def char(self):
        return "P"

    def can_move(self, board, row, col, row1, col1):
        # Пешка может ходить только по вертикали
        # "взятие на проходе" не реализовано
        # Пешка может сделать из начального положения ход на 2 клетки
        # вперёд, поэтому поместим индекс начального ряда в start_row.
        if board.field[row][col].get_color() == WHITE:
            direction = 1
            start_row = 1
        else:
            direction = -1
            start_row = 6
        # ход на 1 клетку
        if row + direction == row1 and col == col1 and board.field[row1][col1] is None:
            return True

        # ход на 2 клетки из начального положения
        if (row == start_row and col == col1
                and row + 2 * direction == row1
                and board.field[row + direction][col] is None):
            return True
        return False

    def can_attack(self, board, row, col, row1, col1):
        direction = 1 if (self.color == WHITE) else -1
        return (row + direction == row1
                and (col + 1 == col1 or col - 1 == col1))


class Knight:
    '''Класс коня. Пока что заглушка, которая может ходить в любую клетку.'''

    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color

    def char(self):
        return 'N'  # kNight, буква 'K' уже занята королём

    def can_move(self, board, row, col, row1, col1):
        if ((abs(row - row1) == 2 and abs(col - col1) == 1) or (abs(row - row1) == 1 and abs(col - col1) == 2) and
                (board.field[row1][col1] is None or board.field[row1][col1].get_color() != self.color)):
            return True
        return False

    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)


class King:
    '''Класс короля. Пока что заглушка, которая может ходить в любую клетку.'''

    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color

    def char(self):
        return 'K'

    def can_move(self, board, row, col, row1, col1):
        if correct_coords(row, col) and correct_coords(row1, col1) and (
                abs(row - row1) <= 1 and abs(col - col1) <= 1) and (
                board.field[row1][col1] is None or board.field[row1][col1].get_color() != self.color):
            if self.color == WHITE:
                board.castling0w, board.castling7w = False, False
            else:
                board.castling7b, board.castling0b = False, False
            return True
        return False

    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)


class Queen:
    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color

    def char(self):
        return 'Q'

    def can_move(self, board, row, col, row1, col1):
        if not correct_coords(row1, col1):
            return False
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if row == row1 or col == col1:
            step = 1 if (row1 >= row) else -1
            for r in range(row + step, row1, step):
                if not (board.get_piece(r, col) is None):
                    return False
            step = 1 if (col1 >= col) else -1
            for c in range(col + step, col1, step):
                if not (board.get_piece(row, c) is None):
                    return False
            return True
        if row - col == row1 - col1:
            step = 1 if (row1 >= row) else -1
            for r in range(row + step, row1, step):
                c = col - row + r
                if not (board.get_piece(r, c) is None):
                    return False
            return True
        if row + col == row1 + col1:
            step = 1 if (row1 >= row) else -1
            for r in range(row + step, row1, step):
                c = row + col - r
                if not (board.get_piece(r, c) is None):
                    return False
            return True
        return False

    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)


class Bishop:
    '''Класс слона. Пока что заглушка, которая может ходить в любую клетку.'''

    def __init__(self, color):
        self.color = color

    def get_color(self):
        return self.color

    def char(self):
        return 'B'

    def can_move(self, board, row, col, row1, col1):
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if row - col == row1 - col1:
            step = 1 if (row1 >= row) else -1
            for r in range(row + step, row1, step):
                c = col - row + r
                if not (board.get_piece(r, c) is None):
                    return False
            return True
        if row + col == row1 + col1:
            step = 1 if (row1 >= row) else -1
            for r in range(row + step, row1, step):
                c = row + col - r
                if not (board.get_piece(r, c) is None):
                    return False
            return True
        return False

    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)
    

class ChessGUI(QWidget):
    global flag_highlight_moves

    def __init__(self, player1, player2):
        super().__init__()
        self.player1 = player1
        self.player2 = player2
        self.board = Board()
        self.selected_piece = None  # Хранит выбранную клетку (row, col)
        self.is_flipped = False  # Отслеживает переворот доски
        self.init_ui()
        self.flag_highlight_moves = flag_highlight_moves
        self.timer_label = QLabel("Время: 00:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 16))
        self.layout.addWidget(self.timer_label)

        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_timer)
        self.game_timer.start(1000)  # Обновление каждую секунду
        self.start_time = datetime.now()
        self.elapsed_time = QTime(0, 0, 0)

    def update_timer(self):
        self.elapsed_time = self.elapsed_time.addSecs(1)
        self.timer_label.setText(f"Время: {self.elapsed_time.toString('hh:mm:ss')}")

    def init_ui(self):
        self.setWindowTitle(f"Шахматы: {self.player1} против {self.player2}")
        self.setGeometry(100, 100, 600, 700)
        self.layout = QVBoxLayout()

        self.status_label = QLabel("Ход белых")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16))
        self.layout.addWidget(self.status_label)

        self.grid_layout = QGridLayout()
        self.buttons = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                button = QPushButton(self.board.cell(7 - row, col))
                button.setFont(QFont("Courier", 14))
                button.setFixedSize(60, 60)
                button.setStyleSheet(self.get_cell_color(row, col))
                button.clicked.connect(self.make_move(row, col))
                self.buttons[row][col] = button
                self.grid_layout.addWidget(button, row, col)

        self.layout.addLayout(self.grid_layout)
        self.setLayout(self.layout)
        self.castling_layout = QHBoxLayout()

        self.castling_0w_button = QPushButton("Рокировка 0-0-0 для белых")
        self.castling_0w_button.setFont(QFont("Arial", 8))
        self.castling_0w_button.clicked.connect(self.castling_0w)
        self.castling_layout.addWidget(self.castling_0w_button)

        self.castling_7w_button = QPushButton("Рокировка 0-0 для белых")
        self.castling_7w_button.setFont(QFont("Arial", 8))
        self.castling_7w_button.clicked.connect(self.castling_7w)
        self.castling_layout.addWidget(self.castling_7w_button)

        self.castling_0b_button = QPushButton("Рокировка 0-0-0 для черных")
        self.castling_0b_button.setFont(QFont("Arial", 8))
        self.castling_0b_button.clicked.connect(self.castling_0b)
        self.castling_layout.addWidget(self.castling_0b_button)

        self.castling_7b_button = QPushButton("Рокировка 0-0 для черных")
        self.castling_7b_button.setFont(QFont("Arial", 8))
        self.castling_7b_button.clicked.connect(self.castling_7b)
        self.castling_layout.addWidget(self.castling_7b_button)

        self.layout.addLayout(self.castling_layout)

        self.layout.addLayout(self.castling_layout)
        self.setLayout(self.layout)

    def castling_0w(self):
        """Выполняет длинную рокировку (0-0-0)."""
        if self.board.color == 1 and self.board.castling0():
            self.castling_0w_button.hide()
            self.castling_7w_button.hide()
            self.update_board()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный ход")

    def castling_0b(self):
        if self.board.color == 2 and self.board.castling0():
            self.castling_0b_button.hide()
            self.castling_7b_button.hide()
            self.update_board()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный ход")

    def castling_7w(self):
        """Выполняет короткую рокировку (0-0)."""

        if self.board.color == 1 and self.board.castling7():
            self.castling_7w_button.hide()
            self.castling_0w_button.hide()
            self.update_board()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный ход")

    def castling_7b(self):
        if self.board.color == 2 and self.board.castling7():
            self.castling_7b_button.hide()
            self.castling_0b_button.hide()
            self.update_board()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный ход")

    def get_cell_color(self, row, col):
        """Возвращает цвет клетки шахматной доски."""
        if (row + col) % 2 == 0:
            return "background-color: rgb(255, 229, 204);"
        else:
            return "background-color: rgb(200, 100, 0);"

    def make_move(self, row, col):
        def handler():
            actual_row, actual_col = self.get_actual_coordinates(row, col)
            if self.selected_piece is None:
                # Выбор клетки с фигурой
                if self.board.cell(actual_row, actual_col) != " ":
                    self.selected_piece = (row, col)
                    self.buttons[row][col].setStyleSheet("background-color: rgb(120, 220, 220);")
                    if flag_highlight_moves:
                        self.highlight_moves(actual_row, actual_col)
                else:
                    QMessageBox.warning(self, "Ошибка", "Выберите клетку с фигурой")
            else:

                start_row, start_col = self.get_actual_coordinates(*self.selected_piece)
                current_piece = self.board.field[start_row][start_col]
                if (current_piece is not None and current_piece.char() == "P") and (
                        (current_piece.get_color() == 1 and actual_row == 7) or (
                        current_piece.get_color() == 2 and actual_row == 0)) and (
                        current_piece.can_move(self.board, start_row, start_col, actual_row, actual_col) or
                        current_piece.can_attack(self.board, start_row, start_col, actual_row, actual_col)):
                    dialog = PromotionDialog(self)
                    if dialog.exec():  # Если пользователь нажал на одну из кнопок
                        char = dialog.selected_piece
                        self.board.move_and_promote_pawn(start_row, start_col, actual_row, actual_col, char)
                    self.update_board()

                # Попытка сделать ход
                elif self.board.move_piece(start_row, start_col, actual_row, actual_col):
                    # Проверяем, достигла ли пешка противоположного конца доски
                    self.update_board()
                else:
                    QMessageBox.warning(self, "Ошибка", "Неверный ход")
                # Сброс выделения
                self.selected_piece = None
                self.reset_button_colors()

        return handler

    def highlight_moves(self, row, col):
        """Подсвечивает возможные ходы для выбранной фигуры."""
        current_piece = self.board.field[row][col]
        if current_piece is None:
            return  # Если в клетке нет фигуры, подсветка невозможна

        for i in range(8):
            for j in range(8):
                target_piece = self.board.field[i][j]
                if (current_piece.can_move(self.board, row, col, i, j) and target_piece is None) or \
                        (current_piece.can_attack(self.board, row, col, i, j) and
                         target_piece is not None and  # Проверяем, есть ли фигура в целевой клетке
                         current_piece.get_color() != target_piece.get_color()):
                    # Преобразуем координаты в зависимости от флага переворота
                    display_row, display_col = (7 - i if not self.is_flipped else i,
                                                7 - j if not self.is_flipped else j)
                    self.buttons[display_row][display_col].setStyleSheet(
                        "background-color: rgb(153, 255, 255);")

    def reset_button_colors(self):
        """Сбрасывает цвета клеток на исходные."""
        for row in range(8):
            for col in range(8):
                self.buttons[row][col].setStyleSheet(self.get_cell_color(row, col))

    def update_board(self):
        """Обновляет текст на кнопках и статус игрока, переворачивает доску."""
        self.is_flipped = not self.is_flipped  # Меняем состояние переворота доски

        # Обновляем отображение доски
        for row in range(8):
            for col in range(8):
                actual_row, actual_col = self.get_actual_coordinates(row, col)
                self.buttons[row][col].setText(self.board.cell(actual_row, actual_col))

        current_color = self.board.current_player_color()
        opponent_color = opponent(current_color)

        if self.board.is_check(opponent_color):
            if self.board.is_mate(opponent_color):
                #  указываем, кто выиграл
                winner = "Белые" if current_color == WHITE else "Чёрные"
                self.status_label.setText(f"Игра окончена. Победили {winner}.")
                self.show_game_over(winner)  # Показать победителя

        else:
            current_player = "Ход белых" if current_color == WHITE else "Ход чёрных"
            self.status_label.setText(current_player)

    def get_actual_coordinates(self, row, col):
        """
        Преобразует координаты кнопок в соответствии с состоянием переворота.
        """

        if self.is_flipped:
            return row, col
        return 7 - row, 7 - col

    def select_piece(self, piece):
        """Обрабатывает выбор фигуры."""
        self.selected_piece = piece  # Сохраняем выбранную фигуру
        self.accept()  # Закрываем окно

    def show_game_over(self, winner):
        """Показать победителя и обновить статистику"""
        conn = sqlite3.connect("chess_game.db")
        cursor = conn.cursor()

        # Рассчитываем время игры
        end_time = datetime.now()
        elapsed_time = int((end_time - self.start_time).total_seconds())  # Время в секундах (округлено вниз)

        # Обновление статистики для обоих игроков
        for color, player in enumerate([self.player1, self.player2]):
            cursor.execute("SELECT * FROM statistics WHERE name = ?", (player,))
            result = cursor.fetchone()
            if result:
                # Игрок существует, обновляем статистику
                name, rounds, wins, time_played = result

                # Обработка времени (поддержка обоих форматов)
                try:
                    if ":" in time_played:  # Формат hh:mm:ss
                        time_parts = time_played.split(':')
                        time_in_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(
                            float(time_parts[2]))
                    else:  # Формат в секундах (число с плавающей точкой)
                        time_in_seconds = int(float(time_played))  # Убираем дробную часть секунд
                except (ValueError, TypeError):
                    # Если данные некорректны, задаем дефолтное значение
                    time_in_seconds = 0

                new_rounds = rounds + 1
                # Увеличиваем победы только для победителя
                if color + 1 == self.board.current_player_color():
                    wins += 1

                new_time_played = time_in_seconds + elapsed_time
                # Преобразуем время обратно в строку 'hh:mm:ss'
                new_time_played_str = str(timedelta(seconds=new_time_played))

                cursor.execute(
                    "UPDATE statistics SET rounds = ?, wins = ?, time_played = ? WHERE name = ?",
                    (new_rounds, wins, new_time_played_str, player)
                )
            else:
                # Игрока нет, создаем запись
                is_winner = 1 if color + 1 == self.board.current_player_color() else 0
                formatted_time = str(timedelta(seconds=elapsed_time))  # Время в формате 'hh:mm:ss'
                cursor.execute(
                    "INSERT INTO statistics (name, rounds, wins, time_played) VALUES (?, ?, ?, ?)",
                    (player, 1, is_winner, formatted_time)
                )
        conn.commit()
        conn.close()
        # Переход в главное меню с сообщением о победе
        self.menu = MainMenu(f"Игра завершена! Победили {winner}!")
        self.menu.show()
        self.close()


class PromotionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Преобразование пешки")
        self.setModal(True)
        self.setFixedSize(300, 200)
        self.selected_piece = None  # Сохраняет выбранную фигуру

        # Убираем возможность закрыть окно
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        # Основной макет
        layout = QVBoxLayout()

        # Сообщение
        label = QLabel("Выберите фигуру для превращения:")
        layout.addWidget(label)

        # Кнопки для выбора фигур
        pieces = [("Ферзь", "Q"), ("Ладья", "R"), ("Слон", "B"), ("Конь", "N")]
        for piece_name, piece_char in pieces:
            button = QPushButton(piece_name)
            button.clicked.connect(lambda _, p=piece_char: self.select_piece(p))
            layout.addWidget(button)

        # Установка макета
        self.setLayout(layout)

    def select_piece(self, piece):
        """
        Обрабатывает выбор фигуры.
        """
        self.selected_piece = piece  # Сохраняем выбранную фигуру
        self.accept()  # Закрываем окно

    def closeEvent(self, event):
        """
        Блокируем возможность закрыть окно без выбора.
        """
        if self.selected_piece is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите фигуру для превращения.")
            event.ignore()
        else:
            event.accept()


class MainMenu(QWidget):
    def __init__(self, text=None):
        super().__init__()
        self.text = text

        self.setWindowTitle("Chess Game - Главное меню")
        self.setGeometry(100, 100, 600, 400)

        # Layout основного меню
        self.layout = QVBoxLayout()

        # Заголовок меню
        self.title_label = QLabel(self.text if self.text else "Добро пожаловать в шахматы!")
        self.title_label.setFont(QFont("Arial", 20))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)

        # Кнопка для начала игры
        self.start_game_button = QPushButton("Начать игру")
        self.start_game_button.setFont(QFont("Arial", 16))
        self.start_game_button.clicked.connect(self.start_game)
        self.layout.addWidget(self.start_game_button)

        # Кнопка для статистики
        self.statistics_button = QPushButton("Статистика")
        self.statistics_button.setFont(QFont("Arial", 16))
        self.statistics_button.clicked.connect(self.open_statistics)
        self.layout.addWidget(self.statistics_button)

        # Кнопка для включения/выключения подсветки
        self.highlight_toggle_button = QPushButton("Включить подсветку ходов фигур")
        self.highlight_toggle_button.setFont(QFont("Arial", 16))
        self.highlight_toggle_button.clicked.connect(self.toggle_highlight)
        self.layout.addWidget(self.highlight_toggle_button)

        # Кнопка для выхода из игры
        self.exit_button = QPushButton("Выход")
        self.exit_button.setFont(QFont("Arial", 16))
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

        # Для хранения состояния подсветки
        self.highlight_enabled = False

        # Создаем центральный layout
        self.setLayout(self.layout)

    def open_statistics(self):
        """Открыть окно статистики"""
        self.statistics_window = StatisticsWindow()
        self.statistics_window.show()

    def start_game(self):
        """Показывает окно ввода имен игроков и запускает игру"""
        while True:
            dialog = PlayerNamesDialog(self)
            if dialog.exec():  # Если игроки ввели имена и нажали "Ок"
                player1, player2 = dialog.get_player_names()
                if player1 and player2:  # Если имена валидны
                    self.hide()  # Скрыть главное меню
                    self.chess_game = ChessGUI(player1, player2)
                    self.chess_game.show()
                    break  # Выход из цикла, так как игра началась
                else:
                    # Если имена невалидные, диалог повторяется
                    QMessageBox.warning(self, "Ошибка", "Имена игроков не могут быть одинаковыми или пустыми!")

    def toggle_highlight(self):
        global flag_highlight_moves
        """Переключает подсветку ходов фигур"""
        self.highlight_enabled = not self.highlight_enabled
        if self.highlight_enabled:
            self.highlight_toggle_button.setText("Выключить подсветку ходов фигур")
            self.highlight_toggle_button.setStyleSheet("background-color: rgb(120, 220, 220);")
            flag_highlight_moves = True
        else:
            self.highlight_toggle_button.setText("Включить подсветку ходов фигур")
            self.highlight_toggle_button.setStyleSheet("background-color: none;")
            flag_highlight_moves = False


class PlayerNamesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введите имена игроков")
        self.setGeometry(100, 100, 400, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel("Введите имена игроков:")
        self.layout.addWidget(self.label)

        self.player1_input = QLineEdit(self)
        self.player1_input.setPlaceholderText("Имя игрока 1 (Белые)")
        self.layout.addWidget(self.player1_input)

        self.player2_input = QLineEdit(self)
        self.player2_input.setPlaceholderText("Имя игрока 2 (Черные)")
        self.layout.addWidget(self.player2_input)

        # Кнопки ОК и Отмена
        self.buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ок")
        self.cancel_button = QPushButton("Отмена")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.ok_button)
        self.buttons_layout.addWidget(self.cancel_button)

        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)

    def get_player_names(self):
        """Возвращает имена игроков из полей ввода, проверяя, что они не совпадают"""
        player1 = self.player1_input.text().strip()
        player2 = self.player2_input.text().strip()

        if player1 == player2:
            QMessageBox.warning(self, "Ошибка", "Имена игроков не могут совпадать!")
            return None, None  # Возвращаем пустые значения, чтобы обработать это снаружи
        if not player1 or not player2:
            QMessageBox.warning(self, "Ошибка", "Имена игроков не могут быть пустыми!")
            return None, None

        return player1, player2


class StatisticsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Статистика")
        self.setGeometry(100, 100, 600, 400)
        self.layout = QVBoxLayout()

        # Поиск игрока
        self.title_label = QLabel("Введите имя игрока для поиска:")
        self.layout.addWidget(self.title_label)

        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)

        self.search_button = QPushButton("Найти")
        self.search_button.clicked.connect(self.search_player_statistics)
        self.layout.addWidget(self.search_button)

        # Отображение рейтинга игроков
        self.rating_label = QLabel("Рейтинг игроков (по умолчанию: по времени в игре):")
        self.rating_label.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.rating_label)

        # Сортировка рейтинга
        self.sort_buttons_layout = QHBoxLayout()
        self.time_sort_button = QPushButton("По времени в игре")
        self.time_sort_button.clicked.connect(lambda: self.load_ranking("time_played"))
        self.games_sort_button = QPushButton("По количеству игр")
        self.games_sort_button.clicked.connect(lambda: self.load_ranking("rounds"))
        self.ratio_sort_button = QPushButton("По проценту побед")
        self.ratio_sort_button.clicked.connect(lambda: self.load_ranking("win_ratio"))

        self.sort_buttons_layout.addWidget(self.time_sort_button)
        self.sort_buttons_layout.addWidget(self.games_sort_button)
        self.sort_buttons_layout.addWidget(self.ratio_sort_button)
        self.layout.addLayout(self.sort_buttons_layout)

        # Таблица для рейтинга
        self.ranking_table = QLabel()
        self.layout.addWidget(self.ranking_table)

        self.setLayout(self.layout)

        # Загрузка начального рейтинга
        self.load_ranking("time_played")

    def search_player_statistics(self):
        player_name = self.name_input.text().strip()

        if not player_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя игрока!")
            return

        conn = sqlite3.connect("chess_game.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statistics WHERE name = ?", (player_name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            name, rounds, wins, time_played = result
            win_ratio = wins / rounds if rounds > 0 else 0
            stats_message = (
                f"Имя: {name}\n"
                f"Сыграно игр: {rounds}\n"
                f"Выиграно игр: {wins}\n"
                f"Время в игре: {time_played}\n"
                f"Процент побед: {win_ratio:.2%}"
            )
            QMessageBox.information(self, "Статистика игрока", stats_message)
        else:
            QMessageBox.warning(self, "Ошибка", "Игрок не найден!")

    def load_ranking(self, sort_by):
        conn = sqlite3.connect("chess_game.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, rounds, wins, time_played FROM statistics")
        players = cursor.fetchall()
        conn.close()

        # Добавляем параметр "процент побед"
        ranking_data = [
            (
                player[0],
                player[1],
                player[2],
                player[3],
                (player[2] / player[1] if player[1] > 0 else 0)  # Вычисление процента побед
            )
            for player in players
        ]
        # Сортируем данные в зависимости от параметра
        if sort_by == "time_played":
            ranking_data.sort(key=lambda x: x[3], reverse=True)
        elif sort_by == "rounds":
            ranking_data.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == "win_ratio":
            ranking_data.sort(key=lambda x: x[4], reverse=True)
        # Форматируем данные для отображения
        ranking_text = "Имя | Игры | Победы | Время | % Побед\n"
        ranking_text += "-" * 40 + "\n"
        for player in ranking_data:
            ranking_text += f"{player[0]} | {player[1]} | {player[2]} | {player[3]} | {player[4]:.2%}\n"
        self.ranking_table.setText(ranking_text)
        self.ranking_table.setFont(QFont("Courier", 10))
        self.ranking_table.setAlignment(Qt.AlignmentFlag.AlignTop)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    app = QApplication([])
    window = MainMenu()
    window.show()

    sys.excepthook = except_hook
    sys.exit(app.exec())
