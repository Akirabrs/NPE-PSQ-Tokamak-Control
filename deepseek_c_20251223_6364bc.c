#ifndef NPE_CONFIG_H
#define NPE_CONFIG_H

#include <stdint.h>
#include <stdbool.h>
#include <math.h>

// ================= TOKAMAK PARAMETERS =================
#define TOKAMAK_MAJOR_RADIUS 1.8f
#define TOKAMAK_MINOR_RADIUS 0.6f
#define TOKAMAK_TOROIDAL_FIELD 5.3f
#define TOKAMAK_PLASMA_CURRENT 15.0f

// ================= PLASMA PARAMETERS =================
#define PLASMA_TEMPERATURE_CORE 15.0f
#define PLASMA_DENSITY_CORE 1.0e20f
#define PLASMA_BETA_TARGET 0.03f
#define PLASMA_LI_TARGET 1.0f

// ================= STABILITY PARAMETERS =================
#define SAFETY_FACTOR_Q95_MIN 3.0f
#define SAFETY_FACTOR_Q95_MAX 5.0f
#define BETA_NORMAL_LIMIT 3.5f
#define LOWER_HYBRID_LIMIT 0.8f

// ================= CONTROL PARAMETERS =================
#define NUM_PF_COILS 10
#define NUM_VERTICAL_COILS 4
#define NUM_HORIZONTAL_COILS 4
#define NUM_HEATING_SYSTEMS 3

// ================= SAFETY LIMITS =================
#define DISRUPTION_CURRENT_RAMP 3.0f
#define VERTICAL_DISPLACEMENT_MAX 0.15f
#define RADIATION_PEAK_LIMIT 10.0f
#define WALL_LOAD_LIMIT 1.0f

// ================= CHARACTERISTIC TIMES =================
#define PLASMA_CURRENT_RISE_TIME 30.0f
#define ENERGY_CONFINEMENT_TIME 5.0f
#define DISRUPTION_WARNING_TIME 0.05f
#define MITIGATION_RESPONSE_TIME 0.01f

// ================= DATA STRUCTURES =================
typedef struct {
    float plasma_current;
    float safety_factor_q95;
    float beta_normalized;
    float li_inductance;
    float radial_position;
    float vertical_position;
    float elongation;
    float triangularity;
    float temperature_core;
    float temperature_edge;
    float density_core;
    float density_edge;
    float mhd_activity_level;
    float ntm_amplitude;
    float elm_frequency;
    float neutron_rate;
    float impurity_concentration;
    float radiation_power;
} PlasmaState;

typedef struct {
    PlasmaState current_state;
    PlasmaState target_state;
    float pf_coil_currents[NUM_PF_COILS];
    float vertical_coil_currents[NUM_VERTICAL_COILS];
    float horizontal_coil_currents[NUM_HORIZONTAL_COILS];
    
    struct {
        float power;
        float frequency;
        bool enabled;
    } heating_systems[NUM_HEATING_SYSTEMS];
    
    float fuel_injection_rate;
    float impurity_injection_rate;
    
    enum {
        PSQ_STATE_INIT,
        PSQ_STATE_RAMP_UP,
        PSQ_STATE_FLAT_TOP,
        PSQ_STATE_RAMP_DOWN,
        PSQ_STATE_DISRUPTION,
        PSQ_STATE_MITIGATION,
        PSQ_STATE_SAFE_SHUTDOWN
    } controller_state;
    
    float simulation_time;
    uint32_t iteration_count;
    float state_history[1000][10];
    bool disruption_detected;
    bool mitigation_activated;
    float disruption_warning_time;
    float energy_confinement_time;
    float fusion_gain_Q;
    float stored_energy;
} PlasmaControlSystem;

typedef struct {
    float interferometer_density[32];
    float thomson_scattering_temp[20];
    float bolometer_channels[48];
    float magnetics_probes[64];
    float soft_xray_array[64];
    float neutron_cameras[8];
    float spectroscopy_lines[16];
    float mhd_spectrum[1024];
    float coherence_analysis[32][32];
    bool system_ok;
    float data_acquisition_rate;
} DiagnosticsSystem;

typedef struct {
    struct {
        bool locked_mode_detected;
        bool vertical_displacement_event;
        bool density_limit_exceeded;
        bool beta_limit_exceeded;
        bool current_quench_detected;
        bool thermal_quench_detected;
    } disruption_flags;
    
    struct {
        bool massive_gas_injection_ready;
        bool pellet_injection_ready;
        bool killer_pulse_ready;
        bool runaway_electron_mitigation;
    } mitigation_systems;
    
    float gas_injection_valve_position;
    float pellet_injection_rate;
    float killer_pulse_amplitude;
    uint32_t disruption_count;
    uint32_t mitigation_success_count;
    float last_disruption_time;
} SafetyMitigationSystem;

// Types for plasma_safety.c
typedef struct {
    float disruption_probability;
    float time_to_disruption;
    char most_likely_cause[64];
} DisruptionPrediction;

typedef enum {
    MITIGATION_NONE,
    MITIGATION_MGI,
    MITIGATION_PELLET,
    MITIGATION_KILLERPULSE,
    MITIGATION_MGI_KILLERPULSE,
    MITIGATION_CONTROL_ADJUST
} MitigationAction;

typedef struct {
    MitigationAction action;
    float urgency;
    char control_adjustment[128];
} MitigationDecision;

#endif // NPE_CONFIG_H