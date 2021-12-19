from multiplierless.rootfinding import initial_guess, pbairstow_even


def test_rootfind():
    # vA = vector2(0.1, 1.2)
    # vA1 = vector2(2.3, 3.4)
    # vr = vector2(4.5, 5.6)
    # vrj = vector2(6.7, 7.8)
    # vAorig, vA1orig = suppress_orig(vA, vA1, vr, vrj)
    # print(check_newton(vAorig, vA1orig, vr))
    # vA1 = suppress(vA, vA1, vr, vrj)
    # print(check_newton(vA, vA1, vr))
    h = [5.0, 2.0, 9.0, 6.0, 2.0]
    vr0s = initial_guess(h)
    # print(vr0s[1])
    # vA, pb = horner(h, vr0s[1])
    # print(vA)
    # print(pb)
    # vA1, _ = horner(pb, vr0s[1])
    # print(vA1)
    _, niter, found = pbairstow_even(h, vr0s)
    print([niter, found])
    # print([find_rootq(-r.x, -r.y) for r in vrs])
    assert niter == 7
