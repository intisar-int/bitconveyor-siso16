module siso_16 (
  input  wire        clk,rst,load,
  input  wire		 left_right,Din,           
  input  wire [15:0] A,
  output wire        Dout,
   output wire [15:0] shift_reg_out      
);

  reg [15:0] shift_reg;

  always @(posedge clk) 
  begin
    if (rst)
      shift_reg <= 16'b0;
    else if (load)
      shift_reg <= A;
    else if (left_right)
      shift_reg <= {shift_reg[14:0], Din};
    else
      shift_reg <= {Din, shift_reg[15:1]};
  end

  assign Dout = left_right ? shift_reg[15] : shift_reg[0];
  assign shift_reg_out = shift_reg;

endmodule 