# CC0 1.0 Universal Public Domain Dedication
# This work is dedicated to the public domain under CC0 1.0.
# https://creativecommons.org/publicdomain/zero/1.0/
# No rights reserved. Free for any use, forever.

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class SensorData:
    joint_temp_K: float
    quench_margin_K: float
    flibe_flow_mult: float
    sweep_freq_hz: float
    q_factor: float
    tbr: float
    divertor_flux_mw_m2: float

class FusionControlKernel:
    def __init__(self):
        self.stability_window = {
            "flibe_flow_mult_min": 1.15,
            "flibe_flow_mult_max": 1.25,
            "sweep_freq_hz": 1.2,
            "sweep_tolerance": 0.1,
            "q_target_min": 14.8,
            "tbr_target_min": 1.25,
            "quench_margin_min": 7.5
        }
        self.state = {"joint_temp_K": 20.0, "quench_margin_K": 8.0,
                      "flibe_flow_mult": 1.0, "sweep_freq_hz": 1.0,
                      "q_factor": 0.0, "tbr": 0.8, "divertor_flux": 10.0}
        self.time = 0.0
        self.dt = 0.1

    def _update_surrogates(self):
        self.state["joint_temp_K"] += 0.002 * (self.state["flibe_flow_mult"] - 1.2) * self.dt
        q_boost = 0.8 * (self.state["flibe_flow_mult"] - 1.2) * (1.2 - abs(self.state["sweep_freq_hz"] - 1.2))
        self.state["q_factor"] = max(0.0, self.state["q_factor"] + q_boost * self.dt * 5.0)
        self.state["tbr"] = min(1.3, self.state["tbr"] + 0.008 * (self.state["flibe_flow_mult"] - 1.1) * self.dt)
        self.state["divertor_flux"] = max(5.0, 12.0 - 4.0 * abs(self.state["sweep_freq_hz"] - 1.2))
        self.state["quench_margin_K"] = max(0.0, 28.0 - self.state["joint_temp_K"])
        self.time += self.dt

    def _is_in_stability_window(self) -> bool:
        return (self.stability_window["flibe_flow_mult_min"] <= self.state["flibe_flow_mult"] <= self.stability_window["flibe_flow_mult_max"] and
                abs(self.state["sweep_freq_hz"] - self.stability_window["sweep_freq_hz"]) <= self.stability_window["sweep_tolerance"] and
                self.state["q_factor"] >= self.stability_window["q_target_min"] and
                self.state["tbr"] >= self.stability_window["tbr_target_min"] and
                self.state["quench_margin_K"] >= self.stability_window["quench_margin_min"])

    def get_optimal_action(self) -> Dict:
        return {
            "flibe_flow_adjust": 1.20 - self.state["flibe_flow_mult"],
            "sweep_adjust": 1.2 - self.state["sweep_freq_hz"]
        }

    def _apply_control_action(self, action: Dict):
        self.state["flibe_flow_mult"] += action["flibe_flow_adjust"] * 0.4
        self.state["sweep_freq_hz"] += action["sweep_adjust"] * 0.4
        self.state["flibe_flow_mult"] = np.clip(self.state["flibe_flow_mult"], 1.0, 1.3)
        self.state["sweep_freq_hz"] = np.clip(self.state["sweep_freq_hz"], 0.5, 2.0)

    def run_control_loop(self, steps: int = 300):
        history = {"time": [], "joint_temp": [], "q_factor": [], "tbr": [], "in_window": []}
        for _ in range(steps):
            in_window = self._is_in_stability_window()
            if not in_window:
                action = self.get_optimal_action()
                self._apply_control_action(action)
            self._update_surrogates()
            history["time"].append(self.time)
            history["joint_temp"].append(self.state["joint_temp_K"])
            history["q_factor"].append(self.state["q_factor"])
            history["tbr"].append(self.state["tbr"])
            history["in_window"].append(in_window)
        return history, self._is_in_stability_window()

# ====================== RUN IT ======================
if __name__ == "__main__":
    kernel = FusionControlKernel()
    history, final_stable = kernel.run_control_loop(steps=300)
    print("INSIDE Global Harmony Window ✅" if final_stable else "Outside")
