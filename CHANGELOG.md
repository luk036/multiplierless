# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-09

### Features
- **Transpose-form FIR Verilog generation with cross-CSE**: Added a transpose-form FIR generator as the default (`form: 'transpose'`), keeping the direct form available via `form: 'direct'`; both use cross-CSE shared sub-expression elimination, with the missing-comma issue in CSD port lists fixed via post-processing. (#32844a8)
- **Verilog/spectral strategy registries + `LowpassOracle`**: Extracted `LowpassOracle` with a `_scan_constraints` Template Method, a `SpectralMethod` enum + `spectral_fact_select`, and a `VERILOG_GENERATORS` registry. (#870dbd4)
- **cocotb simulation + testbench generator**: Added a `sim/` runner with Windows workarounds and `tools/gen_test_bench.py` for iverilog verification. (#0c08dff)

### Performance
- **Vectorized constraint scan**: Replaced the per-row Python dot-product loop in `LowpassOracle.assess_feas` with one `spectrum @ x` matvec plus boolean masks, preserving round-robin cut selection — assess_feas 3.05s → 0.082s (~37×), `main()` 3.66s → 0.49s (~7.5×). (#04021d4)
- **Direct CSD quantization + rfft power spectrum**: Added `csd_quantize()` (no string round-trip), replaced the matrix-multiply power spectrum with `np.fft.rfft`, and pre-allocated the gradient buffer. (#6ce65fd)
- **Cached FFT matrices**: Cache the `Bn`/`An` matrices in `spectral_fact_fft` (they depend only on filter order) — 5× warm-cache speedup at N=32. (#a593b20)

### Bug Fixes
- **Quantize on demand**: Retry after a feasibility cut now quantizes on demand. (#79118e7)
- **Local `RoundRobin` helper**: Added a local mirror of `ellalgo.round_robin` (which only exists on ellalgo's dev branch) so CI collection no longer fails. (#36aac1c, #ac6acb0)
- **mypy annotation**: Added a missing type annotation. (#94a69b6)

### Testing & Code Quality
- **Benchmarks**: Added `tests/test_benchmarks.py`. (#04021d4)
- **flake8/ruff cleanups**: Fixed E501 line-too-long and removed unused variables (F841). (#e8c036f, #4595071)

### Code Cleanup
- **Removed PyScaffold boilerplate**: Deleted `skeleton.py`/`test_skeleton.py`, dropped Python < 3.9 compat, dead entry points, stale `IFLOW.md`, duplicate `LICENSE`, and AI scratch files. (#2fbb581, #ac000f5, #f462db6)
- **Removed AI slop**: Stripped docstring/comment boilerplate; applied black and used `csd_quantize` in the output path. (#baafb91, #4e56854)

### Documentation
- **svgbob FIR diagram**: Added to the module docstring. (#1d63661)
- **AGENTS.md**: Added agent guidelines. (#dd7ac96)

### Build & CI
- **Python 3.10+**: Dropped Python 3.9 and start from 3.10. (#5f6dbdf)
- **CI dependency fixes**: Install `lds-gen` from git and force-reinstall after `setup.py develop --no-deps`; repaired broken `entry_points`/`skeleton` imports. (#ee4aa07, #7a8f3c7, #9fce48f, #3b82994)

### Maintenance
- **Generated Verilog outputs** committed; FIR design and simulation scripts updated. (#63c03c0, #95d55c7)

## [0.1.0] - 2024-01-15

### Added
- Initial release of multiplierless package
- Spectral factorization implementation
- Lowpass oracle with CSD constraints
- Property-based tests with Hypothesis
- Verilog implementation examples
- IIR filter design capabilities
