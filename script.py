import sqlite3

# Укажите путь к файлу базы данных
db_path = "chess_game.db"

# Подключаемся к базе данных
conn = sqlite3.connect(db_path)

# Создаём курсор для выполнения SQL-запросов
cursor = conn.cursor()

# SQL-запрос для создания таблицы
create_table_query = '''
CREATE TABLE IF NOT EXISTS statistics (
    name TEXT PRIMARY KEY,        -- Имя игрока (уникальный ключ)
    rounds INTEGER DEFAULT 0,     -- Количество сыгранных раундов (по умолчанию 0)
    wins INTEGER DEFAULT 0,       -- Количество побед (по умолчанию 0)
    time_played TEXT DEFAULT '00:00:00' -- Время, проведённое в игре (по умолчанию 00:00:00)
)
'''
cursor.execute(create_table_query)
print("Таблица 'statistics' успешно создана или уже существует.")
conn.commit()
conn.close()
