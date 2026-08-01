#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InstrumentRegistry: Loads hardware safety bounds from a YAML config file.
Swap config/instrument_autoscript.yaml to target a different TEM instrument.
"""

import os
import yaml


class InstrumentRegistry:
    """
    Loads and exposes instrument-specific safety limits from a YAML config file.
    Provides get_limit(key) to retrieve named safety parameters.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "instrument_autoscript.yaml"
            )
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"InstrumentRegistry config not found at: {config_path}"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.instrument_name = data.get("instrument", "unknown")
        self.description = data.get("description", "")
        self._limits = data.get("limits", {})

    def get_limit(self, key: str):
        """
        Return the safety limit value for a named key.
        Raises KeyError if the limit is not defined in the config.
        """
        if key not in self._limits:
            raise KeyError(
                f"Safety limit '{key}' is not defined in the InstrumentRegistry "
                f"for instrument '{self.instrument_name}'."
            )
        return self._limits[key]

    def all_limits(self) -> dict:
        """Return all limits as a dictionary."""
        return dict(self._limits)
