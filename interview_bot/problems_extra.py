# problems_extra.py — дополнительные задачи (по 30 на каждый уровень)

PROBLEMS_EXTRA = [
    # ─────────────────── СТАЖЁР (intern) — ещё 30 ───────────────────
    {
        "title": "Второй максимальный элемент",
        "level": "intern",
        "description": (
            "Дан массив целых чисел `nums` длиной не менее 2. "
            "Верни второй по величине уникальный элемент массива."
        ),
        "examples": [
            {"input": "nums = [3, 1, 4, 1, 5, 9]", "output": "5"},
            {"input": "nums = [1, 2]", "output": "1"},
            {"input": "nums = [-1, -2, -3]", "output": "-2"},
        ],
        "constraints": ["2 <= nums.length <= 10⁴", "-10⁹ <= nums[i] <= 10⁹"],
        "hint1": "Попробуй отсортировать массив и взять второй уникальный элемент с конца.",
        "hint2": "Или пройди массив один раз, отслеживая `first_max` и `second_max`. Обновляй их при нахождении нового максимума.",
        "hint3": "Инициализируй `first = second = float('-inf')`. Для каждого `n`: если `n > first` → `second = first; first = n`; иначе если `n > second and n != first` → `second = n`. Верни `second`.",
        "solution_text": (
            "Отследи два максимума за один проход. Инициализируй `first = second = float('-inf')`. "
            "При нахождении нового максимума сдвигай: second ← first, first ← n. "
            "Если n меньше first, но больше second и не равен first — обновляй second.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [5, 5, 5] → второго уникального нет; задача гарантирует уникальность, но провальный тест — nums = [2, 2, 1] → ожидается 1, а не 2.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Подсчёт вхождений символа",
        "level": "intern",
        "description": (
            "Даны строка `s` и символ `ch`. "
            "Верни количество вхождений символа `ch` в строке `s` без использования метода `count`."
        ),
        "examples": [
            {"input": 's = "hello", ch = "l"', "output": "2"},
            {"input": 's = "banana", ch = "a"', "output": "3"},
            {"input": 's = "xyz", ch = "a"', "output": "0"},
        ],
        "constraints": ["1 <= s.length <= 10⁵", "ch — один символ"],
        "hint1": "Пройди по каждому символу строки и сравнивай с `ch`.",
        "hint2": "Используй цикл `for c in s` и счётчик `result`, который увеличиваешь при совпадении.",
        "hint3": "Полная реализация: `result = 0; for c in s: if c == ch: result += 1; return result`. Также работает: `sum(1 for c in s if c == ch)`.",
        "solution_text": (
            "Пройди по строке, считая совпадения с `ch`. Простой счётчик в цикле даёт O(n).\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": 's = "aA", ch = "a" → ожидается 1 (не 2). Регистр важен — заглавная A не равна строчной a.',
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Переворот числа",
        "level": "intern",
        "description": (
            "Дано 32-битное целое число `x`. Верни число с перевёрнутыми цифрами. "
            "Если перевёрнутое число выходит за диапазон [-2³¹, 2³¹-1], верни 0."
        ),
        "examples": [
            {"input": "x = 123", "output": "321"},
            {"input": "x = -123", "output": "-321"},
            {"input": "x = 120", "output": "21"},
        ],
        "constraints": ["-2³¹ <= x <= 2³¹-1"],
        "hint1": "Преврати число в строку, переверни, учти знак и ведущие нули.",
        "hint2": "Знак: `sign = -1 if x < 0 else 1`. Переверни `str(abs(x))`, убери ведущие нули через `int(...)`. Верни `sign * result` если в диапазоне, иначе 0.",
        "hint3": "Полная реализация: `sign = -1 if x < 0 else 1; rev = int(str(abs(x))[::-1]); result = sign * rev; return result if -2**31 <= result <= 2**31-1 else 0`.",
        "solution_text": (
            "Определи знак, переверни строковое представление абсолютного значения, "
            "восстанови знак, проверь диапазон. `int(...)` автоматически убирает ведущие нули.\n"
            "⏱ Сложность: O(log x) — количество цифр."
        ),
        "failing_test": "x = 1534236469 → ожидается 0 (переполнение). Перевёрнутое 9646324351 > 2³¹-1.",
        "time_complexity": "O(log x)",
        "space_complexity": "O(log x)",
    },
    {
        "title": "Сумма цифр числа",
        "level": "intern",
        "description": (
            "Дано неотрицательное целое число `n`. Верни сумму его цифр."
        ),
        "examples": [
            {"input": "n = 123", "output": "6", "explanation": "1+2+3 = 6"},
            {"input": "n = 0", "output": "0"},
            {"input": "n = 9999", "output": "36"},
        ],
        "constraints": ["0 <= n <= 10⁹"],
        "hint1": "Можно извлекать последнюю цифру через `n % 10` и убирать её через `n //= 10`.",
        "hint2": "Или переведи в строку и суммируй: `sum(int(d) for d in str(n))`.",
        "hint3": "Итеративно: `total = 0; while n > 0: total += n % 10; n //= 10; return total`. Для n=0 верни 0 до цикла. Или: `return sum(int(d) for d in str(n))`.",
        "solution_text": (
            "Итеративно: извлекай последнюю цифру (`n % 10`), добавляй к сумме, сдвигай (`n //= 10`).\n"
            "⏱ Сложность: O(log n) по времени, O(1) по памяти."
        ),
        "failing_test": "n = 0 → ожидается 0. Цикл `while n > 0` сразу завершится, нужно вернуть 0.",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Пропущенное число",
        "level": "intern",
        "description": (
            "Дан массив `nums` из n различных чисел в диапазоне [0, n]. "
            "Одно число пропущено. Найди и верни его."
        ),
        "examples": [
            {"input": "nums = [3, 0, 1]", "output": "2"},
            {"input": "nums = [0, 1]", "output": "2"},
            {"input": "nums = [9,6,4,2,3,5,7,0,1]", "output": "8"},
        ],
        "constraints": ["n == nums.length", "0 <= nums[i] <= n", "все числа уникальны"],
        "hint1": "Сумма чисел от 0 до n равна n*(n+1)//2. Вычти из неё сумму массива.",
        "hint2": "Ожидаемая сумма: `expected = n*(n+1)//2` где n = len(nums). Фактическая: `actual = sum(nums)`. Ответ: `expected - actual`.",
        "hint3": "Однострочно: `return len(nums)*(len(nums)+1)//2 - sum(nums)`. Также решается через XOR: `result = len(nums); for i, v in enumerate(nums): result ^= i ^ v; return result`.",
        "solution_text": (
            "Математически: ожидаемая сумма [0..n] = n*(n+1)//2. Вычти реальную сумму — получишь пропущенное.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [0] → ожидается 1. n=1, expected=1, sum=0, ответ=1.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Простое число",
        "level": "intern",
        "description": (
            "Дано целое число `n`. Верни `True`, если n — простое число, иначе `False`. "
            "Простое число делится только на 1 и на себя, при этом n > 1."
        ),
        "examples": [
            {"input": "n = 2", "output": "True"},
            {"input": "n = 4", "output": "False", "explanation": "4 = 2 × 2"},
            {"input": "n = 17", "output": "True"},
            {"input": "n = 1", "output": "False"},
        ],
        "constraints": ["1 <= n <= 10⁶"],
        "hint1": "Проверь делимость n на все числа от 2 до n-1. Если нашёл делитель — не простое.",
        "hint2": "Оптимизация: делители всегда парные, и один из них ≤ √n. Проверяй только до `int(n**0.5) + 1`.",
        "hint3": "Полная реализация: `if n < 2: return False; for i in range(2, int(n**0.5)+1): if n % i == 0: return False; return True`. Для n=2 цикл не выполняется → возвращает True.",
        "solution_text": (
            "Проверяй делители от 2 до √n включительно. Если делитель найден — не простое. "
            "Числа < 2 не простые.\n"
            "⏱ Сложность: O(√n) по времени, O(1) по памяти."
        ),
        "failing_test": "n = 1 → ожидается False. 1 по определению не является простым числом.",
        "time_complexity": "O(√n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Конвертация температур",
        "level": "intern",
        "description": (
            "Дана температура `celsius` в градусах Цельсия. "
            "Верни список `[fahrenheit, kelvin]`, округлённый до 5 знаков после запятой.\n"
            "Формулы: Fahrenheit = Celsius × 9/5 + 32; Kelvin = Celsius + 273.15"
        ),
        "examples": [
            {"input": "celsius = 36.50", "output": "[97.7, 309.65]"},
            {"input": "celsius = 122.11", "output": "[251.798, 395.26]"},
            {"input": "celsius = 0", "output": "[32.0, 273.15]"},
        ],
        "constraints": ["-1000 <= celsius <= 1000"],
        "hint1": "Примени формулы: fahrenheit = celsius * 9/5 + 32; kelvin = celsius + 273.15.",
        "hint2": "Верни список из двух значений. Используй `round(value, 5)` для округления.",
        "hint3": "Полная реализация: `f = round(celsius * 9/5 + 32, 5); k = round(celsius + 273.15, 5); return [f, k]`.",
        "solution_text": (
            "Примени обе формулы и округли до 5 знаков через `round(value, 5)`.\n"
            "⏱ Сложность: O(1)."
        ),
        "failing_test": "celsius = 0 → Kelvin = 273.15 (не 273.0). Частая ошибка — забыть прибавить 273.15.",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Сортировка пузырьком",
        "level": "intern",
        "description": (
            "Реализуй сортировку пузырьком. Дан список целых чисел `nums`. "
            "Отсортируй его по возрастанию на месте (in-place) и верни."
        ),
        "examples": [
            {"input": "nums = [5, 2, 8, 1, 9]", "output": "[1, 2, 5, 8, 9]"},
            {"input": "nums = [3, 3, 1]", "output": "[1, 3, 3]"},
            {"input": "nums = [1]", "output": "[1]"},
        ],
        "constraints": ["1 <= nums.length <= 10³", "-10⁴ <= nums[i] <= 10⁴"],
        "hint1": "Каждый проход «всплывает» наибольший элемент в конец. Повторяй n-1 раз.",
        "hint2": "Внешний цикл `for i in range(len(nums)-1)`: внутренний `for j in range(len(nums)-i-1)`: если `nums[j] > nums[j+1]` — своп.",
        "hint3": "С оптимизацией: `swapped = True; i = 0; while swapped: swapped = False; for j in range(len(nums)-i-1): if nums[j]>nums[j+1]: nums[j],nums[j+1]=nums[j+1],nums[j]; swapped=True; i+=1`. Ранний выход при отсутствии свопов.",
        "solution_text": (
            "Внешний цикл по проходам (n-1 итерация). Внутренний цикл сравнивает соседей и меняет местами. "
            "Оптимизация: если за проход не было ни одного свопа — массив уже отсортирован, выходи.\n"
            "⏱ Сложность: O(n²) в худшем случае, O(n) в лучшем (уже отсортирован)."
        ),
        "failing_test": "nums = [2, 1, 1] → ожидается [1, 1, 2]. Дубликаты должны оставаться рядом.",
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Удаление дубликатов из списка",
        "level": "intern",
        "description": (
            "Дан список `nums`. Верни новый список с удалёнными дубликатами, "
            "сохранив исходный порядок первых вхождений."
        ),
        "examples": [
            {"input": "nums = [1, 3, 2, 1, 4, 3]", "output": "[1, 3, 2, 4]"},
            {"input": "nums = [1, 1, 1]", "output": "[1]"},
            {"input": "nums = [5, 4, 3]", "output": "[5, 4, 3]"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴"],
        "hint1": "Используй вспомогательное множество для отслеживания увиденных элементов.",
        "hint2": "Пройди по nums. Если элемент ещё не в seen — добавь в seen и в result.",
        "hint3": "Полная реализация: `seen = set(); result = []; [result.append(x) or seen.add(x) for x in nums if x not in seen]; return result`. Или через dict: `list(dict.fromkeys(nums))` — сохраняет порядок в Python 3.7+.",
        "solution_text": (
            "Пройди по списку с вспомогательным set(). Добавляй элемент в результат только при первом появлении.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [3, 1, 2, 1, 3] → ожидается [3, 1, 2]. Порядок должен соответствовать первым вхождениям.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Перевод в двоичную систему",
        "level": "intern",
        "description": (
            "Дано неотрицательное целое число `n`. Верни его двоичное представление в виде строки. "
            "Не используй встроенный `bin()`."
        ),
        "examples": [
            {"input": "n = 0", "output": '"0"'},
            {"input": "n = 10", "output": '"1010"'},
            {"input": "n = 255", "output": '"11111111"'},
        ],
        "constraints": ["0 <= n <= 10⁹"],
        "hint1": "Делай n % 2 для получения текущего бита, затем n //= 2. Собирай биты в обратном порядке.",
        "hint2": "Формируй список битов: пока n > 0, добавляй `n % 2` и делай `n //= 2`. Переверни список и объедини в строку.",
        "hint3": "Полная реализация: `if n == 0: return '0'; bits = []; while n > 0: bits.append(str(n % 2)); n //= 2; return ''.join(reversed(bits))`. Обязательно обработай n=0.",
        "solution_text": (
            "Итеративно делим на 2, собираем остатки (биты) справа налево, затем переворачиваем. "
            "Специальный случай: n=0 → '0'.\n"
            "⏱ Сложность: O(log n) по времени, O(log n) по памяти."
        ),
        "failing_test": "n = 0 → ожидается '0'. Цикл `while n > 0` не выполнится, нужна отдельная проверка.",
        "time_complexity": "O(log n)",
        "space_complexity": "O(log n)",
    },
    {
        "title": "Количество слов в строке",
        "level": "intern",
        "description": (
            "Дана строка `s`. Верни количество слов в ней. "
            "Слова разделены одним или несколькими пробелами. Ведущие и хвостовые пробелы игнорируй."
        ),
        "examples": [
            {"input": 's = "Hello World"', "output": "2"},
            {"input": 's = "  spaces   everywhere  "', "output": "2"},
            {"input": 's = "one"', "output": "1"},
            {"input": 's = "   "', "output": "0"},
        ],
        "constraints": ["0 <= s.length <= 10⁵"],
        "hint1": "Разбей строку на слова через `split()`. Метод split() без аргументов автоматически обрабатывает множественные пробелы и ведущие/хвостовые.",
        "hint2": "`s.split()` возвращает список слов. Верни `len(...)` этого списка.",
        "hint3": "Однострочно: `return len(s.split())`. Без split(): `stripped = s.strip(); return 0 if not stripped else len([w for w in stripped.split(' ') if w])`.",
        "solution_text": (
            "`len(s.split())` — split без аргументов разбивает по любым пробелам и убирает пустые токены.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": 's = "   " → ожидается 0. `s.split()` вернёт [], len([]) = 0 — верно.',
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Среднее арифметическое",
        "level": "intern",
        "description": (
            "Дан список чисел `nums`. Верни среднее арифметическое его элементов. "
            "Результат округли до 5 знаков после запятой."
        ),
        "examples": [
            {"input": "nums = [1, 2, 3, 4, 5]", "output": "3.0"},
            {"input": "nums = [10, 20]", "output": "15.0"},
            {"input": "nums = [7]", "output": "7.0"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴", "-10⁶ <= nums[i] <= 10⁶"],
        "hint1": "Среднее = сумма элементов / количество элементов.",
        "hint2": "Используй `sum(nums) / len(nums)`. Деление всегда float в Python 3.",
        "hint3": "Полная реализация: `return round(sum(nums) / len(nums), 5)`. Пустой список не встречается по условию задачи.",
        "solution_text": (
            "`sum(nums) / len(nums)` — простое деление в Python 3 возвращает float.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [1, 2] → ожидается 1.5, не 1 (целочисленное деление). В Python 3 `/` всегда float.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Транспозиция матрицы",
        "level": "intern",
        "description": (
            "Дана матрица `matrix` размером m×n. Верни её транспонированную версию (n×m). "
            "Транспонирование: строки становятся столбцами."
        ),
        "examples": [
            {"input": "matrix = [[1,2,3],[4,5,6]]", "output": "[[1,4],[2,5],[3,6]]"},
            {"input": "matrix = [[1,2],[3,4]]", "output": "[[1,3],[2,4]]"},
        ],
        "constraints": ["m == matrix.length", "n == matrix[0].length", "1 <= m, n <= 1000"],
        "hint1": "Элемент на позиции [i][j] в исходной матрице становится элементом [j][i] в транспонированной.",
        "hint2": "Создай новую матрицу n×m. Заполни: `result[j][i] = matrix[i][j]` для всех i, j.",
        "hint3": "Однострочно: `return [list(row) for row in zip(*matrix)]`. `zip(*matrix)` транспонирует матрицу, возвращая кортежи строк.",
        "solution_text": (
            "`zip(*matrix)` разворачивает строки матрицы как аргументы zip, результат — транспозиция.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": "matrix = [[1,2,3]] → ожидается [[1],[2],[3]]. Матрица 1×3 транспонируется в 3×1.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Наименьший элемент без min()",
        "level": "intern",
        "description": (
            "Дан непустой массив целых чисел `nums`. Найди и верни минимальный элемент "
            "без использования встроенной функции `min`."
        ),
        "examples": [
            {"input": "nums = [3, 1, 4, 1, 5]", "output": "1"},
            {"input": "nums = [-5, -3, -8]", "output": "-8"},
            {"input": "nums = [42]", "output": "42"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴", "-10⁹ <= nums[i] <= 10⁹"],
        "hint1": "Начни с первого элемента как текущего минимума. Пройди остальные и обновляй минимум.",
        "hint2": "Инициализируй `current_min = nums[0]`. Для каждого элемента: `if num < current_min: current_min = num`.",
        "hint3": "Полная реализация: `current_min = nums[0]; for num in nums[1:]: if num < current_min: current_min = num; return current_min`. НИКОГДА не инициализируй через float('inf') для обратной задачи без проверки.",
        "solution_text": (
            "Инициализируй текущий минимум первым элементом. Пройди по остальным, обновляя при нахождении меньшего.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [-1, -2, -3] → ожидается -3. Инициализация через 0 сломает ответ на всех отрицательных.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Знак числа",
        "level": "intern",
        "description": (
            "Дано целое число `num`. Верни:\n"
            "- `1`, если num > 0\n"
            "- `-1`, если num < 0\n"
            "- `0`, если num == 0"
        ),
        "examples": [
            {"input": "num = -5", "output": "-1"},
            {"input": "num = 0", "output": "0"},
            {"input": "num = 7", "output": "1"},
        ],
        "constraints": ["-10⁹ <= num <= 10⁹"],
        "hint1": "Три ветки: > 0 → 1; < 0 → -1; == 0 → 0.",
        "hint2": "Можно сократить: `return 0 if num == 0 else (1 if num > 0 else -1)`.",
        "hint3": "Математически: `import math; return math.copysign(1, num)` даёт ±1.0 (не обрабатывает 0 как 0). Лучше явная проверка: `if num > 0: return 1; if num < 0: return -1; return 0`.",
        "solution_text": (
            "Проверяй три случая: num > 0 → 1; num < 0 → -1; иначе → 0.\n"
            "⏱ Сложность: O(1)."
        ),
        "failing_test": "num = 0 → ожидается 0, не 1 и не -1. Нулевой случай должен быть обработан явно.",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Возведение в степень",
        "level": "intern",
        "description": (
            "Дано число `base` и целый показатель `exp` (≥ 0). "
            "Верни base^exp без использования оператора `**` и функции `pow`."
        ),
        "examples": [
            {"input": "base = 2, exp = 10", "output": "1024"},
            {"input": "base = 3, exp = 0", "output": "1"},
            {"input": "base = 5, exp = 3", "output": "125"},
        ],
        "constraints": ["-100 <= base <= 100", "0 <= exp <= 20"],
        "hint1": "Перемножай base сам на себя exp раз в цикле.",
        "hint2": "Инициализируй `result = 1`. В цикле `for _ in range(exp)`: `result *= base`.",
        "hint3": "Полная реализация: `result = 1; for _ in range(exp): result *= base; return result`. Для exp=0 цикл не выполнится и result=1 — верно. Для base=0, exp=0 → по математике 0⁰=1.",
        "solution_text": (
            "Инициализируй result=1, умножай на base exp раз. exp=0 → сразу возвращаем 1.\n"
            "⏱ Сложность: O(exp) по времени, O(1) по памяти."
        ),
        "failing_test": "base = 0, exp = 0 → ожидается 1 (по условию задачи). Убедись, что возвращается 1.",
        "time_complexity": "O(exp)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Капитализация слов",
        "level": "intern",
        "description": (
            "Дана строка `s`. Верни новую строку, где каждое слово начинается с заглавной буквы, "
            "остальные буквы слова — строчные. Не используй метод `title()`."
        ),
        "examples": [
            {"input": 's = "hello world"', "output": '"Hello World"'},
            {"input": 's = "THE QUICK BROWN FOX"', "output": '"The Quick Brown Fox"'},
            {"input": 's = "one"', "output": '"One"'},
        ],
        "constraints": ["1 <= s.length <= 10⁴"],
        "hint1": "Разбей строку на слова. Для каждого слова: первую букву сделай заглавной, остальные — строчными.",
        "hint2": "Для слова `w`: `w[0].upper() + w[1:].lower()` если слово не пустое.",
        "hint3": "Полная реализация: `words = s.split(); result = [w[0].upper() + w[1:].lower() for w in words if w]; return ' '.join(result)`. Метод `capitalize()` тоже работает: `' '.join(w.capitalize() for w in s.split())`.",
        "solution_text": (
            "Разбей на слова через split(), к каждому применяй `capitalize()` или ручную трансформацию, "
            "склей через join().\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": 's = "hELLO wORLD" → ожидается "Hello World". `capitalize()` опускает весь остаток в lower.',
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Сортировка строк по длине",
        "level": "intern",
        "description": (
            "Дан список строк `words`. Верни его отсортированным по длине строк. "
            "При равной длине сохраняй исходный порядок (стабильная сортировка)."
        ),
        "examples": [
            {"input": 'words = ["banana", "apple", "kiwi", "cherry"]', "output": '["kiwi", "apple", "banana", "cherry"]'},
            {"input": 'words = ["a", "bb", "ccc"]', "output": '["a", "bb", "ccc"]'},
            {"input": 'words = ["same", "size"]', "output": '["same", "size"]'},
        ],
        "constraints": ["1 <= words.length <= 10³", "1 <= words[i].length <= 100"],
        "hint1": "Используй встроенную функцию `sorted()` с ключом сортировки.",
        "hint2": "`sorted(words, key=len)` — сортирует по длине, Python's sorted стабилен.",
        "hint3": "Полная реализация: `return sorted(words, key=len)`. Если нужна сортировка на месте: `words.sort(key=len)`. Стабильность гарантирована стандартом Python (алгоритм Timsort).",
        "solution_text": (
            "`sorted(words, key=len)` — Python's sorted() стабилен, поэтому при равных длинах "
            "исходный порядок сохраняется.\n"
            "⏱ Сложность: O(n log n)."
        ),
        "failing_test": 'words = ["bb", "aa"] → ожидается ["bb", "aa"] (стабильность при равных длинах). Оба имеют длину 2.',
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Сумма квадратов",
        "level": "intern",
        "description": (
            "Дано целое число `n`. Верни сумму квадратов всех натуральных чисел от 1 до n включительно."
        ),
        "examples": [
            {"input": "n = 3", "output": "14", "explanation": "1² + 2² + 3² = 1+4+9 = 14"},
            {"input": "n = 1", "output": "1"},
            {"input": "n = 5", "output": "55"},
        ],
        "constraints": ["1 <= n <= 10⁴"],
        "hint1": "Пройди от 1 до n и суммируй квадраты.",
        "hint2": "Используй `sum(i*i for i in range(1, n+1))`.",
        "hint3": "Формула: `n*(n+1)*(2*n+1)//6` даёт результат за O(1). Или: `return sum(i**2 for i in range(1, n+1))`.",
        "solution_text": (
            "Через цикл: O(n). Через формулу: `n*(n+1)*(2*n+1)//6` — O(1).\n"
            "⏱ Оптимальная сложность: O(1) по формуле."
        ),
        "failing_test": "n = 1 → ожидается 1. Убедись, что диапазон включает n (range(1, n+1)).",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Переворот слов в строке",
        "level": "intern",
        "description": (
            "Дана строка `s` с словами, разделёнными пробелами. "
            "Верни строку, в которой порядок слов обратный."
        ),
        "examples": [
            {"input": 's = "Hello World"', "output": '"World Hello"'},
            {"input": 's = "  sky  is  blue  "', "output": '"blue is sky"'},
            {"input": 's = "a"', "output": '"a"'},
        ],
        "constraints": ["1 <= s.length <= 10⁴"],
        "hint1": "Разбей на слова через split(), переверни список, склей обратно через join().",
        "hint2": "`words = s.split()` убирает лишние пробелы. `words[::-1]` переворачивает. `' '.join(...)` склеивает.",
        "hint3": "Однострочно: `return ' '.join(s.split()[::-1])`. Важно: `split()` без аргументов убирает ведущие/хвостовые пробелы и множественные пробелы между словами.",
        "solution_text": (
            "`' '.join(s.split()[::-1])` — split разбивает и убирает лишние пробелы, [::-1] переворачивает.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": 's = "  spaces  " → ожидается "spaces", не " spaces ". split() без аргументов убирает пробелы.',
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Проверка: является ли строка числом",
        "level": "intern",
        "description": (
            "Дана строка `s`. Верни `True`, если строка представляет собой целое число "
            "(возможно, со знаком + или -), иначе `False`."
        ),
        "examples": [
            {"input": 's = "123"', "output": "True"},
            {"input": 's = "-42"', "output": "True"},
            {"input": 's = "3.14"', "output": "False", "explanation": "дробное — не целое"},
            {"input": 's = "abc"', "output": "False"},
        ],
        "constraints": ["1 <= s.length <= 100"],
        "hint1": "Попробуй обернуть `int(s)` в try/except. Если ValueError — не число.",
        "hint2": "Или вручную: убери знак в начале (если есть), затем проверь `s.isdigit()`.",
        "hint3": "Через try/except: `try: int(s); return True; except ValueError: return False`. Вручную: `s2 = s.lstrip('+-'); return len(s2) > 0 and s2.isdigit()`.",
        "solution_text": (
            "Самый надёжный способ — `int(s)` в try/except ValueError. "
            "Ручная проверка: убери ±знак, проверь isdigit().\n"
            "⏱ Сложность: O(n)."
        ),
        "failing_test": 's = "+" → ожидается False. `int("+")` бросает ValueError — верно. Вручную: после lstrip("+") остаётся "" — пустая строка, len=0 → False.',
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Чётные и нечётные числа",
        "level": "intern",
        "description": (
            "Дан список целых чисел `nums`. Верни словарь с двумя ключами: "
            "`'even'` — список чётных чисел, `'odd'` — список нечётных, "
            "в исходном порядке."
        ),
        "examples": [
            {"input": "nums = [1, 2, 3, 4, 5]", "output": "{'even': [2, 4], 'odd': [1, 3, 5]}"},
            {"input": "nums = [2, 4, 6]", "output": "{'even': [2, 4, 6], 'odd': []}"},
            {"input": "nums = []", "output": "{'even': [], 'odd': []}"},
        ],
        "constraints": ["0 <= nums.length <= 10⁴"],
        "hint1": "Разделяй элементы по условию `num % 2 == 0` (чётное) или `num % 2 != 0` (нечётное).",
        "hint2": "Создай словарь с пустыми списками, затем заполни в одном проходе.",
        "hint3": "Полная реализация: `result = {'even': [], 'odd': []}; for n in nums: result['even' if n % 2 == 0 else 'odd'].append(n); return result`.",
        "solution_text": (
            "Один проход, словарь с двумя списками. Деление по условию `n % 2 == 0`.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [-2, -3] → чётные: [-2], нечётные: [-3]. В Python `-2 % 2 == 0`, `-3 % 2 == 1` (не -1).",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Слияние двух словарей",
        "level": "intern",
        "description": (
            "Даны два словаря `d1` и `d2`. Верни новый словарь, объединяющий оба. "
            "При конфликте ключей — значение из `d2` имеет приоритет."
        ),
        "examples": [
            {"input": "d1 = {'a': 1, 'b': 2}, d2 = {'b': 3, 'c': 4}", "output": "{'a': 1, 'b': 3, 'c': 4}"},
            {"input": "d1 = {}, d2 = {'x': 1}", "output": "{'x': 1}"},
            {"input": "d1 = {'a': 1}, d2 = {}", "output": "{'a': 1}"},
        ],
        "constraints": ["Ключи — строки, значения — целые числа"],
        "hint1": "Скопируй d1, затем обнови ключами из d2 (`update` перезапишет конфликты).",
        "hint2": "`result = d1.copy(); result.update(d2); return result`.",
        "hint3": "В Python 3.9+: `return d1 | d2`. В Python 3.5+: `return {**d1, **d2}`. Оба варианта дают d2 приоритет при конфликте ключей.",
        "solution_text": (
            "`{**d1, **d2}` — распаковка словарей. При дублировании ключей побеждает последний (d2).\n"
            "⏱ Сложность: O(n+m) по времени и памяти."
        ),
        "failing_test": "d1 = {'a': 1}, d2 = {'a': 2} → ожидается {'a': 2}. d2 должен иметь приоритет.",
        "time_complexity": "O(n+m)",
        "space_complexity": "O(n+m)",
    },
    {
        "title": "Подсчёт строк в тексте",
        "level": "intern",
        "description": (
            "Дана строка `text`, представляющая многострочный текст. "
            "Верни количество непустых строк в нём."
        ),
        "examples": [
            {"input": 'text = "line1\\nline2\\nline3"', "output": "3"},
            {"input": 'text = "line1\\n\\nline3"', "output": "2", "explanation": "Пустая строка не считается"},
            {"input": 'text = ""', "output": "0"},
        ],
        "constraints": ["0 <= text.length <= 10⁵"],
        "hint1": "Разбей текст на строки через `splitlines()`. Отфильтруй пустые.",
        "hint2": "`len([line for line in text.splitlines() if line.strip()])`.",
        "hint3": "Полная реализация: `return sum(1 for line in text.splitlines() if line.strip())`. `strip()` убирает пробелы — строка из одних пробелов тоже считается пустой.",
        "solution_text": (
            "splitlines() разбивает по переносам строк. Фильтруем непустые (strip() != '').\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": 'text = "\\n\\n\\n" → ожидается 0. Три строки, но все пустые.',
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Замена подстроки",
        "level": "intern",
        "description": (
            "Даны строки `s`, `old` и `new`. Верни строку `s`, в которой все вхождения "
            "подстроки `old` заменены на `new`. Не используй метод `replace()`."
        ),
        "examples": [
            {"input": 's = "hello world", old = "world", new = "Python"', "output": '"hello Python"'},
            {"input": 's = "aaa", old = "a", new = "b"', "output": '"bbb"'},
            {"input": 's = "abc", old = "x", new = "y"', "output": '"abc"'},
        ],
        "constraints": ["1 <= s.length <= 10⁴", "1 <= old.length <= 100"],
        "hint1": "Найди первое вхождение `old` в `s`, замени, продолжи поиск после замены.",
        "hint2": "Используй `s.find(old)` для поиска. При нахождении: `s = s[:idx] + new + s[idx+len(old):]`, продолжай с позиции `idx + len(new)`.",
        "hint3": "Через split/join: `return new.join(s.split(old))`. `s.split(old)` разбивает по разделителю, `new.join(...)` склеивает с заменой.",
        "solution_text": (
            "`new.join(s.split(old))` — split разбивает по old, join склеивает с new.\n"
            "⏱ Сложность: O(n·m) по времени, O(n) по памяти."
        ),
        "failing_test": 's = "aaaa", old = "aa", new = "b" → ожидается "bb". split("aa") = ["","",""] → join → "bb".',
        "time_complexity": "O(n·m)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Проверка делимости",
        "level": "intern",
        "description": (
            "Дан список целых чисел `nums` и делитель `k`. "
            "Верни список чисел из `nums`, которые делятся на `k` без остатка, в исходном порядке."
        ),
        "examples": [
            {"input": "nums = [1, 2, 3, 4, 6, 8], k = 2", "output": "[2, 4, 6, 8]"},
            {"input": "nums = [5, 10, 15], k = 5", "output": "[5, 10, 15]"},
            {"input": "nums = [1, 3, 7], k = 2", "output": "[]"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴", "1 <= k <= 10⁶"],
        "hint1": "Используй `n % k == 0` для проверки делимости.",
        "hint2": "Отфильтруй элементы с помощью list comprehension или filter().",
        "hint3": "Полная реализация: `return [n for n in nums if n % k == 0]`. Или: `list(filter(lambda n: n % k == 0, nums))`.",
        "solution_text": (
            "`[n for n in nums if n % k == 0]` — list comprehension с фильтрацией по остатку.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [0, 5], k = 5 → ожидается [0, 5]. 0 делится на любое k (0 % k == 0).",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Сумма чётных чисел Фибоначчи",
        "level": "intern",
        "description": (
            "Дано число `n`. Верни сумму всех чётных чисел Фибоначчи, не превышающих `n`.\n"
            "Последовательность Фибоначчи: 1, 1, 2, 3, 5, 8, 13, 21, 34, ..."
        ),
        "examples": [
            {"input": "n = 10", "output": "10", "explanation": "2 + 8 = 10"},
            {"input": "n = 34", "output": "44", "explanation": "2 + 8 + 34 = 44"},
            {"input": "n = 1", "output": "0"},
        ],
        "constraints": ["1 <= n <= 10⁹"],
        "hint1": "Генерируй числа Фибоначчи до n. Суммируй чётные.",
        "hint2": "Инициализируй a=1, b=1. В цикле: если b чётное — добавляй к сумме. Шаг: a,b = b, a+b.",
        "hint3": "Полная реализация: `a, b = 1, 1; total = 0; while b <= n: if b % 2 == 0: total += b; a, b = b, a+b; return total`. Каждое третье число Фибоначчи чётное.",
        "solution_text": (
            "Итерируй пары Фибоначчи, суммируй чётные. Каждое третье число Фиб. чётное (1,1,2,3,5,8,...).\n"
            "⏱ Сложность: O(log n)."
        ),
        "failing_test": "n = 1 → ожидается 0. Числа Фибоначчи ≤ 1: [1,1]. Ни одного чётного → 0.",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Наибольший общий делитель",
        "level": "intern",
        "description": (
            "Даны два натуральных числа `a` и `b`. Найди их наибольший общий делитель (НОД) "
            "без использования встроенной функции `math.gcd`."
        ),
        "examples": [
            {"input": "a = 12, b = 8", "output": "4"},
            {"input": "a = 7, b = 5", "output": "1"},
            {"input": "a = 100, b = 75", "output": "25"},
        ],
        "constraints": ["1 <= a, b <= 10⁹"],
        "hint1": "Используй алгоритм Евклида: НОД(a, b) = НОД(b, a % b). Базовый случай: НОД(a, 0) = a.",
        "hint2": "Итеративно: `while b: a, b = b, a % b; return a`.",
        "hint3": "Полная реализация: `while b != 0: a, b = b, a % b; return a`. Рекурсивно: `def gcd(a, b): return a if b == 0 else gcd(b, a % b)`. Алгоритм Евклида за O(log min(a,b)).",
        "solution_text": (
            "Алгоритм Евклида: `while b: a, b = b, a % b`. Когда b=0, a содержит НОД.\n"
            "⏱ Сложность: O(log min(a, b)) по времени, O(1) по памяти."
        ),
        "failing_test": "a = 1, b = 1 → ожидается 1. НОД(1,1) = 1. Алгоритм: 1%1=0 → a=1.",
        "time_complexity": "O(log min(a, b))",
        "space_complexity": "O(1)",
    },
    {
        "title": "Матрица: диагональная сумма",
        "level": "intern",
        "description": (
            "Дана квадратная матрица `matrix` n×n. "
            "Верни сумму элементов главной диагонали (от [0][0] до [n-1][n-1])."
        ),
        "examples": [
            {"input": "matrix = [[1,2,3],[4,5,6],[7,8,9]]", "output": "15", "explanation": "1+5+9 = 15"},
            {"input": "matrix = [[1,2],[3,4]]", "output": "5"},
            {"input": "matrix = [[7]]", "output": "7"},
        ],
        "constraints": ["1 <= n <= 100", "-10⁴ <= matrix[i][j] <= 10⁴"],
        "hint1": "Главная диагональ: элементы [i][i] для i от 0 до n-1.",
        "hint2": "Суммируй `matrix[i][i]` в цикле `for i in range(len(matrix))`.",
        "hint3": "Полная реализация: `return sum(matrix[i][i] for i in range(len(matrix)))`. Для антидиагонали: `matrix[i][n-1-i]`.",
        "solution_text": (
            "`sum(matrix[i][i] for i in range(n))` — главная диагональ имеет одинаковые индексы строки и столбца.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "matrix = [[1]] → ожидается 1. Матрица 1×1, единственный элемент — диагональ.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Подсчёт уникальных элементов",
        "level": "intern",
        "description": (
            "Дан список `nums`. Верни количество уникальных элементов в нём."
        ),
        "examples": [
            {"input": "nums = [1, 2, 2, 3, 3, 3]", "output": "3"},
            {"input": "nums = [5, 5, 5]", "output": "1"},
            {"input": "nums = [1, 2, 3]", "output": "3"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴"],
        "hint1": "Преобразуй список в множество — оно хранит только уникальные элементы.",
        "hint2": "`len(set(nums))` даёт количество уникальных элементов.",
        "hint3": "Однострочно: `return len(set(nums))`. Альтернативно через словарь: `return len(dict.fromkeys(nums))`.",
        "solution_text": (
            "`len(set(nums))` — set автоматически убирает дубликаты.\n"
            "⏱ Сложность: O(n) по времени и памяти."
        ),
        "failing_test": "nums = [1] → ожидается 1. Один элемент — одно уникальное значение.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Частота элементов",
        "level": "intern",
        "description": (
            "Дан список `nums`. Верни словарь, где ключи — элементы списка, "
            "а значения — их частота (количество вхождений)."
        ),
        "examples": [
            {"input": "nums = [1, 2, 2, 3, 3, 3]", "output": "{1: 1, 2: 2, 3: 3}"},
            {"input": "nums = ['a', 'b', 'a']", "output": "{'a': 2, 'b': 1}"},
            {"input": "nums = [5]", "output": "{5: 1}"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴"],
        "hint1": "Пройди по списку, наращивай счётчик для каждого ключа в словаре.",
        "hint2": "`freq = {}; for x in nums: freq[x] = freq.get(x, 0) + 1`.",
        "hint3": "Через collections: `from collections import Counter; return dict(Counter(nums))`. Вручную: `freq = {}; [freq.update({x: freq.get(x, 0)+1}) for x in nums]; return freq`.",
        "solution_text": (
            "Словарь с Counter или `dict.get(key, 0) + 1`. Counter — самый читаемый способ.\n"
            "⏱ Сложность: O(n) по времени и памяти."
        ),
        "failing_test": "nums = [1, 1, 1] → ожидается {1: 3}, не {1: 1}. Счётчик должен накапливаться.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Пересечение двух множеств",
        "level": "intern",
        "description": (
            "Даны два списка `a` и `b`. Верни список уникальных элементов, "
            "присутствующих в обоих списках. Порядок в результате не важен."
        ),
        "examples": [
            {"input": "a = [1,2,3,4], b = [3,4,5,6]", "output": "[3, 4]"},
            {"input": "a = [1,2,3], b = [4,5,6]", "output": "[]"},
            {"input": "a = [1,1,2], b = [1,2,2]", "output": "[1, 2]"},
        ],
        "constraints": ["1 <= a.length, b.length <= 10⁴"],
        "hint1": "Преобразуй оба списка в множества и используй операцию пересечения `&`.",
        "hint2": "`set(a) & set(b)` даёт пересечение. Конвертируй в список.",
        "hint3": "Полная реализация: `return list(set(a) & set(b))`. Или: `return list(set(a).intersection(set(b)))`. Уникальность гарантирована set.",
        "solution_text": (
            "`list(set(a) & set(b))` — пересечение множеств за O(min(n,m)).\n"
            "⏱ Сложность: O(n+m) по времени, O(n+m) по памяти."
        ),
        "failing_test": "a = [1,1,1], b = [1,1,1] → ожидается [1]. Результат должен содержать только уникальные элементы.",
        "time_complexity": "O(n+m)",
        "space_complexity": "O(n+m)",
    },
    {
        "title": "Числа в диапазоне",
        "level": "intern",
        "description": (
            "Дан список чисел `nums`, а также границы `lo` и `hi`. "
            "Верни список чисел из `nums`, попадающих в диапазон [lo, hi] включительно."
        ),
        "examples": [
            {"input": "nums = [1,5,3,8,2], lo = 2, hi = 5", "output": "[5, 3, 2]"},
            {"input": "nums = [10, 20, 30], lo = 5, hi = 25", "output": "[10, 20]"},
            {"input": "nums = [1, 2, 3], lo = 5, hi = 10", "output": "[]"},
        ],
        "constraints": ["-10⁶ <= lo <= hi <= 10⁶", "1 <= nums.length <= 10⁴"],
        "hint1": "Фильтруй элементы, проверяя двойное неравенство `lo <= num <= hi`.",
        "hint2": "Используй list comprehension: `[n for n in nums if lo <= n <= hi]`.",
        "hint3": "Полная реализация: `return [n for n in nums if lo <= n <= hi]`. Python позволяет цепочки сравнений `lo <= n <= hi`, что читается как математика.",
        "solution_text": (
            "`[n for n in nums if lo <= n <= hi]` — Python поддерживает цепочки сравнений.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [5], lo = 5, hi = 5 → ожидается [5]. Границы включительно.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },

    # ─────────────────── JUNIOR — ещё 30 ───────────────────
    {
        "title": "Поиск пика",
        "level": "junior",
        "description": (
            "Дан массив `nums`. Элемент называется пиком, если он строго больше соседей. "
            "Для крайних элементов сосед только один. Верни индекс любого пика."
        ),
        "examples": [
            {"input": "nums = [1, 2, 3, 1]", "output": "2"},
            {"input": "nums = [1, 2, 1, 3, 5, 6, 4]", "output": "5"},
            {"input": "nums = [1]", "output": "0"},
        ],
        "constraints": ["1 <= nums.length <= 10⁵", "nums[i] != nums[i+1]"],
        "hint1": "Линейный поиск: пройди и верни первый i где nums[i] > обоих соседей.",
        "hint2": "Бинарный поиск: mid — если nums[mid] < nums[mid+1], пик правее. Иначе — левее или mid.",
        "hint3": "Бинарный поиск: `lo, hi = 0, len(nums)-1; while lo < hi: mid=(lo+hi)//2; if nums[mid]<nums[mid+1]: lo=mid+1; else: hi=mid; return lo`. O(log n).",
        "solution_text": (
            "Бинарный поиск: если mid < mid+1, пик гарантированно правее. Сужай диапазон.\n"
            "⏱ Сложность: O(log n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [3, 2, 1] → ожидается 0 (убывающий массив, пик — левый край).",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Одиночное число (XOR)",
        "level": "junior",
        "description": (
            "Дан массив `nums`, где каждый элемент встречается дважды, кроме одного. "
            "Найди и верни тот единственный элемент. Реши за O(n) и O(1) памяти."
        ),
        "examples": [
            {"input": "nums = [2, 2, 1]", "output": "1"},
            {"input": "nums = [4, 1, 2, 1, 2]", "output": "4"},
            {"input": "nums = [1]", "output": "1"},
        ],
        "constraints": ["1 <= nums.length <= 3×10⁴", "каждый элемент кроме одного встречается ровно 2 раза"],
        "hint1": "XOR двух одинаковых числел даёт 0. XOR числа с 0 даёт само число.",
        "hint2": "Применяй XOR ко всем элементам: парные числа обнулятся, останется одиночное.",
        "hint3": "Полная реализация: `result = 0; for n in nums: result ^= n; return result`. Однострочно: `from functools import reduce; return reduce(lambda a,b: a^b, nums)`.",
        "solution_text": (
            "`result = 0; for n in nums: result ^= n` — XOR всех элементов. Парные дают 0, одиночное остаётся.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [1] → ожидается 1. Один элемент XOR 0 = 1.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Слияние интервалов",
        "level": "junior",
        "description": (
            "Дан список интервалов `intervals = [[start, end], ...]`. "
            "Объедини перекрывающиеся интервалы и верни результат."
        ),
        "examples": [
            {"input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]"},
            {"input": "intervals = [[1,4],[4,5]]", "output": "[[1,5]]"},
            {"input": "intervals = [[1,4]]", "output": "[[1,4]]"},
        ],
        "constraints": ["1 <= intervals.length <= 10⁴", "intervals[i].length == 2"],
        "hint1": "Отсортируй интервалы по началу. Затем пройди и сливай перекрывающиеся.",
        "hint2": "Сохраняй `current` интервал. Если следующий начинается до конца current — обновляй конец: `current[1] = max(current[1], next[1])`.",
        "hint3": "Полная реализация: `intervals.sort(); merged = [intervals[0]]; for s,e in intervals[1:]: if s <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], e); else: merged.append([s,e]); return merged`.",
        "solution_text": (
            "Сортируй по старту. Итерируй: если текущий интервал перекрывается с последним в результате — расширяй его. Иначе добавляй новый.\n"
            "⏱ Сложность: O(n log n) по времени, O(n) по памяти."
        ),
        "failing_test": "intervals = [[1,4],[2,3]] → ожидается [[1,4]]. Интервал [2,3] полностью внутри [1,4].",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Поворот массива",
        "level": "junior",
        "description": (
            "Дан массив `nums` и число `k`. Сдвинь массив вправо на `k` позиций. "
            "Элементы, выходящие за правый конец, переходят в начало."
        ),
        "examples": [
            {"input": "nums = [1,2,3,4,5,6,7], k = 3", "output": "[5,6,7,1,2,3,4]"},
            {"input": "nums = [-1,-100,3,99], k = 2", "output": "[3,99,-1,-100]"},
        ],
        "constraints": ["1 <= nums.length <= 10⁵", "0 <= k <= 10⁵"],
        "hint1": "k может быть больше длины массива — используй `k = k % len(nums)`.",
        "hint2": "Через срез: `nums[:] = nums[-k:] + nums[:-k]`.",
        "hint3": "Через три разворота (O(1) память): переверни весь массив, переверни первые k, переверни остальные. Пример: [1,2,3,4,5], k=2 → [5,4,3,2,1] → [4,5,3,2,1] → [4,5,1,2,3].",
        "solution_text": (
            "Три разворота: `reverse(0, n-1); reverse(0, k-1); reverse(k, n-1)`. O(n) время, O(1) память.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [1,2], k = 3 → k % 2 = 1 → ожидается [2,1]. Обязательно взять k по модулю.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Первый уникальный символ",
        "level": "junior",
        "description": (
            "Дана строка `s`. Найди первый символ, который встречается в строке только один раз, "
            "и верни его индекс. Если такого нет — верни -1."
        ),
        "examples": [
            {"input": 's = "leetcode"', "output": "0"},
            {"input": 's = "loveleetcode"', "output": "2"},
            {"input": 's = "aabb"', "output": "-1"},
        ],
        "constraints": ["1 <= s.length <= 10⁵", "s состоит только из строчных латинских букв"],
        "hint1": "Сначала подсчитай частоту каждого символа, затем найди первый с частотой 1.",
        "hint2": "Используй `Counter(s)` или словарь для подсчёта. Затем пройди по строке и найди первый с count=1.",
        "hint3": "Полная реализация: `from collections import Counter; count = Counter(s); for i, c in enumerate(s): if count[c] == 1: return i; return -1`.",
        "solution_text": (
            "Counter для подсчёта + проход по строке для нахождения первого символа с count==1.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти (алфавит фиксированного размера)."
        ),
        "failing_test": 's = "aabb" → ожидается -1. Все символы встречаются дважды.',
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Середина связного списка",
        "level": "junior",
        "description": (
            "Дан связный список. Верни узел, являющийся серединой списка. "
            "Если список чётной длины — верни второй из двух средних узлов."
        ),
        "examples": [
            {"input": "head = [1,2,3,4,5]", "output": "узел 3"},
            {"input": "head = [1,2,3,4,5,6]", "output": "узел 4", "explanation": "два средних — 3 и 4, верни второй"},
        ],
        "constraints": ["1 <= nodes.length <= 100"],
        "hint1": "Метод черепахи и зайца: медленный указатель двигается на 1, быстрый на 2.",
        "hint2": "Когда быстрый достигает конца — медленный указывает на середину.",
        "hint3": "Полная реализация: `slow = fast = head; while fast and fast.next: slow = slow.next; fast = fast.next.next; return slow`. Для чётного числа узлов вернётся второй средний — именно то, что нужно.",
        "solution_text": (
            "Два указателя (медленный и быстрый). Быстрый идёт вдвое быстрее. Когда заканчивается — медленный на середине.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "head = [1,2,3,4] → ожидается узел 3 (второй средний). fast проходит 4 шага, slow — 2.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Максимальная глубина бинарного дерева",
        "level": "junior",
        "description": (
            "Дано бинарное дерево. Верни его максимальную глубину (количество узлов на самом длинном пути от корня до листа)."
        ),
        "examples": [
            {"input": "root = [3,9,20,null,null,15,7]", "output": "3"},
            {"input": "root = [1,null,2]", "output": "2"},
            {"input": "root = []", "output": "0"},
        ],
        "constraints": ["0 <= nodes.count <= 10⁴"],
        "hint1": "Рекурсия: глубина = 1 + max(глубина_левого, глубина_правого).",
        "hint2": "Базовый случай: если node is None — вернуть 0.",
        "hint3": "Полная реализация: `def maxDepth(root): if not root: return 0; return 1 + max(maxDepth(root.left), maxDepth(root.right))`. BFS: поуровневый обход, счётчик уровней.",
        "solution_text": (
            "Рекурсивно: `if not root: return 0; return 1 + max(maxDepth(root.left), maxDepth(root.right))`.\n"
            "⏱ Сложность: O(n) по времени, O(h) по памяти (h — высота дерева)."
        ),
        "failing_test": "root = [] → ожидается 0. Пустое дерево имеет глубину 0.",
        "time_complexity": "O(n)",
        "space_complexity": "O(h)",
    },
    {
        "title": "Симметричное дерево",
        "level": "junior",
        "description": (
            "Дано бинарное дерево. Проверь, является ли оно зеркально симметричным "
            "(симметрично относительно своего центра). Верни True/False."
        ),
        "examples": [
            {"input": "root = [1,2,2,3,4,4,3]", "output": "True"},
            {"input": "root = [1,2,2,null,3,null,3]", "output": "False"},
        ],
        "constraints": ["1 <= nodes.count <= 1000"],
        "hint1": "Напиши вспомогательную функцию `isMirror(left, right)`, которая сравнивает два поддерева.",
        "hint2": "Дерева зеркальны, если: их корни равны, левое поддерево left зеркально правому поддереву right.",
        "hint3": "Рекурсивно: `def isMirror(l, r): if not l and not r: return True; if not l or not r: return False; return l.val==r.val and isMirror(l.left,r.right) and isMirror(l.right,r.left)`.",
        "solution_text": (
            "Вспомогательная функция isMirror(left, right): сравнивает значения и рекурсивно проверяет внешние и внутренние пары.\n"
            "⏱ Сложность: O(n) по времени, O(h) по памяти."
        ),
        "failing_test": "root = [1,2,2,null,3,null,3] → ожидается False. Правые дочерние не симметричны.",
        "time_complexity": "O(n)",
        "space_complexity": "O(h)",
    },
    {
        "title": "Число в римскую запись",
        "level": "junior",
        "description": (
            "Дано целое число `num` (1 ≤ num ≤ 3999). Преобразуй его в римскую запись."
        ),
        "examples": [
            {"input": "num = 3", "output": '"III"'},
            {"input": "num = 58", "output": '"LVIII"', "explanation": "L=50, V=5, III=3"},
            {"input": "num = 1994", "output": '"MCMXCIV"'},
        ],
        "constraints": ["1 <= num <= 3999"],
        "hint1": "Создай таблицу пар (значение, символ) от большего к меньшему, включая вычитательные формы (IV, IX, XL, XC, CD, CM).",
        "hint2": "Жадный алгоритм: пока num > 0, находи наибольшее значение ≤ num, добавляй символ, вычитай значение.",
        "hint3": "Таблица: `vals = [1000,900,500,400,100,90,50,40,10,9,5,4,1]; syms = ['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I']`. Цикл: `for v,s in zip(vals,syms): while num>=v: result+=s; num-=v`.",
        "solution_text": (
            "Жадный алгоритм с таблицей 13 пар (включая вычитательные). Берёт максимально возможный символ каждый раз.\n"
            "⏱ Сложность: O(1) — диапазон фиксирован до 3999."
        ),
        "failing_test": "num = 4 → ожидается 'IV', не 'IIII'. Вычитательная форма обязательна.",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Движение нулей в конец",
        "level": "junior",
        "description": (
            "Дан массив `nums`. Перемести все нули в конец массива, "
            "сохранив относительный порядок ненулевых элементов. Модифицируй на месте."
        ),
        "examples": [
            {"input": "nums = [0,1,0,3,12]", "output": "[1,3,12,0,0]"},
            {"input": "nums = [0]", "output": "[0]"},
            {"input": "nums = [1,0,0,2]", "output": "[1,2,0,0]"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴"],
        "hint1": "Используй указатель `write_pos` для следующей позиции записи ненулевого элемента.",
        "hint2": "Пройди массив: для каждого ненулевого элемента запиши его в позицию write_pos, инкрементируй write_pos. Затем заполни оставшийся хвост нулями.",
        "hint3": "Полная реализация: `write = 0; for n in nums: if n != 0: nums[write] = n; write += 1; while write < len(nums): nums[write] = 0; write += 1`.",
        "solution_text": (
            "Указатель write_pos: переписываем ненулевые, потом заполняем хвост нулями. O(n), O(1).\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [0,0,1] → ожидается [1,0,0]. Нули должны быть в конце, не в начале.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Три суммы (3Sum)",
        "level": "junior",
        "description": (
            "Дан массив `nums`. Найди все уникальные тройки [a, b, c] такие, что a + b + c = 0. "
            "Тройки не должны повторяться."
        ),
        "examples": [
            {"input": "nums = [-1,0,1,2,-1,-4]", "output": "[[-1,-1,2],[-1,0,1]]"},
            {"input": "nums = [0,1,1]", "output": "[]"},
            {"input": "nums = [0,0,0]", "output": "[[0,0,0]]"},
        ],
        "constraints": ["3 <= nums.length <= 3000", "-10⁵ <= nums[i] <= 10⁵"],
        "hint1": "Отсортируй массив. Зафиксируй первый элемент, используй два указателя для поиска пары.",
        "hint2": "Для каждого i: left=i+1, right=n-1. Если сумма > 0 — right--, < 0 — left++, = 0 — сохрани тройку, двигай оба, пропуская дубликаты.",
        "hint3": "Пропуск дубликатов: `if i > 0 and nums[i] == nums[i-1]: continue` (для фиксированного). После нахождения тройки: `while left<right and nums[left]==nums[left+1]: left++` и аналогично для right.",
        "solution_text": (
            "Сортировка + двойные указатели. Для каждого фиксированного элемента — сжимающееся окно. Дубликаты пропускаем явно.\n"
            "⏱ Сложность: O(n²) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [-2,0,0,2,2] → ожидается [[-2,0,2]] (без дубликатов). Пропуск дубликатов обязателен.",
        "time_complexity": "O(n²)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Прыжки по массиву (Jump Game)",
        "level": "junior",
        "description": (
            "Дан массив `nums`, где nums[i] — максимальная длина прыжка с позиции i. "
            "Начинаешь с позиции 0. Можно ли добраться до последнего индекса?"
        ),
        "examples": [
            {"input": "nums = [2,3,1,1,4]", "output": "True"},
            {"input": "nums = [3,2,1,0,4]", "output": "False"},
            {"input": "nums = [0]", "output": "True"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴", "0 <= nums[i] <= 10⁵"],
        "hint1": "Отслеживай максимально достижимую позицию `max_reach`. Если текущая позиция > max_reach — до конца не добраться.",
        "hint2": "Жадный: `max_reach = 0; for i in range(len(nums)): if i > max_reach: return False; max_reach = max(max_reach, i + nums[i]); return True`.",
        "hint3": "Полная реализация: `max_reach = 0; for i, jump in enumerate(nums): if i > max_reach: return False; max_reach = max(max_reach, i+jump); return True`.",
        "solution_text": (
            "Жадный: обновляй max_reach = max(max_reach, i+nums[i]). Если i > max_reach — застряли.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [3,2,1,0,4] → ожидается False. После позиции 3 max_reach = 3, позиция 4 недостижима.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Наидлиннейший общий префикс",
        "level": "junior",
        "description": (
            "Дан массив строк `strs`. Найди наидлиннейший общий префикс среди всех строк. "
            "Если его нет — верни пустую строку."
        ),
        "examples": [
            {"input": 'strs = ["flower","flow","flight"]', "output": '"fl"'},
            {"input": 'strs = ["dog","racecar","car"]', "output": '""'},
            {"input": 'strs = ["interspecies","interstellar","interstate"]', "output": '"inters"'},
        ],
        "constraints": ["1 <= strs.length <= 200", "0 <= strs[i].length <= 200"],
        "hint1": "Начни с первой строки как кандидата на префикс. Сокращай его пока он не станет префиксом всех остальных строк.",
        "hint2": "Для каждой строки: пока `not s.startswith(prefix)` — убирай последний символ из prefix.",
        "hint3": "Полная реализация: `prefix = strs[0]; for s in strs[1:]: while not s.startswith(prefix): prefix = prefix[:-1]; if not prefix: return ''; return prefix`.",
        "solution_text": (
            "Сокращай первую строку пока она не станет префиксом каждой следующей. Startswith проверяет наличие.\n"
            "⏱ Сложность: O(S) где S — суммарная длина всех строк."
        ),
        "failing_test": 'strs = ["","b"] → ожидается "". Пустая строка — префикс любой строки, но сразу возвращаем "".',
        "time_complexity": "O(S)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Расстояние Хэмминга",
        "level": "junior",
        "description": (
            "Даны два целых числа `x` и `y`. Верни расстояние Хэмминга — "
            "количество позиций, в которых соответствующие биты различаются."
        ),
        "examples": [
            {"input": "x = 1, y = 4", "output": "2", "explanation": "1=0001, 4=0100, различаются 2 бита"},
            {"input": "x = 3, y = 1", "output": "1"},
        ],
        "constraints": ["0 <= x, y <= 2³¹-1"],
        "hint1": "XOR выделяет биты, в которых числа различаются. Подсчитай единицы в XOR.",
        "hint2": "`xor = x ^ y`. Подсчитай количество единичных битов в xor.",
        "hint3": "Полная реализация: `return bin(x ^ y).count('1')`. Метод bin() возвращает строку вроде '0b101'. `.count('1')` считает единицы.",
        "solution_text": (
            "`bin(x ^ y).count('1')` — XOR выделяет различия, затем считаем единичные биты.\n"
            "⏱ Сложность: O(1) — максимум 32 бита."
        ),
        "failing_test": "x = 0, y = 0 → ожидается 0. XOR = 0, нет единичных битов.",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Обнаружение цикла в связном списке",
        "level": "junior",
        "description": (
            "Дан связный список. Определи, содержит ли он цикл. Верни True/False."
        ),
        "examples": [
            {"input": "head = [3,2,0,-4], pos = 1", "output": "True", "explanation": "хвост указывает на узел 1"},
            {"input": "head = [1,2], pos = 0", "output": "True"},
            {"input": "head = [1], pos = -1", "output": "False"},
        ],
        "constraints": ["0 <= nodes.count <= 10⁴"],
        "hint1": "Используй два указателя: медленный (1 шаг) и быстрый (2 шага). Если встретятся — цикл есть.",
        "hint2": "Алгоритм Флойда: `slow = fast = head; while fast and fast.next: slow = slow.next; fast = fast.next.next; if slow == fast: return True; return False`.",
        "hint3": "Полная реализация: `slow = fast = head; while fast and fast.next: slow=slow.next; fast=fast.next.next; if slow is fast: return True; return False`.",
        "solution_text": (
            "Алгоритм черепахи и зайца Флойда. Если цикл есть — они обязательно встретятся.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "head = [1], pos = -1 → ожидается False. Один узел без цикла.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Реализация стека с поддержкой min()",
        "level": "junior",
        "description": (
            "Реализуй стек, поддерживающий операции `push(val)`, `pop()`, `top()` и `getMin()`. "
            "Все операции должны выполняться за O(1)."
        ),
        "examples": [
            {"input": "push(-2), push(0), push(-3), getMin() → pop(), top(), getMin()", "output": "-3, 0, -2"},
        ],
        "constraints": ["pop/top/getMin вызываются только для непустого стека"],
        "hint1": "Храни отдельный вспомогательный стек минимумов. При push — добавляй в min_stack минимум из (val, текущий_мин).",
        "hint2": "При pop — также pop из min_stack. getMin() возвращает вершину min_stack.",
        "hint3": "Реализация: `self.stack=[]; self.min_stack=[]; push: self.stack.append(val); self.min_stack.append(min(val, self.min_stack[-1] if self.min_stack else val)); pop: self.stack.pop(); self.min_stack.pop(); getMin: return self.min_stack[-1]`.",
        "solution_text": (
            "Параллельный стек минимумов. При каждом push кладём min(val, current_min). При pop — убираем из обоих стеков.\n"
            "⏱ Сложность: O(1) для всех операций."
        ),
        "failing_test": "push(5), push(3), push(7), getMin() → ожидается 3. 7 не является минимумом.",
        "time_complexity": "O(1)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Подмножества (Subsets)",
        "level": "junior",
        "description": (
            "Дан массив уникальных целых чисел `nums`. Верни все возможные подмножества (включая пустое)."
        ),
        "examples": [
            {"input": "nums = [1,2,3]", "output": "[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]"},
            {"input": "nums = [0]", "output": "[[],[0]]"},
        ],
        "constraints": ["1 <= nums.length <= 10", "все элементы уникальны"],
        "hint1": "Для n элементов: 2ⁿ подмножеств. Бекслединг или итеративный подход.",
        "hint2": "Итеративно: начни с [[]]. Для каждого нового элемента — добавь его ко всем существующим подмножествам.",
        "hint3": "Итеративно: `result = [[]]; for num in nums: result += [sub + [num] for sub in result]; return result`. Бэктрекинг: рекурсивно добавляй/не добавляй каждый элемент.",
        "solution_text": (
            "Итеративно: для каждого элемента удваиваем количество подмножеств, добавляя элемент ко всем существующим.\n"
            "⏱ Сложность: O(2ⁿ) по времени и памяти."
        ),
        "failing_test": "nums = [1,2] → ожидается [[], [1], [2], [1,2]]. Пустое подмножество обязательно.",
        "time_complexity": "O(2ⁿ)",
        "space_complexity": "O(2ⁿ)",
    },
    {
        "title": "Дерево: путь к заданной сумме",
        "level": "junior",
        "description": (
            "Дано бинарное дерево и целое `targetSum`. Существует ли путь от корня до листа, "
            "сумма узлов которого равна targetSum? Верни True/False."
        ),
        "examples": [
            {"input": "root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22", "output": "True"},
            {"input": "root = [1,2,3], targetSum = 5", "output": "False"},
            {"input": "root = [], targetSum = 0", "output": "False"},
        ],
        "constraints": ["0 <= nodes.count <= 5000", "-1000 <= Node.val, targetSum <= 1000"],
        "hint1": "Рекурсия: вычитай значение текущего узла из targetSum. В листе проверяй остаток = 0.",
        "hint2": "Базовый случай: если node is None → False. Если лист (нет детей) → val == targetSum.",
        "hint3": "Полная реализация: `def hasPathSum(root, target): if not root: return False; if not root.left and not root.right: return root.val == target; return hasPathSum(root.left, target-root.val) or hasPathSum(root.right, target-root.val)`.",
        "solution_text": (
            "Рекурсивно уменьшай target. В листе проверяй равенство нулю. DFS по дереву.\n"
            "⏱ Сложность: O(n) по времени, O(h) по памяти."
        ),
        "failing_test": "root = [1,2], targetSum = 1 → ожидается False. Узел 1 не лист, путь до листа суммирует 1+2=3.",
        "time_complexity": "O(n)",
        "space_complexity": "O(h)",
    },
    {
        "title": "Количество единичных битов",
        "level": "junior",
        "description": (
            "Дано беззнаковое целое число `n`. Верни количество единичных битов в его двоичном представлении (вес Хэмминга)."
        ),
        "examples": [
            {"input": "n = 11", "output": "3", "explanation": "11 = 1011₂, три '1'"},
            {"input": "n = 128", "output": "1", "explanation": "128 = 10000000₂"},
            {"input": "n = 4294967293", "output": "31"},
        ],
        "constraints": ["0 <= n < 2³²"],
        "hint1": "Используй `bin(n).count('1')` или побитовые операции.",
        "hint2": "Трюк с `n & (n-1)`: сбрасывает самый правый единичный бит. Повторяй пока n > 0.",
        "hint3": "Через `n & (n-1)`: `count = 0; while n: n &= n-1; count += 1; return count`. Быстрее чем перебор всех битов. Или однострочно: `return bin(n).count('1')`.",
        "solution_text": (
            "`bin(n).count('1')` — просто и читаемо. Или `n &= n-1` в цикле — убирает по одному биту за O(k) где k — количество единиц.\n"
            "⏱ Сложность: O(1) — максимум 32 бита."
        ),
        "failing_test": "n = 0 → ожидается 0. bin(0) = '0b0', count('1') = 0.",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Число провинций (Union-Find)",
        "level": "junior",
        "description": (
            "Дана матрица смежности `isConnected[n][n]`. Два города соединены прямо или транзитивно. "
            "Верни количество провинций (связных компонентов)."
        ),
        "examples": [
            {"input": "isConnected = [[1,1,0],[1,1,0],[0,0,1]]", "output": "2"},
            {"input": "isConnected = [[1,0,0],[0,1,0],[0,0,1]]", "output": "3"},
        ],
        "constraints": ["1 <= n <= 200"],
        "hint1": "DFS/BFS из каждого непосещённого города. Каждый новый старт = новая провинция.",
        "hint2": "Или Union-Find: для каждого ребра (i,j) объединяй компоненты. Ответ = количество уникальных корней.",
        "hint3": "DFS: `visited = [False]*n; provinces = 0; for i in range(n): if not visited[i]: dfs(i, isConnected, visited); provinces += 1; return provinces`. DFS: помечаем всех соседей как посещённых.",
        "solution_text": (
            "DFS из каждого непосещённого узла. Каждый запуск DFS = новая провинция.\n"
            "⏱ Сложность: O(n²) по времени (обход матрицы), O(n) по памяти."
        ),
        "failing_test": "isConnected = [[1]] → ожидается 1. Один город = одна провинция.",
        "time_complexity": "O(n²)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Матрица: спиральный обход",
        "level": "junior",
        "description": (
            "Дана матрица `matrix` размером m×n. Верни все элементы в порядке спирального обхода (по часовой стрелке от внешнего края)."
        ),
        "examples": [
            {"input": "matrix = [[1,2,3],[4,5,6],[7,8,9]]", "output": "[1,2,3,6,9,8,7,4,5]"},
            {"input": "matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]", "output": "[1,2,3,4,8,12,11,10,9,5,6,7]"},
        ],
        "constraints": ["m == matrix.length", "n == matrix[0].length", "1 <= m, n <= 10"],
        "hint1": "Поддерживай четыре границы: top, bottom, left, right. Сужай их после каждого прохода.",
        "hint2": "Обходи: слева-направо по top, сверху-вниз по right, справа-налево по bottom, снизу-вверх по left. Двигай границы.",
        "hint3": "Полная реализация: `top,bottom,left,right=0,m-1,0,n-1; while top<=bottom and left<=right: [добавь row top слева-направо]; top+=1; [добавь col right сверху-вниз]; right-=1; if top<=bottom: [добавь row bottom справа-налево]; bottom-=1; if left<=right: [добавь col left снизу-вверх]; left+=1`.",
        "solution_text": (
            "Четыре границы. Итеративно обходи каждую сторону и сдвигай соответствующую границу.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": "matrix = [[1]] → ожидается [1]. Матрица 1×1.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Наименьший общий предок в BST",
        "level": "junior",
        "description": (
            "Дано двоичное дерево поиска (BST) и два узла `p` и `q`. "
            "Найди их наименьшего общего предка (LCA)."
        ),
        "examples": [
            {"input": "root = [6,2,8,0,4,7,9], p = 2, q = 8", "output": "6"},
            {"input": "root = [6,2,8,0,4,7,9], p = 2, q = 4", "output": "2"},
        ],
        "constraints": ["2 <= nodes.count <= 10⁵", "BST инвариант соблюдён"],
        "hint1": "В BST: если оба узла меньше текущего — иди влево. Оба больше — вправо. Иначе — это LCA.",
        "hint2": "Итеративно: `while root: if p.val < root.val and q.val < root.val: root = root.left; elif p.val > root.val and q.val > root.val: root = root.right; else: return root`.",
        "hint3": "Полная реализация: `node = root; while node: if p.val < node.val and q.val < node.val: node = node.left; elif p.val > node.val and q.val > node.val: node = node.right; else: return node`.",
        "solution_text": (
            "BST свойство позволяет за O(h) итеративно найти LCA. Разделение влево/вправо/текущий.\n"
            "⏱ Сложность: O(h) по времени, O(1) по памяти."
        ),
        "failing_test": "p = q = любой узел → LCA = сам узел. Узел является своим собственным предком.",
        "time_complexity": "O(h)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Реализация очереди через стеки",
        "level": "junior",
        "description": (
            "Реализуй очередь (FIFO) используя только два стека. "
            "Операции: `push(x)`, `pop()`, `peek()`, `empty()`."
        ),
        "examples": [
            {"input": "push(1), push(2), peek() → pop() → empty()", "output": "1, 1, False"},
        ],
        "constraints": ["1 <= x <= 9", "pop/peek вызываются только для непустой очереди"],
        "hint1": "Стек 1 для входящих данных, стек 2 для исходящих. Когда стек 2 пуст — переноси в него весь стек 1.",
        "hint2": "push: s1.append(x). pop: если s2 пуст — перелей s1 в s2. return s2.pop().",
        "hint3": "Полная реализация: `self.in_stack=[]; self.out_stack=[]; push: self.in_stack.append(x); _move: if not self.out_stack: while self.in_stack: self.out_stack.append(self.in_stack.pop()); pop: self._move(); return self.out_stack.pop(); peek: self._move(); return self.out_stack[-1]`.",
        "solution_text": (
            "Два стека: входной и выходной. Ленивый перенос (только когда выходной пуст) даёт амортизированный O(1).\n"
            "⏱ Сложность: O(1) амортизированно."
        ),
        "failing_test": "push(1), push(2), pop() → ожидается 1. Очередь FIFO — первым вышел первый вошедший.",
        "time_complexity": "O(1) амортизированно",
        "space_complexity": "O(n)",
    },
    {
        "title": "Перестановки массива",
        "level": "junior",
        "description": (
            "Дан массив уникальных целых чисел `nums`. Верни все возможные перестановки."
        ),
        "examples": [
            {"input": "nums = [1,2,3]", "output": "[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]"},
            {"input": "nums = [0,1]", "output": "[[0,1],[1,0]]"},
            {"input": "nums = [1]", "output": "[[1]]"},
        ],
        "constraints": ["1 <= nums.length <= 6", "все числа уникальны"],
        "hint1": "Бэктрекинг: на каждом шаге выбирай непомеченный элемент, добавляй в текущую перестановку.",
        "hint2": "Или: для каждой позиции — своп текущего элемента с каждым последующим, рекурсия, своп обратно.",
        "hint3": "Бэктрекинг: `def bt(path, used): if len(path)==len(nums): result.append(path[:]); return; for i,n in enumerate(nums): if used[i]: continue; used[i]=True; path.append(n); bt(path,used); path.pop(); used[i]=False`. Вызови bt([],[False]*n).",
        "solution_text": (
            "Бэктрекинг с флагом used[]. На каждом уровне выбираем любой незадействованный элемент, рекурсируем, откатываемся.\n"
            "⏱ Сложность: O(n! × n) по времени и памяти."
        ),
        "failing_test": "nums = [1,2] → ожидается [[1,2],[2,1]]. Ровно n! перестановок.",
        "time_complexity": "O(n!·n)",
        "space_complexity": "O(n!·n)",
    },
    {
        "title": "Клон графа",
        "level": "junior",
        "description": (
            "Дан связный неориентированный граф. Каждый узел содержит val и список соседей. "
            "Верни глубокую копию (клон) графа."
        ),
        "examples": [
            {"input": "adjList = [[2,4],[1,3],[2,4],[1,3]]", "output": "клон того же графа"},
        ],
        "constraints": ["1 <= nodes.count <= 100", "1 <= Node.val <= 100"],
        "hint1": "Используй словарь `visited` для отображения оригинальных узлов на клонированные (чтобы избежать бесконечной рекурсии).",
        "hint2": "DFS: если узел уже в visited — верни его клон. Иначе создай клон, добавь в visited, рекурсивно клонируй соседей.",
        "hint3": "Полная реализация: `visited = {}; def dfs(node): if node in visited: return visited[node]; clone = Node(node.val); visited[node] = clone; clone.neighbors = [dfs(n) for n in node.neighbors]; return clone; return dfs(node)`.",
        "solution_text": (
            "DFS + словарь visited. При первом посещении создаём клон и сразу кладём в словарь (до обработки соседей — важно для циклов).\n"
            "⏱ Сложность: O(V+E) по времени и памяти."
        ),
        "failing_test": "Граф с циклом: [1→2→1]. Без memoization уйдём в бесконечную рекурсию.",
        "time_complexity": "O(V+E)",
        "space_complexity": "O(V)",
    },
    {
        "title": "Минимальный путь в сетке",
        "level": "junior",
        "description": (
            "Дана сетка `grid` размером m×n с числами. Найди путь от верхнего левого угла [0][0] "
            "до нижнего правого [m-1][n-1] с минимальной суммой. Двигаться можно только вправо или вниз."
        ),
        "examples": [
            {"input": "grid = [[1,3,1],[1,5,1],[4,2,1]]", "output": "7", "explanation": "1→3→1→1→1 = 7"},
            {"input": "grid = [[1,2],[1,1]]", "output": "3"},
        ],
        "constraints": ["1 <= m, n <= 200", "0 <= grid[i][j] <= 200"],
        "hint1": "Динамическое программирование: dp[i][j] — минимальная стоимость пути до [i][j].",
        "hint2": "dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]). Граничные условия: первая строка и первый столбец заполняются напрямую.",
        "hint3": "Полная реализация: `m,n=len(grid),len(grid[0]); dp=[[0]*n for _ in range(m)]; dp[0][0]=grid[0][0]; for i in range(1,m): dp[i][0]=dp[i-1][0]+grid[i][0]; for j in range(1,n): dp[0][j]=dp[0][j-1]+grid[0][j]; for i in range(1,m): for j in range(1,n): dp[i][j]=grid[i][j]+min(dp[i-1][j],dp[i][j-1]); return dp[-1][-1]`.",
        "solution_text": (
            "DP: dp[i][j] = grid[i][j] + min(сверху, слева). Заполняй слева направо, сверху вниз.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": "grid = [[1]] → ожидается 1. Один элемент — путь из него самого.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Лестница минимальных прыжков",
        "level": "junior",
        "description": (
            "Дан массив `nums`, где nums[i] — максимальный прыжок с позиции i. "
            "Верни минимальное количество прыжков для достижения последней позиции."
        ),
        "examples": [
            {"input": "nums = [2,3,1,1,4]", "output": "2", "explanation": "0→1→4"},
            {"input": "nums = [2,3,0,1,4]", "output": "2"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴", "0 <= nums[i] <= 1000"],
        "hint1": "Жадный подход: отслеживай `current_end` (конец текущего прыжка) и `farthest` (максимально достижимая позиция).",
        "hint2": "Когда достигаем current_end — делаем прыжок, current_end = farthest.",
        "hint3": "Полная реализация: `jumps=0; current_end=0; farthest=0; for i in range(len(nums)-1): farthest=max(farthest, i+nums[i]); if i==current_end: jumps+=1; current_end=farthest; if current_end>=len(nums)-1: break; return jumps`.",
        "solution_text": (
            "Жадный: `farthest` — максимум достижимого. При достижении `current_end` — делаем прыжок и расширяем горизонт.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [1] → ожидается 0. Уже на последней позиции, прыжков не нужно.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Уникальные пути в сетке",
        "level": "junior",
        "description": (
            "Дана сетка m×n. Робот начинает в верхнем левом углу и хочет попасть в нижний правый. "
            "Он может двигаться только вправо или вниз. Сколько уникальных путей существует?"
        ),
        "examples": [
            {"input": "m = 3, n = 7", "output": "28"},
            {"input": "m = 3, n = 2", "output": "3"},
            {"input": "m = 1, n = 1", "output": "1"},
        ],
        "constraints": ["1 <= m, n <= 100"],
        "hint1": "DP: dp[i][j] — количество путей до [i][j]. dp[i][j] = dp[i-1][j] + dp[i][j-1].",
        "hint2": "Граничные условия: вся первая строка и первый столбец = 1 (только один путь — прямо или вниз).",
        "hint3": "Через комбинаторику: `from math import comb; return comb(m+n-2, m-1)`. Нужно сделать (m-1) шагов вниз и (n-1) шагов вправо — выбрать их расположение.",
        "solution_text": (
            "Комбинаторика: C(m+n-2, m-1). Или DP: dp[i][j] = dp[i-1][j] + dp[i][j-1], dp[0][...]=dp[...][0]=1.\n"
            "⏱ Сложность: O(m×n) DP, O(1) комбинаторика."
        ),
        "failing_test": "m = 1, n = 1 → ожидается 1. Только один путь — никуда не двигаться.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Сумма диапазонов (Range Sum Query)",
        "level": "junior",
        "description": (
            "Дан массив `nums`. Реализуй класс `NumArray` с методом `sumRange(left, right)`, "
            "возвращающим сумму элементов от индекса left до right включительно."
        ),
        "examples": [
            {"input": "nums=[-2,0,3,-5,2,-1]; sumRange(0,2)=1; sumRange(2,5)=-1; sumRange(0,5)=-3", "output": "1, -1, -3"},
        ],
        "constraints": ["1 <= nums.length <= 10⁴", "sumRange вызывается до 10⁴ раз"],
        "hint1": "Для многих запросов предвычисли префиксные суммы.",
        "hint2": "prefix[i] = nums[0] + ... + nums[i-1]. sumRange(l,r) = prefix[r+1] - prefix[l].",
        "hint3": "В __init__: `self.prefix = [0] * (n+1); for i,v in enumerate(nums): self.prefix[i+1] = self.prefix[i]+v`. sumRange: `return self.prefix[right+1] - self.prefix[left]`.",
        "solution_text": (
            "Prefix sum: предвычисляем суммы за O(n), каждый запрос за O(1).\n"
            "⏱ Инициализация: O(n). Запрос: O(1)."
        ),
        "failing_test": "sumRange(0,0) → ожидается nums[0]. prefix[1] - prefix[0] = nums[0]. Проверь граничный случай.",
        "time_complexity": "O(1) на запрос",
        "space_complexity": "O(n)",
    },
    {
        "title": "Найди дубликат в массиве",
        "level": "junior",
        "description": (
            "Дан массив `nums` из n+1 целых чисел в диапазоне [1, n]. Ровно одно число повторяется. "
            "Найди его без изменения массива и за O(1) дополнительной памяти."
        ),
        "examples": [
            {"input": "nums = [1,3,4,2,2]", "output": "2"},
            {"input": "nums = [3,1,3,4,2]", "output": "3"},
        ],
        "constraints": ["1 <= n <= 10⁵", "каждое число в [1, n]", "ровно одно повторяется"],
        "hint1": "Представь массив как связный список: индекс i → nums[i]. Дубликат образует цикл.",
        "hint2": "Алгоритм Флойда для обнаружения цикла: фаза 1 — найти точку встречи, фаза 2 — найти начало цикла.",
        "hint3": "Фаза 1: `slow=fast=nums[0]; while True: slow=nums[slow]; fast=nums[nums[fast]]; if slow==fast: break`. Фаза 2: `slow=nums[0]; while slow!=fast: slow=nums[slow]; fast=nums[fast]; return slow`.",
        "solution_text": (
            "Алгоритм Флойда: массив как граф (i → nums[i]). Цикл образован дубликатом. Две фазы: точка встречи → начало цикла.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [1,1] → ожидается 1. n=1, массив [1,1], дубликат = 1.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },

    # ─────────────────── MIDDLE — ещё 30 ───────────────────
    {
        "title": "Произведение массива кроме себя",
        "level": "middle",
        "description": (
            "Дан массив `nums`. Верни массив `answer`, где `answer[i]` — произведение всех элементов nums, "
            "кроме nums[i]. Реши без деления за O(n)."
        ),
        "examples": [
            {"input": "nums = [1,2,3,4]", "output": "[24,12,8,6]"},
            {"input": "nums = [-1,1,0,-3,3]", "output": "[0,0,9,0,0]"},
        ],
        "constraints": ["2 <= nums.length <= 10⁵", "гарантируется, что результат помещается в 32-битное целое"],
        "hint1": "Для каждой позиции нужно произведение всех элементов СЛЕВА и всех СПРАВА.",
        "hint2": "Два прохода: первый — префиксные произведения (слева), второй — суффиксные (справа). Комбинируй.",
        "hint3": "Реализация: `n=len(nums); ans=[1]*n; prefix=1; for i in range(n): ans[i]=prefix; prefix*=nums[i]; suffix=1; for i in range(n-1,-1,-1): ans[i]*=suffix; suffix*=nums[i]; return ans`.",
        "solution_text": (
            "Два прохода: накапливаем префиксные произведения слева→право, суффиксные справа→лево. Результат = prefix[i] × suffix[i].\n"
            "⏱ Сложность: O(n) по времени, O(1) дополнительно (не считая результата)."
        ),
        "failing_test": "nums = [0,0] → ожидается [0,0]. Оба элемента нуль, произведение каждого 'кроме себя' = 0.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "K наиболее частых элементов",
        "level": "middle",
        "description": (
            "Дан массив `nums` и число `k`. Верни `k` наиболее часто встречающихся элементов. "
            "Порядок результата не важен."
        ),
        "examples": [
            {"input": "nums = [1,1,1,2,2,3], k = 2", "output": "[1, 2]"},
            {"input": "nums = [1], k = 1", "output": "[1]"},
        ],
        "constraints": ["1 <= nums.length <= 10⁵", "1 <= k <= количество уникальных элементов"],
        "hint1": "Подсчитай частоту через Counter. Затем возьми топ-k по частоте.",
        "hint2": "Через heap: `heapq.nlargest(k, count.keys(), key=count.get)`. Или отсортируй ключи по убыванию частоты.",
        "hint3": "Через bucket sort: создай массив из n+1 корзин (индекс = частота). Заполни элементами. Собери k элементов из конца. O(n).",
        "solution_text": (
            "Counter + nlargest (O(n log k)) или bucket sort (O(n)).\n"
            "`from collections import Counter; return heapq.nlargest(k, Counter(nums).keys(), key=Counter(nums).get)`"
        ),
        "failing_test": "nums = [1,2], k = 2 → ожидается [1,2] (порядок любой). Оба элемент с одинаковой частотой.",
        "time_complexity": "O(n log k)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Минимальный размер подмассива",
        "level": "middle",
        "description": (
            "Дан массив положительных целых `nums` и целое `target`. "
            "Найди минимальную длину подмассива с суммой ≥ target. Если нет — верни 0."
        ),
        "examples": [
            {"input": "target = 7, nums = [2,3,1,2,4,3]", "output": "2", "explanation": "[4,3]"},
            {"input": "target = 4, nums = [1,4,4]", "output": "1"},
            {"input": "target = 11, nums = [1,1,1,1,1,1,1,1]", "output": "0"},
        ],
        "constraints": ["1 <= nums.length <= 10⁵", "1 <= target, nums[i] <= 10⁴"],
        "hint1": "Скользящее окно: расширяй правую границу, сжимай левую когда сумма ≥ target.",
        "hint2": "Поддерживай `current_sum`. При `current_sum >= target`: обновляй min_len, убирай левый элемент.",
        "hint3": "Полная реализация: `left=0; total=0; min_len=float('inf'); for right in range(len(nums)): total+=nums[right]; while total>=target: min_len=min(min_len, right-left+1); total-=nums[left]; left+=1; return 0 if min_len==float('inf') else min_len`.",
        "solution_text": (
            "Скользящее окно: два указателя. Правый расширяет, левый сжимает при достижении условия.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "target = 100, nums = [1,2,3] → ожидается 0. Сумма всего массива = 6 < 100.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Число островов",
        "level": "middle",
        "description": (
            "Дана матрица символов `grid` ('1' — суша, '0' — вода). "
            "Остров — группа смежных '1' (по горизонтали/вертикали). Верни количество островов."
        ),
        "examples": [
            {"input": 'grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]', "output": "1"},
            {"input": 'grid = [["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]', "output": "3"},
        ],
        "constraints": ["1 <= m, n <= 300"],
        "hint1": "DFS/BFS из каждой непосещённой '1'. Помечай посещённые как '0'. Каждый старт = новый остров.",
        "hint2": "Для каждой ячейки (i,j) с grid[i][j]=='1': count+=1, запусти DFS, помечая '1' как '0'.",
        "hint3": "DFS: `def dfs(i,j): if i<0 or i>=m or j<0 or j>=n or grid[i][j]!='1': return; grid[i][j]='0'; dfs(i+1,j);dfs(i-1,j);dfs(i,j+1);dfs(i,j-1)`.",
        "solution_text": (
            "DFS из каждой непосещённой '1', помечая весь остров. Счётчик запусков = количество островов.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": "grid = [['0']] → ожидается 0. Нет суши — нет островов.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Расшифровка строки (Decode String)",
        "level": "middle",
        "description": (
            "Дана закодированная строка. Правило: `k[encoded_string]` — строка повторяется k раз. "
            "Верни декодированную строку. Скобки могут быть вложены."
        ),
        "examples": [
            {"input": 's = "3[a]2[bc]"', "output": '"aaabcbc"'},
            {"input": 's = "3[a2[c]]"', "output": '"accaccacc"'},
            {"input": 's = "2[abc]3[cd]ef"', "output": '"abcabccdcdcdef"'},
        ],
        "constraints": ["1 <= s.length <= 30", "1 <= k <= 300"],
        "hint1": "Используй стек. При встрече числа — парси полностью. При '[' — push строка+число. При ']' — pop и повтори.",
        "hint2": "Стек хранит пары (current_string, multiplier). При ']': достань пару, создай prev_str + current*mult.",
        "hint3": "Реализация: `stack=[]; current=''; k=0; for c in s: if c.isdigit(): k=k*10+int(c); elif c=='[': stack.append((current,k)); current=''; k=0; elif c==']': prev,num=stack.pop(); current=prev+current*num; else: current+=c; return current`.",
        "solution_text": (
            "Стек пар (строка, число). При '[' сохраняем контекст, при ']' восстанавливаем и умножаем.\n"
            "⏱ Сложность: O(max_k^depth × n) — в худшем случае. O(n) дополнительно."
        ),
        "failing_test": 's = "10[a]" → ожидается "aaaaaaaaaa". k может быть многозначным числом.',
        "time_complexity": "O(output_length)",
        "space_complexity": "O(output_length)",
    },
    {
        "title": "Генерация правильных скобок",
        "level": "middle",
        "description": (
            "Дано число `n`. Верни все комбинации правильно расставленных n пар скобок."
        ),
        "examples": [
            {"input": "n = 3", "output": '["((()))","(()())","(())()","()(())","()()()"]'},
            {"input": "n = 1", "output": '["()"]'},
        ],
        "constraints": ["1 <= n <= 8"],
        "hint1": "Бэктрекинг: добавляй '(' если открытых < n, добавляй ')' если закрытых < открытых.",
        "hint2": "Параметры рекурсии: `open_count`, `close_count`, `current`. Когда open==close==n — добавь в результат.",
        "hint3": "Реализация: `result=[]; def bt(s, open, close): if len(s)==2*n: result.append(s); return; if open<n: bt(s+'(', open+1, close); if close<open: bt(s+')', open, close+1); bt('',0,0); return result`.",
        "solution_text": (
            "Бэктрекинг: на каждом шаге можно добавить '(' (если не исчерпаны) или ')' (если есть незакрытые).\n"
            "⏱ Сложность: O(4ⁿ/√n) — число правильных скобочных последовательностей (числа Каталана)."
        ),
        "failing_test": "n = 0 → ожидается ['']. Формально, ноль пар — одна пустая последовательность. Задача гарантирует n≥1.",
        "time_complexity": "O(4ⁿ/√n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Поворот матрицы на 90°",
        "level": "middle",
        "description": (
            "Дана квадратная матрица `matrix` n×n. Поверни её на 90° по часовой стрелке на месте."
        ),
        "examples": [
            {"input": "matrix = [[1,2,3],[4,5,6],[7,8,9]]", "output": "[[7,4,1],[8,5,2],[9,6,3]]"},
            {"input": "matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]", "output": "[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]"},
        ],
        "constraints": ["n == matrix.length == matrix[0].length", "1 <= n <= 20"],
        "hint1": "Поворот на 90° = транспонирование + зеркальное отражение по горизонтали (реверс каждой строки).",
        "hint2": "Шаг 1: транспонируй (`matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]` для i<j). Шаг 2: реверс каждой строки.",
        "hint3": "Полная реализация: `n=len(matrix); for i in range(n): for j in range(i+1,n): matrix[i][j],matrix[j][i]=matrix[j][i],matrix[i][j]; for row in matrix: row.reverse()`.",
        "solution_text": (
            "Транспозиция (swap [i][j] и [j][i] для i<j) + реверс каждой строки = поворот на 90° по часовой.\n"
            "⏱ Сложность: O(n²) по времени, O(1) по памяти."
        ),
        "failing_test": "matrix = [[1]] → ожидается [[1]]. Матрица 1×1 не изменяется при повороте.",
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Топологическая сортировка (Kahn)",
        "level": "middle",
        "description": (
            "Дано `numCourses` курсов (0..n-1) и список зависимостей `prerequisites = [[a,b]]` "
            "(сначала b, потом a). Можно ли пройти все курсы? Верни True/False."
        ),
        "examples": [
            {"input": "numCourses = 2, prerequisites = [[1,0]]", "output": "True"},
            {"input": "numCourses = 2, prerequisites = [[1,0],[0,1]]", "output": "False", "explanation": "Цикл"},
        ],
        "constraints": ["1 <= numCourses <= 2000", "0 <= prerequisites.length <= 5000"],
        "hint1": "Топологическая сортировка: если в графе нет цикла — можно пройти все курсы.",
        "hint2": "Алгоритм Кана: считай входящие степени (in-degree). Начинай с узлов с in-degree=0. При обработке — уменьшай степени соседей.",
        "hint3": "Реализация: `from collections import deque; graph=[[] for _ in range(n)]; in_deg=[0]*n; for a,b in prereqs: graph[b].append(a); in_deg[a]+=1; q=deque(i for i in range(n) if in_deg[i]==0); count=0; while q: node=q.popleft(); count+=1; for nei in graph[node]: in_deg[nei]-=1; if in_deg[nei]==0: q.append(nei); return count==n`.",
        "solution_text": (
            "Алгоритм Кана: BFS по вершинам с нулевым in-degree. Если обработали все n вершин — цикла нет.\n"
            "⏱ Сложность: O(V+E) по времени и памяти."
        ),
        "failing_test": "prerequisites = [] → ожидается True. Нет зависимостей — все курсы проходимы.",
        "time_complexity": "O(V+E)",
        "space_complexity": "O(V+E)",
    },
    {
        "title": "Самая длинная общая подпоследовательность (LCS)",
        "level": "middle",
        "description": (
            "Даны строки `text1` и `text2`. Верни длину наидлиннейшей общей подпоследовательности (LCS). "
            "Подпоследовательность — удаление символов без изменения порядка."
        ),
        "examples": [
            {"input": 'text1 = "abcde", text2 = "ace"', "output": "3", "explanation": '"ace"'},
            {"input": 'text1 = "abc", text2 = "abc"', "output": "3"},
            {"input": 'text1 = "abc", text2 = "def"', "output": "0"},
        ],
        "constraints": ["1 <= text1.length, text2.length <= 1000"],
        "hint1": "DP: dp[i][j] — LCS для text1[:i] и text2[:j].",
        "hint2": "Если text1[i-1] == text2[j-1]: dp[i][j] = dp[i-1][j-1] + 1. Иначе: max(dp[i-1][j], dp[i][j-1]).",
        "hint3": "Полная реализация: `m,n=len(text1),len(text2); dp=[[0]*(n+1) for _ in range(m+1)]; for i in range(1,m+1): for j in range(1,n+1): if text1[i-1]==text2[j-1]: dp[i][j]=dp[i-1][j-1]+1; else: dp[i][j]=max(dp[i-1][j],dp[i][j-1]); return dp[m][n]`.",
        "solution_text": (
            "DP таблица m×n. При совпадении символов +1 по диагонали, иначе max сверху/слева.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": 'text1 = "a", text2 = "b" → ожидается 0. Нет общих символов.',
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Редакционное расстояние (Edit Distance)",
        "level": "middle",
        "description": (
            "Даны строки `word1` и `word2`. Найди минимальное число операций (вставка, удаление, замена) "
            "для превращения word1 в word2."
        ),
        "examples": [
            {"input": 'word1 = "horse", word2 = "ros"', "output": "3"},
            {"input": 'word1 = "intention", word2 = "execution"', "output": "5"},
            {"input": 'word1 = "", word2 = "a"', "output": "1"},
        ],
        "constraints": ["0 <= word1.length, word2.length <= 500"],
        "hint1": "DP: dp[i][j] — расстояние для word1[:i] и word2[:j].",
        "hint2": "Если символы равны: dp[i][j] = dp[i-1][j-1]. Иначе: 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]).",
        "hint3": "Инициализация: dp[i][0] = i (удаление i символов); dp[0][j] = j (вставка j символов). Переходы: `if w1[i-1]==w2[j-1]: dp[i][j]=dp[i-1][j-1]; else: dp[i][j]=1+min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])`.",
        "solution_text": (
            "DP: dp[i][j] — редакционное расстояние prefix'ов. При совпадении — копируем диагональ, иначе 1 + min трёх операций.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": 'word1 = "a", word2 = "a" → ожидается 0. Строки уже равны.',
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Матрица: обнуление строк и столбцов",
        "level": "middle",
        "description": (
            "Дана матрица `matrix` m×n. Если элемент равен 0, то весь его ряд и столбец обнуляются. "
            "Модифицируй матрицу на месте."
        ),
        "examples": [
            {"input": "matrix = [[1,1,1],[1,0,1],[1,1,1]]", "output": "[[1,0,1],[0,0,0],[1,0,1]]"},
            {"input": "matrix = [[0,1,2,0],[3,4,5,2],[1,3,1,5]]", "output": "[[0,0,0,0],[0,4,5,0],[0,3,1,0]]"},
        ],
        "constraints": ["m == matrix.length", "n == matrix[0].length", "1 <= m, n <= 200"],
        "hint1": "Сначала найди все строки и столбцы с нулями, затем обнули их.",
        "hint2": "Первый проход: собери наборы `zero_rows` и `zero_cols`. Второй: обнули все строки/столбцы из наборов.",
        "hint3": "O(1) памяти: используй первую строку и первый столбец как метки. Сначала проверь, есть ли нули в первой строке/столбце (для корректной обработки самих маркеров).",
        "solution_text": (
            "Два прохода: найди множества строк и столбцов с нулями, затем обнули их. O(m+n) дополнительно.\n"
            "⏱ Сложность: O(m×n) по времени, O(m+n) по памяти."
        ),
        "failing_test": "matrix = [[1,0]] → ожидается [[0,0]]. Весь ряд и столбец 1 обнуляются.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m+n)",
    },
    {
        "title": "Задача о рюкзаке 0/1",
        "level": "middle",
        "description": (
            "Дан список `weights` весов и `values` стоимостей предметов, и вместимость `W`. "
            "Найди максимальную стоимость предметов, которые можно положить в рюкзак. "
            "Каждый предмет используется не более одного раза."
        ),
        "examples": [
            {"input": "weights=[1,3,4,5], values=[1,4,5,7], W=7", "output": "9", "explanation": "предметы весом 3+4"},
            {"input": "weights=[2,3], values=[3,4], W=5", "output": "7"},
        ],
        "constraints": ["1 <= n <= 1000", "1 <= W <= 1000"],
        "hint1": "DP: dp[i][w] — максимальная стоимость для первых i предметов и вместимости w.",
        "hint2": "Либо берём предмет i: dp[i][w] = dp[i-1][w-wi] + vi (если w >= wi). Либо нет: dp[i][w] = dp[i-1][w]. Берём max.",
        "hint3": "Оптимизация памяти: используй 1D массив, обходи справа налево. `for i in range(n): for w in range(W, weights[i]-1, -1): dp[w] = max(dp[w], dp[w-weights[i]]+values[i])`.",
        "solution_text": (
            "1D DP с обходом справа налево (чтобы не взять предмет дважды). dp[w] = max(не брать, брать).\n"
            "⏱ Сложность: O(n×W) по времени, O(W) по памяти."
        ),
        "failing_test": "weights=[5], values=[10], W=3 → ожидается 0. Предмет не влезает в рюкзак.",
        "time_complexity": "O(n·W)",
        "space_complexity": "O(W)",
    },
    {
        "title": "Количество палиндромных подстрок",
        "level": "middle",
        "description": (
            "Дана строка `s`. Верни количество подстрок, являющихся палиндромами."
        ),
        "examples": [
            {"input": 's = "abc"', "output": "3", "explanation": '"a","b","c"'},
            {"input": 's = "aaa"', "output": "6", "explanation": '"a","a","a","aa","aa","aaa"'},
        ],
        "constraints": ["1 <= s.length <= 1000"],
        "hint1": "Для каждого центра (символ или пара символов) расширяй палиндром влево-вправо.",
        "hint2": "Центров 2n-1: n одиночных (нечётные) и n-1 парных (чётные). Расширяй пока символы совпадают.",
        "hint3": "Полная реализация: `count=0; for center in range(2*n-1): left=center//2; right=left+center%2; while left>=0 and right<n and s[left]==s[right]: count+=1; left-=1; right+=1; return count`.",
        "solution_text": (
            "Расширение от центра: 2n-1 возможных центров. Каждый расширяем двумя указателями.\n"
            "⏱ Сложность: O(n²) по времени, O(1) по памяти."
        ),
        "failing_test": 's = "a" → ожидается 1. Один символ — один палиндром.',
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Поиск в повёрнутом отсортированном массиве",
        "level": "middle",
        "description": (
            "Массив `nums` был отсортирован, затем повёрнут на неизвестный сдвиг. "
            "Найди `target` в нём. Верни индекс или -1."
        ),
        "examples": [
            {"input": "nums = [4,5,6,7,0,1,2], target = 0", "output": "4"},
            {"input": "nums = [4,5,6,7,0,1,2], target = 3", "output": "-1"},
            {"input": "nums = [1], target = 0", "output": "-1"},
        ],
        "constraints": ["1 <= nums.length <= 5000", "все значения уникальны"],
        "hint1": "Бинарный поиск: определи, какая половина отсортирована, и проверяй target в ней.",
        "hint2": "Если `nums[left] <= nums[mid]` — левая половина отсортирована. Проверь, попадает ли target в неё.",
        "hint3": "Реализация: `while lo<=hi: mid=(lo+hi)//2; if nums[mid]==target: return mid; if nums[lo]<=nums[mid]: if nums[lo]<=target<nums[mid]: hi=mid-1; else: lo=mid+1; else: if nums[mid]<target<=nums[hi]: lo=mid+1; else: hi=mid-1; return -1`.",
        "solution_text": (
            "Бинарный поиск: одна из половин всегда строго отсортирована. Проверяем target в ней, сужаем.\n"
            "⏱ Сложность: O(log n) по времени, O(1) по памяти."
        ),
        "failing_test": "nums = [3,1], target = 1 → ожидается 1. Правая половина [1] отсортирована, target в ней.",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Игра Жизнь Конвея",
        "level": "middle",
        "description": (
            "Дана бинарная матрица `board`. Примени правила игры «Жизнь»:\n"
            "- Живая клетка (1) с 2-3 живыми соседями — выживает, иначе умирает.\n"
            "- Мёртвая клетка (0) с ровно 3 живыми соседями — оживает.\n"
            "Обнови матрицу на месте (одновременное обновление)."
        ),
        "examples": [
            {"input": "board = [[0,1,0],[0,0,1],[1,1,1],[0,0,0]]", "output": "[[0,0,0],[1,0,1],[0,1,1],[0,1,0]]"},
        ],
        "constraints": ["m == board.length", "n == board[0].length", "1 <= m, n <= 25"],
        "hint1": "Чтобы не потерять исходное состояние: используй дополнительные значения (2 — умерла, -1 — ожила).",
        "hint2": "Первый проход: пометь изменения спецзначениями. Второй: примени изменения (2→0, -1→1 и 0→1→1).",
        "hint3": "Подсчёт живых соседей: `sum(board[r][c] in (1,2) for r,c in 8 направлений)`. Если live==2 и cell==1 или live==3: ставим нужное значение.",
        "solution_text": (
            "Двухфазный подход: маркируй изменения через спецзначения (чтобы читать оригинал), затем финализируй.\n"
            "⏱ Сложность: O(m×n) по времени, O(1) доп. памяти."
        ),
        "failing_test": "board = [[1,1],[1,0]] → ожидается [[1,1],[1,1]]. Мёртвая [1][1] имеет 3 живых соседей → оживает.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Наибольший прямоугольник из 1 в матрице",
        "level": "middle",
        "description": (
            "Дана бинарная матрица `matrix` из '0' и '1'. "
            "Найди наибольший прямоугольник, состоящий только из '1', и верни его площадь."
        ),
        "examples": [
            {"input": 'matrix = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]]', "output": "6"},
            {"input": 'matrix = [["0"]]', "output": "0"},
            {"input": 'matrix = [["1"]]', "output": "1"},
        ],
        "constraints": ["1 <= m, n <= 200"],
        "hint1": "Для каждой строки вычисли высоту столбца (количество единиц подряд сверху). Применяй задачу о наибольшем прямоугольнике в гистограмме.",
        "hint2": "Обновление высот: если matrix[i][j]=='1': heights[j]+=1; иначе heights[j]=0.",
        "hint3": "Наибольший прямоугольник в гистограмме через стек: `stack=[]; max_area=0; for i,h in enumerate(heights+[0]): while stack and heights[stack[-1]]>h: height=heights[stack.pop()]; width=i if not stack else i-stack[-1]-1; max_area=max(max_area,height*width); stack.append(i)`.",
        "solution_text": (
            "Строка за строкой обновляй высоты гистограммы. К каждой гистограмме применяй алгоритм O(n) через стек.\n"
            "⏱ Сложность: O(m×n) по времени, O(n) по памяти."
        ),
        "failing_test": 'matrix = [["0"]] → ожидается 0. Нет единиц — площадь 0.',
        "time_complexity": "O(m·n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Наибольший возрастающий путь в матрице",
        "level": "middle",
        "description": (
            "Дана матрица `matrix` m×n. Найди длину наибольшего возрастающего пути. "
            "Двигаться можно вверх/вниз/влево/вправо, следующая ячейка должна быть строго больше."
        ),
        "examples": [
            {"input": "matrix = [[9,9,4],[6,6,8],[2,1,1]]", "output": "4", "explanation": "[1,2,6,9]"},
            {"input": "matrix = [[3,4,5],[3,2,6],[2,2,1]]", "output": "4", "explanation": "[3,4,5,6]"},
        ],
        "constraints": ["m == matrix.length", "n == matrix[0].length", "1 <= m, n <= 200"],
        "hint1": "DFS с мемоизацией: для каждой ячейки — длина пути из неё.",
        "hint2": "`memo[i][j]` = max путь начиная с (i,j). Рекурсивно проверяй 4 соседей с большим значением.",
        "hint3": "Реализация: `memo=[[0]*n for _ in range(m)]; def dfs(i,j): if memo[i][j]: return memo[i][j]; best=1; for di,dj in dirs: ni,nj=i+di,j+dj; if 0<=ni<m and 0<=nj<n and matrix[ni][nj]>matrix[i][j]: best=max(best,1+dfs(ni,nj)); memo[i][j]=best; return best; return max(dfs(i,j) for all i,j)`.",
        "solution_text": (
            "DFS + мемоизация. Каждая ячейка вычисляется один раз, результат кешируется.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": "matrix = [[1]] → ожидается 1. Путь длиной 1 из единственного элемента.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Кратчайший путь в двоичной матрице",
        "level": "middle",
        "description": (
            "Дана матрица `grid` n×n из 0 и 1. Найди длину кратчайшего пути от [0][0] до [n-1][n-1] "
            "через нулевые ячейки. Можно двигаться в 8 направлениях. Если пути нет — верни -1."
        ),
        "examples": [
            {"input": "grid = [[0,1],[1,0]]", "output": "2"},
            {"input": "grid = [[0,0,0],[1,1,0],[1,1,0]]", "output": "4"},
            {"input": "grid = [[1,0,0],[1,1,0],[1,1,0]]", "output": "-1"},
        ],
        "constraints": ["n == grid.length == grid[0].length", "1 <= n <= 100"],
        "hint1": "BFS из [0][0]. Ищем кратчайший путь по нулевым ячейкам.",
        "hint2": "Если grid[0][0]==1 или grid[n-1][n-1]==1 — сразу возвращай -1. BFS с расстоянием.",
        "hint3": "Реализация: `from collections import deque; if grid[0][0] or grid[-1][-1]: return -1; q=deque([(0,0,1)]); grid[0][0]=1; while q: r,c,d=q.popleft(); if r==n-1 and c==n-1: return d; for dr,dc in 8 направлений: nr,nc=r+dr,c+dc; if 0<=nr<n and 0<=nc<n and grid[nr][nc]==0: grid[nr][nc]=1; q.append((nr,nc,d+1)); return -1`.",
        "solution_text": (
            "BFS (гарантирует кратчайший путь). Помечаем посещённые, чтобы не заходить повторно.\n"
            "⏱ Сложность: O(n²) по времени и памяти."
        ),
        "failing_test": "grid = [[0]] → ожидается 1. Начало = конец, длина пути = 1.",
        "time_complexity": "O(n²)",
        "space_complexity": "O(n²)",
    },
    {
        "title": "Задача о покупке акций с перерывом (Cooldown)",
        "level": "middle",
        "description": (
            "Дан массив `prices`. Можно покупать и продавать акции неограниченное число раз, "
            "но после продажи нельзя покупать следующий день (cooldown). Найди максимальную прибыль."
        ),
        "examples": [
            {"input": "prices = [1,2,3,0,2]", "output": "3", "explanation": "купить@1, продать@2, cooldown, купить@0, продать@2"},
            {"input": "prices = [1]", "output": "0"},
        ],
        "constraints": ["1 <= prices.length <= 5000", "0 <= prices[i] <= 1000"],
        "hint1": "Состояния: held (держу акцию), sold (только что продал), rest (кулдаун прошёл).",
        "hint2": "Переходы: held = max(held, rest - price); sold = held + price; rest = max(rest, sold).",
        "hint3": "Инициализация: held=-prices[0], sold=0, rest=0. Полная реализация: `for price in prices[1:]: held, sold, rest = max(held, rest-price), held+price, max(rest, sold); return max(sold, rest)`.",
        "solution_text": (
            "Три состояния: held, sold, rest. Переход: held=max(held, rest-price); sold=held_prev+price; rest=max(rest,sold_prev).\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "prices = [1] → ожидается 0. Нет возможности купить и продать с прибылью.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Количество способов декодировать строку",
        "level": "middle",
        "description": (
            "Дана строка `s` из цифр. Буква 'A'-'Z' кодируется как '1'-'26'. "
            "Верни количество способов декодировать строку."
        ),
        "examples": [
            {"input": 's = "12"', "output": "2", "explanation": '"AB" (1,2) или "L" (12)'},
            {"input": 's = "226"', "output": "3", "explanation": '"BZ","VF","BBF"'},
            {"input": 's = "06"', "output": "0"},
        ],
        "constraints": ["1 <= s.length <= 100"],
        "hint1": "DP: dp[i] — количество способов декодировать s[:i].",
        "hint2": "Одиночная цифра: если s[i-1]!='0' → dp[i] += dp[i-1]. Двойная: если s[i-2:i] в '10'..'26' → dp[i] += dp[i-2].",
        "hint3": "Инициализация: dp[0]=1 (пустая строка), dp[1]=0 if s[0]=='0' else 1. Цикл с i от 2 до n. Возвращай dp[n].",
        "solution_text": (
            "DP: dp[i] += dp[i-1] если одна цифра допустима; += dp[i-2] если двузначное 10-26.\n"
            "⏱ Сложность: O(n) по времени, O(n) или O(1) по памяти."
        ),
        "failing_test": 's = "0" → ожидается 0. Нет буквы с кодом 0.',
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Восстановление IP-адресов",
        "level": "middle",
        "description": (
            "Дана строка `s` из цифр. Верни все допустимые IP-адреса, которые можно получить, "
            "вставив три точки. IP-октет: 0-255, без ведущих нулей (кроме '0')."
        ),
        "examples": [
            {"input": 's = "25525511135"', "output": '["255.255.11.135","255.255.111.35"]'},
            {"input": 's = "0000"', "output": '["0.0.0.0"]'},
            {"input": 's = "1111111111111111"', "output": "[]"},
        ],
        "constraints": ["1 <= s.length <= 20"],
        "hint1": "Бэктрекинг: на каждом шаге выбирай 1, 2 или 3 символа для текущего октета.",
        "hint2": "Проверяй валидность октета: не пустой, ≤ 255, без ведущих нулей (кроме '0').",
        "hint3": "def bt(start, parts): if len(parts)==4 and start==len(s): result.append('.'.join(parts)); return; if len(parts)==4: return; for length in 1,2,3: segment=s[start:start+length]; if not segment or (segment[0]=='0' and len(segment)>1) or int(segment)>255: continue; bt(start+length, parts+[segment])",
        "solution_text": (
            "Бэктрекинг: 4 октета, каждый 1-3 символа. Валидация: 0-255, нет ведущих нулей.\n"
            "⏱ Сложность: O(1) — максимум 3⁴ = 81 вариант."
        ),
        "failing_test": 's = "010010" → один из ответов "0.10.0.10". Октет "0" допустим, "010" — нет (ведущий ноль).',
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Наидлиннейшая возрастающая подпоследовательность (DP)",
        "level": "middle",
        "description": (
            "Дан массив `nums`. Найди длину наидлиннейшей строго возрастающей подпоследовательности (LIS). "
            "Реши за O(n log n)."
        ),
        "examples": [
            {"input": "nums = [10,9,2,5,3,7,101,18]", "output": "4", "explanation": "[2,3,7,101]"},
            {"input": "nums = [0,1,0,3,2,3]", "output": "4"},
            {"input": "nums = [7,7,7,7,7,7,7]", "output": "1"},
        ],
        "constraints": ["1 <= nums.length <= 2500"],
        "hint1": "DP за O(n²): dp[i] = max длина LIS, заканчивающейся в nums[i].",
        "hint2": "За O(n log n): поддерживай массив `tails` (минимальных хвостов). Для каждого элемента бинарный поиск.",
        "hint3": "O(n log n): `tails=[]; for n in nums: pos=bisect_left(tails, n); if pos==len(tails): tails.append(n); else: tails[pos]=n; return len(tails)`. tails не является LIS, но его длина = длине LIS.",
        "solution_text": (
            "Массив `tails` + бинарный поиск (bisect_left). Каждый элемент обрабатывается за O(log n).\n"
            "⏱ Сложность: O(n log n) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [4,10,4,3,8,9] → ожидается 3. LIS: [3,8,9] или [4,8,9].",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Клетки под атакой ладьи",
        "level": "middle",
        "description": (
            "Дана шахматная доска 8×8 в виде матрицы (символы: '.', 'R' — ладья, 'p' — пешка, 'B' — слон). "
            "Найди количество пешек под атакой ладьи (ладья одна). Слон блокирует путь."
        ),
        "examples": [
            {"input": "board = (8×8 матрица с 'R','p','B','.')", "output": "3"},
        ],
        "constraints": ["Доска всегда 8×8", "ровно одна 'R'"],
        "hint1": "Найди позицию ладьи. Пройди в четырёх направлениях, останавливаясь на 'B' или крае.",
        "hint2": "Для каждого направления (dr,dc): двигайся пока в пределах доски. Если встретил 'p' — count++. Если 'B' — стоп.",
        "hint3": "Реализация: найди r0,c0 ладьи. for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]: r,c=r0+dr,c0+dc; while 0<=r<8 and 0<=c<8: if board[r][c]=='B': break; if board[r][c]=='p': count+=1; break; r+=dr; c+=dc",
        "solution_text": (
            "Найди ладью, проверь 4 луча. Каждый луч останавливается на слоне или пешке (пешка засчитывается).\n"
            "⏱ Сложность: O(1) — доска фиксированного размера 8×8."
        ),
        "failing_test": "Пешка за слоном не считается атакованной — слон блокирует луч.",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Наибольшая прямоугольная область в гистограмме",
        "level": "middle",
        "description": (
            "Дан массив `heights`, где heights[i] — высота i-го столбца гистограммы. "
            "Найди площадь наибольшего прямоугольника в этой гистограмме."
        ),
        "examples": [
            {"input": "heights = [2,1,5,6,2,3]", "output": "10"},
            {"input": "heights = [2,4]", "output": "4"},
        ],
        "constraints": ["1 <= heights.length <= 10⁵", "0 <= heights[i] <= 10⁴"],
        "hint1": "Для каждого столбца нужно знать: как далеко влево и вправо простирается прямоугольник этой высоты.",
        "hint2": "Используй монотонный стек (возрастающий). При нахождении меньшего элемента — вычисляй площадь для поднятых элементов.",
        "hint3": "Реализация: `stack=[]; max_area=0; for i,h in enumerate(heights+[0]): while stack and heights[stack[-1]]>h: height=heights[stack.pop()]; width=i if not stack else i-stack[-1]-1; max_area=max(max_area,height*width); stack.append(i); return max_area`.",
        "solution_text": (
            "Монотонный стек: при уменьшении высоты вычисляем площадь для каждого 'поднятого' столбца. Sentinel [0] в конце.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": "heights = [6,2,5,4,5,1,6] → ожидается 12. Прямоугольник высотой 2 и шириной 6.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Задача об активациях (Task Scheduler)",
        "level": "middle",
        "description": (
            "Дан список задач (символы) и кулдаун `n` (между одинаковыми задачами ≥ n интервалов). "
            "Найди минимальное время выполнения всех задач (иногда нужно простаивать)."
        ),
        "examples": [
            {"input": "tasks = ['A','A','A','B','B','B'], n = 2", "output": "8", "explanation": "A B _ A B _ A B"},
            {"input": "tasks = ['A','A','A','B','B','B'], n = 0", "output": "6"},
            {"input": "tasks = ['A','A','A','A','A','A','B','C','D','E','F','G'], n = 2", "output": "16"},
        ],
        "constraints": ["1 <= tasks.length <= 10⁴", "0 <= n <= 100"],
        "hint1": "Наиболее частая задача определяет минимальное время. Формула: (max_count - 1) * (n + 1) + tasks_with_max_count.",
        "hint2": "Но если задач много, они заполнят простои. Реальный ответ: max(len(tasks), формула).",
        "hint3": "Полная реализация: `from collections import Counter; count=Counter(tasks); max_count=max(count.values()); tasks_with_max=list(count.values()).count(max_count); return max(len(tasks), (max_count-1)*(n+1)+tasks_with_max)`.",
        "solution_text": (
            "Формула: (max_count-1)×(n+1) + tasks_with_max. Но ответ не может быть меньше len(tasks).\n"
            "⏱ Сложность: O(n) по времени и памяти."
        ),
        "failing_test": "tasks=['A','B','C','D'], n=3 → ожидается 4. Все разные, никаких простоев.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Наиболее длинный путь без повторения узлов в дереве",
        "level": "middle",
        "description": (
            "Дано бинарное дерево. Найди длину наибольшего пути между двумя любыми узлами "
            "(не обязательно через корень). Длина в рёбрах."
        ),
        "examples": [
            {"input": "root = [1,2,3]", "output": "2"},
            {"input": "root = [1,2,3,4,5]", "output": "3"},
        ],
        "constraints": ["1 <= nodes.count <= 10⁴"],
        "hint1": "DFS: для каждого узла вычисли высоту левого и правого поддерева. Диаметр через узел = left_h + right_h.",
        "hint2": "Глобальная переменная `max_diameter`. DFS возвращает высоту, обновляет max_diameter.",
        "hint3": "Реализация: `self.max_d=0; def dfs(node): if not node: return 0; left=dfs(node.left); right=dfs(node.right); self.max_d=max(self.max_d, left+right); return 1+max(left,right); dfs(root); return self.max_d`.",
        "solution_text": (
            "DFS: высота поддерева = 1 + max(left, right). Диаметр через узел = left + right. Обновляй глобальный максимум.\n"
            "⏱ Сложность: O(n) по времени, O(h) по памяти."
        ),
        "failing_test": "root = [1] → ожидается 0. Один узел, нет рёбер.",
        "time_complexity": "O(n)",
        "space_complexity": "O(h)",
    },
    {
        "title": "Наибольший остров (Max Area of Island)",
        "level": "middle",
        "description": (
            "Дана матрица `grid` из 0 и 1. Остров — группа смежных 1. "
            "Верни площадь (количество ячеек) наибольшего острова. Если нет — 0."
        ),
        "examples": [
            {"input": "grid = [[0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,1,1,1,0,0,0],[0,1,1,0,1,0,0,0,0,0,0,0,0],[0,1,0,0,1,1,0,0,1,0,1,0,0],[0,1,0,0,1,1,0,0,1,1,1,0,0],[0,0,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,0,1,1,1,0,0,0],[0,0,0,0,0,0,0,1,1,0,0,0,0]]", "output": "6"},
            {"input": "grid = [[0,0,0,0,0,0,0,0]]", "output": "0"},
        ],
        "constraints": ["m == grid.length", "n == grid[0].length", "1 <= m, n <= 50"],
        "hint1": "DFS/BFS из каждой непосещённой 1. Суммируй площадь. Обновляй максимум.",
        "hint2": "DFS возвращает площадь острова. Помечай посещённые ячейки (grid[i][j] = 0).",
        "hint3": "Реализация: `def dfs(i,j): if i<0 or i>=m or j<0 or j>=n or grid[i][j]==0: return 0; grid[i][j]=0; return 1+dfs(i+1,j)+dfs(i-1,j)+dfs(i,j+1)+dfs(i,j-1); return max(dfs(i,j) for i in range(m) for j in range(n))`.",
        "solution_text": (
            "DFS из каждой '1', помечаем посещённые. DFS возвращает площадь. Берём максимум.\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": "grid = [[1]] → ожидается 1. Остров из одной ячейки.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Минимальный путь в треугольнике",
        "level": "middle",
        "description": (
            "Дан треугольник (список списков). Найди минимальную сумму пути сверху вниз. "
            "На каждом шаге можно перейти к смежному элементу следующей строки."
        ),
        "examples": [
            {"input": "triangle = [[2],[3,4],[6,5,7],[4,1,8,3]]", "output": "11", "explanation": "2+3+5+1=11"},
            {"input": "triangle = [[-10]]", "output": "-10"},
        ],
        "constraints": ["1 <= triangle.length <= 200", "-10⁴ <= triangle[i][j] <= 10⁴"],
        "hint1": "DP снизу вверх: начни с последней строки, для каждого элемента выше бери min из двух путей ниже.",
        "hint2": "`dp = triangle[-1][:]`. Для строки i снизу: `dp[j] = triangle[i][j] + min(dp[j], dp[j+1])`.",
        "hint3": "Полная реализация: `dp=triangle[-1][:]; for i in range(len(triangle)-2, -1, -1): for j in range(len(triangle[i])): dp[j]=triangle[i][j]+min(dp[j],dp[j+1]); return dp[0]`.",
        "solution_text": (
            "DP снизу вверх: dp[j] = triangle[i][j] + min(dp[j], dp[j+1]). Итоговый dp[0] — ответ.\n"
            "⏱ Сложность: O(n²) по времени, O(n) по памяти."
        ),
        "failing_test": "triangle = [[1],[2,3]] → ожидается 3 (1+2). Левый путь дешевле.",
        "time_complexity": "O(n²)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Наибольший общий предок бинарного дерева (LCA)",
        "level": "middle",
        "description": (
            "Дано обычное (не BST) бинарное дерево и два узла `p`, `q`. "
            "Найди их наименьшего общего предка (LCA)."
        ),
        "examples": [
            {"input": "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1", "output": "3"},
            {"input": "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4", "output": "5"},
        ],
        "constraints": ["2 <= nodes.count <= 10⁵", "все Node.val уникальны"],
        "hint1": "Рекурсия: если текущий узел — p или q, верни его. Рекурсивно ищи в левом и правом поддеревьях.",
        "hint2": "Если оба результата не None — текущий узел и есть LCA. Если один из них None — верни другой.",
        "hint3": "Реализация: `def lca(root, p, q): if not root or root is p or root is q: return root; left=lca(root.left,p,q); right=lca(root.right,p,q); if left and right: return root; return left or right`.",
        "solution_text": (
            "Post-order DFS. Если оба поддерева вернули не None — текущий узел и есть LCA.\n"
            "⏱ Сложность: O(n) по времени, O(h) по памяти."
        ),
        "failing_test": "p — предок q → LCA = p. Алгоритм вернёт p при первом обнаружении, не доходя до q.",
        "time_complexity": "O(n)",
        "space_complexity": "O(h)",
    },
    {
        "title": "Покраска забора (Paint Fence)",
        "level": "middle",
        "description": (
            "Дано `n` секций забора и `k` цветов. Секции красятся поочерёдно. "
            "Нельзя красить более двух соседних секций одним цветом. "
            "Найди количество способов покрасить забор."
        ),
        "examples": [
            {"input": "n = 3, k = 2", "output": "6"},
            {"input": "n = 1, k = 1", "output": "1"},
            {"input": "n = 7, k = 2", "output": "42"},
        ],
        "constraints": ["1 <= n <= 50", "1 <= k <= 10⁵"],
        "hint1": "DP: same[i] — способов когда i и i-1 одного цвета. diff[i] — разных цветов.",
        "hint2": "same[i] = diff[i-1] (взяли тот же цвет что в diff). diff[i] = (same[i-1] + diff[i-1]) * (k-1).",
        "hint3": "Инициализация: same=0, diff=k (первая секция k вариантов). Итерировать от 2 до n: new_same=diff; new_diff=(same+diff)*(k-1); same=new_same; diff=new_diff. Ответ: same+diff.",
        "solution_text": (
            "DP: same = способов с одинаковым цветом c предыдущей, diff = с разным. Переходы за O(1) на шаг.\n"
            "⏱ Сложность: O(n) по времени, O(1) по памяти."
        ),
        "failing_test": "n=1, k=1 → ожидается 1. Один цвет, одна секция, один способ.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Слияние K отсортированных массивов",
        "level": "middle",
        "description": (
            "Дан список из `k` отсортированных массивов. Слей их в один отсортированный массив."
        ),
        "examples": [
            {"input": "arrays = [[1,4,7],[2,5,8],[3,6,9]]", "output": "[1,2,3,4,5,6,7,8,9]"},
            {"input": "arrays = [[1],[0]]", "output": "[0,1]"},
        ],
        "constraints": ["1 <= k <= 10⁴", "суммарное количество элементов N <= 10⁵"],
        "hint1": "Min-heap: добавь первый элемент каждого массива. Извлекай минимум, добавляй следующий из того же массива.",
        "hint2": "В heapq храни тройки (value, array_index, element_index).",
        "hint3": "Реализация: `import heapq; heap=[(arr[0],i,0) for i,arr in enumerate(arrays) if arr]; heapq.heapify(heap); result=[]; while heap: val,ai,ei=heapq.heappop(heap); result.append(val); if ei+1<len(arrays[ai]): heapq.heappush(heap,(arrays[ai][ei+1],ai,ei+1)); return result`.",
        "solution_text": (
            "Min-heap из k элементов. Каждый шаг: извлекаем минимум O(log k), добавляем следующий из того же массива.\n"
            "⏱ Сложность: O(N log k) по времени, O(k) по памяти."
        ),
        "failing_test": "arrays = [[],[1]] → ожидается [1]. Пустые массивы не должны ломать алгоритм.",
        "time_complexity": "O(N log k)",
        "space_complexity": "O(k)",
    },

    # ─────────────────── SENIOR — ещё 30 ───────────────────
    {
        "title": "Минимальное окно подстроки (Minimum Window Substring)",
        "level": "senior",
        "description": (
            "Даны строки `s` и `t`. Найди минимальную подстроку `s`, содержащую все символы `t` "
            "(включая дубликаты). Если нет — верни пустую строку."
        ),
        "examples": [
            {"input": 's = "ADOBECODEBANC", t = "ABC"', "output": '"BANC"'},
            {"input": 's = "a", t = "a"', "output": '"a"'},
            {"input": 's = "a", t = "aa"', "output": '""'},
        ],
        "constraints": ["1 <= s.length <= 10⁵", "1 <= t.length <= 10⁵"],
        "hint1": "Скользящее окно: расширяй правую границу. Когда все символы t покрыты — сжимай левую.",
        "hint2": "Счётчик need (нужные символы), have (набрали). При совпадении частот — have++. Когда have==len(need) — сужай окно.",
        "hint3": "Реализация: `from collections import Counter; need=Counter(t); have=0; formed=len(need); l=0; ans=(float('inf'),0,0); window={}; for r,c in enumerate(s): window[c]=window.get(c,0)+1; if c in need and window[c]==need[c]: have+=1; while have==formed: if r-l+1<ans[0]: ans=(r-l+1,l,r); window[s[l]]-=1; if s[l] in need and window[s[l]]<need[s[l]]: have-=1; l+=1; return '' if ans[0]==float('inf') else s[ans[1]:ans[2]+1]`.",
        "solution_text": (
            "Скользящее окно + счётчики. have/formed контролируют покрытие. Сжимаем когда все символы t набраны.\n"
            "⏱ Сложность: O(|s| + |t|) по времени, O(|s| + |t|) по памяти."
        ),
        "failing_test": 's = "aa", t = "aa" → ожидается "aa". Нужно ровно два символа "a", окно должно включать оба.',
        "time_complexity": "O(|s|+|t|)",
        "space_complexity": "O(|s|+|t|)",
    },
    {
        "title": "Отчёт о небе (Skyline Problem)",
        "level": "senior",
        "description": (
            "Дан список зданий `buildings = [[left, right, height]]`. "
            "Верни силуэт горизонта — список точек [x, height] изменения высоты."
        ),
        "examples": [
            {"input": "buildings = [[2,9,10],[3,7,15],[5,12,12],[15,20,10],[19,24,8]]", "output": "[[2,10],[3,15],[7,12],[12,0],[15,10],[20,8],[24,0]]"},
        ],
        "constraints": ["1 <= buildings.length <= 10⁴", "0 <= left < right <= 2³¹-1", "1 <= height <= 2³¹-1"],
        "hint1": "Используй события (events): начало здания → поднятие высоты; конец → опускание. Сортируй события.",
        "hint2": "Сортированные события: начало (x, -h) — отрицательная высота для приоритета. Конец (x, 0). Max-heap для текущих высот.",
        "hint3": "Реализация: `events=[]; for l,r,h in buildings: events.append((l,-h,r)); events.append((r,0,0)); events.sort(); heap=[(0,float('inf'))]; res=[]; for x,neg_h,end in events: while heap[0][1]<=x: heapq.heappop(heap); if neg_h: heapq.heappush(heap,(neg_h,end)); cur_max=-heap[0][0]; if not res or res[-1][1]!=cur_max: res.append([x,cur_max]); return res`.",
        "solution_text": (
            "События + max-heap (через отрицание). Для каждого события проверяем изменение текущего максимума высоты.\n"
            "⏱ Сложность: O(n log n) по времени, O(n) по памяти."
        ),
        "failing_test": "Два здания одной высоты вплотную → точка изменения между ними не должна появляться.",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Регулярные выражения (Regular Expression Matching)",
        "level": "senior",
        "description": (
            "Реализуй сопоставление с паттерном, где '.' — любой символ, '*' — ноль или более предыдущих. "
            "Верни True если строка `s` полностью совпадает с паттерном `p`."
        ),
        "examples": [
            {"input": 's = "aa", p = "a*"', "output": "True"},
            {"input": 's = "ab", p = ".*"', "output": "True"},
            {"input": 's = "aab", p = "c*a*b"', "output": "True"},
        ],
        "constraints": ["1 <= s.length <= 20", "1 <= p.length <= 30"],
        "hint1": "DP: dp[i][j] — совпадает ли s[:i] с p[:j].",
        "hint2": "Если p[j-1]=='*': dp[i][j] = dp[i][j-2] (ноль вхождений) OR (символы совпадают) AND dp[i-1][j]. Иначе: dp[i][j] = dp[i-1][j-1] AND символы совпадают.",
        "hint3": "Инициализация: dp[0][0]=True; для паттернов вида 'a*b*c*': dp[0][j]=dp[0][j-2] если p[j-1]=='*'. Совпадение: p[j-1]=='.' OR p[j-1]==s[i-1].",
        "solution_text": (
            "2D DP. Случай '*': или пропускаем (dp[i][j-2]), или используем (совпадение символов + dp[i-1][j]).\n"
            "⏱ Сложность: O(m×n) по времени и памяти."
        ),
        "failing_test": 's = "aaa", p = "a*a" → ожидается True. Оператор "*" поглощает 2 символа "a", оставляет 1.',
        "time_complexity": "O(m·n)",
        "space_complexity": "O(m·n)",
    },
    {
        "title": "Словарь инопланетян (Alien Dictionary)",
        "level": "senior",
        "description": (
            "Дан список слов из «инопланетного» алфавита в лексикографическом порядке. "
            "Восстанови порядок символов в алфавите. Если порядок невозможен — верни ''."
        ),
        "examples": [
            {"input": 'words = ["wrt","wrf","er","ett","rftt"]', "output": '"wertf"'},
            {"input": 'words = ["z","x"]', "output": '"zx"'},
            {"input": 'words = ["z","x","z"]', "output": '""', "explanation": "цикл"},
        ],
        "constraints": ["1 <= words.length <= 100", "1 <= words[i].length <= 100"],
        "hint1": "Сравнивай соседние слова: первый различающийся символ даёт отношение порядка.",
        "hint2": "Построй граф зависимостей + топологическая сортировка (Kahn). Если есть цикл или слово — префикс следующего — верни ''.",
        "hint3": "Топ. сортировка: `from collections import deque, defaultdict; adj=defaultdict(set); in_deg={c:0 for w in words for c in w}; for w1,w2 in zip(words,words[1:]): for c1,c2 in zip(w1,w2): if c1!=c2: if c2 not in adj[c1]: adj[c1].add(c2); in_deg[c2]+=1; break; else: if len(w2)<len(w1): return ''`.",
        "solution_text": (
            "Граф из попарных сравнений соседних слов + топологическая сортировка Кана. Цикл → пустая строка.\n"
            "⏱ Сложность: O(C) где C — суммарная длина всех слов."
        ),
        "failing_test": 'words = ["abc","ab"] → ожидается "". Слово "abc" перед "ab" при общем префиксе "ab" противоречит порядку.',
        "time_complexity": "O(C)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Критические рёбра в графе (Tarjan's Bridge)",
        "level": "senior",
        "description": (
            "Дан неориентированный граф (n вершин, edges). Найди все критические рёбра (мосты) — "
            "рёбра, удаление которых увеличивает число связных компонентов."
        ),
        "examples": [
            {"input": "n = 4, edges = [[0,1],[1,2],[2,0],[1,3]]", "output": "[[1,3]]"},
            {"input": "n = 2, edges = [[0,1]]", "output": "[[0,1]]"},
        ],
        "constraints": ["1 <= n <= 10⁵", "0 <= edges.length <= 2×10⁵"],
        "hint1": "Алгоритм Тарьяна: DFS с timestamp (disc) и low (минимальный достижимый timestamp).",
        "hint2": "Ребро (u,v) — мост, если low[v] > disc[u] после DFS из u в v.",
        "hint3": "Реализация: `disc=[0]*n; low=[0]*n; timer=[0]; visited=[False]*n; bridges=[]; def dfs(u,parent): visited[u]=True; disc[u]=low[u]=timer[0]; timer[0]+=1; for v in graph[u]: if not visited[v]: dfs(v,u); low[u]=min(low[u],low[v]); if low[v]>disc[u]: bridges.append([u,v]); elif v!=parent: low[u]=min(low[u],disc[v])`.",
        "solution_text": (
            "Алгоритм Тарьяна: DFS + disc/low. Мост: low[v] > disc[u] — нет пути обратно мимо этого ребра.\n"
            "⏱ Сложность: O(V+E) по времени и памяти."
        ),
        "failing_test": "Кратные рёбра (мультиграф): нужно учитывать ребро parent не по номеру вершины, а по индексу ребра.",
        "time_complexity": "O(V+E)",
        "space_complexity": "O(V+E)",
    },
    {
        "title": "Кратчайший путь (Dijkstra)",
        "level": "senior",
        "description": (
            "Дан взвешенный ориентированный граф (n вершин) в виде списка рёбер `times = [[u,v,w]]`. "
            "Найди минимальное время от источника `k` до всех остальных вершин. "
            "Если какая-то вершина недостижима — верни -1."
        ),
        "examples": [
            {"input": "times = [[2,1,1],[2,3,1],[3,4,1]], n = 4, k = 2", "output": "2"},
        ],
        "constraints": ["1 <= k <= n <= 100", "1 <= times.length <= 6000"],
        "hint1": "Алгоритм Дейкстры: min-heap (dist, node). Начни с (0, k).",
        "hint2": "Обновляй расстояние до соседей только если нашли лучший путь. Посещённые вершины пропускай.",
        "hint3": "Реализация: `import heapq; graph=defaultdict(list); for u,v,w in times: graph[u].append((v,w)); dist={i:float('inf') for i in range(1,n+1)}; dist[k]=0; heap=[(0,k)]; while heap: d,u=heapq.heappop(heap); if d>dist[u]: continue; for v,w in graph[u]: if dist[u]+w<dist[v]: dist[v]=dist[u]+w; heapq.heappush(heap,(dist[v],v)); return max(dist.values()) if max(dist.values())<float('inf') else -1`.",
        "solution_text": (
            "Дейкстра с min-heap. Жадный: всегда расширяем ближайшую необработанную вершину.\n"
            "⏱ Сложность: O((V+E) log V) по времени, O(V+E) по памяти."
        ),
        "failing_test": "Граф с недостижимой вершиной → max расстояний = inf → вернуть -1.",
        "time_complexity": "O((V+E) log V)",
        "space_complexity": "O(V+E)",
    },
    {
        "title": "Разбиение строки на палиндромы (Palindrome Partitioning II)",
        "level": "senior",
        "description": (
            "Дана строка `s`. Найди минимальное количество разрезов для разбиения s на палиндромы."
        ),
        "examples": [
            {"input": 's = "aab"', "output": "1", "explanation": '"aa" + "b"'},
            {"input": 's = "a"', "output": "0"},
            {"input": 's = "ab"', "output": "1"},
        ],
        "constraints": ["1 <= s.length <= 2000"],
        "hint1": "DP: dp[i] — минимальное число разрезов для s[:i+1]. Предвычисли is_palindrome[i][j].",
        "hint2": "is_palindrome через расширение от центра. dp[i] = min(dp[j-1]+1) для всех j<=i где s[j:i+1] — палиндром.",
        "hint3": "Предвычисление palindrome: `pal=[[False]*n for _ in range(n)]; for center in range(2*n-1): l,r=center//2,center//2+center%2; while l>=0 and r<n and s[l]==s[r]: pal[l][r]=True; l-=1; r+=1`. DP: `dp=[i for i in range(n)]; for i in range(n): if pal[0][i]: dp[i]=0; continue; for j in range(1,i+1): if pal[j][i]: dp[i]=min(dp[i],dp[j-1]+1)`.",
        "solution_text": (
            "Два DP: 1) матрица палиндромов O(n²). 2) dp[i] = минимальные разрезы. Итого O(n²) время и память.\n"
            "⏱ Сложность: O(n²) по времени и памяти."
        ),
        "failing_test": 's = "aaa" → ожидается 0. Вся строка — палиндром, 0 разрезов.',
        "time_complexity": "O(n²)",
        "space_complexity": "O(n²)",
    },
    {
        "title": "Burst Balloons",
        "level": "senior",
        "description": (
            "Дан массив `nums` воздушных шариков. При сдутии шарика i получаешь nums[i-1]*nums[i]*nums[i+1] монет. "
            "Найди максимальное количество монет от сдутия всех шариков (границы = 1)."
        ),
        "examples": [
            {"input": "nums = [3,1,5,8]", "output": "167", "explanation": "3*1*5=15, 3*5*8=120, 3*8=24, 8=8"},
            {"input": "nums = [1,5]", "output": "10"},
        ],
        "constraints": ["1 <= nums.length <= 300"],
        "hint1": "Интервальное DP: dp[l][r] — максимум монет от сдутия шариков в интервале (l,r) исключительно.",
        "hint2": "Вместо последнего оставшегося думай: какой шарик k сдуть ПОСЛЕДНИМ в интервале (l,r)?",
        "hint3": "dp[l][r] = max(nums[l]*nums[k]*nums[r] + dp[l][k] + dp[k][r]) по всем k в (l,r). Базовый случай: dp[l][r]=0 если r-l<2. Добавь 1 на границы: `nums = [1] + nums + [1]`.",
        "solution_text": (
            "Интервальный DP: 'последний шарик в интервале'. dp[l][r] = max по k ∈ (l,r): nums[l]*nums[k]*nums[r] + dp[l][k] + dp[k][r].\n"
            "⏱ Сложность: O(n³) по времени, O(n²) по памяти."
        ),
        "failing_test": "nums = [1] → ожидается 1. Один шарик: 1*1*1 = 1.",
        "time_complexity": "O(n³)",
        "space_complexity": "O(n²)",
    },
    {
        "title": "Медиана потока v2 (оптимизация)",
        "level": "senior",
        "description": (
            "Реализуй структуру данных MedianFinder, которая поддерживает:\n"
            "- `addNum(num)`: добавить число\n"
            "- `findMedian()`: вернуть медиану текущего набора\n"
            "Все операции должны быть максимально эффективны."
        ),
        "examples": [
            {"input": "addNum(1), addNum(2), findMedian() → addNum(3), findMedian()", "output": "1.5, 2.0"},
        ],
        "constraints": ["-10⁵ <= num <= 10⁵", "вызовы findMedian только при непустом наборе"],
        "hint1": "Два heap: max-heap для левой половины, min-heap для правой. Размеры отличаются не более чем на 1.",
        "hint2": "addNum: добавь в max_heap (через отрицание для Python), балансируй размеры через перекидывание элементов.",
        "hint3": "Реализация: `self.small=[] # max-heap (нег.)`. `self.large=[] # min-heap`. addNum: heappush(small, -num); heappush(large, -heappop(small)); if len(large)>len(small): heappush(small,-heappop(large)). findMedian: if len(small)>len(large): return -small[0]; return (-small[0]+large[0])/2.",
        "solution_text": (
            "Два heap балансируют левую и правую половины. Медиана = вершина большего heap или среднее двух вершин.\n"
            "⏱ Сложность: O(log n) на addNum, O(1) на findMedian."
        ),
        "failing_test": "addNum(2), addNum(3), findMedian() = 2.5. Два элемента, медиана = среднее.",
        "time_complexity": "O(log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "N Ферзей (N-Queens)",
        "level": "senior",
        "description": (
            "Дано число `n`. Расставь n ферзей на шахматной доске n×n так, чтобы они не атаковали друг друга. "
            "Верни все допустимые расстановки."
        ),
        "examples": [
            {"input": "n = 4", "output": '[[ ".Q..","...Q","Q...","..Q." ],[ "..Q.","Q...","...Q",".Q.." ]]'},
            {"input": "n = 1", "output": '[["Q"]]'},
        ],
        "constraints": ["1 <= n <= 9"],
        "hint1": "Бэктрекинг по строкам: для каждой строки пробуй все колонки.",
        "hint2": "Безопасность: ферзь атакует по колонке (col), по главной диагонали (row-col), по побочной диагонали (row+col).",
        "hint3": "Три множества: cols, diag1 (r-c), diag2 (r+c). Бэктрекинг: для каждой строки r выбирай колонку c не в запрещённых. Добавь в множества, рекурсия для r+1, убери (backtrack).",
        "solution_text": (
            "Бэктрекинг + три set для проверки атаки. O(n!) по времени, O(n²) по памяти для хранения результата.\n"
            "⏱ Сложность: O(n!) по времени."
        ),
        "failing_test": "n=4 → ровно 2 решения. Убедись, что не добавляешь дубликаты.",
        "time_complexity": "O(n!)",
        "space_complexity": "O(n²)",
    },
    {
        "title": "Expression Add Operators",
        "level": "senior",
        "description": (
            "Дана строка цифр `num` и целое `target`. Вставь операторы +, -, * между цифрами "
            "так, чтобы выражение давало target. Верни все такие выражения."
        ),
        "examples": [
            {"input": 'num = "123", target = 6', "output": '["1*2*3","1+2+3"]'},
            {"input": 'num = "232", target = 8', "output": '["2*3+2","2+3*2"]'},
            {"input": 'num = "3456237490", target = 9191', "output": "[]"},
        ],
        "constraints": ["1 <= num.length <= 10", "-2³¹ <= target <= 2³¹-1"],
        "hint1": "Бэктрекинг: на каждом шаге выбирай следующий фрагмент числа и оператор.",
        "hint2": "Отслеживай `current_eval` (текущая сумма) и `last_operand` (последнее слагаемое для обработки умножения).",
        "hint3": "При умножении: new_eval = current - last + last*current_num. Это позволяет корректно обрабатывать приоритет умножения без скобок.",
        "solution_text": (
            "Бэктрекинг с отслеживанием last_operand. Умножение: вычитаем last, прибавляем last*n (переприоритет).\n"
            "⏱ Сложность: O(4ⁿ × n) по времени и памяти."
        ),
        "failing_test": 'num = "105", target = 5 → включает "1*0+5" и "10-5". Нельзя использовать ведущие нули в числах (кроме "0" самого по себе).',
        "time_complexity": "O(4ⁿ·n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Количество меньших элементов справа (Count of Smaller Numbers After Self)",
        "level": "senior",
        "description": (
            "Дан массив `nums`. Для каждого элемента подсчитай количество элементов справа, которые строго меньше его."
        ),
        "examples": [
            {"input": "nums = [5,2,6,1]", "output": "[2,1,1,0]"},
            {"input": "nums = [-1]", "output": "[0]"},
            {"input": "nums = [-1,-1]", "output": "[0,0]"},
        ],
        "constraints": ["1 <= nums.length <= 10⁵", "-10⁴ <= nums[i] <= 10⁴"],
        "hint1": "Merge sort подход: при слиянии считай, сколько элементов из правой половины меньше текущего.",
        "hint2": "Или BIT (Binary Indexed Tree / Fenwick Tree): координатное сжатие + запросы на PREFIX сумму.",
        "hint3": "Merge sort: при слиянии, когда правый[j] < левый[i], все элементы left[i..] имеют правый[j] справа. BIT: обходи nums справа налево, запрашивай prefix_sum(val-1), обновляй val.",
        "solution_text": (
            "Merge sort с подсчётом инверсий: при слиянии, если right[j] < left[i], то j элементов правой части меньше left[i].\n"
            "⏱ Сложность: O(n log n) по времени, O(n) по памяти."
        ),
        "failing_test": "nums = [1,2,3] → ожидается [0,0,0]. Нет элементов справа меньше каждого в порядке возрастания.",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Решение судоку (Sudoku Solver)",
        "level": "senior",
        "description": (
            "Дана частично заполненная доска судоку 9×9. Заполни её корректно на месте. "
            "Пустые клетки обозначены '.'."
        ),
        "examples": [
            {"input": "board = (9×9 матрица с цифрами и '.')", "output": "заполненная доска"},
        ],
        "constraints": ["Каждая строка/столбец/блок 3×3 содержат цифры 1-9 без повторений", "гарантируется ровно одно решение"],
        "hint1": "Бэктрекинг: найди пустую клетку, пробуй цифры 1-9, проверяй допустимость.",
        "hint2": "Допустимость: цифра не встречается в той же строке, столбце и блоке 3×3.",
        "hint3": "Оптимизация: предвычисли множества занятых цифр для rows[r], cols[c], boxes[(r//3)*3+c//3]. При заполнении обновляй, при откате — убирай. Это ускоряет проверку до O(1).",
        "solution_text": (
            "Бэктрекинг с предвычисленными множествами rows/cols/boxes. Для каждой пустой клетки пробуем 1-9, откатываемся при неудаче.\n"
            "⏱ Сложность: O(9^m) где m — число пустых клеток (ограничено 81)."
        ),
        "failing_test": "Клетка с единственным вариантом — всё равно проходим бэктрекинг (просто быстро). Без оптимизации порядка обхода возможно O(9⁸¹).",
        "time_complexity": "O(9^m)",
        "space_complexity": "O(1)",
    },
    {
        "title": "Кратчайший суперстринг (Shortest Superstring)",
        "level": "senior",
        "description": (
            "Дан массив слов `words`. Найди кратчайшую строку, которая является надстрокой (суперстрокой) "
            "для всех слов в массиве (каждое слово является подстрокой результата)."
        ),
        "examples": [
            {"input": 'words = ["alex","loves","leetcode"]', "output": '"alexlovesleetcode"'},
            {"input": 'words = ["catg","ctaagt","gcta","ttca","atgcatc"]', "output": '"gctaagttcatgcatc"'},
        ],
        "constraints": ["1 <= words.length <= 12", "1 <= words[i].length <= 20"],
        "hint1": "Задача коммивояжёра (TSP) на строках. DP с битмасками: dp[mask][i] — минимальная длина для посещённых слов mask, заканчивающаяся словом i.",
        "hint2": "Предвычисли `overlap[i][j]` — максимальный суффикс words[i], совпадающий с префиксом words[j].",
        "hint3": "dp[mask|(1<<j)][j] = min(dp[mask][i] + len(words[j]) - overlap[i][j]). Ответ: реконструируй путь из dp[(1<<n)-1][i].",
        "solution_text": (
            "TSP DP с битмасками. Состояние: (mask посещённых, последнее слово). Предвычисление перекрытий за O(n²×L).\n"
            "⏱ Сложность: O(n²×2ⁿ) по времени, O(n×2ⁿ) по памяти."
        ),
        "failing_test": 'words = ["a","b"] → ожидается "ab" или "ba" (длина 2). Перекрытие нулевое.',
        "time_complexity": "O(n²·2ⁿ)",
        "space_complexity": "O(n·2ⁿ)",
    },
    {
        "title": "Максимальный разрыв (Maximum Gap)",
        "level": "senior",
        "description": (
            "Дан массив `nums`. После сортировки верни максимальную разность между соседними элементами. "
            "Реши за O(n) без стандартной сортировки."
        ),
        "examples": [
            {"input": "nums = [3,6,9,1]", "output": "3"},
            {"input": "nums = [10]", "output": "0"},
        ],
        "constraints": ["1 <= nums.length <= 10⁵", "0 <= nums[i] <= 10⁹"],
        "hint1": "Bucket sort / pigeonhole principle: при n элементах максимальный разрыв ≥ (max-min)/(n-1).",
        "hint2": "Разбей диапазон на n-1 корзин размером `bucket_size = max((max-min)//(n-1), 1)`. Максимальный разрыв — между корзинами.",
        "hint3": "Для каждой корзины храни только min и max. Разрыв = bucket[i].min - bucket[i-1].max для непустых соседних корзин. Гарантируется, что максимальный разрыв не внутри корзины, а между ними.",
        "solution_text": (
            "Bucket sort: n-1 корзин. Разрыв всегда между соседними непустыми корзинами (принцип клеток).\n"
            "⏱ Сложность: O(n) по времени и памяти."
        ),
        "failing_test": "nums = [1, 10000000] → ожидается 9999999. Два элемента, разрыв между ними.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Word Ladder II",
        "level": "senior",
        "description": (
            "Даны `beginWord`, `endWord` и `wordList`. Найди все кратчайшие последовательности трансформаций "
            "от beginWord до endWord (за одну трансформацию меняется одна буква, результат должен быть в wordList)."
        ),
        "examples": [
            {"input": 'beginWord="hit", endWord="cog", wordList=["hot","dot","dog","lot","log","cog"]', "output": '[["hit","hot","dot","dog","cog"],["hit","hot","lot","log","cog"]]'},
            {"input": 'beginWord="hit", endWord="cog", wordList=["hot","dot","dog","lot","log"]', "output": "[]"},
        ],
        "constraints": ["1 <= beginWord.length <= 5", "1 <= wordList.length <= 500"],
        "hint1": "BFS для нахождения кратчайшего расстояния + BFS/DFS для восстановления всех путей.",
        "hint2": "BFS строит граф предшественников (parents[word] = set(слов, от которых пришли). Затем DFS от endWord обратно до beginWord.",
        "hint3": "BFS по уровням: обрабатываем все слова уровня перед удалением из wordSet. Это даёт все кратчайшие пути. Затем рекурсивный DFS по parents для восстановления.",
        "solution_text": (
            "BFS строит дерево кратчайших путей (parents dict). DFS обходит дерево от endWord к beginWord, добавляет перевёрнутые пути.\n"
            "⏱ Сложность: O(N×L²) где N — слов, L — длина слова."
        ),
        "failing_test": "endWord не в wordList → пустой список. Проверяй заранее.",
        "time_complexity": "O(N·L²)",
        "space_complexity": "O(N·L)",
    },
    {
        "title": "Потоки в сети (Network Flow — Max Flow)",
        "level": "senior",
        "description": (
            "Дан ориентированный граф с пропускными способностями рёбер. "
            "Найди максимальный поток от источника `source` до стока `sink` (алгоритм Форда-Фалкерсона / BFS)."
        ),
        "examples": [
            {"input": "graph = [[0,16,13,0,0,0],[0,0,10,12,0,0],[0,4,0,0,14,0],[0,0,9,0,0,20],[0,0,0,7,0,4],[0,0,0,0,0,0]], source=0, sink=5", "output": "23"},
        ],
        "constraints": ["2 <= n <= 20", "0 <= capacity <= 1000"],
        "hint1": "Алгоритм Эдмондса-Карпа: BFS находит дополняющий путь. Увеличивай поток вдоль пути на min(bottleneck).",
        "hint2": "Используй матрицу остаточных пропускных способностей. После увеличения потока обновляй: rg[u][v] -= flow; rg[v][u] += flow.",
        "hint3": "BFS: находит путь от source до sink в остаточном графе. Если путь найден — увеличивай поток. Повторяй пока пути есть.",
        "solution_text": (
            "Эдмондс-Карп (BFS дополняющих путей): каждый BFS за O(VE), всего O(VE²) итераций.\n"
            "⏱ Сложность: O(V×E²) по времени, O(V²) по памяти."
        ),
        "failing_test": "source = sink → ожидается 0 (нет смысла в потоке из источника в себя).",
        "time_complexity": "O(V·E²)",
        "space_complexity": "O(V²)",
    },
    {
        "title": "Ближайшая пара точек",
        "level": "senior",
        "description": (
            "Дан массив точек `points = [[x,y]]`. Найди минимальное расстояние между двумя точками. "
            "Реши за O(n log n)."
        ),
        "examples": [
            {"input": "points = [[0,0],[1,0],[3,0]]", "output": "1.0"},
            {"input": "points = [[1,1],[3,4],[-1,0]]", "output": "2.8284"},
        ],
        "constraints": ["2 <= points.length <= 10⁴", "-10⁶ <= x, y <= 10⁶"],
        "hint1": "Разделяй и властвуй: разбей по x-координате, рекурсивно ищи в каждой половине, проверь полосу d вдоль границы.",
        "hint2": "После нахождения d = min(d_left, d_right): рассматривай только точки в полосе ±d от границы. Сортируй по y и проверяй соседей (не более 7 сравнений).",
        "hint3": "Реализация: `def closest(pts): if len(pts)<=3: brute_force; mid=len(pts)//2; mx=pts[mid][0]; d=min(closest(pts[:mid]), closest(pts[mid:])); strip=[p for p in pts if abs(p[0]-mx)<d]; strip.sort(key=lambda p:p[1]); for i,p in enumerate(strip): for q in strip[i+1:]: if q[1]-p[1]>=d: break; d=min(d,dist(p,q)); return d`.",
        "solution_text": (
            "Divide & Conquer. Полоса вдоль медианы содержит ≤ 8 точек в окне 2d×d, поэтому внутренний цикл O(1).\n"
            "⏱ Сложность: O(n log² n) или O(n log n) с предсортировкой по y."
        ),
        "failing_test": "points = [[0,0],[0,0]] → ожидается 0.0. Совпадающие точки имеют нулевое расстояние.",
        "time_complexity": "O(n log² n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Суффиксный массив (построение)",
        "level": "senior",
        "description": (
            "Дана строка `s`. Построй суффиксный массив (SA) — массив индексов суффиксов, "
            "отсортированных лексикографически. Реши за O(n log n)."
        ),
        "examples": [
            {"input": 's = "banana"', "output": "[5,3,1,0,4,2]", "explanation": "a, ana, anana, banana, na, nana"},
            {"input": 's = "aab"', "output": "[0,1,2]"},
        ],
        "constraints": ["1 <= s.length <= 10⁵"],
        "hint1": "Наивно: отсортировать все суффиксы за O(n² log n). Оптимально: prefix doubling (Манбер-Майерс) за O(n log n).",
        "hint2": "Prefix doubling: на k-м шаге ранжируем суффиксы по первым 2^k символам. Используем ранги предыдущего шага как 'цифры' для radix sort.",
        "hint3": "SA-IS алгоритм строит суффиксный массив за O(n). Для практических целей: `sorted(range(len(s)), key=lambda i: s[i:])` за O(n² log n) — приемлемо для n<1000.",
        "solution_text": (
            "Prefix doubling: каждые 2^k символов удваивают длину ключа сортировки. O(n log² n) с обычной сортировкой, O(n log n) с radix sort.\n"
            "⏱ Сложность: O(n log² n) с простой реализацией."
        ),
        "failing_test": 's = "a" → ожидается [0]. Один суффикс — сам по себе.',
        "time_complexity": "O(n log² n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Алгоритм KMP (поиск подстроки)",
        "level": "senior",
        "description": (
            "Реализуй алгоритм Кнута-Морриса-Пратта для поиска всех вхождений паттерна `pattern` в строке `text`. "
            "Верни список стартовых индексов."
        ),
        "examples": [
            {"input": 'text = "aabxaabyaab", pattern = "aab"', "output": "[0,4,8]"},
            {"input": 'text = "aaaa", pattern = "aa"', "output": "[0,1,2]"},
        ],
        "constraints": ["1 <= text.length, pattern.length <= 10⁵"],
        "hint1": "Предвычисли prefix-function (failure function) для паттерна. Она показывает, куда 'перепрыгнуть' при несовпадении.",
        "hint2": "prefix[i] = длина наибольшего собственного префикса-суффикса для pattern[:i+1].",
        "hint3": "KMP поиск: `j=0; for i,c in enumerate(text): while j>0 and c!=pattern[j]: j=prefix[j-1]; if c==pattern[j]: j+=1; if j==len(pattern): result.append(i-j+1); j=prefix[j-1]`.",
        "solution_text": (
            "Prefix function + KMP поиск. При несовпадении откатываемся по prefix function — не с нуля.\n"
            "⏱ Сложность: O(n+m) по времени, O(m) по памяти."
        ),
        "failing_test": 'text = "aaa", pattern = "aa" → ожидается [0,1]. Перекрывающиеся вхождения допустимы.',
        "time_complexity": "O(n+m)",
        "space_complexity": "O(m)",
    },
    {
        "title": "Алгоритм Манакера (Longest Palindromic Substring)",
        "level": "senior",
        "description": (
            "Дана строка `s`. Найди наидлиннейшую палиндромическую подстроку за O(n)."
        ),
        "examples": [
            {"input": 's = "babad"', "output": '"bab"'},
            {"input": 's = "cbbd"', "output": '"bb"'},
            {"input": 's = "racecar"', "output": '"racecar"'},
        ],
        "constraints": ["1 <= s.length <= 10⁵"],
        "hint1": "Алгоритм Манакера: трансформируй строку вставкой '#' между символами. Затем за O(n) вычисли радиус палиндрома для каждого центра.",
        "hint2": "Поддерживай текущий 'зонтик' (центр c и правая граница r). Используй зеркальный центр для ускорения.",
        "hint3": "Трансформация: 'abc' → '#a#b#c#'. Для позиции i: p[i] = min(r-i, p[2*c-i]) если i<r, иначе 0. Затем расширяй. При расширении за r обновляй c,r.",
        "solution_text": (
            "Манакер: O(n) через 'зонтик' (текущий наибольший палиндром). Зеркальный центр позволяет переиспользовать уже вычисленные значения.\n"
            "⏱ Сложность: O(n) по времени, O(n) по памяти."
        ),
        "failing_test": 's = "a" → ожидается "a". Один символ — палиндром длиной 1.',
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Взвешенное планирование задач (Weighted Job Scheduling)",
        "level": "senior",
        "description": (
            "Дан список задач `jobs = [[start, end, profit]]`. Задачи не могут перекрываться. "
            "Найди максимальную суммарную прибыль от выбранного подмножества задач."
        ),
        "examples": [
            {"input": "jobs = [[1,2,50],[3,5,20],[6,19,100],[2,100,200]]", "output": "250"},
            {"input": "jobs = [[1,3,20],[2,5,20],[3,10,100],[4,6,70],[6,9,60]]", "output": "150"},
        ],
        "constraints": ["1 <= jobs.length <= 10⁵"],
        "hint1": "Отсортируй по времени окончания. DP: dp[i] — максимальная прибыль до задачи i включительно.",
        "hint2": "Для задачи i: либо берём её (dp[j] + profit[i] где j — последняя задача, не пересекающаяся с i), либо нет (dp[i-1]).",
        "hint3": "Бинарный поиск для нахождения j: наибольший j с end[j] <= start[i]. dp[i] = max(dp[i-1], dp[j]+profit[i]). `from bisect import bisect_right; ends=[job[1] for job in sorted_jobs]; j=bisect_right(ends, start_i)-1`.",
        "solution_text": (
            "DP по задачам (сортировка по end). Бинарный поиск находит последнюю совместимую задачу за O(log n).\n"
            "⏱ Сложность: O(n log n) по времени, O(n) по памяти."
        ),
        "failing_test": "jobs = [[1,2,10],[1,2,20]] → ожидается 20. Выбираем прибыльнейшую из двух в одно время.",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Минимальное остовное дерево (Kruskal)",
        "level": "senior",
        "description": (
            "Дан взвешенный граф из n вершин и списка рёбер `edges = [[u, v, weight]]`. "
            "Найди суммарный вес минимального остовного дерева (MST)."
        ),
        "examples": [
            {"input": "n=4, edges=[[0,1,10],[0,2,6],[0,3,5],[1,3,15],[2,3,4]]", "output": "19"},
            {"input": "n=2, edges=[[0,1,5]]", "output": "5"},
        ],
        "constraints": ["2 <= n <= 10⁵", "1 <= edges.length <= 2×10⁵"],
        "hint1": "Алгоритм Крускала: сортируй рёбра по весу. Добавляй ребро если оно не создаёт цикл (Union-Find).",
        "hint2": "Union-Find с ранговой оптимизацией и сжатием путей: find(x) + union(x,y).",
        "hint3": "Реализация: `edges.sort(key=lambda e:e[2]); parent=list(range(n)); rank=[0]*n; def find(x): while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]; return x; def union(x,y): px,py=find(x),find(y); if px==py: return False; if rank[px]<rank[py]: px,py=py,px; parent[py]=px; if rank[px]==rank[py]: rank[px]+=1; return True; total=0; for u,v,w in edges: if union(u,v): total+=w; return total`.",
        "solution_text": (
            "Крускал: сортировка рёбер + Union-Find. Добавляем минимальные рёбра не создающие цикл.\n"
            "⏱ Сложность: O(E log E) по времени, O(V) по памяти."
        ),
        "failing_test": "Граф не связный → MST не существует. Обрабатывай этот случай отдельно.",
        "time_complexity": "O(E log E)",
        "space_complexity": "O(V)",
    },
    {
        "title": "Наибольшая прямоугольная подматрица нулей",
        "level": "senior",
        "description": (
            "Дана бинарная матрица. Найди площадь наибольшей прямоугольной подматрицы, "
            "состоящей только из 1. Это обобщение задачи о прямоугольнике в гистограмме."
        ),
        "examples": [
            {"input": "matrix = [[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]", "output": "6"},
            {"input": "matrix = [[0]]", "output": "0"},
            {"input": "matrix = [[1]]", "output": "1"},
        ],
        "constraints": ["1 <= rows, cols <= 200"],
        "hint1": "Для каждой строки вычисли высоту столбца (число единиц подряд над ней). Применяй алгоритм гистограммы.",
        "hint2": "heights[j] = heights[j]+1 если matrix[i][j]=='1', иначе 0. Затем вызови largestRectangleInHistogram(heights).",
        "hint3": "largestRectangle через монотонный стек: `stack=[]; max_area=0; for i,h in enumerate(heights+[0]): while stack and heights[stack[-1]]>h: height=heights[stack.pop()]; w=i if not stack else i-stack[-1]-1; max_area=max(max_area,height*w); stack.append(i); return max_area`.",
        "solution_text": (
            "Строка за строкой обновляем высоты + largestRectangleHistogram через стек. O(m×n) итого.\n"
            "⏱ Сложность: O(m×n) по времени, O(n) по памяти."
        ),
        "failing_test": "matrix = [[0,0],[0,0]] → ожидается 0. Нет единиц.",
        "time_complexity": "O(m·n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Топологическая сортировка: порядок курсов (Course Schedule II)",
        "level": "senior",
        "description": (
            "Дано `numCourses` и список зависимостей. Верни порядок прохождения всех курсов. "
            "Если невозможно — верни пустой список."
        ),
        "examples": [
            {"input": "numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]", "output": "[0,2,1,3] или [0,1,2,3]"},
            {"input": "numCourses = 1, prerequisites = []", "output": "[0]"},
            {"input": "numCourses = 2, prerequisites = [[0,1],[1,0]]", "output": "[]"},
        ],
        "constraints": ["1 <= numCourses <= 2000"],
        "hint1": "Алгоритм Кана: BFS по вершинам с in-degree=0. Добавляй в результат по мере обработки.",
        "hint2": "Граф + in-degree. BFS из всех вершин с нулевым in-degree. При обработке снижай in-degree соседей.",
        "hint3": "Аналогично Course Schedule I, но сохраняй порядок. `order=[]; q=deque(i for i in range(n) if in_deg[i]==0); while q: node=q.popleft(); order.append(node); for nei in graph[node]: in_deg[nei]-=1; if in_deg[nei]==0: q.append(nei); return order if len(order)==n else []`.",
        "solution_text": (
            "Kahn's BFS топологическая сортировка. Если обработали все n курсов — возвращаем порядок, иначе [].\n"
            "⏱ Сложность: O(V+E) по времени и памяти."
        ),
        "failing_test": "prerequisites = [[0,0]] → ожидается []. Самозависимость = цикл.",
        "time_complexity": "O(V+E)",
        "space_complexity": "O(V+E)",
    },
    {
        "title": "Автозаполнение системы поиска (Design Search Autocomplete System)",
        "level": "senior",
        "description": (
            "Реализуй систему автозаполнения. Дан список sentences и times (частоты). "
            "input(c): добавляет символ в текущий запрос, возвращает топ-3 исторических предложения по частоте."
        ),
        "examples": [
            {"input": "sentences=['i love you','island','iroman','i love leetcode'], times=[5,3,2,2]; input('i')→['i love you','island','i love leetcode']"},
        ],
        "constraints": ["1 <= sentences.length <= 100"],
        "hint1": "Используй Trie для быстрого поиска по префиксу. Каждый узел Trie хранит список предложений с их частотами.",
        "hint2": "При вводе '#' — сохрани текущее предложение, сбрось буфер. Иначе — ищи в Trie по текущему буферу.",
        "hint3": "В каждом узле Trie: dict предложение→частота. При поиске по префиксу: дойди до узла, верни топ-3 по частоте (при равенстве — лексикографически меньшее первым).",
        "solution_text": (
            "Trie + словарь частот в узлах. input('#') сохраняет предложение. Поиск по префиксу за O(prefix_len + k log k).\n"
            "⏱ Сложность: O(n×L) на построение, O(L + k log k) на запрос."
        ),
        "failing_test": "При вводе '#' текущий запрос становится историческим. Следующий input начинается с чистого буфера.",
        "time_complexity": "O(n·L) на построение",
        "space_complexity": "O(n·L)",
    },
    {
        "title": "Longest Consecutive Sequence",
        "level": "senior",
        "description": (
            "Дан массив `nums`. Найди длину наидлиннейшей последовательности "
            "подряд идущих натуральных чисел. Реши за O(n)."
        ),
        "examples": [
            {"input": "nums = [100,4,200,1,3,2]", "output": "4", "explanation": "[1,2,3,4]"},
            {"input": "nums = [0,3,7,2,5,8,4,6,0,1]", "output": "9"},
        ],
        "constraints": ["0 <= nums.length <= 10⁵", "-10⁹ <= nums[i] <= 10⁹"],
        "hint1": "Помести все числа в set. Для каждого числа — если num-1 не в set, это начало последовательности.",
        "hint2": "Начиная с начала последовательности, считай длину, пока num+1 в set.",
        "hint3": "Полная реализация: `num_set=set(nums); best=0; for n in num_set: if n-1 not in num_set: cur=n; length=1; while cur+1 in num_set: cur+=1; length+=1; best=max(best,length); return best`.",
        "solution_text": (
            "Hash set + старт только от начал последовательностей (n-1 не в set). Каждый элемент обрабатывается O(1).\n"
            "⏱ Сложность: O(n) по времени и памяти."
        ),
        "failing_test": "nums = [] → ожидается 0. Пустой массив.",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
    },
    {
        "title": "Shortest Path Visiting All Nodes",
        "level": "senior",
        "description": (
            "Дан неориентированный граф n вершин (список смежности `graph`). "
            "Найди длину кратчайшего пути, посещающего все вершины. Можно посещать вершины повторно."
        ),
        "examples": [
            {"input": "graph = [[1,2,3],[0],[0],[0]]", "output": "4"},
            {"input": "graph = [[1],[0,2,4],[1,3,4],[2],[1,2]]", "output": "4"},
        ],
        "constraints": ["1 <= n <= 12", "0 <= graph[i][j] < n"],
        "hint1": "BFS с состоянием (current_node, visited_mask). Кратчайший путь — BFS по умолчанию.",
        "hint2": "Состояний: n × 2ⁿ. Стартуем из каждой вершины с visited={i}.",
        "hint3": "Реализация: `from collections import deque; visited=set(); q=deque(); for i in range(n): state=(i,1<<i); q.append((state,0)); visited.add(state); full=(1<<n)-1; while q: (node,mask),dist=q.popleft(); if mask==full: return dist; for nei in graph[node]: new_mask=mask|(1<<nei); if (nei,new_mask) not in visited: visited.add((nei,new_mask)); q.append(((nei,new_mask),dist+1))`.",
        "solution_text": (
            "BFS с битовой маской посещённых вершин. Состояние (node, mask), цель — mask = (1<<n)-1.\n"
            "⏱ Сложность: O(n × 2ⁿ) по времени и памяти."
        ),
        "failing_test": "graph = [[0]] → ожидается 0. Одна вершина, уже посещена.",
        "time_complexity": "O(n·2ⁿ)",
        "space_complexity": "O(n·2ⁿ)",
    },
    {
        "title": "Число способов расставить скобки (Catalan числа)",
        "level": "senior",
        "description": (
            "Дано n. Найди n-е число Каталана — количество правильных скобочных последовательностей "
            "из n пар скобок. Реши несколькими способами: формула, рекуррентность, DP."
        ),
        "examples": [
            {"input": "n = 0", "output": "1"},
            {"input": "n = 3", "output": "5"},
            {"input": "n = 5", "output": "42"},
        ],
        "constraints": ["0 <= n <= 19"],
        "hint1": "Формула: C(n) = C(2n, n) / (n+1). Рекуррентность: C(0)=1; C(n) = sum(C(i)*C(n-1-i)) для i от 0 до n-1.",
        "hint2": "DP: `dp[0]=1; for i in range(1,n+1): dp[i]=sum(dp[j]*dp[i-1-j] for j in range(i))`.",
        "hint3": "Числа Каталана: 1, 1, 2, 5, 14, 42, 132, 429... Формула через биномиальный коэффициент: `from math import comb; return comb(2*n, n) // (n+1)`.",
        "solution_text": (
            "Через формулу: comb(2n,n)//(n+1) — O(n). Через DP: O(n²). Оба дают правильный ответ для n≤19.\n"
            "⏱ Сложность: O(1) или O(n²) в зависимости от метода."
        ),
        "failing_test": "n=0 → ожидается 1. Пустая последовательность — тривиальный случай.",
        "time_complexity": "O(1) формула / O(n²) DP",
        "space_complexity": "O(n)",
    },
    {
        "title": "Минимальное покрытие вершин (Vertex Cover — NP, аппроксимация)",
        "level": "senior",
        "description": (
            "Дан неориентированный граф. Найди приближённое минимальное покрытие вершин (2-аппроксимация). "
            "Вернуть множество вершин, покрывающих все рёбра."
        ),
        "examples": [
            {"input": "n=5, edges=[[0,1],[0,2],[1,2],[1,3],[3,4]]", "output": "[0,1,3] или другое корректное покрытие"},
        ],
        "constraints": ["1 <= n <= 100", "допускается 2-аппроксимация"],
        "hint1": "Жадный 2-аппроксимационный алгоритм: пока есть непокрытые рёбра — возьми произвольное ребро (u,v), добавь оба конца в покрытие, удали все инцидентные рёбра.",
        "hint2": "Алгоритм гарантирует решение не хуже 2×OPT (оптимальное покрытие не может быть меньше половины нашего).",
        "hint3": "Реализация: `cover=set(); remaining=set(map(tuple,edges)); while remaining: u,v=next(iter(remaining)); cover.add(u); cover.add(v); remaining={e for e in remaining if u not in e and v not in e}; return list(cover)`.",
        "solution_text": (
            "2-аппроксимация: жадно берём ребро и обоих его концов в покрытие. Удаляем все инцидентные рёбра.\n"
            "⏱ Сложность: O(V+E) по времени и памяти."
        ),
        "failing_test": "Результат может отличаться от оптимального, но гарантированно ≤ 2×OPT. Проверяй что все рёбра покрыты.",
        "time_complexity": "O(V+E)",
        "space_complexity": "O(V+E)",
    },
    {
        "title": "Потоки с минимальной стоимостью (Min-Cost Max-Flow)",
        "level": "senior",
        "description": (
            "Дан граф с пропускными способностями и стоимостями рёбер. "
            "Найди максимальный поток минимальной стоимости от источника до стока."
        ),
        "examples": [
            {"input": "n=4, source=0, sink=3; edges: (0,1,cap=3,cost=1), (0,2,cap=2,cost=3), (1,3,cap=2,cost=1), (2,3,cap=2,cost=2), (1,2,cap=1,cost=2)", "output": "flow=4, cost=12"},
        ],
        "constraints": ["2 <= n <= 50", "0 <= cost <= 100"],
        "hint1": "SPFA (Bellman-Ford с очередью) или Dijkstra с потенциалами для нахождения кратчайшего пути по стоимости. Увеличивай поток вдоль пути.",
        "hint2": "Остаточный граф: для каждого ребра (u,v,cap,cost) добавь обратное (v,u,0,-cost).",
        "hint3": "Алгоритм: пока есть путь от source до sink с минимальной стоимостью — увеличивай поток на минимальное bottleneck, обновляй остаточный граф, прибавляй cost×flow к ответу.",
        "solution_text": (
            "SPFA для нахождения кратчайшего по стоимости пути в остаточном графе. Повторяем пока возможно увеличение потока.\n"
            "⏱ Сложность: O(V×E×max_flow) в худшем случае."
        ),
        "failing_test": "Если нет пути source→sink — поток 0, стоимость 0.",
        "time_complexity": "O(V·E·f)",
        "space_complexity": "O(V+E)",
    },
]
