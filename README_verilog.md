# Multiplierless FIR Filter SystemVerilog Implementation

This directory contains the SystemVerilog implementation of a multiplierless FIR lowpass filter using Canonical Signed Digit (CSD) representation.

## Files

- `fir_filter.sv`: Main FIR filter module implementing the multiplierless design
- `fir_filter_tb.sv`: Testbench for verifying the filter functionality
- `README_verilog.md`: This documentation file

## Filter Specifications

- Filter type: Lowpass FIR
- Number of taps (N): 32
- Non-zero digits per coefficient (nzz): 4
- Passband edge: 0.12π
- Stopband edge: 0.20π
- Passband ripple: ±0.025 dB
- Stopband attenuation: 0.125

## Implementation Details

### CSD Representation
The filter uses Canonical Signed Digit (CSD) representation to eliminate multipliers:
- Each coefficient is represented using CSD format
- Multiplications are implemented using shift-add operations
- Reduces hardware complexity and power consumption

### Fixed-Point Format
- Data width: 16 bits (Q1.15 format)
- Coefficient width: 16 bits (Q1.15 format)
- Accumulator width: 32 bits

### Architecture
- Sequential processing using a single accumulator
- Shift register for input samples
- Pipeline registers for timing control

## Simulation

To run the simulation:

```bash
# Using a SystemVerilog simulator (e.g., Vivado, ModelSim, Questa)
vlog fir_filter.sv fir_filter_tb.sv
vsim -c fir_filter_tb -do "run -all; quit"
```

The testbench performs the following tests:
1. Impulse response verification
2. Sine wave response
3. Step response

## Expected Results

The testbench will generate a VCD waveform file (`fir_filter_tb.vcd`) that can be analyzed with waveform viewers. The output should show:
- Correct impulse response matching the filter coefficients
- Proper lowpass filtering of sine wave inputs
- Expected step response characteristics

## Integration

To integrate this filter into your design:
1. Instantiate the `fir_filter` module with appropriate parameters
2. Connect the clock, reset, and data interfaces
3. Monitor `valid_out` to know when output data is ready
4. The output will be scaled to match the input data width

## Performance Considerations

- Latency: Approximately TAPS + pipeline_delay clock cycles
- Throughput: One sample processed every clock cycle after initial pipeline fill
- Resource utilization: Minimal due to multiplierless design