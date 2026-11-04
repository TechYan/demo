// SPDX-License-Identifier: Apache-2.0
// Recipe: force only a READY channel owned by that agent; always release explicit controls.
class svip_axi_controls_recipe_seq extends svip_axi_contract_seq;
  `uvm_object_utils(svip_axi_controls_recipe_seq)
  function new(string name="svip_axi_controls_recipe_seq"); super.new(name); endfunction
  virtual task body();
    svip_axi_txn t;
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    write_check('h1000,4);
    sub.force_ready(SVIP_AXI_AR,1,0);
    t=request(1,'h1000,4); send(t); repeat(8) @(negedge ctrl.clk);
    if(mgr.cfg.vif.arvalid!==1 || mgr.cfg.vif.arready!==0) `uvm_error("CONTROL_AR","AR READY override did not stall")
    sub.force_ready(SVIP_AXI_AR,0,0); wait_all();
    sub.hold_responses(1,1); // Pauses new responses, not an already presented VALID.
    t=request(0,'h1100,4); send(t); t=request(1,'h1000,4); send(t);
    repeat(20) @(negedge ctrl.clk);
    if(mgr.cfg.vif.bvalid!==0 || mgr.cfg.vif.rvalid!==0) `uvm_error("CONTROL_HOLD","hold started a response")
    sub.hold_responses(0,0); wait_all();
    read_check('h1100,4);
  endtask
endclass
class svip_axi_controls_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_controls_example)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function svip_axi_contract_seq create_sequence(); return svip_axi_controls_recipe_seq::type_id::create("controls_recipe"); endfunction
endclass
