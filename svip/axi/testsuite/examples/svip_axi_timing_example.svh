// SPDX-License-Identifier: Apache-2.0
// Recipe: timing policies are runtime objects; no driver subclass or pin force is needed.
class svip_axi_timing_recipe_seq extends svip_axi_contract_seq;
  `uvm_object_utils(svip_axi_timing_recipe_seq)
  function new(string name="svip_axi_timing_recipe_seq"); super.new(name); endfunction
  virtual task body();
    longint unsigned predecessor;
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    mgr.cfg.timing.apply(SVIP_AXI_TIMING_ZERO);
    mgr.cfg.timing.aw_valid.set_fixed(1);
    mgr.cfg.timing.w_valid.set_range(0,2);
    sub.cfg.timing.aw_ready.set_bursty(0,1,100,3,3);
    sub.cfg.timing.b_lat.set_fixed(3);
    sub.cfg.timing.r_lat.set_fixed(1);
    sub.cfg.timing.r_beat.set_fixed(2);
    write_check('h1000,4);
    predecessor=ctrl.last_aw_cycle>ctrl.last_wlast_cycle ? ctrl.last_aw_cycle : ctrl.last_wlast_cycle;
    if(ctrl.last_b_cycle-predecessor!=4) `uvm_error("TIMING_RECIPE_B","fixed B latency3 must handshake4 physical cycles later")
    read_check('h1000);
    if(ctrl.last_r_cycle-ctrl.last_ar_cycle!=2) `uvm_error("TIMING_RECIPE_R","fixed R latency1 must handshake2 physical cycles later")
    read_check('h1000,4);
    // Restore a simple profile before this sequence yields the shared timing objects.
    mgr.cfg.timing.apply(SVIP_AXI_TIMING_ZERO); sub.cfg.timing.apply(SVIP_AXI_TIMING_ZERO);
  endtask
endclass
class svip_axi_timing_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_timing_example)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function svip_axi_contract_seq create_sequence(); return svip_axi_timing_recipe_seq::type_id::create("timing_recipe"); endfunction
endclass
