interface ctrl_if;
  logic valid;
  modport master(output valid);
  modport slave(input valid);
endinterface

module chip_top #(
  parameter int DATA_W = 16
) (
  input  logic                  clk,
  input  logic                  rst_n,
  input  logic [DATA_W-1:0]     rx_data,
  output logic [DATA_W-1:0]     tx_data,
  output logic [3:0]            status,
  inout  wire                   pad,
  ctrl_if.master                ctrl,
  input  logic [7:0]            lanes [2],
  input  logic                  legacy_mode
);
endmodule
