![Python application](https://github.com/luk036/multiplierless/workflows/Python%20application/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/multiplierless/badge/?version=latest)](https://multiplierless.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/luk036/multiplierless/branch/main/graph/badge.svg?token=DEx23tq9W4)](https://codecov.io/gh/luk036/multiplierless)

# multiplierless

> Multiplierless FIR filter design in Python

A lowpass filter is a type of signal processing tool that allows low-frequency signals to pass through while reducing or blocking high-frequency signals. The "multiplierless" aspect means the filter is designed to work without using multiplication operations, which can be beneficial in certain hardware implementations.

The code uses several mathematical operations and transformations, including spectral factorization and its inverse, which are advanced concepts in signal processing. It also uses the CSD number representation, which is a special way of representing numbers that's useful in digital filter design.

The output of this code is not a final filter design, but rather an intermediate step in an iterative optimization process. It provides updated filter coefficients and frequency response characteristics that can be used in further iterations of the design process.

This code is part of a larger system for designing digital filters, specifically tailored for situations where multiplication operations need to be avoided. It's a specialized tool that would be used by engineers or researchers working on digital signal processing systems with specific hardware constraints.

## Dependencies

- [numpy](https://numpy.org/)
- [luk036/csdigit](https://github.com/luk036/csdigit) — CSD conversion
- [luk036/ellalgo](https://github.com/luk036/ellalgo) — cutting-plane / ellipsoid method
- [luk036/ginger](https://github.com/luk036/ginger) — polynomial root-finding

The three `luk036/*` dependencies are pinned to commits in `setup.cfg` because
the root-finding `ginger` package is not published on PyPI.

## Features

- Multiplierless (CSD) FIR coefficient design
- Spectral factorization via FFT or Aberth-Ehrlich root-finding
- Ellipsoid-method optimization through `ellalgo`
- Transpose- and direct-form Verilog generation with cross-CSE
- JSON-in / JSON-out CLI (`fir-design`)

## Installation

Requires Python 3.10 or newer.

```bash
pip install .
```

## Quickstart

```python
import numpy as np
from multiplierless import spectral_fact

# Define auto-correlation coefficients
r = np.array([1.0, 0.5, 0.2, 0.1])

# Compute minimum-phase impulse response
h = spectral_fact(r)

print("Impulse response:", h)
```

## CLI

```bash
# Design from a JSON specification; prints the result to stdout
fir-design sample_filter.json

# Write the result (including optional Verilog) to a file
fir-design sample_filter.json -o result.json
```

See `fir_design_input.schema.json` and `fir_design_output.schema.json` for the
input and output formats.

## Performance

Run benchmarks with pytest-benchmark:

```bash
pip install pytest-benchmark
pytest --benchmark-only
```

## See also

- [multiplierless-cpp](https://github.com/luk036/multiplierless-cpp)
- [Presentation Slides](https://luk036.github.io/cvx)

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.0.2. For details and usage
information on PyScaffold see https://pyscaffold.org/.
