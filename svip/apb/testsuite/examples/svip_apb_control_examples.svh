// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Independent response fixture owns PREADY; requester controls remain unchanged.
class svip_apb_backpressure_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_backpressure_test)
  function new(string name,uvm_component parent);super.new(name,parent);endfunction
  task stalled(svip_apb_data_t expected,int cycles);
    svip_apb_strb_t expected_strb=0;
    if(cfg.apb4)for(int lane=0;lane<cfg.data_width/8;lane++)expected_strb[lane]=1;
    do @(vif.mon_cb);while(vif.mon_cb.psel!==1 || vif.mon_cb.penable!==1);
    for(int i=0;i<cycles;i++)begin
      if(vif.mon_cb.pready!==0 || vif.mon_cb.psel!==1 || vif.mon_cb.penable!==1 ||
         vif.mon_cb.paddr!=='h80 || vif.mon_cb.pwrite!==1 || vif.mon_cb.pwdata!==expected ||
         vif.mon_cb.pprot!==0 || vif.mon_cb.pstrb!==expected_strb)
        `uvm_fatal("TEST_BACKPRESSURE","selected write changed while response was withheld")
      #1ps;
      if(ctrl.bus_completions!=1 || terminal.items.size()!=1)
        `uvm_fatal("TEST_BACKPRESSURE","request completed before PREADY was released")
      if(i+1<cycles)@(vif.mon_cb);
    end
  endtask
  task run_case();
    svip_apb_txn t=cfg.create_txn("blocked_write");
    svip_apb_data_t next_data=data_pattern('h2468ace0);
    bit abort_write=(case_name=="backpressure_reset_write");
    checked_write('h80,'h13579bdf);
    t.write=1;t.addr='h80;t.data=next_data;t.strb='1;
    ctrl.manual_response=1;ctrl.manual_ready=0;ctrl.manual_error=0;
    fork
      submit(t);
      begin
        stalled(next_data,16);
        if(abort_write)begin
          @(negedge ctrl.clk);ctrl.resetn=0;
          #1ps;
          if(vif.psel!==0 || vif.penable!==0) `uvm_fatal("TEST_BACKPRESSURE","reset did not idle pins")
          @(negedge ctrl.clk);ctrl.resetn=1;
        end else ctrl.manual_ready=1;
      end
    join
    if(t.status!==(abort_write?SVIP_APB_RESET_ABORTED:SVIP_APB_OK) || t.wait_cycles!=16)
      `uvm_fatal("TEST_BACKPRESSURE","held request lost its result or exact wait count")
    ctrl.manual_response=0;ctrl.manual_ready=1;
    if(!abort_write)for(int lane=0;lane<cfg.data_width/8;lane++)gold['h80+lane]=next_data[lane*8+:8];
    // This fixture commits memory on the actual bus handshake, never on a stall.
    checked_read('h80);
    if(ctrl.bus_completions!=(abort_write?2:3) || observed.items.size()!=(abort_write?2:3) || terminal.items.size()!=3)
      `uvm_fatal("TEST_BACKPRESSURE","false completion or lost recovery")
  endtask
endclass

// The convenience sequence expresses an exact, reproducible address/data list.
class svip_apb_directed_pattern_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_directed_pattern_test)
  function new(string name,uvm_component parent);super.new(name,parent);endfunction
  task run_case();
    svip_apb_rw_seq seq=svip_apb_rw_seq::type_id::create("directed");
    svip_apb_data_t words[6]='{'0,'1,32'haa55aa55,32'h55aa55aa,32'h01234567,32'h89abcdef};
    svip_apb_addr_t addresses[6]='{'h40,'h44,'h48,'h4c,'h50,'h54};
    seq.cfg=cfg;
    foreach(words[i])begin
      svip_apb_data_t expected=data_pattern(words[i]);
      logic [2:0] protection=cfg.apb4?3'(i):3'b000;
      seq.addr=addresses[i];seq.write=1;seq.data=expected;seq.strb='1;seq.prot=protection;
      sent++;seq.start(agent.sqr);#1ps;
      if(seq.result.status!==SVIP_APB_OK || observed.items[$].addr!==addresses[i] ||
         observed.items[$].data!==expected || observed.items[$].prot!==protection)
        `uvm_fatal("TEST_DIRECTED_PATTERN","write pins did not match the requested literal/protection")
      seq.write=0;sent++;seq.start(agent.sqr);#1ps;
      if(seq.result.status!==SVIP_APB_OK || seq.data!==expected ||
         observed.items[$].data!==expected || observed.items[$].prot!==protection)
        `uvm_fatal("TEST_DIRECTED_PATTERN","readback or read protection differed from the literal")
    end
    if(ctrl.bus_completions!=12 || observed.items.size()!=12)
      `uvm_fatal("TEST_DIRECTED_PATTERN","a directed transfer was lost or duplicated")
  endtask
endclass

// Fixed bits and random bits coexist: low-byte high nibble A, low nibble random.
class svip_apb_constrained_pattern_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_constrained_pattern_test)
  function new(string name,uvm_component parent);super.new(name,parent);endfunction
  task run_case();
    bit [15:0] low_values=0;
    svip_apb_addr_t first_address;
    bit varied_address=0;
    svip_apb_strb_t full_strb=0;
    logic [2:0] protection=cfg.apb4?3'b101:3'b000;
    for(int lane=0;lane<cfg.data_width/8;lane++)full_strb[lane]=1;
    for(int i=0;i<40;i++)begin
      svip_apb_txn t=cfg.create_txn("constrained_pattern");
      svip_apb_addr_t address;
      svip_apb_data_t expected;
      if(!t.randomize() with {write==1;addr inside {['h40:'h7f]};data[7:4]==4'ha;
                             strb==local::full_strb;prot==local::protection;})
        `uvm_fatal("TEST_CONSTRAINED_PATTERN","randomize failed")
      address=t.addr;expected=t.data;
      if(i==0)first_address=address;else if(address!=first_address)varied_address=1;
      submit(t);
      if(t.status!==SVIP_APB_OK || observed.items[$].addr!==address ||
         observed.items[$].data!==expected || observed.items[$].data[7:4]!==4'ha ||
         observed.items[$].prot!==protection || observed.items[$].strb!==full_strb)
        `uvm_fatal("TEST_CONSTRAINED_PATTERN","actual pattern did not satisfy the requested constraints")
      low_values[observed.items[$].data[3:0]]=1;
      for(int lane=0;lane<cfg.data_width/8;lane++)gold[longint'(address)+lane]=expected[lane*8+:8];
      checked_read(address,protection);
    end
    if($countones(low_values)<2 || !varied_address || ctrl.bus_completions!=80)
      `uvm_fatal("TEST_CONSTRAINED_PATTERN","sent traffic did not vary or lost a transfer")
  endtask
endclass

class svip_apb_byte_lane_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_byte_lane_test)
  function new(string name,uvm_component parent);super.new(name,parent);endfunction
  task run_case();
    svip_apb_rw_seq seq=svip_apb_rw_seq::type_id::create("byte_lane");
    checked_write('h80,0);
    seq.cfg=cfg;seq.addr='h80;seq.write=1;seq.prot=3'b101;
    for(int lane=0;lane<cfg.data_width/8;lane++)begin
      bit [7:0] literal=8'('h5a+lane*'h11);
      svip_apb_data_t expected=0;
      svip_apb_strb_t strobe=0;
      expected[lane*8+:8]=literal;strobe[lane]=1;
      seq.data=expected;seq.strb=strobe;sent++;seq.start(agent.sqr);#1ps;
      if(seq.result.status!==SVIP_APB_OK || observed.items[$].data!==expected ||
         observed.items[$].strb!==strobe || observed.items[$].prot!==3'b101)
        `uvm_fatal("TEST_BYTE_LANE","byte data was not placed in the selected lane")
      gold['h80+lane]=literal;checked_read('h80);
    end
    // Zero strobe is a legal completed transfer with no byte update in this fixture.
    seq.data=data_pattern('1);seq.strb=0;sent++;seq.start(agent.sqr);#1ps;
    if(seq.result.status!==SVIP_APB_OK || observed.items[$].strb!==0)
      `uvm_fatal("TEST_BYTE_LANE","zero-strobe transfer did not complete")
    checked_read('h80);
  endtask
endclass
