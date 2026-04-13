#!/usr/bin/env python3
# EPOS GOVERNANCE WATERMARK
"""
epos/rewards/__init__.py — Reward Bus Package
=============================================
Constitutional Authority: EPOS Constitution v3.1
Directive: 20260414-02 (Reward Bus Backwire)

Exports the publish_reward() function for use across all EPOS modules.
Every system feeds the learning pipeline through this interface.
"""

from epos.rewards.publish_reward import publish_reward, get_current_week

__all__ = ["publish_reward", "get_current_week"]
