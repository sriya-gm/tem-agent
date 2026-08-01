#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflows module - Policy-Driven Edition.
Implements the decision-making policies for high-resolution imaging and tomography.
Instead of sequential scripts, these functions act as state-policy mappings that analyze
microscope state and image feedback to determine the next logical action.
This module is dependency-free.
"""

import math
from typing import Tuple, List, Dict, Any
import autoscript_interface as mi

def cross_correlate(im0: mi.AutoScriptImageAdapter, im1: mi.AutoScriptImageAdapter) -> Tuple[float, float]:
    """
    Computes the displacement shift of the target feature between a reference
    image (im0) and a current image (im1).
    
    Returns:
        dX, dY (float, float): The physical offset in meters.
    """
    dX = im1.offset_x - im0.offset_x
    dY = im1.offset_y - im0.offset_y
    return dX, dY

def high_res_imaging_policy(state: dict, current_image: mi.AutoScriptImageAdapter, 
                            target_mag: int, acquired_final: bool,
                            autofocus_done: bool = False) -> Tuple[str, Dict[str, Any]]:
    """
    Evaluates state and image feedback to choose the next action for high-resolution imaging.
    
    Returns:
        action_name (str), action_args (dict)
    """
    # 1. Goal already achieved?
    if acquired_final:
        return 'finish', {}

    # 2. Safety/valves check
    if state['beam_blanked'] or not state['column_valve_open']:
        return 'ensure_beam_on', {}

    # 3. Magnification check
    if abs(state['magnification'] - target_mag) > 0.05 * target_mag:
        return 'set_magnification', {'magnification': target_mag}

    # 4. Focus check (Threshold: 0.90 quality)
    if current_image.quality < 0.90 and not autofocus_done:
        return 'autofocus', {'reason': f"Image quality too low ({current_image.quality:.4f} < 0.90)"}

    # 5. Drift alignment check (Threshold: 1.0 nm drift)
    # At high resolution, we align the feature to the optical center (0.0, 0.0)
    drift = math.sqrt(current_image.offset_x**2 + current_image.offset_y**2)
    if drift > 1e-9:
        return 'align_stage', {
            'dX': current_image.offset_x, 
            'dY': current_image.offset_y,
            'reason': f"Lateral drift detected ({drift*1e9:.1f} nm > 1.0 nm)"
        }

    # 6. All conditions met: acquire the science image
    return 'acquire_final_image', {}

def tomography_policy(state: dict, current_image: mi.AutoScriptImageAdapter,
                      target_angles: List[float], completed_angles: List[float],
                      reference_template: mi.AutoScriptImageAdapter,
                      autofocused_angles: List[float] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Evaluates state and image feedback to choose the next action for a tomography tilt series.
    
    Returns:
        action_name (str), action_args (dict)
    """
    # 1. Goal already achieved?
    if len(completed_angles) >= len(target_angles):
        return 'finish', {}

    # 2. Safety/valves check
    if state['beam_blanked'] or not state['column_valve_open']:
        return 'ensure_beam_on', {}

    # 3. Check if we have a template for drift tracking.
    # We must acquire this reference at the starting position before tilting.
    if reference_template is None:
        return 'acquire_reference_template', {}

    # Find the next angle we need to acquire
    next_angle = None
    for angle in target_angles:
        if angle not in completed_angles:
            next_angle = angle
            break

    # 4. Check stage tilt angle
    current_tilt = state['stage_position']['A']
    if abs(current_tilt - next_angle) > 0.01:
        return 'tilt_stage', {'target_angle': next_angle}

    # 5. Focus check (Threshold: 0.90 quality)
    if autofocused_angles is None:
        autofocused_angles = []
    if current_image.quality < 0.90 and next_angle not in autofocused_angles:
        return 'autofocus', {'reason': f"Image quality too low ({current_image.quality:.4f} < 0.90) at tilt {next_angle}°"}

    # 6. Drift alignment check (Threshold: 2.0 nm drift relative to starting reference template)
    # We compute drift relative to the starting reference image to keep the same feature centered.
    dX, dY = cross_correlate(reference_template, current_image)
    drift = math.sqrt(dX**2 + dY**2)
    if drift > 2e-9:
        return 'align_stage', {
            'dX': dX, 
            'dY': dY,
            'reason': f"Stage drift relative to template detected ({drift*1e9:.1f} nm > 2.0 nm)"
        }

    # 7. Focused, aligned, and at the correct tilt: acquire projection data
    return 'acquire_projection_image', {'angle': next_angle}

def optimize_focus_sweep(dwell: float = 2e-6, steps: int = 7) -> float:
    """
    Helper workflow to perform a software-driven autofocus sweep.
    """
    state = mi.get_microscope_state()
    center_df = state['defocus_m']
    sweep_range = 300e-9
    
    start_df = center_df - (sweep_range / 2)
    end_df = center_df + (sweep_range / 2)
    
    defocus_values = []
    step_size = sweep_range / (steps - 1)
    for i in range(steps):
        defocus_values.append(start_df + i * step_size)
        
    quality_scores = []
    
    print(f"[Autofocus Workflow] Sweeping focus from {start_df*1e9:.1f}nm to {end_df*1e9:.1f}nm...")
    
    for df in defocus_values:
        mi.set_defocus(df)
        img, _ = mi.acquire_image(dwell=dwell)
        score = mi.evaluate_image_quality(img)
        quality_scores.append(score)
        
    # Quadratic interpolation peak-find
    max_score = -1.0
    max_idx = -1
    for i, s in enumerate(quality_scores):
        if s > max_score:
            max_score = s
            max_idx = i
            
    if 0 < max_idx < steps - 1:
        d_prev, s_prev = defocus_values[max_idx - 1], quality_scores[max_idx - 1]
        d_curr, s_curr = defocus_values[max_idx], quality_scores[max_idx]
        d_next, s_next = defocus_values[max_idx + 1], quality_scores[max_idx + 1]
        
        denom = s_prev - 2.0 * s_curr + s_next
        if abs(denom) > 1e-12:
            optimal_df = d_curr - 0.5 * ((s_next - s_prev) * step_size) / denom
        else:
            optimal_df = d_curr
    else:
        optimal_df = defocus_values[max_idx]
        
    mi.set_defocus(optimal_df)
    print(f"[Autofocus Workflow] Focus optimized. Best defocus: {optimal_df*1e9:.1f} nm")
    return optimal_df
