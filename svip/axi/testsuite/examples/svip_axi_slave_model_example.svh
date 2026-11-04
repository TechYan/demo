// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Recipe: a sequence chooses when the subordinate processes and replies to requests.
class svip_axi_slave_model_recipe_seq extends svip_axi_contract_seq;
  `uvm_object_utils(svip_axi_slave_model_recipe_seq)
  function new(string name="svip_axi_slave_model_recipe_seq"); super.new(name); endfunction
  virtual task body();
    int size,reply_count;
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    size=p_sequencer.cfg.max_size()<3 ? p_sequencer.cfg.max_size() : 3;
    if(sub.cfg.memory_mode!=SVIP_AXI_MEMORY || sub.cfg.mem==null)
      `uvm_fatal("SLAVE_RECIPE_MEMORY","default internal memory was not installed")
    fork
      begin
        svip_axi_txn t,r;
        t=request(0,'h1000,2,size,SVIP_AXI_INCR,1,37); completed(t,r);
        if(r.buser!=svip_axi_user_t'('h31)) `uvm_error("SLAVE_RECIPE_BUSER","sequence-selected BUSER was lost")
        t=request(1,'h1000,2,size,SVIP_AXI_INCR,1); completed(t,r);
        if(r.rresp.size()!=2 || r.ruser.size()!=2) `uvm_fatal("SLAVE_RECIPE_READ","read response omitted beats")
        foreach(r.rresp[i])
          if(r.rresp[i]!=SVIP_AXI_OKAY || r.ruser[i]!=svip_axi_user_t'('h51+i))
            `uvm_error("SLAVE_RECIPE_RUSER","sequence-selected read status/USER was lost")
      end
      begin
        svip_axi_txn req,rsp;
        repeat(2) begin
          sub.get_request(req);
          repeat(3) @(negedge ctrl.clk);
          // This explicit call commits a write or snapshots a read exactly once.
          rsp=sub.default_response(req);
          if(rsp==null) `uvm_fatal("SLAVE_RECIPE_DEFAULT","default processing rejected a live request")
          if(req.dir==SVIP_AXI_WR) rsp.buser=svip_axi_user_t'('h31);
          else foreach(rsp.ruser[i]) rsp.ruser[i]=svip_axi_user_t'('h51+i);
          if(!sub.send_response(req,rsp)) `uvm_fatal("SLAVE_RECIPE_SEND","live response was rejected")
          reply_count++;
        end
      end
    join
    wait_all(); repeat(8) @(negedge ctrl.clk);
    if(n_sent!=2 || n_done!=2 || reply_count!=2)
      `uvm_error("SLAVE_RECIPE_COMPLETIONS","manager and responder did not complete exactly two requests")
  endtask
endclass

class svip_axi_slave_model_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_slave_model_example)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  virtual function void configure_test(); sc.sub_response_mode=SVIP_AXI_SUB_USER; endfunction
  virtual function svip_axi_contract_seq create_sequence(); return svip_axi_slave_model_recipe_seq::type_id::create("slave_model_recipe"); endfunction
endclass
