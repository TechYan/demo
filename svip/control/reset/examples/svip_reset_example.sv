// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Project-owned HDL clock; no clock generator UVC or signal package is needed.
module svip_reset_example;
  timeunit 1ps; timeprecision 1ps;
  import svip_control_common_pkg::*;
  import svip_reset_pkg::*;
  bit clk=0;
  always #25 clk=~clk;
  wire rst_n;
  logic received=1;
  svip_control_pin_if#(1,1'b1) pin(rst_n,clk);
  svip_control_pin_if clock_pin(clk,clk);
  assign rst_n=pin.drive_value;
  always @(posedge clk or negedge rst_n)if(!rst_n)received<=0;else received<=1;

  class project_clock_ref extends svip_control_clock_ref;
    function new(svip_control_endpoint endpoint);super.new(endpoint);endfunction
    virtual function bit is_running();return 1;endfunction
    // This reset example only uses actual edge IDs, not period prediction.
    virtual function bit predicts_rise(svip_control_tick_t at_tick);return 0;endfunction
  endclass
  initial begin
    svip_control_registry resources;
    svip_control_sv_binding#(1,1'b1) binding;
    svip_control_sv_binding#(1) clock_binding;
    svip_control_endpoint endpoint,clock_endpoint;
    svip_reset_controller reset;
    project_clock_ref reference_clock;
    svip_control_result r,old_release;
    svip_control_tick_t epoch;
    string reason;bit ok;
    #1;resources=new;binding=new(pin);clock_binding=new(clock_pin,"",0);
    if(!resources.register_pin("reset",binding,"dut.rst_n",0,"tb",0,SVIP_CONTROL_RESET,
      SVIP_CONTROL_DIRECT_PIN,endpoint,reason))$fatal(1,"%s",reason);
    if(!resources.register_pin("external_clock",clock_binding,"dut.clk",0,"project",1,SVIP_CONTROL_CLOCK,
      SVIP_CONTROL_DIRECT_PIN,clock_endpoint,reason))$fatal(1,"%s",reason);
    reset=new(endpoint,1);reference_clock=new(clock_endpoint);
    fork reset.monitor();join_none
    reset.set_source("software",1,svip_control_now()+300,r);epoch=reset.watch.epoch();
    if(r.status!=SVIP_CONTROL_COMPLETED || rst_n!==0 || received!==0 || epoch!=1)$fatal(1,"actual async reset");
    reset.set_source("software",1,svip_control_now()+300,r);
    if(reset.watch.epoch()!=epoch)$fatal(1,"repeated assertion epoch");
    reset.set_source("watchdog",1,svip_control_now()+300,r);
    reset.set_source("software",0,svip_control_now()+300,r);
    if(rst_n!==0)$fatal(1,"other source lost");
    reset.set_source("watchdog",0,svip_control_now()+300,r);
    if(rst_n!==1)$fatal(1,"physical release");
    reset.source_after_edge("scheduled",1,reference_clock,clock_binding.rises()+1,svip_control_now()+300,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || r.applied_tick!=clock_binding.last_rise() || received!==0)$fatal(1,"external-clock assertion");
    reset.source_after_edge("scheduled",0,reference_clock,clock_binding.rises()+1,svip_control_now()+300,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || rst_n!==1 || received!==0)$fatal(1,"release is not receiver ready");
    clock_binding.wait_rises(clock_binding.rises()+1,svip_control_now()+300,ok);#1;
    if(!ok || received!==1)$fatal(1,"receiver did not recover");
    fork
      reset.source_at("software",0,svip_control_now()+20,svip_control_now()+300,old_release);
      begin #3;reset.set_source("software",1,svip_control_now()+300,r);end
    join
    if(old_release.status!=SVIP_CONTROL_CANCELLED || rst_n!==0)$fatal(1,"stale source release");
    $display("SVIP_COMPONENT_PASS component=reset");$finish;
  end
  initial begin #2000;$fatal(1,"reset example deadline");end
endmodule
