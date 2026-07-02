"""Generate self-checking Verilog test benches for FIR filter verification.

Reads the JSON output from fir_design and creates test benches that:
  1. Instantiate the generated module
  2. Feed impulse stimulus (transpose) or static values (direct)
  3. Compare outputs against expected values computed from CSD coefficients
  4. Report PASS/FAIL via $display/$error

Usage:
    python tools/gen_test_bench.py                          # uses fir_filter_output.json
    python tools/gen_test_bench.py my_output.json           # custom output file
"""

import json
import re
import sys
from pathlib import Path


def csd_to_int(csd_str: str) -> int:
    """Convert a dotless CSD string ('+', '-', '0') to its integer value."""
    val = 0
    for i, ch in enumerate(csd_str):
        power = len(csd_str) - 1 - i
        if ch == "+":
            val += 1 << power
        elif ch == "-":
            val -= 1 << power
    return val


def load_json(path: str | Path) -> dict:
    with open(path) as f:
        return json.load(f)


def parse_widths(verilog: str) -> tuple[int, int]:
    """Parse input_width and output_width from Verilog module text."""
    iw = ow = None
    for line in verilog.splitlines():
        m = re.search(r"input\s+signed\s+\[(\d+):0\]", line)
        if m and "x" in line:
            iw = int(m.group(1)) + 1
        m = re.search(r"output\s+signed\s+\[(\d+):0\]", line)
        if m and ("y" in line or "h0" in line):
            ow = int(m.group(1)) + 1
    if iw is None:
        raise ValueError("Could not parse input_width from Verilog")
    return iw, ow or (iw + 20)


def gen_tb_transpose(data: dict) -> str:
    """Generate self-checking test bench for transpose-form FIR filter."""
    coeffs = data["coefficients"]
    N = len(coeffs)
    verilog = data["verilog"]
    input_width, output_width = parse_widths(verilog)

    # Build expected values from CSD strings
    csd_raw = [c["csd"] for c in coeffs]
    max_len = max(len(s) for s in csd_raw)
    expected = []
    for s in csd_raw:
        raw = s.replace(".", "")
        while len(raw) < max_len:
            raw = "0" + raw
        expected.append(csd_to_int(raw))

    # Generate per-cycle expected value as case statement
    expected_case = "\n".join(
        f"            {i}: expected = {'-' if e < 0 else ''}{output_width}'sd{abs(e)};"
        for i, e in enumerate(expected)
    )

    tb = f"""// Auto-generated test bench for transpose-form FIR filter
// N = {N}, input_width = {input_width}, output_width = {output_width}

`timescale 1ns / 1ps

module tb_fir_filter_transpose;

    reg clk;
    reg rst_n;
    reg signed [{input_width - 1}:0] x;
    wire signed [{output_width - 1}:0] y;

    fir_filter uut (
        .clk(clk),
        .rst_n(rst_n),
        .x(x),
        .y(y)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    integer i, errors;
    reg signed [{output_width - 1}:0] expected;

    initial begin
        errors = 0;
        $display("========================================");
        $display("Transpose-Form FIR Filter Test Bench");
        $display("N=%0d, input_width=%0d, output_width=%0d", {N}, {input_width}, {output_width});
        $display("========================================");
        $display("");

        rst_n = 0;
        x = 0;
        #15;
        rst_n = 1;
        #5;

        for (i = 0; i < {N}; i = i + 1) begin
            if (i == 0) x = 1;
            else x = 0;
            @(posedge clk);
            #1;
            case (i)
{expected_case}
            endcase
            if (y !== expected) begin
                $display("FAIL: cycle %0d: y=%0d, expected=%0d", i, y, expected);
                errors = errors + 1;
            end else begin
                $display("PASS: cycle %0d: y=%0d", i, y);
            end
        end

        for (i = 0; i < 4; i = i + 1) begin
            @(posedge clk);
            #1;
            if (y !== 0) begin
                $display("FAIL: tail cycle %0d: y=%0d, expected=0", {N} + i, y);
                errors = errors + 1;
            end
        end

        $display("");
        if (errors == 0) begin
            $display("========================================");
            $display("ALL TESTS PASSED (%0d checks)", {N});
            $display("========================================");
        end else begin
            $display("========================================");
            $display("FAILURES: %0d / %0d tests failed", errors, {N});
            $display("========================================");
        end
        $finish;
    end

endmodule
"""
    return tb


def gen_tb_direct(data: dict) -> str:
    """Generate self-checking test bench for direct-form multiplier bank."""
    coeffs = data["coefficients"]
    N = len(coeffs)
    verilog = data["verilog"]
    input_width, _ = parse_widths(verilog)

    # Build expected values from CSD strings
    csd_raw = [c["csd"] for c in coeffs]
    max_len = max(len(s) for s in csd_raw)
    expected = []
    for s in csd_raw:
        raw = s.replace(".", "")
        while len(raw) < max_len:
            raw = "0" + raw
        expected.append(csd_to_int(raw))

    # Collect output port names and widths
    port_widths = []
    for line in verilog.splitlines():
        m = re.search(r"output\s+signed\s+\[(\d+):0\]\s+(\w+)", line)
        if m:
            port_widths.append((m.group(2), int(m.group(1)) + 1))

    # Build port declarations and connections
    port_decls = "\n".join(
        f"    wire signed [{pw - 1}:0] {name};" for name, pw in port_widths
    )
    port_connects = "\n".join(
        f"        .{name}({name})" + ("," if i < len(port_widths) - 1 else "")
        for i, (name, _pw) in enumerate(port_widths)
    )

    # Build per-coefficient expected values for the case statement
    expected_hex = [f"        {pw}'sd{e}" for (_, pw), e in zip(port_widths, expected)]

    # Build test: apply several test values
    test_values = [1, -1, 127, -128]
    test_blocks = []
    for tv in test_values:
        if abs(tv) >= (1 << (input_width - 1)):
            continue
        block = f"        // Test x = {tv}\n"
        block += f"        x = {tv};\n"
        block += "        #10;\n"
        for i, (name, pw) in enumerate(port_widths):
            exp = expected[i] * tv
            exp_str = f"{pw}'sd{abs(exp)}" if exp >= 0 else f"-{pw}'sd{abs(exp)}"
            block += f"        if ({name} !== {exp_str}) begin\n"
            block += f'            $display("FAIL: x={tv}, {name}=%0d, expected=%0d", {name}, {exp});\n'
            block += "            errors = errors + 1;\n"
            block += "        end else begin\n"
            block += f'            $display("PASS: x={tv}, {name}=%0d", {name});\n'
            block += "        end\n"
        test_blocks.append(block)

    tests = "\n".join(test_blocks)

    mod_name = None
    for line in verilog.splitlines():
        m = re.search(r"module\s+(\w+)", line)
        if m:
            mod_name = m.group(1)
            break

    tb = f"""// Auto-generated test bench for direct-form FIR multiplier bank
// N = {N}, input_width = {input_width}

`timescale 1ns / 1ps

module tb_fir_filter_direct;

    reg signed [{input_width - 1}:0] x;
{port_decls}

    {mod_name} uut (
        .x(x),
{port_connects}
    );

    integer errors;

    initial begin
        errors = 0;
        $display("========================================");
        $display("Direct-Form FIR Multiplier Bank Test Bench");
        $display("N=%0d, input_width=%0d", {N}, {input_width});
        $display("========================================");
        $display("");

{tests}
        // Summary
        $display("");
        if (errors == 0) begin
            $display("========================================");
            $display("ALL TESTS PASSED");
            $display("========================================");
        end else begin
            $display("========================================");
            $display("FAILURES: %0d tests failed", errors);
            $display("========================================");
        end
        $finish;
    end

endmodule
"""
    return tb


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "fir_filter_output.json"
    data = load_json(path)
    verilog = data.get("verilog", "")
    is_transpose = "posedge clk" in verilog

    if is_transpose:
        tb = gen_tb_transpose(data)
        out_name = "tb_fir_filter_transpose.v"
    else:
        tb = gen_tb_direct(data)
        out_name = "tb_fir_filter_direct.v"

    Path(out_name).write_text(tb)
    print(f"Generated {out_name} ({len(tb)} chars)")


if __name__ == "__main__":
    main()
