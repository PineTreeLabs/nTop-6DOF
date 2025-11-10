"""
Simple Python script to run AVL analysis at multiple alpha values.
"""

import subprocess
import os
import re
import sys

def run_avl_at_alpha(avl_exe, avl_file, mass_file, alpha, output_prefix):
    """
    Run AVL at a specific alpha and save results.

    Returns:
    --------
    results : dict
        Dictionary with CL, CD, CM, etc.
    """

    # Build command sequence - each command on its own line
    commands = [
        "LOAD",
        avl_file,
        "MASS",
        mass_file,
        "OPER",
        "A",
        f"A {alpha}",
        "",  # Blank line to confirm
        "X",  # Execute
        "",  # Blank line after execute
        "FT",  # Write forces
        f"{output_prefix}.ft",
        "",  # Blank to return to OPER
        "QUIT",
        ""  # Final blank
    ]

    # Create command input
    cmd_input = "\n".join(commands)

    # Run AVL
    try:
        result = subprocess.run(
            [avl_exe],
            input=cmd_input,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.path.dirname(avl_file)
        )

        # Parse the .ft file if it exists
        ft_file = f"{output_prefix}.ft"
        if os.path.exists(ft_file):
            return parse_ft_file(ft_file, alpha)
        else:
            print(f"  Warning: Output file {ft_file} not created")
            return None

    except subprocess.TimeoutExpired:
        print(f"  Timeout at alpha={alpha}")
        return None
    except Exception as e:
        print(f"  Error at alpha={alpha}: {e}")
        return None


def parse_ft_file(ft_file, alpha):
    """Parse AVL .ft output file."""

    results = {'alpha': alpha, 'CL': 0.0, 'CD': 0.0, 'CM': 0.0}

    try:
        with open(ft_file, 'r') as f:
            content = f.read()

            # Parse coefficients
            match = re.search(r'CLtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                results['CL'] = float(match.group(1))

            match = re.search(r'CDtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                results['CD'] = float(match.group(1))

            match = re.search(r'Cmtot\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                results['CM'] = float(match.group(1))

            match = re.search(r'e\s*=\s*([-+]?\d*\.\d+)', content)
            if match:
                results['e'] = float(match.group(1))

    except Exception as e:
        print(f"  Error parsing {ft_file}: {e}")

    return results


def main():
    # Paths
    avl_exe = r"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe"
    base_dir = r"C:\Users\bradrothenberg\OneDrive - nTop\OUT\parts\nTopAVL\nTop6DOF\avl_files"

    avl_file = os.path.join(base_dir, "uav.avl")
    mass_file = os.path.join(base_dir, "uav.mass")

    # Alpha values to test
    alphas = [-5, -2, 0, 2, 5, 8, 10, 12, 15]

    print("=" * 70)
    print("AVL ALPHA SWEEP ANALYSIS")
    print("=" * 70)
    print(f"Geometry: {avl_file}")
    print(f"Mass:     {mass_file}")
    print(f"Alpha range: {alphas[0]}° to {alphas[-1]}°")
    print("=" * 70)
    print()

    results = []

    for alpha in alphas:
        print(f"Running alpha = {alpha:6.1f}°...", end='', flush=True)

        output_prefix = os.path.join(base_dir, f"alpha_{alpha:+04.0f}")
        result = run_avl_at_alpha(avl_exe, avl_file, mass_file, alpha, output_prefix)

        if result:
            results.append(result)
            ld_ratio = result['CL'] / result['CD'] if result['CD'] > 0.0001 else 0
            print(f" CL={result['CL']:7.4f}, CD={result['CD']:7.5f}, L/D={ld_ratio:6.1f}")
        else:
            print(" FAILED")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Alpha':>8s}  {'CL':>8s}  {'CD':>8s}  {'CM':>8s}  {'L/D':>8s}")
    print("-" * 70)

    for r in results:
        ld = r['CL'] / r['CD'] if r['CD'] > 0.0001 else 0
        print(f"{r['alpha']:8.1f}  {r['CL']:8.4f}  {r['CD']:8.5f}  {r['CM']:8.4f}  {ld:8.1f}")

    print("=" * 70)

    # Find max L/D
    if results:
        best = max(results, key=lambda r: r['CL'] / r['CD'] if r['CD'] > 0.0001 else 0)
        best_ld = best['CL'] / best['CD'] if best['CD'] > 0.0001 else 0

        print(f"\nBest L/D = {best_ld:.1f} at alpha = {best['alpha']:.1f}°")
        print(f"  CL = {best['CL']:.4f}")
        print(f"  CD = {best['CD']:.5f}")

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
