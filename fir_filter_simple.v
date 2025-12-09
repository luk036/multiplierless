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

    // Shift register for input samples
    reg signed [DATA_WIDTH-1:0] shift_reg [0:TAPS-1];

    // Accumulator for filter output
    reg signed [ACC_WIDTH-1:0] accumulator;

    // Pipeline registers
    reg [4:0] tap_counter;
    reg processing;

    // CSD coefficients (simplified for synthesis)
    wire signed [COEF_WIDTH-1:0] coefficients [0:TAPS-1];
    assign coefficients[0] = 16'sd415;
    assign coefficients[1] = 16'sd1251;
    assign coefficients[2] = 16'sd2017;
    assign coefficients[3] = 16'sd2876;
    assign coefficients[4] = 16'sd3725;
    assign coefficients[5] = 16'sd4428;
    assign coefficients[6] = 16'sd4858;
    assign coefficients[7] = 16'sd4957;
    assign coefficients[8] = 16'sd4615;
    assign coefficients[9] = 16'sd3904;
    assign coefficients[10] = 16'sd2872;
    assign coefficients[11] = 16'sd1671;
    assign coefficients[12] = 16'sd471;
    assign coefficients[13] = -16'sd557;
    assign coefficients[14] = -16'sd1307;
    assign coefficients[15] = -16'sd1694;
    assign coefficients[16] = -16'sd1697;
    assign coefficients[17] = -16'sd1374;
    assign coefficients[18] = -16'sd842;
    assign coefficients[19] = -16'sd245;
    assign coefficients[20] = 16'sd298;
    assign coefficients[21] = 16'sd702;
    assign coefficients[22] = 16'sd900;
    assign coefficients[23] = 16'sd876;
    assign coefficients[24] = 16'sd708;
    assign coefficients[25] = 16'sd405;
    assign coefficients[26] = 16'sd110;
    assign coefficients[27] = -16'sd144;
    assign coefficients[28] = -16'sd317;
    assign coefficients[29] = -16'sd382;
    assign coefficients[30] = -16'sd369;
    assign coefficients[31] = -16'sd454;

    // Initialize shift register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            integer i;
            for (i = 0; i < TAPS; i = i + 1) begin
                shift_reg[i] <= 0;
            end
            tap_counter <= 0;
            processing <= 0;
            accumulator <= 0;
            valid_out <= 0;
        end else begin
            // Shift in new input sample
            integer j;
            shift_reg[0] <= data_in;
            for (j = 0; j < TAPS-1; j = j + 1) begin
                shift_reg[j+1] <= shift_reg[j];
            end

            // Sequential processing
            if (!processing) begin
                tap_counter <= 0;
                accumulator <= 0;
                processing <= 1;
            end else if (tap_counter < TAPS) begin
                // Simple multiplication (not CSD for synthesis compatibility)
                accumulator <= accumulator + (shift_reg[tap_counter] * coefficients[tap_counter]);
                tap_counter <= tap_counter + 1;
            end else begin
                // Output the result
                data_out <= accumulator[ACC_WIDTH-1:ACC_WIDTH-DATA_WIDTH];
                valid_out <= 1;
                processing <= 0;
            end
        end
    end

endmodule