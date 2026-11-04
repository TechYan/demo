// Generated from XPG config: demo.register-bringup

// Step 1: read REG__XPG__PCIE__CTRL_000
// Read the initial control value without comparing.
read_reg(0, `REG__XPG__PCIE__CTRL_000, regval);

// Step 2: write REG__XPG__PCIE__CTRL_000
// Write the complete control register.
write_reg(0, `REG__XPG__PCIE__CTRL_000, 32'h1);

// Step 3: rmw REG__XPG__PCIE__CFG_004.{mode, threshold}
// Set mode and threshold in one read-modify-write.
//   mode = 0x3
//   threshold = 0x20
read_reg(0, `REG__XPG__PCIE__CFG_004, regval);
regval = (regval & ~32'hFFF0) | 32'h2030;
write_reg(0, `REG__XPG__PCIE__CFG_004, regval);

// Step 4: read_check REG__XPG__PCIE__CFG_004.{mode, threshold}
// Compare only the two configured fields.
//   mode = 0x3
//   threshold = 0x20
read_reg(0, `REG__XPG__PCIE__CFG_004, regval);
if ((regval & 32'hFFF0) !== 32'h2030)
  $error("read_check failed: REG__XPG__PCIE__CFG_004.{mode, threshold}, expected=32'h2030, actual=0x%0h", (regval & 32'hFFF0));

// Step 5: poll REG__XPG__PCIE__STATUS_001.{ready}
// Poll ready with a 1000 us timeout and a 10 us interval.
//   ready = 0x1
begin : POLL_REG_XPG_PCIE_STATUS_001_READY
  int unsigned poll_elapsed_us;
  bit poll_done;
  poll_elapsed_us = 0;
  poll_done = 1'b0;
  while (poll_elapsed_us <= 1000) begin
    read_reg(0, `REG__XPG__PCIE__STATUS_001, regval);
    if ((regval & 32'h2) === 32'h2) begin
      poll_done = 1'b1;
      break;
    end
    if (poll_elapsed_us >= 1000) break;
    #(10 * 1us);
    poll_elapsed_us += 10;
  end
  if (!poll_done) $error("poll timeout: REG__XPG__PCIE__STATUS_001.{ready}, timeout_us=1000");
end

// Step 6: delay delay
// Wait 25 microseconds.
#(25 * 1us);
