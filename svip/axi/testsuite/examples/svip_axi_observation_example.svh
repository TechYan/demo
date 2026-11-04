// SPDX-License-Identifier: Apache-2.0
// Recipe: analysis subscribers observe; they never participate in bus scheduling.
class svip_axi_recipe_listener extends uvm_subscriber #(svip_axi_txn);
  `uvm_component_utils(svip_axi_recipe_listener)
  int seen;
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function void write(svip_axi_txn item);
    seen++; `uvm_info("OBSERVED_TRANSACTION",item.convert2string(),UVM_LOW)
  endfunction
endclass
class svip_axi_observation_recipe_seq extends svip_axi_contract_seq;
  `uvm_object_utils(svip_axi_observation_recipe_seq)
  function new(string name="svip_axi_observation_recipe_seq"); super.new(name); endfunction
  virtual task body();
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    write_check('h1000,4); read_check('h1000,4); repeat(5) @(negedge ctrl.clk);
  endtask
endclass
class svip_axi_observation_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_observation_example)
  svip_axi_recipe_listener listener;
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function void configure_test();
    listener=svip_axi_recipe_listener::type_id::create("listener",this);
    mc.tracker_mode=SVIP_AXI_TRACKER_CHANNEL; mc.tracker_filename="example_mgr.tracker.log";
    sc.tracker_mode=SVIP_AXI_TRACKER_TXN; sc.tracker_filename="example_sub.tracker.log";
  endfunction
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase); mgr.ap.connect(listener.analysis_export);
  endfunction
  function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    if(listener.seen!=2) `uvm_error("OBSERVATION_RECIPE","expected one complete write and one complete read")
  endfunction
  virtual function svip_axi_contract_seq create_sequence(); return svip_axi_observation_recipe_seq::type_id::create("observation_recipe"); endfunction
endclass
