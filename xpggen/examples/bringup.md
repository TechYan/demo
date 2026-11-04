# demo.register-bringup

Synthetic RNOC example: configure fields, check them, poll ready, then delay.

Source: `examples/rnoc.sample.json`

| # | Op | Target | Address | Value | Comment |
|---:|---|---|---|---|---|
| 1 | read | `REG__XPG__PCIE__CTRL_000` | `0x0` | `-` | Read the initial control value without comparing. |
| 2 | write | `REG__XPG__PCIE__CTRL_000` | `0x0` | `0x1` | Write the complete control register. |
| 3 | rmw | `REG__XPG__PCIE__CFG_004.{mode, threshold}` | `0x10` | `mode=0x3; threshold=0x20` | Set mode and threshold in one read-modify-write. |
| 4 | read_check | `REG__XPG__PCIE__CFG_004.{mode, threshold}` | `0x10` | `mode=0x3; threshold=0x20` | Compare only the two configured fields. |
| 5 | poll | `REG__XPG__PCIE__STATUS_001.{ready}` | `0x4` | `ready=0x1` | Poll ready with a 1000 us timeout and a 10 us interval. |
| 6 | delay | `delay` | `-` | `25 us` | Wait 25 microseconds. |
