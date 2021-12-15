---
title: Finding the roots of a real polynomial simultaneously using Bairstow\'s method
author: Wai-Shing Luk
...

# Abstract

Aberth's method of finding the roots of polynomials is shown to be robust. However, in this method, complex arithmetic is required even if the polynomial is real, since it starts with a complex initial approximation. For real polynomials, we propose a new method that does not require any complex arithmetic in the iterative process. It is based on the observation that Aberth\'s method is a system use of Newton's methods. Then, in the proposed method, a similar technique is applied to Bairstow\'s procedure. As a result, the method requires half as much computation per iteration as Aberth\'s method. Numerical experiments show that the new method exhibits competitive overall performance for the polynomials tested.

## Introduction

Consider a problem of finding the roots of a real polynomial $P(X)$ As described in many numerical textbooks, deflation is a standard technique. An alternative approach is to use the formula given by Weierstrass (see \[10\] and references therein).

where $N$ is the degree of the polynomial and $^{(n)}$ denotes the iteration index, used to find the zeros simultaneously. Note that the order of convergence of this method is quadratic. A related method for finding quadratic factors was given by Dvorciuk \[6\]. In 1973, Aberth proposed another method with a cubic rate of convergence \[1\].

which $P\prime(x)$ denotes the dervative of $P(x)$. These methods have recently been studied for parallel implementations \[5, 4, 7\]. In a previous discussion \[3\], it was pointed out that Aberth\'s method can be seen as a modification of Maehly\'s proceduce \[11, p. 259\], simply replacing the computed zeros with all other iterates. We call this generalized idea the *Parallel Anticipatory Implicit Deflation* (PAID) method.

As mentioned by Aberth, the symmetry problem can be overcome by using asymmetric iterates for Aberth\'s method \[1\]. However, in this configuration, complex arithmetics cannot be avoided even if the polynomial is real. In this paper, we will not consider the possibility of symmetric iterates using this approach. Instead, we try to use the PAID idea and Bairstow\'s method to overcome this drawback. The idea is similar to the one in the literature \[13\], but the resulting method is simpler, which makes it more competitive with Aberth\'s method.

Recall that Bairstow\'s method avoids complex arithmetic by seeking quadratic factors $\left( x^{2} - r \cdot x - q \right)$ of $P(x)$ \[11, pp. 301-303\]. Let $(A, B)$ be the coefficients of the linear remainder of $P(x)$ such that:

$$P(x) = \left( x^{2} - r \cdot x - q \right)P_{1}(x) + Ax + B.$$

and $\left( A_{1},B_{1} \right)$ the coefficients of the linear remainder of $P_{1}(x)$  such that:

$$P_{1}(x) = \left( x^{2} - r \cdot x - q \right)P_{2}(x) + A_{1}x + B_{1}.$$

Bairstow\'s method can be written as:

Horner-type scheme is used to evaluate $(A,B)$ and $\left( A_{1},B_{1} \right)$ . By following the PAID approach, we construct a parallel method as follows. First, we use a method that suppresses the computation of quadratic factors. Details will be given in Section 2. Next, by replacing the computed quadratic factors with the trial factors of the suppression method, we obtain a simultaneous version of the Bairstow method, which will be described in Section 3. We will also discuss a simple method for selecting initial guesses in Section 4. Numerical results will be presented in Section 5. For the sake of simplicity, we will omit the superscript $^{(n)}$ We will omit superscripts in the following sections if they are understood.

## Modified Bairstow method

A simultaneous version of Bairstow's method can now be obtained by replacing $(\tilde{r}, \tilde{q})$ in (2.3) with the trial factors in case of even-degree polynomials, i.e., $N = 2M$. Starting with $M$ trial factors $(x^2 - r_i^{(0)}x - q_i^{(0)})$, $i = 1,\cdots,M$, the Bairstow iteration is applied to each trial factor in parallel, treating all other factors as computed and performing the suppression process according to (2.3). An overview of the modified Bairstow method is shown in Figure 3.1.

In the case of polynomials of odd degree, we need to make the following special treatment. Before applying to the formula, an extra root is added to the polynomial so that the resulting polynomial is of even degree. In our scheme, for convenience, we choose the root of the origin as the extra root. Thus, if there are any roots of the origin in the original polynomial, they should be removed at the beginning and remembered as part of the solution. The entire algorithm is summarized below.

1.  Remove any roots at the origin from the polynomial and remember them as part of the solution.
2.  If the resulting polynomial is of odd degree, insert a root at the origin to make it of even degree.
3.  Iterate according to the algorithm shown in Figure 3.1 to find the root.
4.  If the original polynomial is of odd degree, delete the root at the origin inserted in step 2.
5.  Add the roots at the origin stored in step 1.

At first glance, the method appears to be inferior to Aberth\'s method because of the high cost of suppressing the quadratic factors. However, as we mentioned before, the method is actually more economical due to the avoidance of complex arithmetic. Table 3.1 shows the amount of computation required per iteration for both methods. Only the leading terms are counted. The first row of the table shows the cost of the Horner type of evaluation. It includes the evaluation of $P\left( x_{i} \right)$ and $P\prime\left( x_{i} \right)$ of the evaluation, and in Aberth's method for $(A,B)$ and $\left( A_{1},B_{1} \right)$ of the evaluation. The second row indicates the cost of suppressing the zeros/quadratic factors.
