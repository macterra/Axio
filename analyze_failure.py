#!/usr/bin/env python3
import json

# Check the most recent completed run for episode details
with open('src/rsa_poc/v440/results/v440_baseline_44_42_20260122_173707.json') as f:
    data = json.load(f)

# Find a failing regime-2 episode
for ep in data.get('episodes', []):
    ep_num = ep.get('episode', 0)
    regime = ep.get('regime', 0)
    success = ep.get('success', False)

    if regime == 2 and not success:
        print(f'Ep{ep_num} (regime 2, FAILED):')
        steps = ep.get('steps', [])
        print(f'  Total steps: {len(steps)}')

        # Look at action pattern
        actions = [s.get('action', '?') for s in steps]
        action_counts = {}
        for a in actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        print(f'  Action counts: {action_counts}')

        # Check last_action_outcome patterns
        outcomes = [s.get('last_action_outcome') for s in steps if s.get('last_action_outcome')]
        outcome_counts = {}
        for o in outcomes:
            outcome_counts[o] = outcome_counts.get(o, 0) + 1
        print(f'  Outcome counts: {outcome_counts}')

        # First 10 actions
        print(f'  First 10 actions: {actions[:10]}')
        break
