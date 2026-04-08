import os
import sys
import subprocess
from pathlib import Path

# Ensure Nuitka is installed
try:
    import nuitka
except ImportError:
    print("❌ Nuitka not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka"])

def build_epos_kernel():
    print("🛡️ EPOS SECURITY: Compiling Kernel to Binary...")
    
    # Path to the package
    package_dir = Path("epos_hq").absolute()
    output_dir = Path("dist").absolute()
    
    # Nuitka Arguments
    # --module: Compile as an importable module (so main.py can import epos_hq)
    # --include-package: Force inclusion of sub-packages
    # --follow-imports: Trace dependencies
    cmd = [
        sys.executable, "-m", "nuitka",
        "--module",
        "--include-package=epos_hq",
        f"--output-dir={output_dir}",
        "--remove-output",  # Cleanup build artifacts
        "--no-pyi-file",    # Don't expose type hints (security)
        str(package_dir)
    ]
    
    print(f"   Executing: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ COMPILATION SUCCESS.")
        print(f"   Binary Artifact located in: {output_dir}")
        print("   The 'epos_hq' source folder can now be removed from distribution.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ BUILD FAILED: {e}")

if __name__ == "__main__":
    build_epos_kernel()
