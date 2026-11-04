// SPDX-License-Identifier: Apache-2.0
// Author: syan
task examples();
  svip_jtag_txn r;
  case(scenario)
    "example_basic":begin
      reset_tms(r);goto_state(SVIP_JTAG_RTI,r);
      scan_word(0,0,32,r);
      insist(r.status==SVIP_JTAG_DONE,"IDCODE scan");
      foreach(r.rx_bits[i])insist(r.rx_bits[i]===((32'h149511c3>>i)&1),"IDCODE");
    end
    "example_patterns":begin setup_bypass();for(int p=0;p<5;p++)bypass_check(132,p);end
    "example_long":begin setup_bypass();bypass_check(4097);end
    "example_callback":begin cb.change=1;setup_bypass();bypass_check(1,1);cb.change=0;end
    "example_passive":begin
      // External master: passive agent receives no sequence items or driver flags.
      repeat(5)manual_cycle(1);manual_cycle(0);
      manual_cycle(1);manual_cycle(1);manual_cycle(0);manual_cycle(0);
      repeat(3)manual_cycle(0,1);manual_cycle(1,1);manual_cycle(1);manual_cycle(0);
      insist(agent.mon.n_scans==1,"passive IR commit");
    end
    "example_raw_pause":begin
      bit tms[],tdi[];
      setup_bypass();goto_state(SVIP_JTAG_SHIFT_DR,r);
      tms=new[4];tdi=new[4];tms='{0,0,1,0};tdi='{1,0,1,0};raw(tms,tdi,r);
      insist(ctrl.state==6,"Pause-DR");
      #123ps; // TCK stopped low; this does not itself move the TAP.
      insist(ctrl.state==6,"stopped clock holds Pause");
      tms='{1,0,0,1,1,0};tdi=new[6];raw(tms,tdi,r);
      insist(ctrl.state==1 && agent.mon.last_scan.tdo_bits.size()==5,"one cumulative committed scan");
    end
    "example_register":begin
      setup_bypass();scan_word(1,2,4,r);scan_word(0,32'h89abcdef,32,r);
      insist(ctrl.value==32'h89abcdef && ctrl.updates==1,"Update side effect");
      scan_word(0,0,32,r);
      foreach(r.rx_bits[i])insist(r.rx_bits[i]===((32'h89abcdef>>i)&1),"register readback");
    end
    default:p1();
  endcase
endtask
