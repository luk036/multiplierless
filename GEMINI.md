# Project Overview

This project, `multiplierless`, is a Python-based tool for designing multiplierless FIR (Finite Impulse Response) filters. The core idea is to create digital filters that do not require multiplication operations, which is highly beneficial for hardware implementations where computational resources are limited.

The project utilizes advanced signal processing concepts such as spectral factorization and the Canonical Signed Digit (CSD) number representation. It's designed as an intermediate step within an iterative optimization process for digital filter design.

**Key Technologies:**
*   **Python:** The primary programming language.
*   **NumPy:** For numerical operations, especially array manipulation.
*   **ellalgo:** A dependency for ellipsoid method algorithms, crucial for the optimization process.
*   **csdigit:** A dependency for Canonical Signed Digit (CSD) representation.
*   **bairstow:** A dependency for root-finding algorithms.

# Building and Running

This project uses `setuptools` and `PyScaffold` for its build system.

## Installation

To set up the development environment and install the necessary dependencies, follow these steps:

1.  **Install core dependencies:**
    ```bash
    pip install decorator numpy
    ```
2.  **Install test dependencies:**
    ```bash
    pip install coverage pytest pytest-benchmark pytest-cov
    ```
3.  **Install external Git dependencies:**
    ```bash
    pip install git+https://github.com/luk036/csdigit.git
    pip install git+https://github.com/luk036/bairstow.git
    pip install git+https://github.com/luk036/ellalgo.git
    ```
4.  **Install the project in editable mode:**
    ```bash
    python setup.py develop
    ```

## Testing

Tests are written using `pytest`. To run the tests and check code coverage:

```bash
pytest --cov=src/
```

## Linting

`flake8` is used for linting to ensure code quality and adherence to style guidelines. To run the linter:

```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

# Development Conventions

*   **Linting:** Code quality is enforced using `flake8` with specific error codes (`E9,F63,F7,F82`) and a maximum line length of 127 characters.
*   **Testing:** `pytest` is the chosen framework for unit and integration testing, with code coverage analysis enabled.
*   **Dependency Management:** Dependencies are managed via `requirements/default.txt` and `requirements/test.txt`. It's noted that dependencies should also be added to `setup.cfg` (unpinned).
*   **Project Scaffolding:** The project was initialized using PyScaffold 4.0.2, which dictates a standard Python project structure and certain development practices.
