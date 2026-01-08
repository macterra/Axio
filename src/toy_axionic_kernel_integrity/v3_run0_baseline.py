#!/usr/bin/env python3
"""
RSA v3.0 Run 0: Baseline Reference (No Adversary)

SHIM: Delegates to canonical script at scripts/rsa_v300_run0_baseline.py
"""
import sys
import os

# Add scripts to path and import canonical entrypoint
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from rsa_v300_run0_baseline import main

if __name__ == "__main__":
    sys.exit(main())

