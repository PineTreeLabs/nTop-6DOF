"""
Debug AVL interaction to see what's happening.
"""

import subprocess
import os

avl_exe = r"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe"
base_dir = r"C:\Users\bradrothenberg\OneDrive - nTop\OUT\parts\nTopAVL\nTop6DOF\avl_files"

avl_file = os.path.join(base_dir, "uav.avl")
mass_file = os.path.join(base_dir, "uav.mass")

# Simpler command sequence
commands = [
    "LOAD",
    "uav.avl",
    "MASS",
    "uav.mass",
    "OPER",
    "A",
    "A 5",
    "",
    "X",
    "",
    "FT",
    "test_output.ft",
    "",
    "QUIT"
]

cmd_input = "\n".join(commands) + "\n"

print("Commands being sent to AVL:")
print("=" * 60)
print(cmd_input)
print("=" * 60)
print()

# Write commands to file for inspection
with open(os.path.join(base_dir, "debug_commands.txt"), 'w') as f:
    f.write(cmd_input)

# Run AVL and capture output
result = subprocess.run(
    [avl_exe],
    input=cmd_input,
    capture_output=True,
    text=True,
    timeout=10,
    cwd=base_dir
)

print("AVL STDOUT:")
print("=" * 60)
print(result.stdout)
print("=" * 60)
print()

print("AVL STDERR:")
print("=" * 60)
print(result.stderr)
print("=" * 60)
print()

print("Return code:", result.returncode)
print()

# Check for output file
ft_file = os.path.join(base_dir, "test_output.ft")
if os.path.exists(ft_file):
    print(f"SUCCESS! Output file created: {ft_file}")
    with open(ft_file, 'r') as f:
        print()
        print("First 30 lines of output:")
        print("=" * 60)
        for i, line in enumerate(f):
            if i >= 30:
                break
            print(line.rstrip())
else:
    print(f"FAILED: Output file not created: {ft_file}")
    print()
    print("Files in avl_files directory:")
    for f in os.listdir(base_dir):
        print(f"  {f}")
