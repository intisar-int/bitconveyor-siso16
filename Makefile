# make sim      -> compile + run the self-checking testbench (needs Icarus Verilog)
# make figures  -> regenerate waveform + PPA figures (needs Python: numpy, matplotlib)
# make all      -> both
.PHONY: all sim figures clean

all: sim figures

sim:
	mkdir -p results/logs build
	iverilog -g2005 -o build/siso_sim rtl/siso_16.v tb/tb_siso_16.v
	vvp build/siso_sim | tee results/logs/sim_log.txt

figures:
	python3 python/make_figures.py

clean:
	rm -rf build
