-- ============================================================
--  УРОК 1: SQL для начинающих — Книжный магазин
--  База данных: lessons | Пользователь: boris
--  Подключение: psql -U boris -d lessons
-- ============================================================
--
--  Схема базы данных:
--    authors      (id, name, country, birth_year)
--    books        (id, title, author_id, genre, price, pages)
--    customers    (id, name, email, city)
--    orders       (id, customer_id, order_date)
--    order_items  (id, order_id, book_id, quantity, price_at_purchase)
--
-- ============================================================


-- ============================================================
--  БЛОК A — SELECT basics (задачи 1–4)
-- ============================================================


-- Задача 1
-- Выведи все книги дороже $20, отсортируй по цене от дорогой к дешёвой.
-- Показать: title, genre, price

-- Твой запрос:


/*  Правильный ответ:
SELECT title, genre, price
FROM books
WHERE price > 20
ORDER BY price DESC;
*/


-- ------------------------------------------------------------

-- Задача 2
-- Найди всех покупателей из Москвы (Moscow).
-- Показать: name, email, city

-- Твой запрос:


/*  Правильный ответ:
SELECT name, email, city
FROM customers
WHERE city = 'Moscow';
*/


-- ------------------------------------------------------------

-- Задача 3
-- Покажи 5 самых толстых книг (по количеству страниц).
-- Показать: title, pages

-- Твой запрос:


/*  Правильный ответ:
SELECT title, pages
FROM books
ORDER BY pages DESC
LIMIT 5;
*/


-- ------------------------------------------------------------

-- Задача 4
-- Найди все книги жанра sci-fi ИЛИ history.
-- Показать: title, genre, price, отсортировать по жанру, затем по названию.

-- Твой запрос:


/*  Правильный ответ:
SELECT title, genre, price
FROM books
WHERE genre = 'sci-fi' OR genre = 'history'
ORDER BY genre, title;

-- Альтернатива через IN:
SELECT title, genre, price
FROM books
WHERE genre IN ('sci-fi', 'history')
ORDER BY genre, title;
*/


-- ============================================================
--  БЛОК B — GROUP BY (задачи 5–8)
-- ============================================================


-- Задача 5
-- Сколько книг есть в каждом жанре?
-- Показать: genre, количество книг. Отсортировать по убыванию количества.

-- Твой запрос:


/*  Правильный ответ:
SELECT genre, COUNT(*) AS book_count
FROM books
GROUP BY genre
ORDER BY book_count DESC;
*/


-- ------------------------------------------------------------

-- Задача 6
-- Какова средняя цена книги в каждом жанре?
-- Показать: genre, средняя цена (округлить до 2 знаков). Отсортировать по цене.

-- Твой запрос:


/*  Правильный ответ:
SELECT genre, ROUND(AVG(price), 2) AS avg_price
FROM books
GROUP BY genre
ORDER BY avg_price DESC;
*/


-- ------------------------------------------------------------

-- Задача 7
-- Топ авторов по количеству книг в магазине.
-- Показать: author_id, количество книг. Отсортировать по убыванию.
-- (Подсказка: на следующем уроке научимся заменять author_id на имя через JOIN)

-- Твой запрос:


/*  Правильный ответ:
SELECT author_id, COUNT(*) AS book_count
FROM books
GROUP BY author_id
ORDER BY book_count DESC;
*/


-- ------------------------------------------------------------

-- Задача 8
-- Найди жанры, в которых средняя цена книги выше $15.
-- Показать: genre, средняя цена. Отсортировать по цене по убыванию.
-- (Подсказка: используй HAVING для фильтрации по результату агрегации)

-- Твой запрос:


/*  Правильный ответ:
SELECT genre, ROUND(AVG(price), 2) AS avg_price
FROM books
GROUP BY genre
HAVING AVG(price) > 15
ORDER BY avg_price DESC;
*/


-- ============================================================
--  БЛОК C — JOIN (задачи 9–12)
-- ============================================================


-- Задача 9
-- Выведи список всех книг вместе с именем автора.
-- Показать: title, genre, price, author name.
-- Использовать: INNER JOIN (книги без автора не показывать)

-- Твой запрос:


/*  Правильный ответ:
SELECT b.title, b.genre, b.price, a.name AS author
FROM books b
INNER JOIN authors a ON b.author_id = a.id
ORDER BY a.name, b.title;
*/


-- ------------------------------------------------------------

-- Задача 10
-- Выведи ВСЕХ авторов и количество их книг в магазине.
-- Авторы без книг должны быть в списке с количеством 0.
-- Показать: author name, country, book_count.
-- Использовать: LEFT JOIN

-- Твой запрос:


/*  Правильный ответ:
SELECT a.name, a.country, COUNT(b.id) AS book_count
FROM authors a
LEFT JOIN books b ON b.author_id = a.id
GROUP BY a.id, a.name, a.country
ORDER BY book_count DESC;
*/


-- ------------------------------------------------------------

-- Задача 11
-- Выведи ВСЕХ покупателей и общую сумму их покупок.
-- Покупатели без заказов должны быть в списке с суммой 0 (или NULL).
-- Показать: customer name, city, total_spent.
-- Использовать: LEFT JOIN через orders + order_items, GROUP BY, SUM

-- Твой запрос:


/*  Правильный ответ:
SELECT c.name, c.city,
       COALESCE(SUM(oi.quantity * oi.price_at_purchase), 0) AS total_spent
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
LEFT JOIN order_items oi ON oi.order_id = o.id
GROUP BY c.id, c.name, c.city
ORDER BY total_spent DESC;
*/


-- ------------------------------------------------------------

-- Задача 12
-- Топ-3 самые продаваемые книги по количеству проданных экземпляров.
-- Показать: title, genre, total_sold (сумма quantity из order_items).
-- Использовать: JOIN books + order_items, GROUP BY, SUM, LIMIT

-- Твой запрос:


/*  Правильный ответ:
SELECT b.title, b.genre, SUM(oi.quantity) AS total_sold
FROM books b
JOIN order_items oi ON oi.book_id = b.id
GROUP BY b.id, b.title, b.genre
ORDER BY total_sold DESC
LIMIT 3;
*/


-- ============================================================
--  БОНУС (по желанию)
-- ============================================================

-- Бонус: Найди покупателей, которые потратили больше $50.
-- Используй HAVING.

/*  Правильный ответ:
SELECT c.name, c.city,
       SUM(oi.quantity * oi.price_at_purchase) AS total_spent
FROM customers c
JOIN orders o ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
GROUP BY c.id, c.name, c.city
HAVING SUM(oi.quantity * oi.price_at_purchase) > 50
ORDER BY total_spent DESC;
*/
