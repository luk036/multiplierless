module fir_filter #(
    parameter DATA_WIDTH = 16,
    parameter COEF_WIDTH = 16,
    parameter ACC_WIDTH = 32,
    parameter TAPS = 32
)(
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] data_in,
    output [DATA_WIDTH-1:0] data_out,
    output valid_out
);

    // CSD coefficients for N=32, nzz=4 lowpass filter
    // Format: signed fixed-point with 16 bits (Q1.15 format)
    reg signed [COEF_WIDTH-1:0] coefficients [0:TAPS-1];
        16'sd415,    // 0.02530592 -> "0.0000+0-0+00-"
        16'sd1251,   // 0.0380998  -> "0.0000+0+00-0-"
        16'sd2017,   // 0.06151268 -> "0.000+00000-0000-0-"
        16'sd2876,   // 0.08775936 -> "0.00+0-0-0+"
        16'sd3725,   // 0.11365458 -> "0.00+00-0+0000+"
        16'sd4428,   // 0.13506537 -> "0.00+000+0+0000-"
        16'sd4858,   // 0.14815305 -> "0.00+0+0-0000-"
        16'sd4957,   // 0.15116266 -> "0.00+0+00-0-"
        16'sd4615,   // 0.14076425 -> "0.00+00+00000000+0000-"
        16'sd3904,   // 0.11909375 -> "0.00+000-0+0-"
        16'sd2872,   // 0.08757255 -> "0.00+0-0-00+"
        16'sd1671,   // 0.05098522 -> "0.000+0-0+000+"
        16'sd471,    // 0.01436508 -> "0.00000+00-0+00+"
        -16'sd557,   // -0.01696102 -> "0.00000-00-0000000+00-"
        -16'sd1307,  // -0.03985817 -> "0.0000-0-0-0+"
        -16'sd1694,  // -0.05164135 -> "0.000-0+0-0-"
        -16'sd1697,  // -0.05172971 -> "0.000-0+0-0-"
        -16'sd1374,  // -0.04184722 -> "0.000-0+0+0+"
        -16'sd842,   // -0.02565308 -> "0.0000-00+0+00+"
        -16'sd245,   // -0.00746042 -> "0.000000-000+000+000-"
        16'sd298,    // 0.0091019   -> "0.000000+00+0+0+"
        16'sd702,    // 0.02139123  -> "0.0000+0-0-00-"
        16'sd900,    // 0.02741899  -> "0.0000+00-000000+00+"
        16'sd876,    // 0.02670435  -> "0.0000+00-0-0+"
        16'sd708,    // 0.02155094  -> "0.00000+0+0+0+"
        16'sd405,    // 0.01236503  -> "0.00000+0-0+0-"
        16'sd110,    // 0.00336273  -> "0.0000000+0-00+00-"
        -16'sd144,   // -0.00440621 -> "0.0000000-0-0+0-"
        -16'sd317,   // -0.00966972 -> "0.000000-0-00-0-"
        -16'sd382,   // -0.01165515 -> "0.00000-0+00-0+"
        -16'sd369,   // -0.01128053 -> "0.00000-0+00+0-"
        -16'sd454    // -0.0138418  -> "0.00000-00+000-0+"
    };

    // Shift register for input samples
    reg signed [DATA_WIDTH-1:0] shift_reg [0:TAPS-1];

    // Accumulator for filter output
    reg signed [ACC_WIDTH-1:0] accumulator;

    // Pipeline registers
    reg [4:0] tap_counter;
    reg processing;

    // Initialize shift register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < TAPS; i++) begin
                shift_reg[i] <= '0;
            end
            tap_counter <= '0;
            processing <= '0;
            accumulator <= '0;
            valid_out <= '0;
        end else begin
            // Shift in new input sample
            shift_reg[0] <= data_in;
            for (int i = 1; i < TAPS; i++) begin
                shift_reg[i] <= shift_reg[i-1];
            end

            // Sequential processing using CSD (shift-add operations)
            if (!processing) begin
                tap_counter <= '0;
                accumulator <= '0;
                processing <= 1'b1;
            end else if (tap_counter < TAPS) begin
                // CSD multiplication: coefficient * sample
                // Using shift-add operations for multiplierless implementation
                reg signed [ACC_WIDTH-1:0] partial_product;
                partial_product = csd_multiply(shift_reg[tap_counter], coefficients[tap_counter]);
                accumulator <= accumulator + partial_product;
                tap_counter <= tap_counter + 1;
            end else begin
                // Output the result (scaled back to DATA_WIDTH)
                data_out <= accumulator[ACC_WIDTH-1:ACC_WIDTH-DATA_WIDTH];
                valid_out <= 1'b1;
                processing <= 1'b0;
            end
        end
    end

    // CSD multiplier function (shift-add implementation)
    function automatic signed [ACC_WIDTH-1:0] csd_multiply(
        input signed [DATA_WIDTH-1:0] multiplicand,
        input signed [COEF_WIDTH-1:0] coefficient
    );
        signed [ACC_WIDTH-1:0] result;
        signed [ACC_WIDTH-1:0] temp;
        result = 0;
        temp = multiplicand;

        // CSD representation: process each bit
        for (int i = 0; i < COEF_WIDTH; i++) begin
            if (coefficient[i] == 1'b1) begin
                result = result + (temp >>> i);
            end
        end

        return result;
    endfunction

// Initialize coefficients
    initial begin
        coefficients[0] = 16'sd415;    // 0.02530592
        coefficients[1] = 16'sd1251;   // 0.0380998
        coefficients[2] = 16'sd2017;   // 0.06151268
        coefficients[3] = 16'sd2876;   // 0.08775936
        coefficients[4] = 16'sd3725;   // 0.11365458
        coefficients[5] = 16'sd4428;   // 0.13506537
        coefficients[6] = 16'sd4858;   // 0.14815305
        coefficients[7] = 16'sd4957;   // 0.15116266
        coefficients[8] = 16'sd4615;   // 0.14076425
        coefficients[9] = 16'sd3904;   // 0.11909375
        coefficients[10] = 16'sd2872;  // 0.08757255
        coefficients[11] = 16'sd1671;  // 0.05098522
        coefficients[12] = 16'sd471;   // 0.01436508
        coefficients[13] = -16'sd557;  // -0.01696102
        coefficients[14] = -16'sd1307; // -0.03985817
        coefficients[15] = -16'sd1694; // -0.05164135
        coefficients[16] = -16'sd1697; // -0.05172971
        coefficients[17] = -16'sd1374; // -0.04184722
        coefficients[18] = -16'sd842;  // -0.02565308
        coefficients[19] = -16'sd245;  // -0.00746042
        coefficients[20] = 16'sd298;   // 0.0091019
        coefficients[21] = 16'sd702;   // 0.02139123
        coefficients[22] = 16'sd900;   // 0.02741899
        coefficients[23] = 16'sd876;   // 0.02670435
        coefficients[24] = 16'sd708;   // 0.02155094
        coefficients[25] = 16'sd405;   // 0.01236503
        coefficients[26] = 16'sd110;   // 0.00336273
        coefficients[27] = -16'sd144;  // -0.00440621
        coefficients[28] = -16'sd317;  // -0.00966972
        coefficients[29] = -16'sd382;  // -0.01165515
        coefficients[30] = -16'sd369;  // -0.01128053
        coefficients[31] = -16'sd454;  // -0.0138418
    end

endmodule