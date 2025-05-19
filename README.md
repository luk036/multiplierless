[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/luk036/multiplierless)
![Python application](https://github.com/luk036/multiplierless/workflows/Python%20application/badge.svg)
[![Build status](https://ci.appveyor.com/api/projects/status/0v1cf05tcueny7d9?svg=true)](https://ci.appveyor.com/project/luk036/multiplierless)
[![Documentation Status](https://readthedocs.org/projects/multiplierless/badge/?version=latest)](https://multiplierless.readthedocs.io/en/latest/?badge=latest)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/a2f75bd3cc1e4c34be4741bdd61168ba)](https://app.codacy.com/app/luk036/multiplierless?utm_source=github.com&utm_medium=referral&utm_content=luk036/multiplierless&utm_campaign=badger)
[![codecov](https://codecov.io/gh/luk036/multiplierless/branch/main/graph/badge.svg?token=DEx23tq9W4)](https://codecov.io/gh/luk036/multiplierless)

# multplierless

> Multiplierless FIR filter design in Python

A lowpass filter is a type of signal processing tool that allows low-frequency signals to pass through while reducing or blocking high-frequency signals. The "multiplierless" aspect means the filter is designed to work without using multiplication operations, which can be beneficial in certain hardware implementations.

The code uses several mathematical operations and transformations, including spectral factorization and its inverse, which are advanced concepts in signal processing. It also uses the CSD number representation, which is a special way of representing numbers that's useful in digital filter design.

The output of this code is not a final filter design, but rather an intermediate step in an iterative optimization process. It provides updated filter coefficients and frequency response characteristics that can be used in further iterations of the design process.

This code is part of a larger system for designing digital filters, specifically tailored for situations where multiplication operations need to be avoided. It's a specialized tool that would be used by engineers or researchers working on digital signal processing systems with specific hardware constraints.

## Dependencies

- [luk036/csdigit](https://github.com/luk036/csdigit.git)
- [luk036/bairstow](https://github.com/luk036/bairstow.git)
- [luk036/ellalgo](https://github.com/luk036/ellalgo.git)

## Features

- At most one square-root per iteration.
- Include oracles for Matrix Inequalities and Network problems.
- Suport Parallel-Cuts.
- Pure Python code.

## Installation

- The core ellipsoid method depends only on the `ellalgo` and `numpy` modules.

## See also

- [multiplierless-cpp](https://github.com/luk036/multiplierless-cpp)
- [Presentation Slides](https://luk036.github.io/cvx)

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.0.2. For details and usage
information on PyScaffold see https://pyscaffold.org/.
