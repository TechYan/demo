// SPDX-License-Identifier: Apache-2.0
// Author: syan
// Each example checks results; the same public API is usable outside this TB.
// ctrl/manual below are independent peer fixtures, replaced by the DUT in a project.
task example_basic_api();
  svip_spi_transfer_seq seq=svip_spi_transfer_seq::type_id::create("example");
  profile(0,8,0);ctrl.reply='{'h3d,'ha7};ctrl.seen.delete();
  seq.cs=0;seq.tx_words='{'h96,'h23};
  seq.check_rx=1;seq.expected_words='{'h3d,'ha7};
  seq.start(spi.sequencer);
  if(seq.result.status!=SVIP_SPI_OK || seq.result.n_received!=2 || seq.result.n_sampled!=16 ||
     ctrl.seen.size()!=2 || ctrl.seen[0]!=='h96 || ctrl.seen[1]!=='h23)
    `uvm_fatal("SPI_ORACLE","public transfer sequence did not complete expected exchange")
endtask

task example_slave_api();
  svip_spi_txn response=svip_spi_txn::type_id::create("response");
  svip_spi_word_t command[]='{'h96,'h23};svip_spi_sample_t returned[];
  profile(0,8,0);response.tx_words='{'h3d,'ha7};
  if(!spi.enqueue_response(response))`uvm_fatal("SPI_TEST","response rejected")
  manual(command,returned);
  if(returned.size()!=2 || returned[0]!=='h3d || returned[1]!=='ha7 ||
     spi.pending_responses()!=0 || completed.items.size()!=1 || completed.items[0].status!=SVIP_SPI_OK ||
     completed.items[0].rx_words[0]!=='h96 || completed.items[0].rx_words[1]!=='h23)
    `uvm_fatal("SPI_ORACLE","queued response or received command incorrect")
endtask

task run_example(string which,output bit handled);
  handled=1;
  case(which)
    "example_basic":example_basic_api();
    "example_modes":begin simple_master(0);simple_master(1);simple_master(2);simple_master(3);end
    "example_nonbyte":simple_master(2,9,1);
    "example_multi_cs":begin simple_master(0,8,0,0);simple_master(3,8,1,`SVIP_SPI_MAX_CS-1);end
    "example_patterns":patterns();
    "example_random":patterns(1);
    "example_slave_queue":example_slave_api();
    "example_callback":slave_generated(0,1);
    "example_passive":passive_modes();
    "example_clock_hold":clock_hold();
    "example_reset":reset_master();
    "example_compare":masked_compare();
    "example_timing":begin
      cfg.t_low_max=cfg.t_low+half_ps*1ps;cfg.t_high_max=cfg.t_high+half_ps*1ps;
      cfg.word_gap=half_ps*1ps;cfg.word_gap_max=half_ps*3ps;
      cfg.frame_delay=0;cfg.frame_delay_max=half_ps*2ps;
      simple_master(0,9,0);simple_master(3,9,1);
      if(observe.frames[$].min_half_period==observe.frames[$].max_half_period)
        `uvm_fatal("SPI_ORACLE","timing variation did not reach pins")
    end
    default:handled=0;
  endcase
endtask
