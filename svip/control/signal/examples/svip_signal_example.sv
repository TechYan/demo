// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Existing HDL clock plus a narrow reference: no clock/reset UVC is compiled.
module svip_signal_example;
  timeunit 1ps; timeprecision 1ps;
  import svip_control_common_pkg::*;
  import svip_signal_pkg::*;
  bit clk=0;
  always #25 clk=~clk;
  wire [64:0] cfg;
  logic [64:0] received='0;
  svip_control_pin_if#(65) pin(cfg,clk);
  svip_control_pin_if clock_pin(clk,clk);
  assign cfg=pin.drive_value;
  always @(posedge clk)received<=cfg;
  class project_clock_ref extends svip_control_clock_ref;
    function new(svip_control_endpoint endpoint);super.new(endpoint);endfunction
    virtual function bit is_running();return 1;endfunction
    virtual function bit predicts_rise(svip_control_tick_t at_tick);
      return at_tick>=25 && (at_tick-25)%50==0;
    endfunction
  endclass
  initial begin
    svip_control_registry resources;
    svip_control_sv_binding#(65) binding;
    svip_control_sv_binding#(1) clock_binding;
    svip_control_endpoint endpoint,clock_endpoint;
    svip_signal_controller signal_bank;
    project_clock_ref reference_clock;
    svip_control_when when_at;
    svip_control_result r;
    string reason;
    #1;resources=new;binding=new(pin);clock_binding=new(clock_pin,"",0);
    if(!resources.register_pin("cfg",binding,"dut.cfg",0,"tb",0,SVIP_CONTROL_SIGNAL,
      SVIP_CONTROL_DIRECT_PIN,endpoint,reason))$fatal(1,"%s",reason);
    if(!resources.register_pin("external_clock",clock_binding,"dut.clk",0,"project",1,SVIP_CONTROL_CLOCK,
      SVIP_CONTROL_DIRECT_PIN,clock_endpoint,reason))$fatal(1,"%s",reason);
    reference_clock=new(clock_endpoint);signal_bank=new(endpoint,reference_clock);
    when_at=new(SVIP_CONTROL_ASYNC_AT,svip_control_now()+3);
    signal_bank.set(65'h10000000000000001,svip_control_mask(65),when_at,svip_control_now()+300,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || r.actual!==65'h10000000000000001)$fatal(1,"65-bit actual data");
    when_at=new(SVIP_CONTROL_BEFORE_CAPTURE,75);when_at.setup_ticks=3;
    signal_bank.set(65'h10000000000000008,svip_control_mask(65),when_at,svip_control_now()+300,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || r.applied_tick!=72 || r.observed_tick!=75 || received!==65'h10000000000000008)$fatal(1,"external-clock capture");
    when_at=new(SVIP_CONTROL_AFTER_SOURCE_EDGE,0,clock_binding.rises()+1);
    signal_bank.set('h55,'hff,when_at,svip_control_now()+300,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || r.applied_tick!=clock_binding.last_rise() ||
      cfg!==65'h10000000000000055 || received!==65'h10000000000000008)$fatal(1,"masked after-edge old/new views");
    signal_bank.expect_value(65'h10000000000000055,svip_control_mask(65),svip_control_now()+100,r);
    if(r.status!=SVIP_CONTROL_COMPLETED)$fatal(1,"actual observation");
    $display("SVIP_COMPONENT_PASS component=signal");$finish;
  end
  initial begin #2000;$fatal(1,"signal example deadline");end
endmodule
