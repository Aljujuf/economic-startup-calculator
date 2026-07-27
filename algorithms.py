from typing import List, Callable, Optional


def newton_method(
    f: Callable[[float], float],
    f_prime: Callable[[float], float],
    x0: float = 0.1,
    max_iter: int = 100,
    tol: float = 1e-8,
) -> Optional[float]:
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        fpx = f_prime(x)
        if abs(fpx) < 1e-12:
            return None
        x_new = x - fx / fpx
        if x_new <= -1 + 1e-6:
            return None
        if abs(x_new - x) < tol:
            return x_new if abs(f(x_new)) < tol * 100 else None
        x = x_new
    return None


def binary_search(
    f: Callable[[float], float],
    low: float,
    high: float,
    max_iter: int = 100,
    tol: float = 1e-8,
) -> Optional[float]:
    f_low = f(low)
    f_high = f(high)

    if f_low * f_high > 0:
        return None

    for _ in range(max_iter):
        mid = (low + high) / 2
        f_mid = f(mid)
        if abs(f_mid) < tol:
            return mid
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return (low + high) / 2


def calculate_irr(cashflows: List[float], guess: float = 0.1) -> float:
    """IRR по годовому потоку: t=0 — вложение, далее чистые потоки."""
    if len(cashflows) < 2:
        return 0.0

    def npv(r: float) -> float:
        return sum(cf / ((1 + r) ** t) for t, cf in enumerate(cashflows))

    def derivative(r: float) -> float:
        return sum(
            -t * cf / ((1 + r) ** (t + 1)) for t, cf in enumerate(cashflows) if t > 0
        )

    for g in (guess, 0.05, 0.2, 0.5, 0.01):
        irr = newton_method(npv, derivative, g)
        if irr is not None and abs(npv(irr)) < 1e-4:
            return round(irr, 4)

    # Подбор интервала для бинарного поиска (NPV убывает по r при «нормальном» проекте)
    rates = [r / 1000 for r in range(1, 5000)]  # 0.001 .. 4.999
    last_v, last_r = npv(rates[0]), rates[0]
    for r in rates[1:]:
        v = npv(r)
        if last_v == 0:
            return round(last_r, 4)
        if last_v * v < 0:
            found = binary_search(npv, last_r, r)
            if found is not None:
                return round(found, 4)
        last_v, last_r = v, r

    return 0.0
