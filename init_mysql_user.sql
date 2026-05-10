-- SQL запрос для инициализации пользователя в MySQL
-- Выполнить в MySQL Workbench или через консоль:

-- Создание пользователя (если его нет)
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin123';

-- Выделение базы данных
USE 23009_logistics_db_new;

-- Выдача прав администратора
GRANT ALL PRIVILEGES ON 23009_logistics_db_new.* TO 'admin'@'localhost';

-- Применение прав
FLUSH PRIVILEGES;

-- Проверка прав пользователя
SHOW GRANTS FOR 'admin'@'localhost';
