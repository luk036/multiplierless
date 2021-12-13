import numpy as np


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
    total 9 mul's + 2 div's
    """
    vp = vr - vrj
    mp = makeG(vr, vp)  # 2 mul's
    va = np.linalg.solve(mp, vA)  # 6 mul's + 2 div's
    a, b = va
    vA1 -= np.array([a, a * vp[0] + b]) # 1 mul
    return vA1


def check_newton(vA, vA1, vr):
    mA1 = makeG(vr, vA1) # 2 mul's
    return np.linalg.solve(mA1, vA) # 6 mul's + 2 div's


def horner(pa, vr):
    r, q = vr
    pb = np.array(pa[:-2])
    pb[1] += pb[0] * r
    n = len(pa) - 1
    for i in range(2, n - 1):
        pb[i] += pb[i - 2] * q + pb[i - 1] * r
    A = pb[n - 3] * q + pb[n - 2] * r + pa[n - 1]
    B = pb[n - 2] * q + pa[n]
    return np.array([A, B]), pb


class Options:
    max_iter: int = 2000
    tol: float = 1e-8


def pbairstow_even(pa, vrs, options = Options()):
    N = len(pa) - 1 # degree, assume even
    M = N // 2
    found = False

    for niter in range(options.max_iter):
        tol = 0.
        for i in range(M):
            vA, pb = horner(pa, vrs[i])
            vA1, _ = horner(pb, vrs[i])
            for j in filter(lambda j: j == i, range(M)): # exclude i
                vA1 = suppress(vA, vA1, vrs[i], vrs[j])
            mA1 = makeG(vrs[i], vA1) # 2 mul's
            vdelta = np.linalg.solve(mA1, vA) # 6 mul's + 2 div's
            vrs[i] -= vdelta # Gauss-Sidel fashion
            tol += abs(vdelta[0]) + abs(vdelta[1])
        if tol < options.tol:
            found = True
            break
    return vrs, niter + 1, found


def main():
    vA = np.array([0.1, 1.2])
    vA1 = np.array([2.3, 3.4])
    vr = np.array([4.5, 5.6])
    vrj = np.array([6.7, 7.8])
    vAorig, vA1orig = suppress_orig(vA, vA1, vr, vrj)
    print(check_newton(vAorig, vA1orig, vr))
    vA1 = suppress(vA, vA1, vr, vrj)
    print(check_newton(vA, vA1, vr))


if __name__ == '__main__':
    main()
