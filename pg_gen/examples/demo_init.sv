// Phase: demo_init
// Inspect the fictional controller before configuration.
read_reg(0, `REG__DEMO_BUS__DEMO_CONTROL_REG__DEMO_CONTROL, regval);
// Enable fictional sampling with a 16-tick demo period.
write_reg(0, `REG__DEMO_BUS__DEMO_SENSOR_REG__DEMO_SENSOR_CONFIG, 32'h1001);
// Enable the fictional controller while preserving other fields.
read_reg(0, `REG__DEMO_BUS__DEMO_CONTROL_REG__DEMO_CONTROL, regval);
regval[0:0] = 1'h1;
write_reg(0, `REG__DEMO_BUS__DEMO_CONTROL_REG__DEMO_CONTROL, regval);
// Wait for fictional sensor readiness with a bounded timeout.
begin : POLL_DEMO_SENSOR_STATUS_READY
  int unsigned poll_elapsed_us;
  bit poll_done;
  poll_elapsed_us = 0;
  poll_done = 1'b0;
  while (poll_elapsed_us <= 1000) begin
    read_reg(0, `REG__DEMO_BUS__DEMO_SENSOR_REG__DEMO_SENSOR_STATUS, regval);
    if ((regval[0:0] == 1'h1)) begin
      poll_done = 1'b1;
      break;
    end
    if (poll_elapsed_us >= 1000) break;
    #(10 * 1us);
    poll_elapsed_us += 10;
  end
  if (!poll_done) $error("poll timeout: DEMO_SENSOR_STATUS.ready, condition eq 0x1, timeout_us=1000");
end
