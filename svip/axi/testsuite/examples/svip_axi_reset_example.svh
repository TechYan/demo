// SPDX-License-Identifier: Apache-2.0
// Recipe: reset outstanding traffic without calling the driver's software flush.
class svip_axi_reset_recipe_seq extends svip_axi_contract_seq;
  `uvm_object_utils(svip_axi_reset_recipe_seq)
  function new(string name="svip_axi_reset_recipe_seq"); super.new(name); endfunction
  virtual task body();
    svip_axi_txn t;
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    write_check('h1000,4);
    mgr.force_ready(SVIP_AXI_B,1,0); mgr.force_ready(SVIP_AXI_R,1,0);
    repeat(3) @(negedge ctrl.clk);
    t=request(0,'h1000,4); expect_abort[t.get_transaction_id()]=1; send(t);
    t=request(1,'h1000,4); expect_abort[t.get_transaction_id()]=1; send(t);
    wait(mgr.cfg.vif.bvalid===1 && mgr.cfg.vif.rvalid===1);
    ctrl.pulse_reset(); wait_all();
    mgr.force_ready(SVIP_AXI_B,0,0); mgr.force_ready(SVIP_AXI_R,0,0);
    read_check('h1000,4); write_check('h1200,4); read_check('h1200,4);
  endtask
endclass
class svip_axi_reset_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_reset_example)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function svip_axi_contract_seq create_sequence();
    return svip_axi_reset_recipe_seq::type_id::create("reset_recipe");
  endfunction
endclass
