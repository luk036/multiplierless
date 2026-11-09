# Project Overview

This project, `multiplierless`, is a Python-based tool for designing multiplierless FIR (Finite Impulse Response) filters. The core idea is to create digital filters that do not require multiplication operations, which is highly beneficial for hardware implementations where computational resources are limited.

The project utilizes advanced signal processing concepts such as spectral factorization and the Canonical Signed Digit (CSD) number representation. It's designed as an intermediate step within an iterative optimization process for digital filter design.

**Key Technologies:**
*   **Python:** The primary programming language.
*   **NumPy:** For numerical operations, especially array manipulation.
*   **ellalgo:** A dependency for ellipsoid method algorithms, crucial for the optimization process.
*   **csdigit:** A dependency for Canonical Signed Digit (CSD) representation.
*   **ginger:** A dependency for root-finding algorithms.

# Building and Running

This project uses `setuptools` and `PyScaffold` for its build system.

## Installation

Requires Python 3.10 or newer. The dependencies are pinned in `setup.cfg`, so a
single editable install fetches everything (including the Git-only `ginger`):

```bash
pip install -e ".[testing]"
```

## Testing

Tests are written using `pytest`. Coverage is enabled by default via
`setup.cfg`:

```bash
pytest
```

The Verilog simulation tests use Icarus Verilog and are skipped automatically
when `iverilog`/`vvp` are not installed.

## Linting

```bash
flake8 src tests tools
black --check src tests tools
isort --check-only src tests tools
mypy src tools
```

# Development Conventions

*   **Linting:** `flake8` with a maximum line length of 88 (Black-compatible),
    plus `black`, `isort`, and `mypy`.
*   **Testing:** `pytest` with `hypothesis`, `pytest-cov`, and
    `pytest-benchmark`.
*   **Dependency Management:** runtime and test dependencies live in
    `setup.cfg`; the files under `requirements/` mirror them for convenience.
*   **Project Scaffolding:** The project was initialized using PyScaffold 4.0.2.
