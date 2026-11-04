// SPDX-License-Identifier: Apache-2.0
// Author: syan
// A selected pair shares ownership/backend once; reset/coordinator are absent.
module svip_clock_signal_example;
  timeunit 1ps;timeprecision 1ps;
  import svip_control_common_pkg::*;
  import svip_clock_pkg::*;
  import svip_signal_pkg::*;
  wire clk;
  wire [31:0] cfg;
  logic [31:0] received=0;
  svip_control_pin_if clock_pin(clk,clk);
  svip_control_pin_if#(32) data_pin(cfg,clk);
  assign clk=clock_pin.drive_value;assign cfg=data_pin.drive_value;
  always @(posedge clk)received<=cfg;
  initial begin
    svip_control_registry resources;
    svip_control_sv_binding#(1) clock_binding;
    svip_control_sv_binding#(32) data_binding;
    svip_control_endpoint clock_endpoint,data_endpoint;
    svip_clock_controller clock;
    svip_signal_controller signal_bank;
    svip_control_when when_at;
    svip_control_result r;
    string reason;
    #1;resources=new;clock_binding=new(clock_pin);data_binding=new(data_pin);
    if(!resources.register_pin("clock",clock_binding,"clk",0,"tb",0,SVIP_CONTROL_CLOCK,SVIP_CONTROL_DIRECT_PIN,clock_endpoint,reason))$fatal(1,"%s",reason);
    if(!resources.register_pin("data",data_binding,"cfg",0,"tb",0,SVIP_CONTROL_SIGNAL,SVIP_CONTROL_DIRECT_PIN,data_endpoint,reason))$fatal(1,"%s",reason);
    clock=new(clock_endpoint,20,30);signal_bank=new(data_endpoint,clock);
    fork clock.run();clock.monitor();join_none
    clock.start(svip_control_now()+500,r);
    when_at=new(SVIP_CONTROL_BEFORE_CAPTURE,clock.next_rise_tick());when_at.setup_ticks=3;
    signal_bank.set(32'h80402001,svip_control_mask(32),when_at,svip_control_now()+500,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || received!==32'h80402001)$fatal(1,"pair capture");
    clock.stop_low(svip_control_now()+500,r);
    if(r.status!=SVIP_CONTROL_COMPLETED)$fatal(1,"pair stop");
    $display("SVIP_COMPONENT_PASS component=clock_signal");$finish;
  end
  initial begin #2000;$fatal(1,"pair example deadline");end
endmodule
