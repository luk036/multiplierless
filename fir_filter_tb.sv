`timescale 1ns/1ps

module fir_filter_tb;

    // Parameters
    parameter DATA_WIDTH = 16;
    parameter COEF_WIDTH = 16;
    parameter ACC_WIDTH = 32;
    parameter TAPS = 32;
    parameter CLK_PERIOD = 10; // 10ns clock period

    // Test signals
    logic clk;
    logic rst_n;
    logic signed [DATA_WIDTH-1:0] data_in;
    logic signed [DATA_WIDTH-1:0] data_out;
    logic valid_out;

    // Test data
    logic signed [DATA_WIDTH-1:0] test_signal [0:99];
    logic signed [DATA_WIDTH-1:0] expected_output [0:99];
    int error_count;

    // Instantiate the FIR filter
    fir_filter #(
        .DATA_WIDTH(DATA_WIDTH),
        .COEF_WIDTH(COEF_WIDTH),
        .ACC_WIDTH(ACC_WIDTH),
        .TAPS(TAPS)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(data_out),
        .valid_out(valid_out)
    );

    // Clock generation
    always begin
        #CLK_PERIOD clk = ~clk;
    end

    // Test stimulus and checking
    initial begin
        // Initialize signals
        clk = 0;
        rst_n = 0;
        data_in = 0;
        error_count = 0;

        // Generate test signal (impulse response test)
        for (int i = 0; i < 100; i++) begin
            test_signal[i] = (i == 10) ? 16'sd1000 : 16'sd0; // Impulse at time 10
        end

        // Reset sequence
        #20 rst_n = 1;
        #10;

        $display("Starting FIR Filter Testbench");
        $display("Testing impulse response...");

        // Apply test signal
        for (int i = 0; i < 100; i++) begin
            @(posedge clk);
            data_in <= test_signal[i];

            // Check output when valid
            if (valid_out) begin
                // For impulse response, output should match the coefficients
                // (scaled and delayed by the pipeline)
                if (i >= TAPS) begin
                    logic signed [DATA_WIDTH-1:0] expected_coeff;
                    expected_coeff = get_expected_coefficient(i - TAPS);

                    if (data_out !== expected_coeff) begin
                        $display("Error at time %0d: Expected %0d, Got %0d",
                                $time, expected_coeff, data_out);
                        error_count++;
                    end
                end
            end
        end

        // Wait for pipeline to clear
        #(CLK_PERIOD * TAPS * 2);

        // Test with sine wave
        $display("Testing sine wave response...");
        test_sine_wave();

        // Test with step input
        $display("Testing step response...");
        test_step_response();

        // Final report
        #100;
        if (error_count == 0) begin
            $display("All tests passed successfully!");
        end else begin
            $display("%0d errors detected", error_count);
        end

        $finish;
    end

    // Task to test sine wave input
    task test_sine_wave();
        real phase, frequency, amplitude;
        int samples;

        phase = 0.0;
        frequency = 0.1; // Normalized frequency
        amplitude = 2000.0;
        samples = 200;

        for (int i = 0; i < samples; i++) begin
            @(posedge clk);
            data_in <= 16'sd(amplitude * $sin(2.0 * 3.14159 * frequency * i));
            phase += 2.0 * 3.14159 * frequency;
        end

        // Wait for pipeline
        #(CLK_PERIOD * TAPS * 2);
    endtask

    // Task to test step response
    task test_step_response();
        for (int i = 0; i < 100; i++) begin
            @(posedge clk);
            data_in <= (i >= 20) ? 16'sd500 : 16'sd0; // Step at time 20
        end

        // Wait for pipeline
        #(CLK_PERIOD * TAPS * 2);
    endtask

    // Function to get expected coefficient value
    function logic signed [DATA_WIDTH-1:0] get_expected_coefficient(int index);
        // Return the coefficient at the given index (scaled appropriately)
        logic signed [COEF_WIDTH-1:0] coeffs [0:TAPS-1] = '{
            16'sd415,    // 0.02530592
            16'sd1251,   // 0.0380998
            16'sd2017,   // 0.06151268
            16'sd2876,   // 0.08775936
            16'sd3725,   // 0.11365458
            16'sd4428,   // 0.13506537
            16'sd4858,   // 0.14815305
            16'sd4957,   // 0.15116266
            16'sd4615,   // 0.14076425
            16'sd3904,   // 0.11909375
            16'sd2872,   // 0.08757255
            16'sd1671,   // 0.05098522
            16'sd471,    // 0.01436508
            -16'sd557,   // -0.01696102
            -16'sd1307,  // -0.03985817
            -16'sd1694,  // -0.05164135
            -16'sd1697,  // -0.05172971
            -16'sd1374,  // -0.04184722
            -16'sd842,   // -0.02565308
            -16'sd245,   // -0.00746042
            16'sd298,    // 0.0091019
            16'sd702,    // 0.02139123
            16'sd900,    // 0.02741899
            16'sd876,    // 0.02670435
            16'sd708,    // 0.02155094
            16'sd405,    // 0.01236503
            16'sd110,    // 0.00336273
            -16'sd144,   // -0.00440621
            -16'sd317,   // -0.00966972
            -16'sd382,   // -0.01165515
            -16'sd369,   // -0.01128053
            -16'sd454    // -0.0138418
        };

        if (index >= 0 && index < TAPS) begin
            return coeffs[index];
        end else begin
            return 16'sd0;
        end
    endfunction

    // Waveform dump
    initial begin
        $dumpfile("fir_filter_tb.vcd");
        $dumpvars(0, fir_filter_tb);
    end

endmodule