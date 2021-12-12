import numpy as np


def makeG(vr, vp):
    r, q = vr
    p, s = vp
    return np.array([[p * r + s, p], [p * q, s]])


def suppress_orig(vA, vA1, vr, vr1):
    """
    total 17 mul's
    """
    vp = vr - vr1
    r, q = vr
    p, s = vp
    Ap = np.array([[s, -p], [-p * q, p * r + s]]) # 2 mul's
    e = Ap[0][0] * Ap[1][1] - Ap[0][1] * Ap[1][0] # 2 mul's
    va = Ap @ vA # 4 mul's
    vA = e * va  # 2 mul's
    a, b = va
    vc = e * vA1 - np.array([a, a * p + b]) # 3 mul
    vA1 = Ap @ vc # 4 mul
    return vA, vA1


def suppress(vA, vA1, vr, vr1):
    """
    total 9 mul's + 2 div's
    """
    vp = vr - vr1
    Gp = makeG(vr, vp)  # 2 mul's
    va = np.linalg.solve(Gp, vA)  # 6 mul's + 2 div's
    a, b = va
    vA1 -= np.array([a, a * vp[0] + b]) # 1 mul
    return vA1


def check_newton(vA, vA1, vr):
    G = makeG(vr, vA1) # 2 mul's
    return np.linalg.solve(G, vA) # 6 mul's + 2 div's


def horner(pa, r, q):
    b0 = pa[0]
    b1 = b0 * r + pa[1]
    n = len(pa) - 1
    for i in range(2, n - 1):
        b2 = b0 * q + b1 * r + pa[i]
        b0, b1 = b1, b2
    A = b0 * q + b1 * r + pa[n - 1]
    B = b1 * q + pa[n]
    return np.array([A, B])


def main():
    vA = np.array([0.1, 1.2])
    vA1 = np.array([2.3, 3.4])
    vr = np.array([4.5, 5.6])
    vr1 = np.array([6.7, 7.8])
    vAorig, vA1orig = suppress_orig(vA, vA1, vr, vr1)
    print(check_newton(vAorig, vA1orig, vr))
    vA1 = suppress(vA, vA1, vr, vr1)
    print(check_newton(vA, vA1, vr))


if __name__ == '__main__':
    main()
