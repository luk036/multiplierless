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
    reg signed [DATA_WIDTH-1:0] shift_reg_0;
    reg signed [DATA_WIDTH-1:0] shift_reg_1;
    reg signed [DATA_WIDTH-1:0] shift_reg_2;
    reg signed [DATA_WIDTH-1:0] shift_reg_3;
    reg signed [DATA_WIDTH-1:0] shift_reg_4;
    reg signed [DATA_WIDTH-1:0] shift_reg_5;
    reg signed [DATA_WIDTH-1:0] shift_reg_6;
    reg signed [DATA_WIDTH-1:0] shift_reg_7;
    reg signed [DATA_WIDTH-1:0] shift_reg_8;
    reg signed [DATA_WIDTH-1:0] shift_reg_9;
    reg signed [DATA_WIDTH-1:0] shift_reg_10;
    reg signed [DATA_WIDTH-1:0] shift_reg_11;
    reg signed [DATA_WIDTH-1:0] shift_reg_12;
    reg signed [DATA_WIDTH-1:0] shift_reg_13;
    reg signed [DATA_WIDTH-1:0] shift_reg_14;
    reg signed [DATA_WIDTH-1:0] shift_reg_15;
    reg signed [DATA_WIDTH-1:0] shift_reg_16;
    reg signed [DATA_WIDTH-1:0] shift_reg_17;
    reg signed [DATA_WIDTH-1:0] shift_reg_18;
    reg signed [DATA_WIDTH-1:0] shift_reg_19;
    reg signed [DATA_WIDTH-1:0] shift_reg_20;
    reg signed [DATA_WIDTH-1:0] shift_reg_21;
    reg signed [DATA_WIDTH-1:0] shift_reg_22;
    reg signed [DATA_WIDTH-1:0] shift_reg_23;
    reg signed [DATA_WIDTH-1:0] shift_reg_24;
    reg signed [DATA_WIDTH-1:0] shift_reg_25;
    reg signed [DATA_WIDTH-1:0] shift_reg_26;
    reg signed [DATA_WIDTH-1:0] shift_reg_27;
    reg signed [DATA_WIDTH-1:0] shift_reg_28;
    reg signed [DATA_WIDTH-1:0] shift_reg_29;
    reg signed [DATA_WIDTH-1:0] shift_reg_30;
    reg signed [DATA_WIDTH-1:0] shift_reg_31;

    // Accumulator for filter output
    reg signed [ACC_WIDTH-1:0] accumulator;

    // Pipeline registers
    reg [4:0] tap_counter;
    reg processing;

    // CSD coefficients
    wire signed [COEF_WIDTH-1:0] coef_0  = 16'sd415;
    wire signed [COEF_WIDTH-1:0] coef_1  = 16'sd1251;
    wire signed [COEF_WIDTH-1:0] coef_2  = 16'sd2017;
    wire signed [COEF_WIDTH-1:0] coef_3  = 16'sd2876;
    wire signed [COEF_WIDTH-1:0] coef_4  = 16'sd3725;
    wire signed [COEF_WIDTH-1:0] coef_5  = 16'sd4428;
    wire signed [COEF_WIDTH-1:0] coef_6  = 16'sd4858;
    wire signed [COEF_WIDTH-1:0] coef_7  = 16'sd4957;
    wire signed [COEF_WIDTH-1:0] coef_8  = 16'sd4615;
    wire signed [COEF_WIDTH-1:0] coef_9  = 16'sd3904;
    wire signed [COEF_WIDTH-1:0] coef_10 = 16'sd2872;
    wire signed [COEF_WIDTH-1:0] coef_11 = 16'sd1671;
    wire signed [COEF_WIDTH-1:0] coef_12 = 16'sd471;
    wire signed [COEF_WIDTH-1:0] coef_13 = -16'sd557;
    wire signed [COEF_WIDTH-1:0] coef_14 = -16'sd1307;
    wire signed [COEF_WIDTH-1:0] coef_15 = -16'sd1694;
    wire signed [COEF_WIDTH-1:0] coef_16 = -16'sd1697;
    wire signed [COEF_WIDTH-1:0] coef_17 = -16'sd1374;
    wire signed [COEF_WIDTH-1:0] coef_18 = -16'sd842;
    wire signed [COEF_WIDTH-1:0] coef_19 = -16'sd245;
    wire signed [COEF_WIDTH-1:0] coef_20 = 16'sd298;
    wire signed [COEF_WIDTH-1:0] coef_21 = 16'sd702;
    wire signed [COEF_WIDTH-1:0] coef_22 = 16'sd900;
    wire signed [COEF_WIDTH-1:0] coef_23 = 16'sd876;
    wire signed [COEF_WIDTH-1:0] coef_24 = 16'sd708;
    wire signed [COEF_WIDTH-1:0] coef_25 = 16'sd405;
    wire signed [COEF_WIDTH-1:0] coef_26 = 16'sd110;
    wire signed [COEF_WIDTH-1:0] coef_27 = -16'sd144;
    wire signed [COEF_WIDTH-1:0] coef_28 = -16'sd317;
    wire signed [COEF_WIDTH-1:0] coef_29 = -16'sd382;
    wire signed [COEF_WIDTH-1:0] coef_30 = -16'sd369;
    wire signed [COEF_WIDTH-1:0] coef_31 = -16'sd454;

    // Sequential processing
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg_0 <= 0;
            shift_reg_1 <= 0;
            shift_reg_2 <= 0;
            shift_reg_3 <= 0;
            shift_reg_4 <= 0;
            shift_reg_5 <= 0;
            shift_reg_6 <= 0;
            shift_reg_7 <= 0;
            shift_reg_8 <= 0;
            shift_reg_9 <= 0;
            shift_reg_10 <= 0;
            shift_reg_11 <= 0;
            shift_reg_12 <= 0;
            shift_reg_13 <= 0;
            shift_reg_14 <= 0;
            shift_reg_15 <= 0;
            shift_reg_16 <= 0;
            shift_reg_17 <= 0;
            shift_reg_18 <= 0;
            shift_reg_19 <= 0;
            shift_reg_20 <= 0;
            shift_reg_21 <= 0;
            shift_reg_22 <= 0;
            shift_reg_23 <= 0;
            shift_reg_24 <= 0;
            shift_reg_25 <= 0;
            shift_reg_26 <= 0;
            shift_reg_27 <= 0;
            shift_reg_28 <= 0;
            shift_reg_29 <= 0;
            shift_reg_30 <= 0;
            shift_reg_31 <= 0;
            tap_counter <= 0;
            processing <= 0;
            accumulator <= 0;
            valid_out <= 0;
        end else begin
            // Shift in new input sample
            shift_reg_31 <= shift_reg_30;
            shift_reg_30 <= shift_reg_29;
            shift_reg_29 <= shift_reg_28;
            shift_reg_28 <= shift_reg_27;
            shift_reg_27 <= shift_reg_26;
            shift_reg_26 <= shift_reg_25;
            shift_reg_25 <= shift_reg_24;
            shift_reg_24 <= shift_reg_23;
            shift_reg_23 <= shift_reg_22;
            shift_reg_22 <= shift_reg_21;
            shift_reg_21 <= shift_reg_20;
            shift_reg_20 <= shift_reg_19;
            shift_reg_19 <= shift_reg_18;
            shift_reg_18 <= shift_reg_17;
            shift_reg_17 <= shift_reg_16;
            shift_reg_16 <= shift_reg_15;
            shift_reg_15 <= shift_reg_14;
            shift_reg_14 <= shift_reg_13;
            shift_reg_13 <= shift_reg_12;
            shift_reg_12 <= shift_reg_11;
            shift_reg_11 <= shift_reg_10;
            shift_reg_10 <= shift_reg_9;
            shift_reg_9 <= shift_reg_8;
            shift_reg_8 <= shift_reg_7;
            shift_reg_7 <= shift_reg_6;
            shift_reg_6 <= shift_reg_5;
            shift_reg_5 <= shift_reg_4;
            shift_reg_4 <= shift_reg_3;
            shift_reg_3 <= shift_reg_2;
            shift_reg_2 <= shift_reg_1;
            shift_reg_1 <= shift_reg_0;
            shift_reg_0 <= data_in;

            // Sequential processing
            if (!processing) begin
                tap_counter <= 0;
                accumulator <= 0;
                processing <= 1;
            end else if (tap_counter < TAPS) begin
                case (tap_counter)
                    0: accumulator <= accumulator + (shift_reg_0 * coef_0);
                    1: accumulator <= accumulator + (shift_reg_1 * coef_1);
                    2: accumulator <= accumulator + (shift_reg_2 * coef_2);
                    3: accumulator <= accumulator + (shift_reg_3 * coef_3);
                    4: accumulator <= accumulator + (shift_reg_4 * coef_4);
                    5: accumulator <= accumulator + (shift_reg_5 * coef_5);
                    6: accumulator <= accumulator + (shift_reg_6 * coef_6);
                    7: accumulator <= accumulator + (shift_reg_7 * coef_7);
                    8: accumulator <= accumulator + (shift_reg_8 * coef_8);
                    9: accumulator <= accumulator + (shift_reg_9 * coef_9);
                    10: accumulator <= accumulator + (shift_reg_10 * coef_10);
                    11: accumulator <= accumulator + (shift_reg_11 * coef_11);
                    12: accumulator <= accumulator + (shift_reg_12 * coef_12);
                    13: accumulator <= accumulator + (shift_reg_13 * coef_13);
                    14: accumulator <= accumulator + (shift_reg_14 * coef_14);
                    15: accumulator <= accumulator + (shift_reg_15 * coef_15);
                    16: accumulator <= accumulator + (shift_reg_16 * coef_16);
                    17: accumulator <= accumulator + (shift_reg_17 * coef_17);
                    18: accumulator <= accumulator + (shift_reg_18 * coef_18);
                    19: accumulator <= accumulator + (shift_reg_19 * coef_19);
                    20: accumulator <= accumulator + (shift_reg_20 * coef_20);
                    21: accumulator <= accumulator + (shift_reg_21 * coef_21);
                    22: accumulator <= accumulator + (shift_reg_22 * coef_22);
                    23: accumulator <= accumulator + (shift_reg_23 * coef_23);
                    24: accumulator <= accumulator + (shift_reg_24 * coef_24);
                    25: accumulator <= accumulator + (shift_reg_25 * coef_25);
                    26: accumulator <= accumulator + (shift_reg_26 * coef_26);
                    27: accumulator <= accumulator + (shift_reg_27 * coef_27);
                    28: accumulator <= accumulator + (shift_reg_28 * coef_28);
                    29: accumulator <= accumulator + (shift_reg_29 * coef_29);
                    30: accumulator <= accumulator + (shift_reg_30 * coef_30);
                    31: accumulator <= accumulator + (shift_reg_31 * coef_31);
                endcase
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