// SPDX-License-Identifier: Apache-2.0
// Recipe: write AA/55 data with alternating byte enables; untouched bytes stay initialized.
class svip_axi_patterns_recipe_seq extends svip_axi_generation_seq;
  `uvm_object_utils(svip_axi_patterns_recipe_seq)
  function new(string name="svip_axi_patterns_recipe_seq"); super.new(name); endfunction
  virtual task body();
    svip_axi_addr_t address=64'h1234567800001000;
    byte unsigned old_bytes[svip_axi_addr_t];
    svip_axi_txn t,r;
    svip_axi_generation_goal_t goal;
    svip_axi_strb_e modes[3]='{SVIP_AXI_STRB_FULL,SVIP_AXI_STRB_RANDOM,SVIP_AXI_STRB_MIXED};
    int bytes=p_sequencer.cfg.data_bytes;
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    write_check(address,1,$clog2(bytes));
    old_bytes=oracle; t=request(0,address,1,$clog2(bytes)); oracle=old_bytes;
    for(int lane=0;lane<bytes;lane++) begin
      t.data[0][lane*8+:8]=lane%2 ? 8'h55 : 8'haa;
      t.strb[0][lane]=(lane%2)==0;
      if((lane%2)==0) oracle[address+lane]=8'haa;
    end
    completed(t,r); read_check(address,1,$clog2(bytes));
    // Public helper modes: initialize untouched bytes, send the filled object, check readback.
    foreach(modes[m]) begin
      goal=make_goal(SVIP_AXI_WR,address+'h1000,2,$clog2(bytes),SVIP_AXI_INCR,'h710+m);
      write_check(goal.addr,goal.beats,goal.size,goal.burst,91);
      t=randomized_request(goal);
      t.fill_wdata(modes[m]);
      send_generated(t,goal,modes[m]);
    end
  endtask
endclass
class svip_axi_patterns_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_patterns_example)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function svip_axi_contract_seq create_sequence();
    return svip_axi_patterns_recipe_seq::type_id::create("patterns_recipe");
  endfunction
endclass
