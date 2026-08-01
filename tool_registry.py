#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ToolRegistry: Loads tool definitions from config/tools.yaml.
Any AI policy can call get_all_tools() to receive the full tool list
without knowing which tools exist at import time.
"""

import os
import yaml


class ToolRegistry:
    """
    Loads and exposes TEM tool definitions from a YAML config file.
    Adding a new tool only requires editing config/tools.yaml.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "tools.yaml"
            )
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"ToolRegistry config not found at: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._tools = data.get("tools", [])

    def get_all_tools(self) -> list:
        """Return the full list of tool definition dicts (Anthropic/OpenAI format)."""
        return list(self._tools)

    def get_tool_names(self) -> set:
        """Return the set of all allowed tool names."""
        return {t["name"] for t in self._tools}

    def get_tool_schema(self, name: str) -> dict:
        """Return the schema dict for a specific tool, or None if not found."""
        for t in self._tools:
            if t["name"] == name:
                return t
        return None
