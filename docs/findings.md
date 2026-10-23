# Findings, checks and known limitations

## What was verified

| Check | Method | Result |
|---|---|---|
| Functional behaviour | `tb/tb_siso_16.v` in Icarus Verilog: 12 directed test cases, hard-coded expected values | 75 checks, 0 errors |
| Testbench strength | Five broken copies of the RTL run against the testbench | All five fail, as they should |
| Synthesis numbers | Genus report windows compared against the transcribed CSVs | Match; areas sum to 178.182 µm² and power components sum to the switching total |

The five broken copies were: shift directions swapped, load beating reset, `Dout` always the MSB, an asynchronous reset, and `Din` ignored on left shifts.

## Arithmetic cross-checks

- Cell areas: slow = 87.552 + 32.832 + 40.698 + 16.416 + 0.684 = 178.182 µm²; fast = 87.552 + 30.780 + 40.698 + 16.416 + 0.684 + 2.052 = 178.182 µm².
- `AOI22XL` has the same area as `AOI22X1` (2.052 µm²), so swapping one cell leaves the total unchanged. Equal area at the two corners is therefore expected.
- Switching power = internal + net: 3726.672 + 764.074 = 4490.746 nW (slow) and 6002.028 + 1493.304 = 7495.332 nW (fast).
- Ratios: leakage 3.16×, internal 1.61×, net 1.95×, switching 1.67×.

## Limitations

- **Synthesis is not reproducible from this repo.** The Genus scripts, constraints and netlists were not among the project files, only the report windows. The data in `synthesis/` is transcribed from those screenshots.
- **No ASIC timing numbers.** The project files contain no Genus timing report, so no slack or maximum frequency is claimed for the standard-cell design. The statement that the fast corner is faster is the expected behaviour of a fast corner, not a measured result. The Quartus timing figures are for a FLEX10K FPGA and are not comparable to the Genus runs.
- **Power assumptions are unknown.** The switching activity and operating frequency used for the Genus power reports are not recorded.
- **Process node.** The library names (`slow_vdd1v0`, `fast_vdd1v0`) are given, but the process node is not stated in the project files, so none is claimed here.
- **Leakage.** Leakage rises 3.2× at the fast corner despite the lower temperature, which is consistent with the fast process corner and the higher supply voltage outweighing the temperature drop. This is an interpretation; the project files do not separate the effects.
- `Dout` is combinational on `left_right`: changing the direction input changes `Dout` immediately, without waiting for a clock edge.
- The testbench checks 12 directed scenarios. It is not exhaustive, and no formal or equivalence checking was run. No place-and-route (floorplan, routing, post-layout power) was done.

## Notes on the original report and slides

- The waveform figures captioned "Cadence SimVision" in the report are Quartus waveform-editor output (`db/siso_16.sim.cvwf`, project `siso_16`). They are labelled as Quartus here.
- The report mentions both 7 and 12 test cases, and its testbench listing has a `$finish` before the last case and a typographic quote in `16’hFFFF`. The testbench in this repo is a clean rewrite that covers all the described scenarios, with expected values listed explicitly.
- The ModelSim captures appear to be offset by one clock cycle from the hex sequences quoted in the report text, because the original testbench changed its inputs at different moments within the clock period. Both are consistent with their own stimulus timing; this repo's testbench makes the timing explicit (inputs change 1 ns after the rising edge).
- The Genus fast-corner window lists the inverter as `INVXL`, while the report text calls it `INVX1`. The CSV follows the Genus window.
- The Quartus project was built for FLEX10K, an FPGA family, while the synthesis comparison uses ASIC standard-cell libraries. They are different flows and are reported separately.
