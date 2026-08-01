# AGENTS.md - Agent Guidelines for multiplierless

## Build, Lint, and Test Commands

### Testing
```bash
# Run all tests (coverage + verbose enabled by default in setup.cfg)
pytest

# Run a single test file
pytest tests/test_spectral_fact.py

# Run a single test function
pytest tests/test_spectral_fact.py::test_spectral_fact

# Run property-based tests (hypothesis in testing extras)
pytest -k "properties"

# Run benchmarks with pytest-benchmark
pytest --benchmark-only
```

### Linting and Formatting
```bash
# Run all pre-commit hooks (recommended before committing)
pre-commit run --all-files

# Individual tools
black src/multiplierless tests/    # Format code
isort src/multiplierless tests/    # Sort imports (black profile)
flake8 src/ tests/                 # Lint (max line length: 88)
mypy src/                          # Type check (Python 3.12 target)
```

### Build
```bash
tox -e build          # Build sdist + wheel
tox -e clean          # Remove build artifacts
```

### Documentation
```bash
tox -e docs           # Build HTML docs
tox -e doctests       # Run doctests
```

### CLI
```bash
# FIR filter design CLI (console_scripts entry point)
fir-design <filter_spec.json>
# Or
python -m multiplierless.fir_design <filter_spec.json>
```

## Code Style Guidelines

### Imports
- **Order**: stdlib → third-party → local (enforced by isort)
- **Tooling**: isort with Black profile (`.isort.cfg`)
- **Third-party deps**: `numpy`, `csdigit` (CSD conversion), `ellalgo` (ellipsoid method), `ginger` (root-finding)

### Formatting
- **Formatter**: Black (24.3.0)
- **Line length**: 88 characters (configured in setup.cfg and `.flake8`)
- **Linting**: flake8 ignores E203, W503 (Black-compatible)
- **Pre-commit**: Enforced via `.pre-commit-config.yaml`

### Type Hints
- **Required**: All function parameters and return types
- **Style**: Modern syntax (`list[str]`, `dict[int, ...]`, `str | None`) — Python ≥ 3.9
- **Walrus operator**: Used in hot paths (`if cut := self.assess_feas(xc):`)

### Naming Conventions
- **Functions**: snake_case (e.g., `spectral_fact`, `csd_quantize`, `create_lowpass_case_params`)
- **Private helpers**: Prefix with underscore (e.g., `_power_spectrum_fft`, `_generate_transpose_verilog`)
- **Classes**: PascalCase (e.g., `LowpassOracleQ`, `Oracle`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULTS`)

### Docstrings
- **Style**: Google-style with `Args:` / `Returns:` sections
- **Module docs**: Describe the module's purpose
```python
def spectral_fact(r: np.ndarray) -> np.ndarray:
    """Spectral factorization of auto-correlation coefficients.

    Default entry point; delegates to the FFT-based implementation.

    Args:
        r: Auto-correlation coefficients.

    Returns:
        Minimum-phase impulse response coefficients.
    """
```

### Error Handling
- **Explicit validation**: Raise `ValueError`/`RuntimeError` for invalid inputs or failed optimization
```python
if not coeffs:
    raise ValueError("At least one coefficient is required")
raise RuntimeError(f"Spectral factorization failed: min={min_val:.6e}")
```
- **CLI exit codes**: Return `1` on failure, `0` on success from `main()`
- **Testing**: Use `pytest.raises` for error conditions

### Testing Patterns
- **Framework**: pytest with hypothesis property-based tests and pytest-benchmark
- **Coverage**: On by default (`--cov multiplierless --cov-report term-missing`)
- **Numerics**: Use `pytest.approx` for floating-point comparisons
- **Naming**: `test_*` prefix, one file per module

### Pre-commit Hooks
- trailing-whitespace, check-added-large-files, check-ast, check-json,
  check-merge-conflict, check-xml, check-yaml, debug-statements,
  end-of-file-fixer, requirements-txt-fixer, mixed-line-ending,
  isort (5.13.2), black (24.3.0), flake8 (7.0.0)

### Configuration Files
- `setup.cfg`: Package metadata, pytest options, flake8 settings, console_scripts entry point
- `pyproject.toml`: Build system
- `tox.ini`: Test environments (default, build, clean, docs, doctests, publish)
- `.isort.cfg`: Import sorting (Black profile)
- `mypy.ini`: Type checking (Python 3.12, ignores `ginger`, `ellalgo`, `csdigit`, `matplotlib`)

## Key Project Context

multiplierless designs multiplierless (CSD-based) FIR filters:
- **Spectral factorization**: `spectral_fact.py` — `spectral_fact` (FFT/Kolmogorov path), `spectral_fact_fft`, `spectral_fact_root` (Aberth-Ehrlich root path), `inverse_spectral_fact`
- **Optimization**: `lowpass_oracle_q.py` provides `LowpassOracleQ` oracle + `csd_quantize`, driven by the `ellalgo` cutting-plane/ellipsoid method
- **CLI + Verilog**: `fir_design.py` reads JSON specs, runs the optimization, and emits CSD coefficients plus synthesizable Verilog modules (transpose form with cross-CSE)
- **Key dependencies**: `numpy`, `csdigit` (CSD conversion), `ellalgo` (ellipsoid method), `ginger` (polynomial root-finding)
- **Output**: Intermediate step in an iterative filter-design optimization loop, not a final filter design
