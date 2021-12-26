---
title: Finding the roots of real polynomials simultaneously using Bairstow\'s method
author: Wai-Shing Luk
...

# Abstract

Aberth\'s method of finding roots of polynomials has been shown to be reliable. However, in this method, complex arithmetic is required even if the polynomial is real, because it starts from an initial approximation of the complex numbers. For real polynomials, we propose a new method that does not require any complex arithmetic during the iteration. It is based on the observation that Aberth\'s method is a systematic use of Newton\'s method. Then, in the proposed method, a similar technique is applied to Bairstow\'s procedure. As a result, the method requires half the amount of computation per iteration as Aberth\'s method. Numerical experiments show that the new method exhibits competitive overall performance in the polynomials tested.

## Introduction

Consider a problem of finding the roots of a real polynomial $P(x)$. As described in many numerical textbooks, deflation is a standard technique. An alternative approach is to use the formula given by Weierstrass (see \[10\] and references therein).

$$x_i^{(n+1)} = x_i^{(n)} - \frac{P(x_i^{(n)})}{\prod_{j \neq i}^N (x_i^{(n)} - x_j^{(n)})}, \quad i = 1,\cdots, N$$

where $N$ is the degree of the polynomial and $^{(n)}$ denotes the iteration index. Note that the order of convergence of this method is quadratic. A related method for finding quadratic factors was given by Dvorciuk \[6\]. In 1973, Aberth proposed another method with a cubic rate of convergence \[1\]:

$$x_i^{(n+1)} = x_i^{(n)} - \frac{P(x_i^{(n)})}{P'(x_i^{(n)}) - \sum_{j \neq i}^N \frac{P(x_i^{(n)})}{x_i^{(n)} - x_j^{(n)}} }, \quad i = 1,\cdots, N$$

where $P'(x)$ denotes the dervative of $P(x)$. These methods have recently been studied for parallel implementations \[5, 4, 7\]. In a previous discussion \[3\], it was pointed out that Aberth\'s method can be seen as a modification of Maehly\'s proceduce \[11, p. 259\], except that the computed zeros are replaced by all other iterates. We refer to this generalized idea as the *Parallel Anticipatory Implicit Deflation* (PAID) method.

As mentioned by Aberth, the symmetry problem can be overcome by using asymmetric iterates for Aberth\'s method \[1\]. However, in this configuration, complex arithmetic cannot be avoided even if the polynomial is real. In this paper, we will not consider the possibility of using symmetric iterates. Instead, we try to use the PAID idea and Bairstow\'s approach to overcome this drawback. This idea is similar to the one in the literature \[13\], but the obtained method is simpler, which makes it more competitive compared to Aberth\'s approach.

Recall that Bairstow\'s method avoids complex arithmetic by seeking quadratic factors $( x^{2} - r \cdot x - q )$ of $P(x)$ \[11, pp. 301-303\]. Let $(A, B)$ be the coefficients of the linear remainder of $P(x)$ such that:

$$P(x) = ( x^{2} - r \cdot x - q ) P_{1}(x) + Ax + B.$$

and $( A_{1},B_{1} )$ the coefficients of the linear residuals of $P_{1}(x)$ such that:

$$P_{1}(x) = ( x^{2} - r \cdot x - q ) P_{2}(x) + A_{1}x + B_{1}.$$

Bairstow\'s method can be written as:

$$ \begin{bmatrix} r^{(n+1)} \\ q^{(n+1)} \end{bmatrix} = \begin{bmatrix} r^{(n)} \\ q^{(n)} \end{bmatrix} - \begin{bmatrix} A_1 r^{(n)} + B_1 & A_1 \\ A_1 q^{(n)} & B_1 \end{bmatrix}^{-1} \begin{bmatrix} A \\ B \end{bmatrix}.$$

The Horner-type scheme is used to evaluate $(A,B)$ and $( A_{1},B_{1} )$. By following the PAID approach, we construct the following parallel method. First, we use a method to suppress the computation of quadratic factors. The details will be given in Section 2. Next, by replacing the computed quadratic factors with the trial factors of the suppression method, we obtain a simultaneous version of the Bairstow method, which will be described in Section 3. We will also discuss a simple method for selecting the initial guess in Section 4. Numerical results will be presented in Section 5. For simplicity, we will omit the superscripts $^{(n)}$ in the following sections if it is understood.

## Suppressing the computed quadratic factor

The first step in developing the novel algorithm is to find a method of suppressing, which is described in \[8\]. Suppose that $( x^{2} - \widetilde{r} \cdot x - \widetilde{q} )$ has been found to be a factor of $P(x)$. Let $\widetilde{P}(x) = P(x)/ ( x^{2} - \widetilde{r} \cdot x - \widetilde{q} )$ be that deflated polynomial. The goal of the suppression is to perform the Bairstow process without explicitly consructing $\widetilde{P}(x)$. Let $(\widetilde{A}, \widetilde{B})$ be the coefficients of the linear remainder of $\widetilde{P}(x)$ and $(\widetilde{A}_{1}, \widetilde{B}_{1})$ be the coefficients of the linear remainder of $\widetilde{P}_{1}$. The relation between $A, B, A_{1}, B_{1}$ and $\widetilde{A}, \widetilde{B}, \widetilde{A}_{1}, \widetilde{B}_{1}$ can be expressed in the following form [8]:

$$ \begin{bmatrix} p \\ l \end{bmatrix} = \begin{bmatrix} r \\ q \end{bmatrix} - \begin{bmatrix} \widetilde{r} \\ \widetilde{q} \end{bmatrix},$$

$$ \begin{bmatrix} \widetilde{A}\_1 \\ \widetilde{B}\_1 \end{bmatrix} = \begin{bmatrix} A_1 \\ B_1 \end{bmatrix} - \begin{bmatrix} p\cdot \tilde{r} + l & p \\ p\cdot \tilde{q} & l \end{bmatrix}^{-1} \begin{bmatrix} A \\ B \end{bmatrix},$$

where $a$, $b$, $c$, $d$, $e$, $f$, $l$, and $p$ are intermediate variables. By repeating this process, the second quadratic factor can be suppressed, starting with $\widetilde{A},\widetilde{B},{\widetilde{A}}_{1},{\widetilde{B}}_{1}$ and so on.

## Modified Bairstow method

A simultaneous version of Bairstow\'s method can now be obtained by replacing $(\widetilde{r}, \widetilde{q})$ in (2.3) with the trial factors in the case of even-degree polynomials, i.e., $N = 2M$. Starting with $M$ trial factors $(x^2 - r_i^{(0)}x - q_i^{(0)})$, $i = 1,\cdots,M$, the Bairstow iteration is applied to each trial factor in parallel, treating all other factors as computed and performing the suppression process according to (2.3). Figure 3.1 shows an overview of the modified Bairstow method.

For polynomials of odd degree, we need to do the following special treatment. Before applying to the formula, an extra root is to be added to the polynomial so that the resulting polynomial is of even degree. In our scheme, for convenience, we choose the root of the origin as the extra root. Thus, if there are roots of the origin in the original polynomial, they should be removed at the beginning and remembered as part of the solution. The entire algorithm is summarized as follows.

1.  Any roots of the origin are removed from the polynomial and remembered as part of the solution.
2.  If the resulting polynomial is odd, insert a root at the origin to make it even.
3.  Iterate according to the algorithm shown in Figure 3.1 to find the roots.
4.  If the original polynomial is of odd degree, delete the root inserted at the origin in step 2.
5.  Add the roots of the origin stored in step 1.

At first glance, the method seems inferior to Aberth\'s method because of the high cost of suppressing quadratic factors. However, as we mentioned before, the method is actually more economical due to the avoidance of complex arithmetic. Table 3.1 shows the amount of computation required per iteration for both methods. Only the leading terms are counted.

|             | Aberth's method | The proposed method |
| ----------- | --------------- | ------------------- |
| Horner      | $8 N^2$         | $4 N M$             |
| Suppression | $4 N^2$         | $8 M^2$             |
| Total       | $12N^2$         | $16 M^2$            |

:Table 3.1

The first row of the table shows the cost of the Horner type of evaluation. It includes the evaluation of $P( x_{i} )$ and $P'( x_{i} )$, while in Aberth\'s method it is the evaluation of $(A,B)$ and $( A_{1},B_{1} )$. The second row indicates the cost of suppressing the zero/quadratic factor. It includes the evaluations of $1/(x_i - x_j)$ in Aberth's method and the evaluations of equation (2.3) in the proposed method. If we count addition, subtraction, multiplication and division as a *flop* (floating point operation), then the total flop for each iteration of Aberth's method is $23N^{2} + O(N)$ and the proposed method is $46M^{2} + O(N)$. Thus, an improvement of about a factor of two is expected.

## Selecting Initial Guess

We follow Aberth's suggestion that the initial guesses should be evenly distributed on a circle with the center $C$ which euqals to the centroid of zeros [1]:

$$z_{j}^{(0)} = C + R \cdot \text{exp}(2\pi ij/N + i\phi)\quad j = 1,\cdots,N,$$

where $i = \sqrt{-1}$. $C$ can be determined by the formula $-a_{N-1}/(N\cdot a_N)$, where $a_N$ and $a_{N-1}$ represent the coefficients of $x^N$ and $x^{N-1}$ respectively. The angle $\phi$ is used to break the symmetry with respect to the real axis, which is taken as $\pi/2N$ in Aberth's discussion. For the parallel Bairstow method, we simply take it to be zero. $R$ is taken as the effective radius $R_e$ proposed by Chen [2]:

$$R = R_{e} = ( - P(C) )^{1/N}$$

for Aberth\'s method. Note that $R_{e}$ is a complex number. For the proposed method, since $R$ must be real, we use $R = \left| P(C) \right|^{1/N}$ instead. As a result, the initial $\{ r_{j}^{(0)},q_{j}^{(0)}\}$ is given by the following equation.


## Numerical Experiment

We have written experimental programs in MATLAB to implement Aberth\'s method and the modified Bairstow\'s method described in Section 3. The number of iterations (iter.) and the number of floating-point operations (flops) were used to measure the performance. Since the two methods have different stopping criteria, we list the maximum value of the actual residual error ($\xi_{\text{max}}$ ), which is defined as $\text{max}_{i}\left| P( x_{i} ) \right|$ for comparison. We followed \[7\] and the test polynomials were taken from Table 1 of \[9\] (see also \[12\]).

These programs were run on Digital Equipment Corporation's DECstation 5000/133 , and the results are listed in Table 5.1. We observe that the convergence rates of the two methods are very similar, except for some polynomials. In the following, we will discuss them. In problems 3, 5, 6, 7, and 9, Aberth\'s method converges more slowly. This is because the corresponding polynomials either contain multiple roots, or only real roots, or both. However, the modified Bairstow\'s method does not necessarily exhibit fast convergence in all cases. For example, in problem 10, slow convergence rates were also found. In Problem 31, the modified Bairstow method required 50 iterations to converge. We observed that for the first 44 iterations, one pair of iterates just wandered, but suddenly approached the root quickly in the last few iterations. An appropriate explanation remains unknown.

## Conclusion

In this paper, the general idea of the proposed method was presented. The advantage of this method is that it avoids complex arithmetic and is inherently parallelizable. Numerical results show the robustness and efficiency of the method.
