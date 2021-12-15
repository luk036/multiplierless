title: Finding roots of real polynomial simultaneously by means of Bairstow's method

# Abstract

Aberth's method for finding the roots of a polynomial was shown to be robust. Howerver, compilex arithmetic is needed in this method even if the polynomial is real, because it starts with complex initial approximations. A novel method is proposed for real polynomials that does not require any complex arithmetic within iterations. It is based on the observation that Aberth's method is a systemic use of Newton's method. The analogous technique is then applied to Bairstow's procedure in the proposed method. As a result, the method needed half computations per iteration than Aberth's method. Numerical experiments showed that the new method exhibited a competitive overall performance for the test polynomials.

## Introduction

Consider a problem of finding the roots of a real polynomial $P(X)$, deflation is a standard technique that was described in many numerical textbooks. An alternative way is to use the formula given by Weierstrass (see [10] and references therein):

where $N$ is the degree of polynomial and $\ ^{(n)}$ denotes the iteration index, for finding zeros simultaneously. Note that the convergence order of this method is quadratic. A related method for finding the quadratic factors was given by Dvorciuk [6]. In 1973, Aberth proposed another method that has cubic convergent rate [1]:

where $P'(x)$ denotes the dervative of $P(X)$. These methods have recently been investigated for parallel implementations [5, 4, 7]. In the previous discussion [3]. it was pointed out that Aberth's method can be viewed as a modification of Maehly's proceduce [11, pp. 259] by merely replacing the computed zeros with all other iterates. We call this generalized idea *Parallel Anticipatory Implicit Deflation* (PAID) approach.

As Aberth mentioned, using Aberth's method with asymmetric iterates can overcome the symmetric problem [1]. However, complex arithmetic will not be avoided in this configuration even when the polygomial is real. The possibility of using this method with symmetric iterates will not be considered in this paper. Instead, we attempt to overcome this deficiency uising PAID idea and Bairstow's method. The idea is similar to the one in [13], but the resulting method is simplier here, which makes it more competitive with Aberth's method.

Recall that Bairstow's method avoids complex arithmetic by seeking the quadratic factor $(x^2 - r\cdot x - q)$ of $P(x)$ [11, pp. 301-303]. Let $(A, B)$ be the coefficients of the linear remainder of $P(x)$ such that:

$$P(x) = (x^2 - r\cdot x - q) P_1(x) + A x + B.$$

and $(A_1, B_1)$ be the coefficients of the linear remainder of $P_1(x)$ such that:

$$P_1(x) = (x^2 - r\cdot x - q) P_2(x) + A_1 x + B_1.$$

Bairstow's method can be written as:

Horner-type scheme is used to evaluate $(A, B)$ and $(A_1, B_1)$. By following PAID approach, we construct a parallel method as follows. First, a method of suppression of computed quadratic factors is employed. The details will be given in section 2. Next, by replacing the computed quadratic factors with the trial factors to the suppression method, we obtain a simultaneous version of Bairstow's method that is described in section 3. We will also discuss a simple method for choosing the initial guesses in section 4. Numerical results will be presented in section 5. For simplicity, we will omit the superscript $\ ^{(n)}$ in the following sections if it is understood.

## The modified Bairstow method

A simultaneous version of Bairstow's method can now be obtained by replacing $(\tilde{r}, \tilde{q})$ in (2.3) with the trial factors in case of even-degree polynomials, i.e., $N = 2M$. Starting with $M$ trial factors $(x^2 - r_i^{(0)}x - q_i^{(0)})$, $i = 1,\cdots,M$, the Bairstow iteration is applied to each trial factor in parallel, treating all the other factors as the computed ones and performing the suppression process according to (2.3). The modified Bairstow method is summarized as shown in Fig. 3.1.

In case of odd-degree polynomials, we need a special treatment as follows. An extra root is added to the polynomial such that the resulting polynomial is even-degree before applying to the formulas. In our scheme, we choose the root at origin as the extra root for convenience. Therefore, if there are any roots at orgin in the original polynomial, they should be removed at the beginning and be remembered as part of the solution. The overall algorithm is summarized as follows.

1. Remove any roots at origin from the polynomial and remember them as part of the solution.
2. If the resulting polynomial is odd-degree, insert a root at origin to make the degree even.
3. Apply the iteration according to the algorithm as shown in Fig. 3.1 to find the roots.
4. If the original polynomial is odd-degree, remove the root at origin that was inserted at step 2.
5. Add the roots at origin that was stored at step 1.

At first sight, it seems that the method is worse than Aberth's method because of the expensive cost of quadratic factors suppression. However, as we mentioned before, since complex arithmetic is avoided, the method is in fact more econmical. Table 3.1 shows the computations required per iteration of two methods. Only the leading terms are counted. The first row of the table indicates the cost of Horner-type evaluations. It includes the evaluations of $P(x_i)$ and $P'(x_i)$ in Aberth's method and the evaluations of $(A, B)$ and $(A_1, B_1)$ in the proposed method. The second row indicates the cost of zeros/quadratic factors suppression.
