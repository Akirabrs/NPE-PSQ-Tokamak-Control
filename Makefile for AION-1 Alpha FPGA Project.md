# Makefile for AION-1 Alpha FPGA Project
# MIT-Level Build System

# ============================================================================
# CONFIGURATION
# ============================================================================

# Tools
VCS         = vcs
VERILATOR   = verilator
SYNOPSYS    = dc_shell
CADENCE     = genus
INNOVUS     = innovus
VERA        = vera
UVM_HOME    = $(UVM_HOME)

# Directories
RTL_DIR     = ./rtl
SIM_DIR     = ./simulation
SYN_DIR     = ./synthesis
PR_DIR      = ./place_route
VERIF_DIR   = ./verification
CONST_DIR   = ./constraints
DOC_DIR     = ./docs
REPORT_DIR  = ./reports

# Targets
TARGET      = aion1_alpha
TECH        = tsmc7
FREQ        = 250

# ============================================================================
# SOURCE FILES
# ============================================================================

# RTL Files
RTL_FILES = \
	$(RTL_DIR)/top/aion1_top.sv \
	$(RTL_DIR)/fpga_hardip/fpga_hardip_psq.sv \
	$(RTL_DIR)/npu_tensor/npu_tensor_core.sv \
	$(RTL_DIR)/serdes/serdes_x4_interface.sv \
	$(RTL_DIR)/noc/noc_128bit_crossbar.sv \
	$(RTL_DIR)/memory/ddr4_controller.sv \
	$(RTL_DIR)/clock/clock_reset_manager.sv \
	$(RTL_DIR)/peripherals/gpio_controller.sv \
	$(RTL_DIR)/security/security_ecc_module.sv \
	$(RTL_DIR)/test/bist_controller.sv

# Verification Files
VERIF_FILES = \
	$(VERIF_DIR)/uvm/test_aion1_psq.sv \
	$(VERIF_DIR)/uvm/aion1_env.sv \
	$(VERIF_DIR)/uvm/plasma_agent.sv \
	$(VERIF_DIR)/uvm/sequences/*.sv \
	$(VERIF_DIR)/formal/*.sv

# Constraint Files
CONST_FILES = \
	$(CONST_DIR)/timing/aion1.tcl \
	$(CONST_DIR)/physical/floorplan.tcl \
	$(CONST_DIR)/power/power_constraints.tcl \
	$(CONST_DIR)/manufacturing/dfm_rules.tcl

# ============================================================================
# TARGETS
# ============================================================================

.PHONY: all clean lint sim synth pr verify power formal

all: lint sim synth pr verify power

# ----------------------------------------------------------------------------
# LINTING
# ----------------------------------------------------------------------------
lint:
	@echo "Running RTL linting..."
	verilator --lint-only $(RTL_FILES) --top-module aion1_top \
		-Wall -Wno-fatal -Wno-style
	@echo "✓ RTL linting passed"

# ----------------------------------------------------------------------------
# SIMULATION
# ----------------------------------------------------------------------------
sim: compile_sim run_sim

compile_sim:
	@echo "Compiling simulation..."
	$(VCS) -full64 -sverilog +define+SIMULATION \
		+incdir+$(RTL_DIR) +incdir+$(VERIF_DIR) \
		$(RTL_FILES) $(VERIF_FILES) \
		-l compile.log

run_sim:
	@echo "Running simulation..."
	./simv +UVM_TESTNAME=aion1_psq_test \
		+UVM_VERBOSITY=UVM_LOW \
		-l simulation.log
	@echo "✓ Simulation completed"

# ----------------------------------------------------------------------------
# SYNTHESIS
# ----------------------------------------------------------------------------
synth: compile_syn optimize report

compile_syn:
	@echo "Running synthesis..."
	$(SYNOPSYS) -f $(SYN_DIR)/synopsys/compile.tcl \
		-x "set_target $(TARGET); set_tech $(TECH)" \
		-l $(REPORT_DIR)/syn_compile.log

optimize:
	@echo "Optimizing design..."
	$(SYNOPSYS) -f $(SYN_DIR)/synopsys/optimize.tcl \
		-x "set_freq $(FREQ)" \
		-l $(REPORT_DIR)/syn_optimize.log

report:
	@echo "Generating synthesis reports..."
	$(SYNOPSYS) -f $(SYN_DIR)/synopsys/report.tcl \
		-l $(REPORT_DIR)/syn_report.log
	@echo "✓ Synthesis completed"

# ----------------------------------------------------------------------------
# PLACE & ROUTE
# ----------------------------------------------------------------------------
pr: init_floorplan placement cts routing finish

init_floorplan:
	@echo "Initializing floorplan..."
	$(INNOVUS) -files $(PR_DIR)/icc2/init.tcl \
		-log $(REPORT_DIR)/pr_init.log

placement:
	@echo "Running placement..."
	$(INNOVUS) -files $(PR_DIR)/icc2/place.tcl \
		-log $(REPORT_DIR)/pr_place.log

cts:
	@echo "Running clock tree synthesis..."
	$(INNOVUS) -files $(PR_DIR)/icc2/cts.tcl \
		-log $(REPORT_DIR)/pr_cts.log

routing:
	@echo "Running routing..."
	$(INNOVUS) -files $(PR_DIR)/icc2/route.tcl \
		-log $(REPORT_DIR)/pr_route.log

finish:
	@echo "Finalizing design..."
	$(INNOVUS) -files $(PR_DIR)/icc2/finish.tcl \
		-log $(REPORT_DIR)/pr_finish.log
	@echo "✓ Place & Route completed"

# ----------------------------------------------------------------------------
# VERIFICATION
# ----------------------------------------------------------------------------
verify: coverage formal equivalence

coverage:
	@echo "Running coverage analysis..."
	urg -dir simv.vdb -report $(REPORT_DIR)/coverage
	@echo "✓ Coverage analysis completed"

formal:
	@echo "Running formal verification..."
	jaspergold -tcl $(VERIF_DIR)/formal/formal.tcl \
		-log $(REPORT_DIR)/formal.log
	@echo "✓ Formal verification completed"

equivalence:
	@echo "Running equivalence checking..."
	conformal -golden $(SYN_DIR)/netlist/$(TARGET)_syn.v \
		-revised $(PR_DIR)/output/$(TARGET)_pr.v \
		-log $(REPORT_DIR)/equivalence.log
	@echo "✓ Equivalence checking completed"

# ----------------------------------------------------------------------------
# POWER ANALYSIS
# ----------------------------------------------------------------------------
power:
	@echo "Running power analysis..."
	voltus -design $(TARGET) \
		-activity $(SIM_DIR)/activity.saif) \
		-log $(REPORT_DIR)/power.log
	python3 tools/analyze_power.py
	@echo "✓ Power analysis completed"

# ----------------------------------------------------------------------------
# TIMING ANALYSIS
# ----------------------------------------------------------------------------
timing:
	@echo "Running timing analysis..."
	pt_shell -f $(CONST_DIR)/timing/pt_analysis.tcl \
		-log $(REPORT_DIR)/timing.log
	@echo "✓ Timing analysis completed"

# ----------------------------------------------------------------------------
# GENERATE DOCUMENTATION
# ----------------------------------------------------------------------------
doc:
	@echo "Generating documentation..."
	doxygen $(DOC_DIR)/doxygen.conf
	@echo "✓ Documentation generated"

# ----------------------------------------------------------------------------
# CLEAN
# ----------------------------------------------------------------------------
clean:
	rm -rf simv* csrc *.log *.vpd *.fsdb *.saif
	rm -rf $(REPORT_DIR)/*
	rm -rf $(SYN_DIR)/output/*
	rm -rf $(PR_DIR)/output/*
	rm -rf innovus.* genus.* dc_*
	rm -rf *.pyc __pycache__
	@echo "✓ Clean completed"

# ----------------------------------------------------------------------------
# BACKUP
# ----------------------------------------------------------------------------
backup:
	@echo "Creating backup..."
	tar -czf aion1_backup_$(shell date +%Y%m%d).tar.gz \
		--exclude='*.log' --exclude='simv*' \
		--exclude='csrc' .
	@echo "✓ Backup created"

# ----------------------------------------------------------------------------
# HELP
# ----------------------------------------------------------------------------
help:
	@echo "AION-1 Alpha FPGA Project Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all       : Run complete flow (lint, sim, synth, pr, verify)"
	@echo "  lint      : Run RTL linting"
	@echo "  sim       : Run simulation"
	@echo "  synth     : Run synthesis"
	@echo "  pr        : Run place and route"
	@echo "  verify    : Run verification (coverage, formal, equivalence)"
	@echo "  power     : Run power analysis"
	@echo "  timing    : Run timing analysis"
	@echo "  doc       : Generate documentation"
	@echo "  clean     : Clean all generated files"
	@echo "  backup    : Create project backup"
	@echo "  help      : Show this help message"