import numpy as np


def makeG(vr, vp):
    r, q = vr
    p, s = vp
    return np.array([[p * r + s, p], [p * q, s]])


def suppress_orig(vA, vA1, vr, vr1):
    vp = vr - vr1
    r, q = vr
    p, s = vp
    Ap = np.array([[s, -p], [-p * q, p * r + s]])
    e = Ap[0][0] * Ap[1][1] - Ap[0][1] * Ap[1][0]
    va = Ap @ vA
    vA = e * va
    a, b = va
    vc = e * vA1 - np.array([a, a * p + b])
    vA1 = Ap @ vc
    return vA, vA1


def suppress(vA, vA1, vr, vr1):
    vp = vr - vr1
    Gp = makeG(vr, vp)
    va = np.linalg.solve(Gp, vA)
    a, b = va
    vA1 -= np.array([a, a * vp[0] + b])
    return vA1


def check_newton(vA, vA1, vr):
    G = makeG(vr, vA1)
    return np.linalg.solve(G, vA)


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
