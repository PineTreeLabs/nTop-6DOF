"""
Geometry parser for nTop-exported wing and tail surfaces.

This module reads LE/TE point data from CSV files and computes
geometric properties for AVL input generation.

Units: Assumes input in inches, converts to feet for AVL
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict
from dataclasses import dataclass


@dataclass
class WingGeometry:
    """Container for wing geometric properties."""
    le_points: np.ndarray  # Leading edge points (N x 3) in feet
    te_points: np.ndarray  # Trailing edge points (N x 3) in feet
    span: float            # Total span in feet
    area: float            # Planform area in ft^2
    mac: float             # Mean aerodynamic chord in feet
    taper_ratio: float     # Tip chord / root chord
    aspect_ratio: float    # b^2 / S
    sweep_le: float        # Leading edge sweep angle in degrees
    sweep_c4: float        # Quarter-chord sweep angle in degrees
    root_chord: float      # Root chord in feet
    tip_chord: float       # Tip chord in feet
    mac_y: float           # Spanwise location of MAC in feet
    mac_le_x: float        # X-location of MAC leading edge in feet
    dihedral: float        # Dihedral angle in degrees


def read_csv_points(filepath: str, units: str = 'inches') -> np.ndarray:
    """
    Read LE or TE points from CSV file.

    Parameters:
    -----------
    filepath : str
        Path to CSV file with x,y,z columns
    units : str
        Input units ('inches' or 'feet')

    Returns:
    --------
    points : np.ndarray
        (N x 3) array of points in feet
    """
    df = pd.read_csv(filepath)
    points = df[['x', 'y', 'z']].values

    # Convert to feet if needed
    if units.lower() == 'inches':
        points = points / 12.0

    return points


def compute_wing_geometry(le_points: np.ndarray, te_points: np.ndarray) -> WingGeometry:
    """
    Compute wing geometric properties from LE/TE points.

    Parameters:
    -----------
    le_points : np.ndarray
        Leading edge points (N x 3) in feet
    te_points : np.ndarray
        Trailing edge points (N x 3) in feet

    Returns:
    --------
    geom : WingGeometry
        Container with all geometric properties
    """

    # Sort by spanwise position (y-coordinate)
    le_sorted = le_points[np.argsort(le_points[:, 1])]
    te_sorted = te_points[np.argsort(te_points[:, 1])]

    # Extract coordinates
    y_stations = le_sorted[:, 1]
    le_x = le_sorted[:, 0]
    le_z = le_sorted[:, 2]
    te_x = te_sorted[:, 0]
    te_z = te_sorted[:, 2]

    # Compute local chord at each station
    chords = te_x - le_x

    # Span (tip to tip)
    span = y_stations[-1] - y_stations[0]

    # Root and tip chords
    root_idx = np.argmin(np.abs(y_stations))
    root_chord = chords[root_idx]
    tip_chord = (chords[0] + chords[-1]) / 2.0  # Average both tips

    # Taper ratio
    taper_ratio = tip_chord / root_chord

    # Planform area (use full span integration)
    area = np.trapezoid(chords, y_stations)

    # Mean aerodynamic chord (MAC) and its location
    # MAC = (2/S) * integral(c^2 * dy)
    mac = (2.0 / area) * np.trapezoid(chords**2, y_stations)

    # MAC spanwise location: y_mac = (2/S) * integral(c * y * dy)
    mac_y = (2.0 / area) * np.trapezoid(chords * y_stations, y_stations)

    # MAC leading edge x-location (interpolate)
    mac_le_x = np.interp(mac_y, y_stations, le_x)

    # Aspect ratio
    aspect_ratio = span**2 / area

    # Leading edge sweep angle (using right half-span)
    half_span_idx = np.where(y_stations >= 0)[0]
    y_half = y_stations[half_span_idx]
    le_x_half = le_x[half_span_idx]

    if len(y_half) > 1:
        le_sweep_fit = np.polyfit(y_half, le_x_half, 1)
        sweep_le = np.degrees(np.arctan(le_sweep_fit[0]))
    else:
        sweep_le = 0.0

    # Quarter-chord sweep angle
    x_c4 = le_x + 0.25 * chords
    x_c4_half = x_c4[half_span_idx]

    if len(y_half) > 1:
        c4_sweep_fit = np.polyfit(y_half, x_c4_half, 1)
        sweep_c4 = np.degrees(np.arctan(c4_sweep_fit[0]))
    else:
        sweep_c4 = 0.0

    # Dihedral angle (from z vs y on right half-span)
    le_z_half = le_z[half_span_idx]

    if len(y_half) > 1:
        dihedral_fit = np.polyfit(y_half, le_z_half, 1)
        dihedral = np.degrees(np.arctan(dihedral_fit[0]))
    else:
        dihedral = 0.0

    return WingGeometry(
        le_points=le_sorted,
        te_points=te_sorted,
        span=span,
        area=area,
        mac=mac,
        taper_ratio=taper_ratio,
        aspect_ratio=aspect_ratio,
        sweep_le=sweep_le,
        sweep_c4=sweep_c4,
        root_chord=root_chord,
        tip_chord=tip_chord,
        mac_y=mac_y,
        mac_le_x=mac_le_x,
        dihedral=dihedral
    )


def estimate_tail_geometry(wing: WingGeometry,
                          v_h: float = 0.6,
                          v_v: float = 0.05,
                          tail_arm_factor: float = 2.5) -> Tuple[Dict, Dict]:
    """
    Estimate horizontal and vertical tail geometry using volume coefficients.

    Parameters:
    -----------
    wing : WingGeometry
        Wing geometric properties
    v_h : float
        Horizontal tail volume coefficient (typical: 0.5-0.7)
    v_v : float
        Vertical tail volume coefficient (typical: 0.04-0.06)
    tail_arm_factor : float
        Tail moment arm as multiple of wing MAC

    Returns:
    --------
    h_tail : dict
        Horizontal tail geometry (area, span, chord, etc.)
    v_tail : dict
        Vertical tail geometry (area, span, chord, etc.)
    """

    # Tail moment arms
    l_h = tail_arm_factor * wing.mac
    l_v = tail_arm_factor * wing.mac

    # Horizontal tail area: S_h = (V_h * S * MAC) / l_h
    s_h = (v_h * wing.area * wing.mac) / l_h

    # Assume horizontal tail aspect ratio similar to wing (scaled down)
    ar_h = wing.aspect_ratio * 0.8
    b_h = np.sqrt(s_h * ar_h)
    c_h = s_h / b_h

    # Vertical tail area: S_v = (V_v * S * b) / l_v
    s_v = (v_v * wing.area * wing.span) / l_v

    # Assume vertical tail aspect ratio (height/chord)
    ar_v = 1.5
    h_v = np.sqrt(s_v * ar_v)
    c_v = s_v / h_v

    # Horizontal tail position - start at root trailing edge
    # Find root chord trailing edge location
    root_idx = np.argmin(np.abs(wing.le_points[:, 1]))
    root_te_x = wing.te_points[root_idx, 0]

    x_h = root_te_x  # Tail starts at root TE

    # Vertical tail position - same as horizontal
    x_v = root_te_x

    h_tail = {
        'area': s_h,
        'span': b_h,
        'chord': c_h,
        'aspect_ratio': ar_h,
        'taper_ratio': 0.8,  # Assume slight taper
        'sweep_c4': 0.0,     # Assume no sweep
        'x_position': x_h,
        'y_position': 0.0,
        'z_position': 0.0,   # Assume on centerline
        'moment_arm': l_h
    }

    v_tail = {
        'area': s_v,
        'height': h_v,
        'chord': c_v,
        'aspect_ratio': ar_v,
        'taper_ratio': 0.7,  # Assume taper
        'sweep_c4': 5.0,     # Slight sweep for stability
        'x_position': x_v,
        'y_position': 0.0,
        'z_position': 0.0,
        'moment_arm': l_v
    }

    return h_tail, v_tail


def print_geometry_summary(wing: WingGeometry, h_tail: Dict = None, v_tail: Dict = None):
    """Print formatted summary of geometric properties."""

    print("=" * 60)
    print("WING GEOMETRY SUMMARY")
    print("=" * 60)
    print(f"Span:              {wing.span:8.3f} ft")
    print(f"Area:              {wing.area:8.3f} ft^2")
    print(f"Mean Aero Chord:   {wing.mac:8.3f} ft")
    print(f"Root Chord:        {wing.root_chord:8.3f} ft")
    print(f"Tip Chord:         {wing.tip_chord:8.3f} ft")
    print(f"Taper Ratio:       {wing.taper_ratio:8.3f}")
    print(f"Aspect Ratio:      {wing.aspect_ratio:8.3f}")
    print(f"LE Sweep:          {wing.sweep_le:8.2f} deg")
    print(f"c/4 Sweep:         {wing.sweep_c4:8.2f} deg")
    print(f"Dihedral:          {wing.dihedral:8.2f} deg")
    print(f"MAC Y-location:    {wing.mac_y:8.3f} ft")
    print(f"MAC LE X-location: {wing.mac_le_x:8.3f} ft")

    if h_tail:
        print("\n" + "=" * 60)
        print("HORIZONTAL TAIL GEOMETRY (ESTIMATED)")
        print("=" * 60)
        print(f"Area:              {h_tail['area']:8.3f} ft^2")
        print(f"Span:              {h_tail['span']:8.3f} ft")
        print(f"Chord:             {h_tail['chord']:8.3f} ft")
        print(f"Aspect Ratio:      {h_tail['aspect_ratio']:8.3f}")
        print(f"Taper Ratio:       {h_tail['taper_ratio']:8.3f}")
        print(f"X Position:        {h_tail['x_position']:8.3f} ft")
        print(f"Moment Arm:        {h_tail['moment_arm']:8.3f} ft")

    if v_tail:
        print("\n" + "=" * 60)
        print("VERTICAL TAIL GEOMETRY (ESTIMATED)")
        print("=" * 60)
        print(f"Area:              {v_tail['area']:8.3f} ft^2")
        print(f"Height:            {v_tail['height']:8.3f} ft")
        print(f"Chord:             {v_tail['chord']:8.3f} ft")
        print(f"Aspect Ratio:      {v_tail['aspect_ratio']:8.3f}")
        print(f"Taper Ratio:       {v_tail['taper_ratio']:8.3f}")
        print(f"X Position:        {v_tail['x_position']:8.3f} ft")
        print(f"Moment Arm:        {v_tail['moment_arm']:8.3f} ft")

    print("=" * 60)


if __name__ == "__main__":
    # Test with current geometry
    import os

    base_path = r"C:\Users\bradrothenberg\OneDrive - nTop\OUT\parts\nTopAVL\nTop6DOF\Data"
    le_file = os.path.join(base_path, "LEpts.csv")
    te_file = os.path.join(base_path, "TEpts.csv")

    le_points = read_csv_points(le_file, units='inches')
    te_points = read_csv_points(te_file, units='inches')

    wing = compute_wing_geometry(le_points, te_points)
    h_tail, v_tail = estimate_tail_geometry(wing)

    print_geometry_summary(wing, h_tail, v_tail)
