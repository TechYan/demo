// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Only common + clock are compiled. No reset/signal/coordinator package.
module svip_clock_example;
  timeunit 1ps; timeprecision 1ps;
  import svip_control_common_pkg::*;
  import svip_clock_pkg::*;
  wire clk;
  svip_control_pin_if pin(clk,clk);
  assign clk=pin.drive_value;
  initial begin
    svip_control_registry resources;
    svip_control_sv_binding#(1) binding;
    svip_control_endpoint endpoint;
    svip_clock_controller clock;
    svip_control_result r;
    svip_control_tick_t accepted,first,edges;
    string reason;
    #1;resources=new;binding=new(pin);
    if(!resources.register_pin("clock",binding,"dut.clk",0,"tb",0,SVIP_CONTROL_CLOCK,
      SVIP_CONTROL_DIRECT_PIN,endpoint,reason))$fatal(1,"%s",reason);
    clock=new(endpoint,20,30);
    fork clock.run();clock.monitor();join_none
    accepted=svip_control_now();clock.start(accepted+500,r);
    if(r.status!=SVIP_CONTROL_COMPLETED)$fatal(1,"start");
    clock.wait_edges(1,svip_control_now()+500,r);first=binding.last_rise();
    if(r.status!=SVIP_CONTROL_COMPLETED || first-accepted!=30)$fatal(1,"full first low");
    #3;clock.stop_low(svip_control_now()+500,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || clk!==0 || binding.last_fall()-first!=20)$fatal(1,"complete high/stop low");
    edges=binding.rises();#47;
    if(binding.rises()!=edges)$fatal(1,"unexpected stopped edge");
    accepted=svip_control_now();clock.start(accepted+500,r);
    clock.wait_edges(1,svip_control_now()+500,r);
    if(binding.last_rise()-accepted!=30)$fatal(1,"restart full low");
    clock.set_period_at_boundary(12,18,svip_control_now()+500,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || clock.period()!=30)$fatal(1,"boundary timing");
    clock.wait_edges(1,svip_control_now()+500,r);
    if(binding.last_rise()-clock.boundary_edge()!=30)$fatal(1,"actual new period");
    clock.stop_low(svip_control_now()+500,r);
    if(r.status!=SVIP_CONTROL_COMPLETED || clock.unexpected_edges!=0)$fatal(1,"final stop");
    $display("SVIP_COMPONENT_PASS component=clock");$finish;
  end
  initial begin #2000;$fatal(1,"clock example deadline");end
endmodule
