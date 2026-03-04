# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Error handling for spectral_fact() function with informative error messages
- Input validation for spectral factorization to catch numerical errors
- Type hints to all public functions in .py files
- __all__ declarations to all .py modules for clearer public API
- Security scanning to CI pipeline with bandit
- Multi-Python version testing (3.9, 3.10, 3.11, 3.12) in CI

### Changed
- Updated pre-commit hook versions to latest stable releases
- Fixed .flake8 configuration to enable proper linting rules
- Removed hardcoded iteration counts from tests, using tolerance-based assertions
- Added missing dependencies (csdigit, ellalgo) to setup.cfg

### Fixed
- Dependency management - csdigit and ellalgo now properly declared in setup.cfg
- Test brittleness by removing hardcoded iteration count assertions

## [0.1.0] - 2024-01-15

### Added
- Initial release of multiplierless package
- Spectral factorization implementation
- Lowpass oracle with CSD constraints
- Property-based tests with Hypothesis
- Verilog implementation examples
- IIR filter design capabilities