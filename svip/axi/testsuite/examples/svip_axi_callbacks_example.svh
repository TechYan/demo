// SPDX-License-Identifier: Apache-2.0
// Recipe: hooks are nonblocking functions; request fields change on the private snapshot.
class svip_axi_recipe_callbacks extends svip_axi_callbacks;
  function new(string name="svip_axi_recipe_callbacks"); super.new(name); endfunction
  virtual function void request(svip_axi_txn req); req.region=4'hc; endfunction
  virtual function void write_response(svip_axi_txn req); req.buser=svip_axi_user_t'('h1_01234567_89abcdef); endfunction
  virtual function void read_response(svip_axi_txn req,ref bit [1:0] rresp[],ref svip_axi_user_t ruser[]);
    foreach(ruser[i]) ruser[i]=svip_axi_user_t'('h2_fedcba98_76543210) ^ i;
  endfunction
endclass
class svip_axi_callbacks_recipe_seq extends svip_axi_contract_seq;
  `uvm_object_utils(svip_axi_callbacks_recipe_seq)
  function new(string name="svip_axi_callbacks_recipe_seq"); super.new(name); endfunction
  virtual task body();
    svip_axi_txn t,r;
    wait(ctrl.resetn===1); repeat(5) @(negedge ctrl.clk);
    t=request(0,'h1000,4); completed(t,r);
    if(r.buser!=svip_axi_user_t'('h1_01234567_89abcdef)) `uvm_error("RECIPE_CALLBACK","write response hook effect missing")
    t=request(1,'h1000,4); completed(t,r);
    foreach(r.ruser[i]) if(r.ruser[i]!=(svip_axi_user_t'('h2_fedcba98_76543210)^i)) `uvm_error("RECIPE_CALLBACK","read response hook effect missing")
  endtask
endclass
class svip_axi_callbacks_example extends svip_axi_test;
  `uvm_component_utils(svip_axi_callbacks_example)
  svip_axi_recipe_callbacks hooks;
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase); hooks=new("hooks");
    mgr.add_callback(hooks); sub.add_callback(hooks);
  endfunction
  virtual function svip_axi_contract_seq create_sequence(); return svip_axi_callbacks_recipe_seq::type_id::create("callbacks_recipe"); endfunction
endclass
