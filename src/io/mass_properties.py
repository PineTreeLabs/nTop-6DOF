"""
Mass properties converter for AVL.

Handles conversion from US Customary units (lbm, inches) to AVL units (slugs, feet).
"""

import numpy as np
import pandas as pd
from typing import Dict


class MassProperties:
    """Container for aircraft mass properties."""

    def __init__(self, mass_lbm: float, cg_inches: np.ndarray, inertia_lbm_in2: np.ndarray):
        """
        Initialize mass properties from US Customary units.

        Parameters:
        -----------
        mass_lbm : float
            Total mass in pounds-mass (lbm)
        cg_inches : np.ndarray
            CG location [x, y, z] in inches
        inertia_lbm_in2 : np.ndarray
            Inertia tensor [Ixx, Iyy, Izz, Ixy, Ixz, Iyz] in lbm*in^2
            If only 3 values provided, assumes Ixy=Ixz=Iyz=0
        """
        self.mass_lbm = mass_lbm
        self.cg_inches = np.array(cg_inches)

        if len(inertia_lbm_in2) == 3:
            self.inertia_lbm_in2 = np.array([
                inertia_lbm_in2[0],  # Ixx
                inertia_lbm_in2[1],  # Iyy
                inertia_lbm_in2[2],  # Izz
                0.0,                  # Ixy
                0.0,                  # Ixz
                0.0                   # Iyz
            ])
        else:
            self.inertia_lbm_in2 = np.array(inertia_lbm_in2)

        # Convert to SI units
        self._convert_to_si()

    def _convert_to_si(self):
        """Convert mass properties from US Customary to SI units."""
        # Mass: lbm to kg
        self.mass_kg = self.mass_lbm * 0.45359237

        # Mass: lbm to slugs (for AVL which uses slugs)
        self.mass_slugs = self.mass_lbm / 32.174

        # CG: inches to feet (for AVL)
        self.cg_ft = self.cg_inches / 12.0

        # CG: inches to meters (for 6-DOF)
        self.cg_m = self.cg_inches * 0.0254

        # Inertia: lbm*in^2 to slug*ft^2 (for AVL)
        # 1 lbm*in^2 = (1/32.174) slug * (1/144) ft^2 = (1/4633.056) slug*ft^2
        self.inertia_slug_ft2 = self.inertia_lbm_in2 / 4633.056

        # Inertia: lbm*in^2 to kg*m^2 (for 6-DOF)
        # 1 lbm*in^2 = 0.45359237 kg * (0.0254)^2 m^2 = 0.0002926397 kg*m^2
        self.inertia_kg_m2 = self.inertia_lbm_in2 * 0.0002926397

    def get_inertia_matrix_slug_ft2(self) -> np.ndarray:
        """Get full 3x3 inertia tensor in slug*ft^2."""
        I = self.inertia_slug_ft2
        return np.array([
            [I[0], -I[3], -I[4]],
            [-I[3], I[1], -I[5]],
            [-I[4], -I[5], I[2]]
        ])

    def get_inertia_matrix_kg_m2(self) -> np.ndarray:
        """Get full 3x3 inertia tensor in kg*m^2."""
        I = self.inertia_kg_m2
        return np.array([
            [I[0], -I[3], -I[4]],
            [-I[3], I[1], -I[5]],
            [-I[4], -I[5], I[2]]
        ])

    def write_avl_mass_file(self, filepath: str, name: str = "UAV"):
        """
        Write AVL .mass file.

        Parameters:
        -----------
        filepath : str
            Output file path
        name : str
            Aircraft name
        """
        with open(filepath, 'w') as f:
            f.write(f"#  {name} Mass File\n")
            f.write("#  Units: slugs, feet\n")
            f.write("#\n")
            f.write(f"#  mass    x       y       z       Ixx     Iyy     Izz     Ixy     Ixz     Iyz\n")
            f.write(f"   {self.mass_slugs:12.6f}  ")
            f.write(f"{self.cg_ft[0]:8.4f}  {self.cg_ft[1]:8.4f}  {self.cg_ft[2]:8.4f}  ")
            f.write(f"{self.inertia_slug_ft2[0]:12.4f}  ")
            f.write(f"{self.inertia_slug_ft2[1]:12.4f}  ")
            f.write(f"{self.inertia_slug_ft2[2]:12.4f}  ")
            f.write(f"{self.inertia_slug_ft2[3]:12.4f}  ")
            f.write(f"{self.inertia_slug_ft2[4]:12.4f}  ")
            f.write(f"{self.inertia_slug_ft2[5]:12.4f}\n")

    def print_summary(self):
        """Print formatted summary of mass properties."""
        print("=" * 60)
        print("MASS PROPERTIES SUMMARY")
        print("=" * 60)
        print("\nOriginal (US Customary):")
        print(f"  Mass:       {self.mass_lbm:10.3f} lbm")
        print(f"  CG:         ({self.cg_inches[0]:8.3f}, {self.cg_inches[1]:8.3f}, {self.cg_inches[2]:8.3f}) in")
        print(f"  Ixx:        {self.inertia_lbm_in2[0]:12.1f} lbm*in^2")
        print(f"  Iyy:        {self.inertia_lbm_in2[1]:12.1f} lbm*in^2")
        print(f"  Izz:        {self.inertia_lbm_in2[2]:12.1f} lbm*in^2")

        print("\nAVL Units (slugs, feet):")
        print(f"  Mass:       {self.mass_slugs:10.6f} slugs")
        print(f"  CG:         ({self.cg_ft[0]:8.4f}, {self.cg_ft[1]:8.4f}, {self.cg_ft[2]:8.4f}) ft")
        print(f"  Ixx:        {self.inertia_slug_ft2[0]:12.4f} slug*ft^2")
        print(f"  Iyy:        {self.inertia_slug_ft2[1]:12.4f} slug*ft^2")
        print(f"  Izz:        {self.inertia_slug_ft2[2]:12.4f} slug*ft^2")

        print("\nSI Units (kg, meters):")
        print(f"  Mass:       {self.mass_kg:10.3f} kg")
        print(f"  CG:         ({self.cg_m[0]:8.4f}, {self.cg_m[1]:8.4f}, {self.cg_m[2]:8.4f}) m")
        print(f"  Ixx:        {self.inertia_kg_m2[0]:12.4f} kg*m^2")
        print(f"  Iyy:        {self.inertia_kg_m2[1]:12.4f} kg*m^2")
        print(f"  Izz:        {self.inertia_kg_m2[2]:12.4f} kg*m^2")
        print("=" * 60)


def read_mass_csv(filepath: str) -> MassProperties:
    """
    Read mass properties from CSV file.

    Expected format:
    avl_mass,avl_CGx,avl_CGy,avl_CGz,avl_Ixx,avl_Iyy,avl_Izz

    Parameters:
    -----------
    filepath : str
        Path to mass CSV file

    Returns:
    --------
    mass_props : MassProperties
        Mass properties object
    """
    df = pd.read_csv(filepath)

    mass_lbm = df['avl_mass'].values[0]
    cg_inches = np.array([
        df['avl_CGx'].values[0],
        df['avl_CGy'].values[0],
        df['avl_CGz'].values[0]
    ])
    inertia_lbm_in2 = np.array([
        df['avl_Ixx'].values[0],
        df['avl_Iyy'].values[0],
        df['avl_Izz'].values[0]
    ])

    return MassProperties(mass_lbm, cg_inches, inertia_lbm_in2)


if __name__ == "__main__":
    import os

    # Test with current mass data
    base_path = r"C:\Users\bradrothenberg\OneDrive - nTop\OUT\parts\nTopAVL\nTop6DOF\Data"
    mass_file = os.path.join(base_path, "mass.csv")

    mass_props = read_mass_csv(mass_file)
    mass_props.print_summary()

    # Write AVL mass file
    output_path = r"C:\Users\bradrothenberg\OneDrive - nTop\OUT\parts\nTopAVL\nTop6DOF\avl_files"
    os.makedirs(output_path, exist_ok=True)
    mass_props.write_avl_mass_file(os.path.join(output_path, "uav.mass"), name="nTop_UAV")

    print(f"\nAVL mass file written to: {os.path.join(output_path, 'uav.mass')}")
