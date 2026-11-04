// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Standalone customer-style integration: core filelist, no APB dependency.
module svip_control_quickstart;
  timeunit 1ps;timeprecision 1ps;
  import svip_control_pkg::*;
  wire clk,rst_n;
  wire [31:0] cfg;
  logic [31:0] received='0;
  svip_control_pin_if clock_pin(clk,clk);
  svip_control_pin_if#(1,1'b1) reset_pin(rst_n,clk);
  svip_control_pin_if#(32) cfg_pin(cfg,clk);
  assign clk=clock_pin.drive_value;
  assign rst_n=reset_pin.drive_value;
  assign cfg=cfg_pin.drive_value;
  always @(posedge clk or negedge rst_n)if(!rst_n)received<=0;else received<=cfg;
  initial begin
    svip_control_registry resources;
    svip_control_sv_binding#(1) clock_binding;
    svip_control_sv_binding#(1,1'b1) reset_binding;
    svip_control_sv_binding#(32) cfg_binding;
    svip_control_endpoint clock_ep,reset_ep,cfg_ep;
    svip_clock_controller clock;
    svip_reset_controller reset;
    svip_signal_controller signal_bank;
    svip_control_when before_capture;
    svip_control_result result;
    string reason;
    #1; // All physical startup pins are known before model initialization.
    resources=new;
    clock_binding=new(clock_pin);reset_binding=new(reset_pin);cfg_binding=new(cfg_pin);
    if(!resources.register_pin("core_clock",clock_binding,"dut.clk",0,"tb",0,
      SVIP_CONTROL_CLOCK,SVIP_CONTROL_DIRECT_PIN,clock_ep,reason))$fatal(1,"%s",reason);
    if(!resources.register_pin("core_reset",reset_binding,"dut.rst_n",0,"tb",0,
      SVIP_CONTROL_RESET,SVIP_CONTROL_DIRECT_PIN,reset_ep,reason))$fatal(1,"%s",reason);
    if(!resources.register_pin("cfg",cfg_binding,"dut.cfg",0,"tb",0,
      SVIP_CONTROL_SIGNAL,SVIP_CONTROL_DIRECT_PIN,cfg_ep,reason))$fatal(1,"%s",reason);
    clock=new(clock_ep,2000,3000);reset=new(reset_ep,1);
    reset.attach(cfg_ep);signal_bank=new(cfg_ep,clock);
    fork clock.run();clock.monitor();reset.monitor();join_none
    clock.start($time+20000,result);
    if(result.status!=SVIP_CONTROL_COMPLETED)$fatal(1,"start: %s",result.reason);
    before_capture=new(SVIP_CONTROL_BEFORE_CAPTURE,clock.next_rise_tick());
    before_capture.setup_ticks=100;
    signal_bank.set(32'h80402001,svip_control_mask(32),before_capture,$time+20000,result);
    if(result.status!=SVIP_CONTROL_COMPLETED || received!==32'h80402001)$fatal(1,"actual capture failed");
    clock.stop_low($time+20000,result);
    if(result.status!=SVIP_CONTROL_COMPLETED || clk!==0)$fatal(1,"stop failed");
    $display("SVIP_CONTROL_QUICKSTART_PASS received=%h",received);$finish;
  end
  initial begin #100000;$fatal(1,"quickstart deadline");end
endmodule
