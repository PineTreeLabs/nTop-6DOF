"""
AVL interface for running analyses and parsing results.
"""

import subprocess
import os
import re
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class AVLResults:
    """Container for AVL analysis results."""
    # Forces and moments
    CL: float
    CD: float
    CM: float
    CY: float
    Cl: float  # Roll moment
    Cn: float  # Yaw moment

    # Control deflections
    alpha: float
    beta: float
    elevator: float = 0.0
    flaperon: float = 0.0
    rudder: float = 0.0

    # Stability derivatives (if available)
    CLa: float = None
    CMa: float = None
    CYb: float = None
    Clb: float = None
    Cnb: float = None

    # Additional info
    e_span_eff: float = None
    neutral_point: float = None


class AVLInterface:
    """
    Interface to AVL executable.

    Handles running AVL, sending commands, and parsing output.
    """

    def __init__(self, avl_exe_path: str):
        """
        Initialize AVL interface.

        Parameters:
        -----------
        avl_exe_path : str
            Path to AVL executable
        """
        self.avl_exe_path = avl_exe_path

        if not os.path.exists(avl_exe_path):
            raise FileNotFoundError(f"AVL executable not found: {avl_exe_path}")

    def run_avl_case(self, avl_file: str, mass_file: str = None,
                    alpha: float = 0.0, beta: float = 0.0,
                    mach: float = 0.0, output_prefix: str = "avl_output") -> AVLResults:
        """
        Run a single AVL analysis case.

        Parameters:
        -----------
        avl_file : str
            Path to .avl geometry file
        mass_file : str
            Path to .mass file (optional)
        alpha : float
            Angle of attack (degrees)
        beta : float
            Sideslip angle (degrees)
        mach : float
            Mach number
        output_prefix : str
            Prefix for output files

        Returns:
        --------
        results : AVLResults
            Analysis results
        """

        # Build command sequence
        commands = []
        commands.append("LOAD")  # Load geometry
        commands.append(avl_file)

        if mass_file and os.path.exists(mass_file):
            commands.append("MASS")  # Load mass file
            commands.append(mass_file)

        commands.append("OPER")  # Enter OPER menu

        # Set operating point
        commands.append("A")  # Set alpha
        commands.append(f"A {alpha}")
        commands.append("")

        commands.append("B")  # Set beta
        commands.append(f"B {beta}")
        commands.append("")

        if mach > 0:
            commands.append("M")  # Set Mach
            commands.append(f"M {mach}")
            commands.append("")

        commands.append("X")  # Execute analysis

        # Save results
        commands.append("FT")  # Write forces to file
        commands.append(f"{output_prefix}.ft")

        commands.append("ST")  # Write stability derivatives
        commands.append(f"{output_prefix}.st")

        commands.append("")  # Return to OPER menu
        commands.append("QUIT")  # Quit AVL

        # Write command file
        cmd_file = f"{output_prefix}_commands.txt"
        with open(cmd_file, 'w') as f:
            f.write("\n".join(commands))

        # Run AVL
        try:
            with open(cmd_file, 'r') as f:
                result = subprocess.run(
                    [self.avl_exe_path],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            # Parse results from output files
            results = self._parse_ft_file(f"{output_prefix}.ft", alpha, beta)

            # Try to parse stability derivatives
            if os.path.exists(f"{output_prefix}.st"):
                stab_derivs = self._parse_st_file(f"{output_prefix}.st")
                results.CLa = stab_derivs.get('CLa')
                results.CMa = stab_derivs.get('CMa')
                results.CYb = stab_derivs.get('CYb')
                results.Clb = stab_derivs.get('Clb')
                results.Cnb = stab_derivs.get('Cnb')
                results.neutral_point = stab_derivs.get('Xnp')

            # Clean up temporary files
            if os.path.exists(cmd_file):
                os.remove(cmd_file)

            return results

        except subprocess.TimeoutExpired:
            raise RuntimeError("AVL execution timed out")
        except Exception as e:
            raise RuntimeError(f"AVL execution failed: {str(e)}")

    def _parse_ft_file(self, ft_file: str, alpha: float, beta: float) -> AVLResults:
        """
        Parse AVL .ft (forces) output file.

        Parameters:
        -----------
        ft_file : str
            Path to .ft file
        alpha, beta : float
            Angles (for record keeping)

        Returns:
        --------
        results : AVLResults
            Parsed results
        """

        if not os.path.exists(ft_file):
            raise FileNotFoundError(f"AVL output file not found: {ft_file}")

        CL = CD = CM = CY = Cl = Cn = 0.0
        e_span_eff = None

        with open(ft_file, 'r') as f:
            content = f.read()

            # Parse force coefficients
            match = re.search(r'CLtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                CL = float(match.group(1))

            match = re.search(r'CDtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                CD = float(match.group(1))

            match = re.search(r'Cmtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                CM = float(match.group(1))

            match = re.search(r'CYtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                CY = float(match.group(1))

            match = re.search(r'Cltot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                Cl = float(match.group(1))

            match = re.search(r'Cntot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                Cn = float(match.group(1))

            match = re.search(r'e\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                e_span_eff = float(match.group(1))

        return AVLResults(
            CL=CL, CD=CD, CM=CM, CY=CY, Cl=Cl, Cn=Cn,
            alpha=alpha, beta=beta,
            e_span_eff=e_span_eff
        )

    def _parse_st_file(self, st_file: str) -> Dict[str, float]:
        """
        Parse AVL .st (stability derivatives) output file.

        Parameters:
        -----------
        st_file : str
            Path to .st file

        Returns:
        --------
        derivs : dict
            Dictionary of stability derivatives
        """

        derivs = {}

        if not os.path.exists(st_file):
            return derivs

        with open(st_file, 'r') as f:
            content = f.read()

            # Common derivatives
            patterns = {
                'CLa': r'CLa\s*=\s*([-+]?\d*\.\d+)',
                'CMa': r'Cma\s*=\s*([-+]?\d*\.\d+)',
                'CYb': r'CYb\s*=\s*([-+]?\d*\.\d+)',
                'Clb': r'Clb\s*=\s*([-+]?\d*\.\d+)',
                'Cnb': r'Cnb\s*=\s*([-+]?\d*\.\d+)',
                'Xnp': r'Xnp\s*=\s*([-+]?\d*\.\d+)'
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    derivs[key] = float(match.group(1))

        return derivs

    def run_alpha_sweep(self, avl_file: str, mass_file: str = None,
                       alpha_range: Tuple[float, float, float] = (-5, 15, 1),
                       beta: float = 0.0, mach: float = 0.0) -> List[AVLResults]:
        """
        Run sweep over angle of attack.

        Parameters:
        -----------
        avl_file : str
            Path to .avl geometry file
        mass_file : str
            Path to .mass file (optional)
        alpha_range : tuple
            (start, stop, step) for alpha sweep in degrees
        beta : float
            Sideslip angle (degrees)
        mach : float
            Mach number

        Returns:
        --------
        results : list of AVLResults
            Results for each alpha
        """

        alphas = np.arange(*alpha_range)
        results = []

        print(f"Running alpha sweep: {alpha_range[0]}° to {alpha_range[1]}° (step {alpha_range[2]}°)")

        for i, alpha in enumerate(alphas):
            print(f"  Alpha = {alpha:6.2f}° ({i+1}/{len(alphas)})", end='\r')

            result = self.run_avl_case(
                avl_file=avl_file,
                mass_file=mass_file,
                alpha=alpha,
                beta=beta,
                mach=mach,
                output_prefix=f"avl_alpha_{alpha:.1f}"
            )

            results.append(result)

        print()  # New line after progress
        return results


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Test AVL interface
    avl_exe = r"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe"
    base_path = r"C:\Users\bradrothenberg\OneDrive - nTop\OUT\parts\nTopAVL\nTop6DOF\avl_files"

    avl_file = os.path.join(base_path, "uav.avl")
    mass_file = os.path.join(base_path, "uav.mass")

    # Create interface
    avl = AVLInterface(avl_exe)

    # Run single case
    print("Running single case at alpha = 2°...")
    result = avl.run_avl_case(avl_file, mass_file, alpha=2.0, beta=0.0, mach=0.25)

    print(f"\nResults:")
    print(f"  CL  = {result.CL:8.5f}")
    print(f"  CD  = {result.CD:8.5f}")
    print(f"  CM  = {result.CM:8.5f}")
    print(f"  L/D = {result.CL/result.CD:8.2f}")

    if result.CLa:
        print(f"  CLa = {result.CLa:8.4f} /rad")
    if result.CMa:
        print(f"  CMa = {result.CMa:8.4f} /rad")

    # Run alpha sweep
    print("\n" + "=" * 60)
    print("Running alpha sweep...")
    results = avl.run_alpha_sweep(avl_file, mass_file, alpha_range=(-5, 15, 1), mach=0.25)

    # Plot results
    alphas = [r.alpha for r in results]
    CLs = [r.CL for r in results]
    CDs = [r.CD for r in results]
    CMs = [r.CM for r in results]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    axes[0, 0].plot(alphas, CLs, 'b.-')
    axes[0, 0].set_xlabel('Alpha (deg)')
    axes[0, 0].set_ylabel('CL')
    axes[0, 0].grid(True)
    axes[0, 0].set_title('Lift Coefficient')

    axes[0, 1].plot(alphas, CDs, 'r.-')
    axes[0, 1].set_xlabel('Alpha (deg)')
    axes[0, 1].set_ylabel('CD')
    axes[0, 1].grid(True)
    axes[0, 1].set_title('Drag Coefficient')

    axes[1, 0].plot(CDs, CLs, 'g.-')
    axes[1, 0].set_xlabel('CD')
    axes[1, 0].set_ylabel('CL')
    axes[1, 0].grid(True)
    axes[1, 0].set_title('Drag Polar')

    axes[1, 1].plot(alphas, CMs, 'm.-')
    axes[1, 1].set_xlabel('Alpha (deg)')
    axes[1, 1].set_ylabel('CM')
    axes[1, 1].grid(True)
    axes[1, 1].set_title('Pitching Moment')
    axes[1, 1].axhline(y=0, color='k', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(base_path, 'avl_analysis.png'), dpi=150)
    print(f"\nPlot saved to: {os.path.join(base_path, 'avl_analysis.png')}")

    plt.show()

    print("\nAVL interface test complete!")
