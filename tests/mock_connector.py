#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MockTEMConnector: A fully in-memory fake connector for dry-run policy tests.
Mirrors the AutoScriptConnector interface exactly so TEMCapabilities
works without any network connection.
"""


class _MockImage:
    """Minimal image object that mimics the AutoScript image pixel_data attribute."""
    def __init__(self):
        import numpy as np
        # Return a realistic-looking static image array
        rng = np.random.default_rng(42)
        self.pixel_data = rng.normal(loc=22000, scale=11000, size=(512, 512)).clip(0, 65535)


class MockTEMConnector:
    """
    Fake TEM connector for dry-run / unit tests.
    All state is kept in memory; no network or hardware interaction.
    """

    def __init__(self):
        self._state = {
            "defocus_m": -150e-9,
            "magnification": 8600,
            "voltage_kv": 300.0,
            "beam_blanked": True,
            "column_valve_open": False,
            "detector": {"type": "BM-Ceta"},
            "stage_position": {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0},
        }
        self._detector_config = {
            "detector_type": "BM-Ceta",
            "dwell_time": 1.0,
            "image_shape": (512, 512)
        }

    def connect(self):
        print("[MockConnector] Connected (mock).")

    def disconnect(self):
        print("[MockConnector] Disconnected (mock).")

    def get_microscope_state(self) -> dict:
        return dict(self._state)

    def set_defocus(self, target_df: float):
        self._state["defocus_m"] = target_df

    def acquire_image(self):
        return _MockImage(), 1e-10  # pixel_size placeholder

    def set_magnification(self, mag: int):
        self._state["magnification"] = mag

    def move_stage(self, dX=0.0, dY=0.0, dZ=0.0, dA=0.0, dB=0.0):
        import math
        sp = self._state["stage_position"]
        sp["X"] += dX
        sp["Y"] += dY
        sp["Z"] += dZ
        sp["A"] += dA
        sp["B"] += dB

    def configure_detector(self, detector_type: str, settings: dict):
        self._detector_config = {"detector_type": detector_type, **settings}
        self._state["detector"] = {"type": detector_type}

    def blank_beam(self):
        self._state["beam_blanked"] = True

    def unblank_beam(self):
        self._state["beam_blanked"] = False

    def open_column_valve(self):
        self._state["column_valve_open"] = True

    def close_column_valve(self):
        self._state["column_valve_open"] = False

    def set_acceleration_voltage(self, voltage_kv: float):
        self._state["voltage_kv"] = voltage_kv
