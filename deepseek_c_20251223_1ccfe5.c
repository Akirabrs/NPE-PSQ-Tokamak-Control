#include "npe_config.h"
#include <stdlib.h>
#include <stdio.h>
#include <complex.h>

#define MU0 (4.0e-7 * M_PI)
#define ELECTRON_CHARGE 1.602e-19
#define ELECTRON_MASS 9.109e-31
#define PROTON_MASS 1.673e-27

float grad_shafranov_solution(float R, float Z, float *params) {
    float a = TOKAMAK_MINOR_RADIUS;
    float R0 = TOKAMAK_MAJOR_RADIUS;
    float r = sqrtf((R - R0)*(R - R0) + Z*Z) / a;
    if (r >= 1.0f) return 0.0f;
    float psi = params[0] * (1.0f - r*r);
    return psi;
}

float safety_factor_profile(float r_normalized, PlasmaState *state) {
    float R0 = TOKAMAK_MAJOR_RADIUS;
    float B_toroidal = TOKAMAK_TOROIDAL_FIELD;
    float I_p = state->plasma_current * 1e6;
    float q = (2.0f * M_PI * B_toroidal * r_normalized * r_normalized *
              TOKAMAK_MINOR_RADIUS * TOKAMAK_MINOR_RADIUS) /
              (MU0 * R0 * I_p);
    q *= (1.0f + 0.5f * r_normalized * r_normalized);
    return q;
}

float calculate_beta(PlasmaState *state) {
    float pressure_avg = (state->density_core * 1e19 * state->temperature_core *
                        1.602e-16) / 3.0f;
    float B_total = sqrtf(TOKAMAK_TOROIDAL_FIELD * TOKAMAK_TOROIDAL_FIELD +
                         powf(MU0 * state->plasma_current * 1e6 /
                         (2.0f * M_PI * TOKAMAK_MINOR_RADIUS), 2));
    float beta = 2.0f * MU0 * pressure_avg / (B_total * B_total);
    return beta;
}

float calculate_beta_normalized(PlasmaState *state) {
    float beta = calculate_beta(state) * 100.0f;
    float beta_N = beta * TOKAMAK_MINOR_RADIUS * TOKAMAK_TOROIDAL_FIELD /
                   state->plasma_current;
    return beta_N;
}

float ntm_island_growth(float w, float w_sat, float delta_prime,
                       float alpha, float beta, float dt) {
    float growth_rate = delta_prime * w +
                       alpha * w / (1.0f + w*w*w) -
                       beta * w;
    float saturation = 1.0f / (1.0f + expf(10.0f * (w - w_sat)));
    return w + dt * growth_rate * saturation;
}

float elm_cycle_model(float time, float pedestal_pressure,
                     float pedestal_current, float *params) {
    float frequency = 0.1f * sqrtf(pedestal_pressure / pedestal_current);
    float amplitude = 0.05f + 0.1f * sinf(2.0f * M_PI * frequency * time);
    return amplitude;
}

float thermal_quench_model(float time_since_onset, float initial_energy,
                          float impurity_concentration) {
    float tau_TQ = 0.001f;
    float energy_loss = initial_energy * expf(-time_since_onset / tau_TQ);
    energy_loss *= (1.0f - 0.5f * impurity_concentration);
    return energy_loss;
}

float current_quench_model(float time_since_TQ, float initial_current,
                          float plasma_resistance) {
    float tau_CQ = 0.01f;
    float current = initial_current * expf(-time_since_TQ / tau_CQ);
    current *= (1.0f - 0.1f * plasma_resistance * time_since_TQ);
    return current;
}

float calculate_disruption_forces(PlasmaState *state, float *coil_currents) {
    float dIp_dt = -state->plasma_current / 0.01f;
    float B_coil = 0.0f;
    for (int i = 0; i < NUM_PF_COILS; i++) {
        B_coil += coil_currents[i] * 1e-6f /
                 (2.0f * M_PI * TOKAMAK_MAJOR_RADIUS);
    }
    float lorentz_force = dIp_dt * B_coil * TOKAMAK_MINOR_RADIUS;
    float B_total = sqrtf(TOKAMAK_TOROIDAL_FIELD * TOKAMAK_TOROIDAL_FIELD +
                         (MU0 * state->plasma_current * 1e6) /
                         (2.0f * M_PI * TOKAMAK_MINOR_RADIUS));
    float magnetic_pressure = B_total * B_total / (2.0f * MU0);
    float force_total = lorentz_force + magnetic_pressure * TOKAMAK_MINOR_RADIUS;
    return force_total;
}

float ecrh_heating_model(float power, float frequency,
                        PlasmaState *state, float *deposition_profile) {
    float f_ce = ELECTRON_CHARGE * TOKAMAK_TOROIDAL_FIELD /
                (2.0f * M_PI * ELECTRON_MASS);
    float absorption = 0.0f;
    if (fabsf(frequency - f_ce) < 1e9) {
        absorption = 0.8f;
    } else {
        absorption = 0.3f * expf(-powf(frequency - f_ce, 2) / (2.0f * 1e18f));
    }
    float power_deposited = power * absorption;
    for (int i = 0; i < 10; i++) {
        float r = i / 10.0f;
        deposition_profile[i] = expf(-powf(r - 0.5f, 2) / 0.1f);
    }
    float delta_T = power_deposited / (state->density_core * 1e19 *
                   ELECTRON_CHARGE * 1000.0f);
    return delta_T;
}

float energy_confinement_time(PlasmaState *state, float heating_power) {
    float Ip = state->plasma_current;
    float Bt = TOKAMAK_TOROIDAL_FIELD;
    float n = state->density_core * 0.1f;
    float R = TOKAMAK_MAJOR_RADIUS;
    float a = TOKAMAK_MINOR_RADIUS;
    float kappa = state->elongation;
    float tau_E = 0.0562f * powf(Ip, 0.93f) * powf(Bt, 0.15f) *
                 powf(n, 0.41f) * powf(R, 1.97f) *
                 powf(a, 0.58f) * powf(kappa, 0.78f);
    tau_E *= powf(heating_power, -0.69f);
    return tau_E;
}

void advance_plasma_state(PlasmaState *state, PlasmaControlSystem *control,
                         float dt) {
    // Current evolution
    float Lp = 5.0e-7f;
    float Rp = 1.0e-6f;
    float V_loop = control->pf_coil_currents[0] * 0.1f;
    float dIp_dt = (V_loop - Rp * state->plasma_current * 1e6) / Lp;
    state->plasma_current += dIp_dt * dt / 1e6;
    
    // Energy balance
    float P_heating = 0.0f;
    for (int i = 0; i < NUM_HEATING_SYSTEMS; i++) {
        if (control->heating_systems[i].enabled) {
            P_heating += control->heating_systems[i].power;
        }
    }
    float P_loss = state->stored_energy / control->energy_confinement_time;
    float dW_dt = P_heating - P_loss;
    state->stored_energy += dW_dt * dt;
    
    float plasma_volume = 2.0f * M_PI * M_PI * TOKAMAK_MAJOR_RADIUS *
                         TOKAMAK_MINOR_RADIUS * TOKAMAK_MINOR_RADIUS *
                         state->elongation;
    state->temperature_core = state->stored_energy * 1e6 /
                            (1.5f * state->density_core * 1e19 *
                            plasma_volume * ELECTRON_CHARGE * 1000.0f);
    
    // Density evolution
    float S_in = control->fuel_injection_rate;
    float tau_p = 10.0f;
    float S_out = state->density_core * 1e19 * plasma_volume / tau_p;
    float dn_dt = (S_in - S_out) / plasma_volume;
    state->density_core += dn_dt * dt / 1e19;
    
    // Position evolution
    float mass_plasma = state->density_core * 1e19 * plasma_volume *
                       (PROTON_MASS + ELECTRON_MASS);
    float F_vertical = 0.0f;
    for (int i = 0; i < NUM_VERTICAL_COILS; i++) {
        F_vertical += control->vertical_coil_currents[i] *
                     state->plasma_current * 0.1f;
    }
    float damping = 0.1f;
    float dVz_dt = (F_vertical - damping * state->vertical_position) / mass_plasma;
    state->vertical_position += state->vertical_position * dt + 0.5f * dVz_dt * dt * dt;
    
    // Stability updates
    state->safety_factor_q95 = safety_factor_profile(0.95f, state);
    state->beta_normalized = calculate_beta_normalized(state);
    state->mhd_activity_level = 0.1f * sinf(control->simulation_time * 100.0f) +
                               0.05f * ((float)rand() / RAND_MAX);
    
    // Disruption conditions
    if (state->safety_factor_q95 < SAFETY_FACTOR_Q95_MIN) {
        state->mhd_activity_level += 0.5f;
    }
    if (state->beta_normalized > BETA_NORMAL_LIMIT) {
        state->mhd_activity_level += 0.3f;
    }
    if (fabsf(state->vertical_position) > VERTICAL_DISPLACEMENT_MAX) {
        state->mhd_activity_level += 0.7f;
    }
}