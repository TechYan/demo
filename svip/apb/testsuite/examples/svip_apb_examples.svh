// SPDX-License-Identifier: Apache-2.0
// Author: syan
class svip_apb_smoke_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_smoke_test)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  task run_case();
    checked_write('h80,'h12345678);
    checked_read('h80);
    if (ctrl.bus_completions!=2 || observed.items.size()!=2)
      `uvm_fatal("TEST_COUNT","smoke requires exactly two pin/monitor completions")
  endtask
endclass

class svip_apb_sequence_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_sequence_test)
  function new(string name,uvm_component parent);super.new(name,parent);endfunction
  task run_case();
    svip_apb_rw_seq seq=svip_apb_rw_seq::type_id::create("user_sequence");
    seq.cfg=cfg;seq.addr='h80;seq.write=1;seq.data=data_pattern('h59a63cc3);
    sent=2;
    seq.start(agent.sqr);
    if(seq.result.status!==SVIP_APB_OK) `uvm_fatal("TEST_SEQUENCE","write sequence failed")
    seq.write=0;seq.start(agent.sqr);#1ps;
    if(seq.result.status!==SVIP_APB_OK || seq.data!==data_pattern('h59a63cc3))
      `uvm_fatal("TEST_SEQUENCE","read sequence lost response")
  endtask
endclass

class svip_apb_random_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_random_test)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  task run_case();
    bit saw_read=0,saw_write=0;
    bit [7:0] prot_seen=0;
    svip_apb_data_t data_or=0,data_and='1;
    repeat(120) begin
      svip_apb_txn t=cfg.create_txn("random_pattern");
      if (!t.randomize() with {addr inside {['h40:'h7f]};}) `uvm_fatal("TEST_RAND","randomize failed")
      ctrl.wait_cycles=$urandom_range(0,5);
      if(t.write) begin
        checked_write(t.addr,t.data,t.strb,t.prot); saw_write=1;
        data_or |= t.data; data_and &= t.data;
      end else begin checked_read(t.addr,t.prot); saw_read=1; end
      prot_seen[observed.items[$].prot]=1;
    end
    if (!saw_read || !saw_write || data_pattern(data_or)!==data_pattern('1) || data_pattern(data_and)!==0)
      `uvm_fatal("TEST_PATTERN","actual random traffic missed direction/data variation")
    if(cfg.apb4 && $countones(prot_seen)<2) `uvm_fatal("TEST_PATTERN","actual PROT never varied")
  endtask
endclass

class svip_apb_stream_seq extends uvm_sequence #(svip_apb_txn);
  `uvm_object_utils(svip_apb_stream_seq)
  svip_apb_cfg cfg;
  virtual svip_apb_test_ctrl_if ctrl;
  function new(string name="stream");super.new(name);endfunction
  task body();
    realtime previous_end=0,period_ns=2.0*ctrl.clock_half_ps*0.001;
    realtime first_gap=-1;
    bit varied_gap=0;
    bit next_write=1;
    svip_apb_data_t literal='h3c965aa5;
    repeat(16)begin
      svip_apb_txn t=cfg.create_txn("stream_request");
      svip_apb_data_t expected=0;
      realtime gap;
      for(int i=0;i<cfg.data_width;i++)expected[i]=literal[i];
      start_item(t);
      t.write=next_write;next_write=!next_write;
      t.addr='h80;t.data=expected;t.strb=t.write?'1:'0;
      finish_item(t);
      if(t.status!==SVIP_APB_OK || t.data!==expected) `uvm_fatal("TEST_STREAM","stream payload/status failed")
      if(previous_end!=0)begin
        gap=t.t_start-previous_end;
        if(cfg.back_to_back && (gap< -0.0001 || gap>0.0001))
          `uvm_fatal("TEST_B2B","back-to-back inserted a bubble")
        if(!cfg.back_to_back && (gap<cfg.min_idle_cycles*period_ns-0.0001 || gap>cfg.max_idle_cycles*period_ns+0.0001))
          `uvm_fatal("TEST_IDLE_GAP","actual idle latency outside configured bounds")
        if(first_gap<0)first_gap=gap;
        else if(gap<first_gap-0.0001 || gap>first_gap+0.0001)varied_gap=1;
      end
      previous_end=t.t_end;
    end
    if(!cfg.back_to_back && cfg.max_idle_cycles>cfg.min_idle_cycles && !varied_gap)
      `uvm_fatal("TEST_IDLE_GAP","random idle latency never varied on pins")
  endtask
endclass

class svip_apb_timing_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_timing_test)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  task run_case();
    svip_apb_stream_seq stream=svip_apb_stream_seq::type_id::create("stream");
    if(case_name=="example_timing")begin
      cfg.back_to_back=0;cfg.min_idle_cycles=2;cfg.max_idle_cycles=2;ctrl.wait_cycles=3;
    end
    stream.cfg=cfg;stream.ctrl=ctrl;sent=16;stream.start(agent.sqr);#1ps;
    if(case_name=="example_timing")begin
      cfg.max_idle_cycles=5;sent+=16;stream.start(agent.sqr);#1ps;
    end
    if(ctrl.bus_completions!=sent || observed.items.size()!=sent) `uvm_fatal("TEST_STREAM","stream lost completions")
  endtask
endclass

class svip_apb_hold_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_hold_test)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  task run_case();
    svip_apb_txn t=cfg.create_txn("held");
    t.write=0; t.addr='h80; t.strb=0; cfg.hold=1;
    fork
      submit(t);
      begin
        repeat(4) @(vif.mon_cb);
        if(vif.psel!==0 || terminal.items.size()!=0 || ctrl.bus_completions!=0)
          `uvm_fatal("TEST_HOLD","held request reached pins or completed")
        cfg.hold=0;
      end
    join
    if(t.status!==SVIP_APB_OK) `uvm_fatal("TEST_HOLD","request did not resume")
    ctrl.wait_cycles=4;t=cfg.create_txn("already_presented");t.addr='h80;t.strb=0;
    fork
      submit(t);
      begin wait(vif.psel===1 && vif.penable===1);cfg.hold=1;end
    join
    if(t.status!==SVIP_APB_OK || t.wait_cycles!=4)
      `uvm_fatal("TEST_HOLD","hold cancelled an already presented transfer")
    repeat(2)@(vif.mon_cb);#1ps;
    if(vif.psel!==0 || vif.penable!==0 || ctrl.bus_completions!=2)
      `uvm_fatal("TEST_HOLD","requester did not idle after draining the transfer")
    cfg.hold=0;ctrl.wait_cycles=0;
    checked_write('h80,'ha55aa55a); checked_read('h80);
  endtask
endclass

class svip_apb_error_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_error_test)
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  task run_case();
    svip_apb_txn t=cfg.create_txn("error_read");
    ctrl.response_error=1; ctrl.error_data_x=1; ctrl.wait_cycles=2;
    t.write=0;t.addr='h80;t.strb=0;submit(t);
    if(t.status!==SVIP_APB_SLVERR || t.slverr!==1 || t.wait_cycles!=2)
      `uvm_fatal("TEST_ERROR","PSLVERR result lost")
    t=cfg.create_txn("error_write");t.write=1;t.addr='h80;
    t.data=data_pattern('hbadc0ffe);t.strb='1;submit(t);
    if(t.status!==SVIP_APB_SLVERR || observed.items[$].status!==SVIP_APB_SLVERR || t.wait_cycles!=2)
      `uvm_fatal("TEST_ERROR","write PSLVERR result / monitor lost")
    ctrl.response_error=0;ctrl.error_data_x=0;ctrl.wait_cycles=0;
    checked_write('h80,'h76543210);checked_read('h80);
  endtask
endclass

class svip_apb_test_reg extends uvm_reg;
  `uvm_object_utils(svip_apb_test_reg)
  uvm_reg_field value;
  uvm_reg_field upper;
  function new(string name="csr",int bits=32); super.new(name,bits,UVM_NO_COVERAGE); endfunction
  function void build(int bits);
    value=uvm_reg_field::type_id::create("value");
    value.configure(this,8,0,"RW",0,0,1,1,1);
    if(bits>8)begin
      upper=uvm_reg_field::type_id::create("upper");
      upper.configure(this,bits-8,8,"RW",0,0,1,1,0);
    end
  endfunction
endclass

class svip_apb_test_block extends uvm_reg_block;
  function new(string name);super.new(name,UVM_NO_COVERAGE);endfunction
endclass

class svip_apb_ral_test extends svip_apb_base_test;
  `uvm_component_utils(svip_apb_ral_test)
  svip_apb_test_block block;
  uvm_reg_map map;
  svip_apb_test_reg csr;
  uvm_reg_predictor #(svip_apb_txn) predictor;
  function new(string name,uvm_component parent); super.new(name,parent); endfunction
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    block=new("registers");
    block.configure(null,"");
    map=block.create_map("map",0,cfg.data_width/8,UVM_LITTLE_ENDIAN,1);
    csr=new("csr",cfg.data_width);csr.configure(block);csr.build(cfg.data_width);
    map.add_reg(csr,'h80,"RW");block.lock_model();
    predictor=uvm_reg_predictor#(svip_apb_txn)::type_id::create("predictor",this);
  endfunction
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    agent.connect_reg_map(map);agent.connect_predictor(predictor,map);
  endfunction
  task run_case();
    uvm_status_e status;
    uvm_reg_data_t value;
    svip_apb_data_t expected=data_pattern('h96a53cc3);
    // RAL owns submissions here; count actual requested frontdoor operations.
    sent=1;
    csr.write(status,expected,UVM_FRONTDOOR,map);
    #1ps;
    if(status!==UVM_IS_OK || csr.get_mirrored_value()!==expected)
      `uvm_fatal("TEST_RAL","frontdoor write / explicit prediction failed")
    if(case_name=="ral_byte_enable")begin
      sent++;
      csr.value.write(status,'h5a,UVM_FRONTDOOR,map);#1ps;
      expected[7:0]='h5a;
      if(status!==UVM_IS_OK || observed.items[$].strb!==1 || csr.get_mirrored_value()!==expected)
        `uvm_fatal("TEST_RAL_BYTE","field write lost byte enable / mirror")
    end
    if(case_name=="ral_reset")begin
      ctrl.wait_cycles=100;sent++;
      fork
        csr.read(status,value,UVM_FRONTDOOR,map);
        begin
          wait(vif.psel===1 && vif.penable===1);@(negedge ctrl.clk);ctrl.resetn=0;
          #1ps;if(vif.psel!==0 || vif.penable!==0) `uvm_fatal("TEST_RAL_RESET","pins not idle")
          @(negedge ctrl.clk);ctrl.resetn=1;
        end
      join
      #1ps;
      if(status!==UVM_NOT_OK || csr.get_mirrored_value()!==expected)
        `uvm_fatal("TEST_RAL_RESET","abort returned success or changed mirror")
      ctrl.wait_cycles=0;
    end
    if(case_name=="ral_error")begin
      ctrl.response_error=1;ctrl.error_data_x=1;sent++;
      csr.read(status,value,UVM_FRONTDOOR,map);#1ps;
      if(status!==UVM_NOT_OK || csr.get_mirrored_value()!==expected)
        `uvm_fatal("TEST_RAL_ERROR",$sformatf("status=%s mirror=%h expected=%h",status.name(),csr.get_mirrored_value(),expected))
      sent++;csr.write(status,data_pattern('h57ca83b6),UVM_FRONTDOOR,map);#1ps;
      if(status!==UVM_NOT_OK || csr.get_mirrored_value()!==expected)
        `uvm_fatal("TEST_RAL_ERROR","error write returned success / changed mirror")
      ctrl.response_error=0;ctrl.error_data_x=0;
    end
    sent++;
    csr.read(status,value,UVM_FRONTDOOR,map);
    #1ps;
    if(status!==UVM_IS_OK || value!==expected || ctrl.bus_completions!=(case_name=="ral_reset"?2:sent))
      `uvm_fatal("TEST_RAL","frontdoor read differs from fixed value")
  endtask
endclass
