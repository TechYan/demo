`timescale 1ps/1ps

// Small deterministic licensed-only fixture. All reference timestamps are ps.
// Explicit drive logs record procedural values immediately after assignment;
// observation logs sample an unchanged predicate around each reference edge.
module xwave_progressive_fixture;
  logic clk, valid, ready, glitch, narrow, initial_x, coverage;
  logic [63:0] bus;
  integer reference;
  time last_rising;

  task automatic scalar_log(input string signal_name, input logic value);
    $fdisplay(reference, "{\"kind\":\"drive\",\"signal\":\"%s\",\"tick_ps\":%0t,\"bits\":\"%b\"}", signal_name, $time, value);
  endtask
  task automatic bus_log;
    $fdisplay(reference, "{\"kind\":\"drive\",\"signal\":\"bus\",\"tick_ps\":%0t,\"bits\":\"%b\"}", $time, bus);
  endtask
  task automatic offset_observation(input time edge_time);
    #2000;
    $fdisplay(reference, "{\"kind\":\"observation\",\"strategy\":\"offset\",\"edge_ps\":%0t,\"observe_ps\":%0t,\"value\":\"%b\"}", edge_time, $time, valid && ready);
  endtask

  initial begin
    reference = $fopen("progressive-reference.jsonl", "w");
    if (!reference) $fatal(1, "Cannot open reference output");
    $fdisplay(reference, "{\"kind\":\"metadata\",\"tick_unit\":\"ps\",\"monitor\":\"explicit_drive_and_unchanged_predicate_at_edges\"}");
    clk = 0; valid = 0; ready = 1; glitch = 0; narrow = 0;
    initial_x = 1'bx; coverage = 0; bus = 64'h8000_0000_0000_0000;
    last_rising = 0;
    scalar_log("clk", clk); scalar_log("valid", valid); scalar_log("ready", ready);
    scalar_log("glitch", glitch); scalar_log("narrow", narrow);
    scalar_log("initial_x", initial_x); scalar_log("coverage", coverage); bus_log();
    $fsdbDumpfile("progressive_wave.fsdb");
    $fsdbDumpvars(0, xwave_progressive_fixture, "+all");
    // Fork after deterministic initialization, avoiding time-zero log races.
    fork
      begin
        #4000 valid = 1; scalar_log("valid", valid);
        #2000 valid = 0; scalar_log("valid", valid);
        #8000 valid = 1; scalar_log("valid", valid);
        #2000 valid = 0; scalar_log("valid", valid);
        #7000 valid = 1; scalar_log("valid", valid);
        #2000 valid = 0; scalar_log("valid", valid);
      end
      begin
        #5000 clk = 1; scalar_log("clk", clk);
        #3000 clk = 0; scalar_log("clk", clk);
        #7000 clk = 1; scalar_log("clk", clk);
        #4000 clk = 0; scalar_log("clk", clk);
        #5000 clk = 1; scalar_log("clk", clk);
        #2000 clk = 0; scalar_log("clk", clk);
        // Clock intentionally stops after this falling edge.
      end
      begin
        #10000 glitch = 1'bx; scalar_log("glitch", glitch);
        #0 glitch = 0; scalar_log("glitch", glitch);
        #0 glitch = 0; scalar_log("glitch", glitch);
      end
      begin
        #11000 narrow = 1; scalar_log("narrow", narrow);
        #1 narrow = 0; scalar_log("narrow", narrow);
      end
      begin
        #12000 bus[3] = 1'bx; bus_log();
        #1000 bus[3] = 0; bus[5] = 1'bz; bus_log();
        #1000 bus[5] = 0; bus_log();
      end
      begin
        #28000;
        $fdisplay(reference, "{\"kind\":\"coverage\",\"state\":\"dump_off\",\"tick_ps\":28000}");
        $fsdbDumpoff;
        #1000 coverage = 1; scalar_log("coverage", coverage);
        #2000 coverage = 0; scalar_log("coverage", coverage);
        #1000 $fsdbDumpon;
        $fdisplay(reference, "{\"kind\":\"coverage\",\"state\":\"dump_on\",\"tick_ps\":32000}");
      end
    join
    #8000;
    $fdisplay(reference, "{\"kind\":\"complete\",\"tick_ps\":40000}");
    $fclose(reference);
    $finish;
  end

  always @(posedge clk) begin
    last_rising = $time;
    // VALID was last assigned >=1000ps before this edge and is withdrawn
    // 1000ps after it. Thus this active-region observation equals t^- here.
    $fdisplay(reference, "{\"kind\":\"observation\",\"strategy\":\"pre_edge\",\"edge_ps\":%0t,\"observe_ps\":%0t,\"value\":\"%b\"}", $time, $time, valid && ready);
    fork
      offset_observation($time);
    join_none
  end
  always @(negedge clk) begin
    if ($time > 0)
      $fdisplay(reference, "{\"kind\":\"observation\",\"strategy\":\"opposite_edge\",\"edge_ps\":%0t,\"observe_ps\":%0t,\"value\":\"%b\"}", last_rising, $time, valid && ready);
  end
endmodule
