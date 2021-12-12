import numpy as np


def makeG(vr, vp):
    r, q = vr
    p, s = vp
    return np.array([[p * r + s, p], [p * q, s]])


def suppress(vA, vA1, vr, vr1):
    vp = vr - vr1
    r, q = vr
    p, s = vp
    Ap = np.array([[p * r + s, p], [p * q, s]])
    e = Ap[0][0] * Ap[1][1] - Ap[0][1] * Ap[1][0]
    va = Ap @ vA
    vA = e * va
    a, b = va
    vc = e * vA1 - np.array([a, a * p + b])
    vA1 = Ap @ vc
    return vA, vA1


def check_newton(vA, vA1, vr):
    A, B = vA
    A1, B1 = vA1
    r, q = vr
    H = np.array([[A1 * r + B1, A1], [A1 * q, B1]])
    return np.linalg.solve(H, vA)
