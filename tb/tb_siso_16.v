// Self-checking testbench for siso_16 -- 12 directed test cases.
// Inputs change 1 ns after a rising clock edge; outputs are checked 1 ns after
// the next rising edge. Expected values are literals (not computed from the RTL).
`timescale 1ns/1ps
module tb_siso_16;
  reg         clk = 0, rst = 0, load = 0, left_right = 0, Din = 0;
  reg  [15:0] A = 16'h0000;
  wire        Dout;
  wire [15:0] shift_reg_out;

  integer checks = 0, errors = 0;

  siso_16 dut (.clk(clk), .rst(rst), .load(load), .left_right(left_right),
               .Din(Din), .A(A), .Dout(Dout), .shift_reg_out(shift_reg_out));

  always #5 clk = ~clk;                       // 10 ns period (100 MHz)

  task tick;       begin @(posedge clk); #1; end endtask

  // Check register contents and Dout (Dout = MSB when shifting left, LSB when shifting right)
  task check(input [15:0] exp, input [8*16-1:0] tag);
    reg exp_dout;
    begin
      exp_dout = left_right ? exp[15] : exp[0];
      checks = checks + 1;
      if (shift_reg_out !== exp || Dout !== exp_dout) begin
        errors = errors + 1;
        $display("FAIL  %0s  t=%0t  reg=%h (exp %h)  Dout=%b (exp %b)",
                 tag, $time, shift_reg_out, exp, Dout, exp_dout);
      end
    end
  endtask

  initial begin
    $dumpfile("results/logs/siso_16.vcd");
    $dumpvars(0, tb_siso_16);

    // TC1: synchronous reset
    rst = 1; load = 0; left_right = 1; Din = 0; A = 16'h0000;           tick; check(16'h0000, "TC1 reset");
    rst = 0;

    // TC2: parallel load 0xABCD
    load = 1; A = 16'hABCD;                                             tick; check(16'hABCD, "TC2 load");
    load = 0;

    // TC3: right shift x8, Din=0
    left_right = 0; Din = 0;
    tick; check(16'h55E6, "TC3 R0 #1");  tick; check(16'h2AF3, "TC3 R0 #2");
    tick; check(16'h1579, "TC3 R0 #3");  tick; check(16'h0ABC, "TC3 R0 #4");
    tick; check(16'h055E, "TC3 R0 #5");  tick; check(16'h02AF, "TC3 R0 #6");
    tick; check(16'h0157, "TC3 R0 #7");  tick; check(16'h00AB, "TC3 R0 #8");

    // TC4: right shift x8, Din=1
    Din = 1;
    tick; check(16'h8055, "TC4 R1 #1");  tick; check(16'hC02A, "TC4 R1 #2");
    tick; check(16'hE015, "TC4 R1 #3");  tick; check(16'hF00A, "TC4 R1 #4");
    tick; check(16'hF805, "TC4 R1 #5");  tick; check(16'hFC02, "TC4 R1 #6");
    tick; check(16'hFE01, "TC4 R1 #7");  tick; check(16'hFF00, "TC4 R1 #8");

    // TC5: load 0x1234, left shift x4, Din=0
    load = 1; A = 16'h1234; left_right = 1; Din = 0;                    tick; check(16'h1234, "TC5 load");
    load = 0;
    tick; check(16'h2468, "TC5 L0 #1");  tick; check(16'h48D0, "TC5 L0 #2");
    tick; check(16'h91A0, "TC5 L0 #3");  tick; check(16'h2340, "TC5 L0 #4");

    // TC6: left shift x4, Din=1
    Din = 1;
    tick; check(16'h4681, "TC6 L1 #1");  tick; check(16'h8D03, "TC6 L1 #2");
    tick; check(16'h1A07, "TC6 L1 #3");  tick; check(16'h340F, "TC6 L1 #4");

    // TC7: load 0xFFFF, one right shift with Din=0 -> 0x7FFF, Dout = LSB = 1
    load = 1; A = 16'hFFFF; left_right = 0; Din = 0;                    tick; check(16'hFFFF, "TC7 load");
    load = 0;                                                           tick; check(16'h7FFF, "TC7 R #1");

    // TC8: Dout selects MSB (left) or LSB (right)
    load = 1; A = 16'h8000; left_right = 1;                             tick; check(16'h8000, "TC8 L dout=1");
    left_right = 0; load = 1;                                           tick; check(16'h8000, "TC8 R dout=0");
    A = 16'h0001; left_right = 1;                                       tick; check(16'h0001, "TC8 L dout=0");
    left_right = 0;                                                     tick; check(16'h0001, "TC8 R dout=1");

    // TC9: reset has priority over load
    rst = 1; load = 1; A = 16'hFFFF;                                    tick; check(16'h0000, "TC9 rst>load");
    rst = 0; load = 0;

    // TC10: load has priority over shift
    load = 1; left_right = 1; Din = 1; A = 16'h5A5A;                    tick; check(16'h5A5A, "TC10 load>shift");
    load = 0;

    // TC11: 16-cycle flush, right then left (Din=0)
    load = 1; A = 16'hFFFF; left_right = 0; Din = 0;                    tick; check(16'hFFFF, "TC11 load");
    load = 0;
    tick; check(16'h7FFF, "TC11 R #1");  tick; check(16'h3FFF, "TC11 R #2");
    tick; check(16'h1FFF, "TC11 R #3");  tick; check(16'h0FFF, "TC11 R #4");
    tick; check(16'h07FF, "TC11 R #5");  tick; check(16'h03FF, "TC11 R #6");
    tick; check(16'h01FF, "TC11 R #7");  tick; check(16'h00FF, "TC11 R #8");
    tick; check(16'h007F, "TC11 R #9");  tick; check(16'h003F, "TC11 R #10");
    tick; check(16'h001F, "TC11 R #11"); tick; check(16'h000F, "TC11 R #12");
    tick; check(16'h0007, "TC11 R #13"); tick; check(16'h0003, "TC11 R #14");
    tick; check(16'h0001, "TC11 R #15"); tick; check(16'h0000, "TC11 R #16");
    load = 1; A = 16'hFFFF; left_right = 1;                             tick; check(16'hFFFF, "TC11 load L");
    load = 0;
    tick; check(16'hFFFE, "TC11 L #1");  tick; check(16'hFFFC, "TC11 L #2");
    tick; check(16'hFFF8, "TC11 L #3");  tick; check(16'hFFF0, "TC11 L #4");
    tick; check(16'hFFE0, "TC11 L #5");  tick; check(16'hFFC0, "TC11 L #6");
    tick; check(16'hFF80, "TC11 L #7");  tick; check(16'hFF00, "TC11 L #8");
    tick; check(16'hFE00, "TC11 L #9");  tick; check(16'hFC00, "TC11 L #10");
    tick; check(16'hF800, "TC11 L #11"); tick; check(16'hF000, "TC11 L #12");
    tick; check(16'hE000, "TC11 L #13"); tick; check(16'hC000, "TC11 L #14");
    tick; check(16'h8000, "TC11 L #15"); tick; check(16'h0000, "TC11 L #16");

    // TC12: reset in the middle of a shift, and reset is synchronous (no change before the edge)
    load = 1; A = 16'hBEEF; left_right = 0; Din = 0;                    tick; check(16'hBEEF, "TC12 load");
    load = 0;
    tick; check(16'h5F77, "TC12 R #1");  tick; check(16'h2FBB, "TC12 R #2");  tick; check(16'h17DD, "TC12 R #3");
    rst = 1; #3;  checks = checks + 1;                                 // still before the next rising edge
    if (shift_reg_out !== 16'h17DD) begin errors = errors + 1; $display("FAIL  TC12 async-reset  reg=%h", shift_reg_out); end
    tick; check(16'h0000, "TC12 rst mid-shift");
    rst = 0;

    $display("--------------------------------------------------");
    $display("12 test cases | %0d checks | %0d errors", checks, errors);
    if (errors == 0) $display("RESULT: PASS"); else $display("RESULT: FAIL");
    $finish;
  end
endmodule
