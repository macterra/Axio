#!/usr/bin/env python3
"""
RSA v3.0 Run 0: Baseline Equivalence Gate

Reuses Run 0 from v2.0 - no changes needed.
Condition A: RSA disabled (10 seeds)
Condition B: RSA enabled + NONE model (10 seeds)

Pass criterion: Exact metric match per seed on all required fields.

NOTE: Run 0 is exempt from exercised-state checks.
"""
import sys
sys.path.insert(0, "src")

# Reuse v2.0 Run 0 baseline directly
from run0_baseline import main

if __name__ == "__main__":
    sys.exit(main())
