interface ctrl_if;
  logic valid;
  modport master(output valid);
  modport slave(input valid);
endinterface

module chip_top #(
  parameter int DATA_W = 32
) (
  input  logic                  rst_n,
  input  logic                  clk,
  input  logic [DATA_W-1:0]     rx_data,
  output logic [DATA_W-1:0]     tx_data,
  input  logic [3:0]            status,
  ctrl_if.slave                 ctrl,
  inout  wire                   pad,
  input  logic [7:0]            lanes [4],
  output logic                  link_up
);
endmodule
