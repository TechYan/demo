// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Checked examples using the same public API as customer test sequences.

  task automatic example_basic();
    svip_control_when at_tick;
    svip_control_result r;
    svip_control_value_t value='0;
    value[256]=1;value[64]=1;value[0]=1;
    check(!core_domain.ready(),"A29 accepting start is not actual clock availability");
    control.domains.wait_ready("core",$time+3,r);check(r.status==SVIP_CONTROL_TIMEOUT,"A29 ready cannot precede first actual edge");
    at_tick=new(SVIP_CONTROL_BEFORE_CAPTURE,core_clock.next_rise_tick());at_tick.setup_ticks=100;
    wide_signal.set(value,svip_control_mask(257),at_tick,$time+20000,r);
    check(r.status==SVIP_CONTROL_COMPLETED,"before capture complete");
    check(wide_q[256]===1 && wide_q[64]===1 && wide_q[0]===1,"receiver actual high bits");
    check(r.observed && !r.effective,"pin observed is distinct from destination effect");
    control.domains.wait_ready("core",$time+100,r);check(r.status==SVIP_CONTROL_COMPLETED,"domain clock/reset availability observed");
  endtask
  

task automatic test_profile_policies();
  svip_control_profile profile;
  svip_control_result r;
  svip_control_transition_plan plan;
  svip_control_when at_tick;
  svip_control_value_t old_a,old_b;
  svip_control_value_t a='0;
  a[64]=1;a[0]=1;
  profile=new("tuple");profile.add(cfg_a_signal,a,svip_control_mask(65));profile.add(cfg_b_signal,32'h83579bdf,svip_control_mask(32));
  control.capture_coherent(profile,core_clock,core_clock.next_rise_tick(),100,$time+20000,r);
  check(r.status==SVIP_CONTROL_COMPLETED,"B01 profile coherent");
  check(tuple_q=={65'h10000000000000001,32'h83579bdf},"B01 real RTL tuple complete");
  control.capture_coherent(profile,core_clock,core_clock.next_rise_tick(),100,$time+20000,r);
  check(r.status==SVIP_CONTROL_COMPLETED,"B05 same value no value-change dependency");
  old_a=cfg_a;old_b=cfg_b;profile.values[0]=0;profile.values[1]='0;profile.values[1][32]=1;
  control.capture_coherent(profile,core_clock,core_clock.next_rise_tick(),100,$time+20000,r);
  check(r.status==SVIP_CONTROL_REJECTED && cfg_a==old_a && cfg_b==old_b,"B02 invalid second field no partial first write");
  profile=new("cross_domain");profile.add(cfg_a_signal,1,1);profile.add(data64_signal,1,1);
  control.capture_coherent(profile,core_clock,core_clock.next_rise_tick(),100,$time+20000,r);
  check(r.status==SVIP_CONTROL_REJECTED,"B02 cross-domain capture coherence rejected");
  plan=new(profile);at_tick=new(SVIP_CONTROL_ASYNC_AT,$time+10);plan.steps.push_back(at_tick);
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time+20);plan.steps.push_back(at_tick);
  plan.request_global_atomic=1;control.transition(plan,$time+20000,r);check(r.status==SVIP_CONTROL_REJECTED,"B02 unsupported global atomic rejected");
  plan.request_global_atomic=0;control.transition(plan,$time+20000,r);
  check(r.status==SVIP_CONTROL_COMPLETED && plan.progress.size()==2,"B03 per-domain barrier reports each step");
  check(plan.progress[0].applied_tick<plan.progress[1].applied_tick,"B03 barrier does not imply simultaneous effects");
endtask



task automatic test_lifecycle_policies();
  svip_control_result r;
  svip_control_when at_tick;
  svip_control_value_t image='0;
  tieoff_control.configure(1,$time+1000,r);check(r.status==SVIP_CONTROL_COMPLETED,"B06 tieoff bootstrap");
  check(tieoff_control.lock(),"B06 tieoff lock");
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time);
  tieoff_signal.set(0,1,at_tick,$time+1000,r);
  check(r.status==SVIP_CONTROL_REJECTED && tieoff===1,"B06 low-level signal path cannot bypass lock");
  tieoff_signal.expect_stable(1,$time+101,$time+200,r);
  check(r.status==SVIP_CONTROL_COMPLETED,"B06 independent actual-pin stability window");
  image[64]=1;image[5]=1;
  fuse_control.load_image(image,$time+1000,r);check(r.status==SVIP_CONTROL_REJECTED,"B08 no POR window");
  reset_high.set_source("por",1,$time+1000,r);
  fuse_control.load_image(image,$time+1000,r);
  check(r.status==SVIP_CONTROL_COMPLETED && fuse_image==65'h10000000000000020,"B07 image loaded with high bit");
  fuse_control.load_image(1,$time+1000,r);check(r.status==SVIP_CONTROL_REJECTED,"B08 consumed POR epoch locked");
  check(!ep_fuse.open_load("FUNCTIONAL_RESET"),"B08 wrong load event rejected");
  reset.set_source("functional",1,$time+1000,r);reset.set_source("functional",0,$time+1000,r);
  check(fuse_image==65'h10000000000000020 && tieoff===1,"B07 functional reset retained image/tieoff");
  reset_high.set_source("por",0,$time+1000,r);reset_high.set_source("por",1,$time+1000,r);
  fuse_control.load_image(65'h10000000000000001,$time+1000,r);
  check(r.status==SVIP_CONTROL_COMPLETED && fuse_image==65'h10000000000000001,"B07 new observed POR epoch can reload");
  reset_high.set_source("por",0,$time+1000,r);
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time);
  fuse_signal.set(0,svip_control_mask(65),at_tick,$time+1000,r);
  check(r.status==SVIP_CONTROL_REJECTED && fuse_image[64]===1,"B08 no ordinary write after window");
endtask



task automatic test_irq();
  svip_control_result r,pulse_result,observation_result;
  svip_control_when at_tick;
  svip_control_tick_t measured,first_tick;
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time+7);
  fork
    short_irq_observer.measure_pulse($time+1000,measured,observation_result);
    irq_source.pulse_time(1,0,1,23,at_tick,$time+1000,pulse_result);
  join
  check(pulse_result.status==SVIP_CONTROL_COMPLETED && observation_result.status==SVIP_CONTROL_COMPLETED && measured==23,"B10 exact short 23ps pulse, no stretch");
  check(irq_q===0,"B10 sub-cycle pulse can be missed by RTL; no hidden synchronizer");
  #1; // Visible idle separates the two examples even in settled-only FSDB.
  first_tick=$time;irq_source.pulse_cycles(1,0,1,2,$time+20000,pulse_result);
  check(pulse_result.status==SVIP_CONTROL_COMPLETED && irq===0 && irq_q===1,"B10 N future captures, release after last capture");
  check(pulse_result.applied_tick==first_tick,"B10 cycle pulse starts at accepted source tick");
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time+17);
  irq_inputs_source.level(4'b1010,at_tick,$time+1000,r);
  check(irq_inputs===4'b1010,"B09 multiple IRQ lines together");
  reference_clock.wait_edges(1,$time+20000,r);
  irq_observer.expect_level(1,$time+1000,r);check(r.status==SVIP_CONTROL_COMPLETED,"B11 DUT output observed");
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time);irq_inputs_source.level(0,at_tick,$time+1000,r);
  check(dut_irq===1,"B11 clearing source does not silently drive sticky DUT output");
  csr.write("pending",4'b1010,$time+50000,r);check(r.status==SVIP_CONTROL_COMPLETED,"B11 clear via real W1C");
  irq_observer.expect_level(0,$time+1000,r);check(r.status==SVIP_CONTROL_COMPLETED,"B11 output clears after CSR");
endtask



task automatic test_csr();
  svip_control_result bus_result,r;
  svip_control_value_t value;
  svip_control_when at_tick;
  svip_control_endpoint bad;
  svip_control_sv_binding#(32) active_binding;
  int before_reads;
  string why;
  csr.write("control",32'h80402001,$time+80000,bus_result);
  check(bus_result.status==SVIP_CONTROL_COMPLETED && bus_result.applied_kind=="CSR_TRANSACTION_COMPLETED","B12 typed bus completion");
  check(!bus_result.observed && !bus_result.effective && csr_output==0,"B12 APB done precedes destination output effect");
  csr_observer.expect_value(32'h80402001,svip_control_mask(32),$time+80000,r,1,SVIP_CONTROL_CAPTURE_VALUE,b_csr_output.capture_id());
  check(r.status==SVIP_CONTROL_COMPLETED && r.observed_tick>bus_result.applied_tick,"B12 actual delayed target-domain observation");
  $display("SVIP_CONTROL_CSR_EFFECT bus_tick=%0d actual_capture_tick=%0d value=%0h",bus_result.applied_tick,r.observed_tick,r.actual);
  csr.read("control",$time+80000,r,value);check(value==32'h80402001,"real CSR readback");
  csr.write("control_byte",8'ha5,$time+80000,r);check(r.status==SVIP_CONTROL_COMPLETED,"native byte strobe write");
  csr.read("control",$time+80000,r,value);check(value==32'h8040a501,"byte update preserved other bytes without RMW");
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time);irq_inputs_source.level(4'b1010,at_tick,$time+1000,r);
  reference_clock.wait_edges(1,$time+20000,r);
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time);irq_inputs_source.level(0,at_tick,$time+1000,r);
  before_reads=csr_reads;csr.write("pending",2,$time+80000,r);
  check(r.status==SVIP_CONTROL_COMPLETED && pending==8 && csr_reads==before_reads,"B14 W1C preserves unrelated pending, no blind read-modify-write");
  csr.write("pending",8,$time+80000,r);check(dut_irq===0,"B14 real pending clear");
  csr.read("read_clear",$time+80000,r,value);check(value==32'h80000001,"B14 explicit side-effect read");
  csr.read("read_clear",$time+80000,r,value);check(value==0,"B14 read-clear hardware effect");
  csr.write("read_clear",1,$time+80000,r);check(r.status==SVIP_CONTROL_REJECTED,"B14 read-clear cannot be RMW-written");
  active_binding=new(csr_output_pin,"svip_control_tb.csr_output_pin.observed",1);
  check(!registry.register_pin("direct_fallback",active_binding,"csr_output",0,"bad",0,SVIP_CONTROL_SIGNAL,SVIP_CONTROL_DIRECT_PIN,bad,why),"B18 CSR canonical output rejects DirectPin owner");
  at_tick=new(SVIP_CONTROL_ASYNC_AT,$time);csr_observer.set(0,svip_control_mask(32),at_tick,$time+1000,r);
  check(r.status==SVIP_CONTROL_REJECTED,"B18 CSR observer cannot drive through low API");
endtask


