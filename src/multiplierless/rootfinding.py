from math import acos, cos, pow, sqrt

from .matrix2 import matrix2
from .vector2 import vector2

PI = acos(-1.0)


def makeG(vr, vp):
    r, q = vr.x, vr.y
    p, s = vp.x, vp.y
    return matrix2(vector2(p * r + s, p), vector2(p * q, s))


def makeadjoint(vr, vp):
    r, q = vr.x, vr.y
    p, s = vp.x, vp.y
    return matrix2(vector2(s, -p), vector2(-p * q, p * r + s))


def suppress_orig(vA, vA1, vr, vrj):
    """
    total 13 mul's + 2 div's
    """
    vp = vr - vrj
    p = vp.x
    Ap = makeadjoint(vr, vp)  # 2 mul's
    e = Ap.det()  # 2 mul's
    va = Ap.dot(vA)  # 4 mul's
    vA = va  # 2 mul's
    a, b = va.x, va.y
    vc = vA1 - vector2(a, a * p + b) / e  # 3 mul
    vA1 = Ap.dot(vc)  # 4 mul
    return vA, vA1


def suppress(vA, vA1, vr, vrj):
    """
    total 8 mul's + 2 div's
    """
    vp = vr - vrj
    mp = makeadjoint(vrj, vp)  # 2 mul's
    vA1 -= mp.mdot(vA) / mp.det()  # 6 mul's + 2 div's
    return vA1


def check_newton(vA, vA1, vr):
    mA1 = makeadjoint(vr, vA1)  # 2 mul's
    return mA1.mdot(vA) / mA1.det()  # 6 mul's + 2 div's


def horner_eval(pa, r):
    pb = pa.copy()
    for i in range(len(pa)):
        pb[i] += pb[i - 1] * r
    return pb[-1]


def horner(pa, vr):
    r, q = vr.x, vr.y
    n = len(pa) - 1
    pb = pa.copy()
    pb[1] += pb[0] * r
    for i in range(2, n):
        pb[i] += pb[i - 2] * q + pb[i - 1] * r
    pb[n] += pb[n - 2] * q
    return vector2(pb[n - 1], pb[n]), pb[:-2]


class Options:
    max_iters: int = 2000
    tol: float = 1e-12


def initial_guess(pa):
    N = len(pa) - 1
    M = N // 2
    c = -pa[1] / (N * pa[0])
    # P = np.poly1d(pa)
    Pc = horner_eval(pa, c)
    re = pow(abs(Pc), 1.0 / N)
    k = 2 * PI / N
    m = c * c + re * re
    vr0s = []
    for i in range(1, M + 1):
        r0 = 2 * (c + re * cos(k * i))
        q0 = m + r0
        vr0s += [vector2(r0, q0)]
    return vr0s


def pbairstow_even(pa, vrs, options=Options()):
    N = len(pa) - 1  # degree, assume even
    M = N // 2
    found = False
    converged = [False] * M
    for niter in range(options.max_iters):
        tol = 0.0
        for i in filter(lambda i: converged[i] is False, range(M)):  # exclude converged
            vA, pb = horner(pa, vrs[i])
            toli = abs(vA.x) + abs(vA.y)
            if toli < options.tol:
                converged[i] = True
                continue
            tol = max(tol, toli)
            vA1, _ = horner(pb, vrs[i])
            for j in filter(lambda j: j != i, range(M)):  # exclude i
                vp = vrs[i] - vrs[j]
                mp = makeadjoint(vrs[j], vp)  # 2 mul's
                vA1 -= mp.mdot(vA) / mp.det()  # 6 mul's + 2 div's
                # vA1 = suppress(vA, vA1, vrs[i], vrs[j])
            mA1 = makeadjoint(vrs[i], vA1)  # 2 mul's
            vrs[i] -= mA1.mdot(vA) / mA1.det()  # Gauss-Seidel fashion
        if tol < options.tol:
            found = True
            break
    return vrs, niter + 1, found


def find_rootq(b, c):
    hb = b / 2.0
    d = hb * hb - c
    if d < 0.0:
        x1 = -hb + (sqrt(-d) if hb < 0.0 else -sqrt(-d)) * 1j
    else:
        x1 = -hb + (sqrt(d) if hb < 0.0 else -sqrt(d))
    x2 = c / x1
    return x1, x2
