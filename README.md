[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/luk036/multiplierless)
![Python application](https://github.com/luk036/multiplierless/workflows/Python%20application/badge.svg)
[![Build Status](https://travis-ci.org/luk036/multiplierless.svg?branch=master)](https://travis-ci.org/luk036/multiplierless)
[![Build status](https://ci.appveyor.com/api/projects/status/0v1cf05tcueny7d9?svg=true)](https://ci.appveyor.com/project/luk036/multiplierless)
[![Documentation Status](https://readthedocs.org/projects/multiplierless/badge/?version=latest)](https://multiplierless.readthedocs.io/en/latest/?badge=latest)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/a2f75bd3cc1e4c34be4741bdd61168ba)](https://app.codacy.com/app/luk036/multiplierless?utm_source=github.com&utm_medium=referral&utm_content=luk036/multiplierless&utm_campaign=badger)
[![codecov](https://codecov.io/gh/luk036/multiplierless/branch/main/graph/badge.svg?token=DEx23tq9W4)](https://codecov.io/gh/luk036/multiplierless)

# multplierless

Multiplierless FIR filter design in Python

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
