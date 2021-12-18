import numpy as np
from math import pow, cos, sqrt


def makeG(vr, vp):
    r, q = vr
    p, s = vp
    return np.array([[p * r + s, p], [p * q, s]])


def suppress_orig(vA, vA1, vr, vrj):
    """
    total 13 mul's + 2 div's
    """
    vp = vr - vrj
    r, q = vr
    p, s = vp
    Ap = np.array([[s, -p], [-p * q, p * r + s]]) # 2 mul's
    e = Ap[0][0] * Ap[1][1] - Ap[0][1] * Ap[1][0] # 2 mul's
    va = Ap @ vA # 4 mul's
    vA = va  # 2 mul's
    a, b = va
    vc = vA1 - np.array([a, a * p + b])/e # 3 mul
    vA1 = Ap @ vc # 4 mul
    return vA, vA1


def suppress(vA, vA1, vr, vrj):
    """
    total 8 mul's + 2 div's
    """
    vp = vr - vrj
    mp = makeG(vrj, vp)  # 2 mul's
    vA1 -= np.linalg.solve(mp, vA)  # 6 mul's + 2 div's
    return vA1


def check_newton(vA, vA1, vr):
    mA1 = makeG(vr, vA1) # 2 mul's
    return np.linalg.solve(mA1, vA) # 6 mul's + 2 div's


def horner(pa, vr):
    r, q = vr
    n = len(pa) - 1
    pb = pa.copy()
    pb[1] += pb[0] * r
    for i in range(2, n):
        pb[i] += pb[i - 2] * q + pb[i - 1] * r
    pb[n] += pb[n - 2] * q
    return np.array([pb[n-1], pb[n]]), pb[:-2]


class Options:
    max_iter: int = 2000
    tol: float = 1e-8


def initial_guess(pa):
    N = len(pa) - 1
    M = N // 2
    c = -pa[1]/(N*pa[0])
    P = np.poly1d(pa)
    re = pow(abs(P(c)), 1./N)
    k = 2 * np.pi / N
    r0s = [2 * (c + re * cos(k * i)) for i in range(1, M + 1)]
    m = c * c + re * re
    q0s = [m + ri for ri in r0s]
    vr0s = [np.array([r0i, q0i]) for r0i, q0i in zip(r0s, q0s)]
    return vr0s


def pbairstow_even(pa, vrs, options = Options()):
    N = len(pa) - 1 # degree, assume even
    M = N // 2
    found = False
    for niter in range(options.max_iter):
        tol = 0.
        for i in range(M):
            vA, pb = horner(pa, vrs[i])
            toli = abs(vA[0]) + abs(vA[1])
            if toli < options.tol:
                continue
            tol = max(tol, toli)
            vA1, _ = horner(pb, vrs[i])
            for j in filter(lambda j: j != i, range(M)): # exclude i
                vp = vrs[i] - vrs[j]
                mp = makeG(vrs[j], vp)  # 2 mul's
                vA1 -= np.linalg.solve(mp, vA)  # 6 mul's + 2 div's
                # vA1 = suppress(vA, vA1, vrs[i], vrs[j])
            mA1 = makeG(vrs[i], vA1) # 2 mul's
            vrs[i] -= np.linalg.solve(mA1, vA) # Gauss-Seidel fashion
        if tol < options.tol:
            found = True
            break
    return vrs, niter + 1, found


def find_rootq(b, c):
    hb = b / 2.
    d = hb * hb - c
    if d < 0.:
        x1 = -hb + (sqrt(-d) if hb < 0. else -sqrt(-d))*1j
    else:
        x1 = -hb + (sqrt(d) if hb < 0. else -sqrt(d))
    x2 = c / x1
    return x1, x2


def main():
    vA = np.array([0.1, 1.2])
    vA1 = np.array([2.3, 3.4])
    vr = np.array([4.5, 5.6])
    vrj = np.array([6.7, 7.8])
    vAorig, vA1orig = suppress_orig(vA, vA1, vr, vrj)
    print(check_newton(vAorig, vA1orig, vr))
    vA1 = suppress(vA, vA1, vr, vrj)
    print(check_newton(vA, vA1, vr))
    h = [5., 2., 9., 6., 2.]
    vr0s = initial_guess(h)
    print(vr0s)
    vA, pb = horner(h, vr0s[1])
    print(vA)
    print(pb)
    vA1, _ = horner(pb, vr0s[1])
    print(vA1)

    vrs, niter, found = pbairstow_even(h, vr0s)
    print([niter, found])
    print([find_rootq(-r[0], -r[1]) for r in vrs])


if __name__ == '__main__':
    main()
