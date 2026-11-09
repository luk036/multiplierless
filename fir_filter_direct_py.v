
module fir_filter_direct_py (
    input signed [15:0] x,      // Input value
    output signed [34:0] h0,
    output signed [34:0] h1,
    output signed [34:0] h2,
    output signed [34:0] h3,
    output signed [34:0] h4,
    output signed [34:0] h5,
    output signed [34:0] h6,
    output signed [34:0] h7,
    output signed [34:0] h8,
    output signed [34:0] h9,
    output signed [34:0] h10,
    output signed [34:0] h11,
    output signed [34:0] h12,
    output signed [34:0] h13,
    output signed [34:0] h14,
    output signed [34:0] h15,
    output signed [34:0] h16,
    output signed [34:0] h17,
    output signed [34:0] h18,
    output signed [34:0] h19,
    output signed [34:0] h20,
    output signed [34:0] h21,
    output signed [34:0] h22,
    output signed [34:0] h23,
    output signed [34:0] h24,
    output signed [34:0] h25,
    output signed [34:0] h26,
    output signed [34:0] h27,
    output signed [34:0] h28,
    output signed [34:0] h29,
    output signed [34:0] h30,
    output signed [34:0] h31
);

    // Create shifted versions of input
    wire signed [34:0] x_shift16 = x <<< 16;
    wire signed [34:0] x_shift15 = x <<< 15;
    wire signed [34:0] x_shift14 = x <<< 14;
    wire signed [34:0] x_shift13 = x <<< 13;
    wire signed [34:0] x_shift12 = x <<< 12;
    wire signed [34:0] x_shift11 = x <<< 11;
    wire signed [34:0] x_shift10 = x <<< 10;
    wire signed [34:0] x_shift9 = x <<< 9;
    wire signed [34:0] x_shift8 = x <<< 8;
    wire signed [34:0] x_shift7 = x <<< 7;
    wire signed [34:0] x_shift6 = x <<< 6;
    wire signed [34:0] x_shift5 = x <<< 5;
    wire signed [34:0] x_shift4 = x <<< 4;
    wire signed [34:0] x_shift3 = x <<< 3;
    wire signed [34:0] x_shift2 = x <<< 2;
    wire signed [34:0] x_shift1 = x <<< 1;
    wire signed [34:0] x_shift0 = x <<< 0;

    // Cross-CSE: shared pattern "0-0-"
    wire signed [34:0] _cse_0 = -x_shift14 - x_shift12;

    // h0: 0000000+0+000-000-00
    assign h0 = x_shift12 + x_shift10 - x_shift6 - x_shift2;

    // h1: 000000+00+00000+00-0
    assign h1 = x_shift13 + x_shift10 + x_shift4 - x_shift1;

    // h2: 00000+00000+00+0-000
    assign h2 = x_shift14 + x_shift8 + x_shift5 - x_shift3;

    // h3: 0000+0-0+0-000000000
    assign h3 = x_shift15 - x_shift13 + x_shift11 - x_shift9;

    // h4: 0000+00+00+0-0000000
    assign h4 = x_shift15 + x_shift12 + x_shift9 - x_shift7;

    // h5: 000+0-00000-00000-00
    assign h5 = x_shift16 - x_shift14 - x_shift8 - x_shift2;

    // h6: 000+00-0+00+00000000
    assign h6 = x_shift16 - x_shift13 + x_shift11 + x_shift8;

    // h7: 000+0000+00+00+00000
    assign h7 = x_shift16 + x_shift11 + x_shift8 + x_shift5;

    // h8: 000+00+0-0+000000000
    assign h8 = x_shift16 + x_shift13 - x_shift11 + x_shift9;

    // h9: 000+00+0-00000000-00
    assign h9 = x_shift16 + x_shift13 - x_shift11 - x_shift2;

    // h10: 000+00000000+0000-0+
    assign h10 = x_shift16 + x_shift7 - x_shift2 + x_shift0;

    // h11: 000+00-0-0-000000000
    assign h11 = x_shift16 + (_cse_0 >>> 1) + -x_shift9;

    // h12: 0000+0+00-00-0000000
    assign h12 = x_shift15 + x_shift13 - x_shift10 - x_shift7;

    // h13: 0000+0-0-0000000-000
    assign h13 = x_shift15 + (_cse_0 >>> 1) + -x_shift3;

    // h14: 0000000+0+0+0000+000
    assign h14 = x_shift12 + x_shift10 + x_shift8 + x_shift3;

    // h15: 000000-0-00+0+000000
    assign h15 = (_cse_0 >>> 1) + x_shift8 + x_shift6;

    // h16: 00000-0-0-00-0000000
    assign h16 = _cse_0 + -x_shift10 - x_shift7;

    // h17: 0000-00+000+000+0000
    assign h17 = -x_shift15 + x_shift12 + x_shift8 + x_shift4;

    // h18: 0000-000+0+00+000000
    assign h18 = -x_shift15 + x_shift11 + x_shift9 + x_shift6;

    // h19: 0000-0+0-0-000000000
    assign h19 = -x_shift15 + x_shift13 + (_cse_0 >>> 3);

    // h20: 00000-0-0000-0-00000
    assign h20 = _cse_0 + (_cse_0 >>> 7);

    // h21: 00000-0+000+0-000000
    assign h21 = -x_shift14 + x_shift12 + x_shift8 - x_shift6;

    // h22: 0000000-0+00-0-00000
    assign h22 = -x_shift12 + x_shift10 + (_cse_0 >>> 7);

    // h23: 0000000+00+0+00+0000
    assign h23 = x_shift12 + x_shift9 + x_shift7 + x_shift4;

    // h24: 000000+0+0+0000+0000
    assign h24 = x_shift13 + x_shift11 + x_shift9 + x_shift4;

    // h25: 00000+00-0-0+0000000
    assign h25 = x_shift14 + (_cse_0 >>> 3) + x_shift7;

    // h26: 00000+00-0+0+0000000
    assign h26 = x_shift14 - x_shift11 + x_shift9 + x_shift7;

    // h27: 00000+00-0-0-0000000
    assign h27 = x_shift14 + (_cse_0 >>> 3) + -x_shift7;

    // h28: 00000+0-0-0000-00000
    assign h28 = x_shift14 + (_cse_0 >>> 2) + -x_shift5;

    // h29: 000000+00000-0+0+000
    assign h29 = x_shift13 - x_shift7 + x_shift5 + x_shift3;

    // h30: 0000000+0+000+0-0000
    assign h30 = x_shift12 + x_shift10 + x_shift6 - x_shift4;

    // h31: 0000000+0-00-0+00000
    assign h31 = x_shift12 - x_shift10 - x_shift7 + x_shift5;
endmodule
