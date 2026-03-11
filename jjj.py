import numpy as np
import random
import time

def f(x):
    x1, x2 = x
    return 32 * x1 * x1 + 63 * x1 * x2 + 32 * x2 * x2 - 5 * x1 + 15 * x2 + 6


def regular_simplex_method(f, x0, a=0.3, eps=1e-7, max_iter=10000):
    n = len(x0)
    x0 = np.array(x0, dtype=float)

    # Вспомогательные коэффициенты для построения правильного симплекса
    d1 = a * (np.sqrt(n + 1) + n - 1) / (n * np.sqrt(2))
    d2 = a * (np.sqrt(n + 1) - 1) / (n * np.sqrt(2))

    # Начальный этап: построение начального симплекса
    simplex = [x0]
    for i in range(n):
        point = x0 + d2
        point[i] += (d1 - d2)
        simplex.append(point)

    for iteration in range(max_iter):
        # Вычислить значения и упорядочить f(x0) <= f(x1) <= ... <= f(xn)
        simplex.sort(key=f)
        f_values = [f(x) for x in simplex]

        # Проверка условия окончания
        # Используем среднеквадратичное отклонение значений функции
        f_mean = np.mean(f_values)
        termination_criterion = np.sqrt(np.sum([(fv - f_mean) ** 2 for fv in f_values]) / (n + 1))

        if termination_criterion < eps or a < eps:
            return simplex[0], f_values[0]

        # Нахождение центра тяжести (xc) всех точек, кроме худшей (xn)
        # И выполнение отражения: y = 2*xc - xn
        centroid = np.mean(simplex[:-1], axis=0)
        xn = simplex[-1]
        y = 2 * centroid - xn

        if f(y) < f(xn):
            simplex[-1] = y
            # Следующая итерация цикла
            continue
        else:
            # Переход к новому симплексу с вдвое меньшим ребром
            # Базовая вершина - x0 (лучшая), остальные xi = (xi + x0) / 2
            a = a / 2
            best_x = simplex[0]
            for i in range(1, n + 1):
                simplex[i] = (simplex[i] + best_x) / 2
            # Следующая итерация цикла

    return simplex[0], f(simplex[0])


def nelder_mead_numpy(f, x_start, step=1.0, maxiter=200, eps=1e-8):
    # Коэффициенты алгоритма
    alpha = 1.0  # Отражение
    gamma = 2.0  # Растяжение
    beta = 0.5  # Сжатие

    # Инициализация симплекса (3 точки для 2D)
    p1 = np.array(x_start, dtype=float)
    p2 = p1 + np.array([step, 0.0])
    p3 = p1 + np.array([0.0, step])
    simplex = [p1, p2, p3]

    for i in range(maxiter):
        # Сортировка по значению функции: b (best), g (good), w (worst)
        simplex.sort(key=f)
        b, g, w = simplex[0], simplex[1], simplex[2]

        # Проверка на выход (разброс значений функции)
        if np.std([f(b), f(g), f(w)]) < eps:
            break

        # Центр тяжести двух лучших точек
        mid = (b + g) / 2.0

        # 2. Отражение
        xr = mid + alpha * (mid - w)

        if f(xr) < f(b):
            # 3. Растяжение
            xe = mid + gamma * (xr - mid)
            if f(xe) < f(xr):
                simplex[2] = xe
            else:
                simplex[2] = xr
        elif f(xr) < f(g):
            # Отраженная точка просто лучше худшей
            simplex[2] = xr
        else:
            # Сжатие
            if f(xr) < f(w):
                xc = mid + beta * (xr - mid)
            else:
                xc = mid + beta * (w - mid)

            if f(xc) < f(w):
                simplex[2] = xc
            else:
                # 5. Редукция - если все плохо, сжимаемся к лучшей точке
                simplex[1] = b + 0.5 * (g - b)
                simplex[2] = b + 0.5 * (w - b)

    return simplex[0], f(simplex[0])

def cyclic_coordinate_descent(f, x0, delta=1.0, alpha=2.0, eps=1e-7, max_iter=1000):
    x = np.array(x0, dtype=float)
    n = len(x)
    k = 0

    while delta > eps and k < max_iter:
        x_old_cycle = np.copy(x)

        # Циклический перебор каждой координаты
        for i in range(n):
            f_current = f(x)

            # Шаг вперед по i-й координате
            x[i] += delta
            if f(x) < f_current:
                continue  # Успех, оставляем

            # Шаг назад
            x[i] -= 2 * delta
            if f(x) < f_current:
                continue  # Успех, оставляем

            # Если никуда не выгодно, возвращаем как было
            x[i] += delta

        # Если за целый цикл по всем координатам мы не сдвинулись
        if np.array_equal(x, x_old_cycle):
            delta /= alpha  # Уменьшаем шаг

        k += 1

    return x, f(x)


def exploratory_search(x_base, delta, f):
    x = np.copy(x_base)
    for i in range(len(x)):
        f_old = f(x)

        # Пробуем шаг вперед
        x[i] += delta[i]
        if f(x) < f_old:
            continue
        else:
            # Пробуем шаг назад
            x[i] -= 2 * delta[i]
            if f(x) < f_old:
                continue
            else:
                x[i] += delta[i]  # Возврат
    return x

def hooke_jeeves_protocol(f, x0, delta_init=1.0, alpha=2.0, eps=1e-6):
    # Инициализация
    n = len(x0)
    x_k_minus_1 = np.array(x0, dtype=float)  # x(k-1)
    x_k = np.copy(x_k_minus_1)  # x(k)
    delta = np.full(n, delta_init, dtype=float)

    while True:
        # Исследующий поиск
        x_res = exploratory_search(x_k, delta, f)

        # Был ли поиск удачным?
        if f(x_res) < f(x_k):
            # ДА
            while True:
                # Поиск по образцу
                # x_p = x(k) + (x(k) - x(k-1))
                x_pattern = x_res + (x_res - x_k_minus_1)

                # Исследующий поиск от точки образца
                x_k_plus_1 = exploratory_search(x_pattern, delta, f)

                # f(x(k+1)) < f(x(k))?
                if f(x_k_plus_1) < f(x_res):
                    x_k_minus_1 = np.copy(x_res)
                    x_res = np.copy(x_k_plus_1)
                    # Продолжаем цикл по образцу
                    continue
                else:
                    # НЕТ
                    x_k = np.copy(x_res)
                    break

        # Проверка на окончание
        if np.linalg.norm(delta) < eps:
            return x_k, f(x_k)
        else:
            # Уменьшить приращения
            delta = delta / alpha


def random_search(f, x0, step_size=2.0, alpha=0.5, eps=1e-6, max_iter=5000):
    x_current = np.array(x0, dtype=float)
    f_current = f(x_current)

    # Количество попыток в одном радиусе перед уменьшением шага
    max_attempts = 50

    for i in range(max_iter):
        success = False

        for attempt in range(max_attempts):
            # Генерируем случайное направление
            direction = np.array([random.uniform(-1, 1), random.uniform(-1, 1)])
            # Нормализуем вектор, чтобы шаг был ровно step_size
            direction = direction / np.linalg.norm(direction)

            # Делаем случайный шаг
            x_new = x_current + step_size * direction
            f_new = f(x_new)

            # Удачный ли шаг?
            if f_new < f_current:
                x_current = x_new
                f_current = f_new
                success = True
                # Если шаг удачный, выходим из цикла попыток и пробуем снова от новой точки
                break

                # Если за все попытки не нашли точку лучше — уменьшаем радиус поиска
        if not success:
            step_size *= alpha

        # Условие остановки по размеру шага
        if step_size < eps:
            break

    return x_current, f_current

start_point = [0.0, 0.0]

print("Истинный результат")
print(f"Точка минимума x1, x2: 9.96, -10.04")
print(f"Значение функции f(x): -94.33")

start = time.perf_counter()
best_point, min_value = regular_simplex_method(f, start_point)
end = time.perf_counter()

print("\nМетод правильного симплекса")
print(f"Точка минимума x1, x2: {best_point}")
print(f"Значение функции f(x): {min_value}")
print(f"Точное время: {(end - start) * 1000:.3f} мс")

start = time.perf_counter()
best_x, best_f = nelder_mead_numpy(f, start_point, step=2.0)
end = time.perf_counter()

print("\nМетод Нелдера-Мида")
print(f"Точка минимума x1, x2: {best_x}")
print(f"Значение функции f(x): {best_f}")
print(f"Точное время: {(end - start) * 1000:.3f} мс")

start = time.perf_counter()
res_x, res_f = cyclic_coordinate_descent(f, start_point)
end = time.perf_counter()

print("\nМетод циклического покоординатного спуска")
print(f"Точка минимума x1, x2: {res_x}")
print(f"Значение функции f(x): {res_f}")
print(f"Точное время: {(end - start) * 1000:.3f} мс")

start = time.perf_counter()
res_x, res_f = hooke_jeeves_protocol(f, start_point, delta_init=2.0, eps=1e-7)
end = time.perf_counter()

print(f"\nМетод Хука-Дживса ")
print(f"Точка минимума x1, x2: {res_x}")
print(f"Значение функции f(x): {res_f}")
print(f"Точное время: {(end - start) * 1000:.3f} мс")

start = time.perf_counter()
best_x, best_f = random_search(f, start_point)
end = time.perf_counter()

print("\nМетод случайного поиска")
print(f"Точка минимума x1, x2: {best_x}")
print(f"Значение функции f(x): {best_f}")
print(f"Точное время: {(end - start) * 1000:.3f} мс")
