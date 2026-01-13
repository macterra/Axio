import sys
sys.path.insert(0, '/home/david/Axio/src')

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v110.state.normative import NormativeStateV110

env = CommitmentTrapV100(max_steps=10, seed=42)
state = NormativeStateV110()

env.reset()
obs = env.get_obs()
feasible = env.get_feasible_actions()
apcm = env.get_apcm(obs)

print('=== Feasible Actions ===')
print(feasible)
print()

print('=== All Preferences ===')
prefs = sorted(state.get_preferences())
print(prefs)
print()

print('=== APCM for all actions ===')
for action in sorted(feasible):
    print(f'{action}:')
    print(f'  violates: {apcm[action]["violates"]}')
    print(f'  satisfies: {apcm[action]["satisfies"]}')
    print()

print('=== Collision Check ===')
print(f'Is collision step: {env.is_collision_step()}')
print()

# Now simulate what the generator should do
print('=== Generator Logic Simulation ===')
required_preservations = set(prefs)  # All prefs are required initially
print(f'Required preservations: {required_preservations}')
print()

for action in sorted(feasible):
    violates = apcm[action]["violates"]
    unauth_violations = violates & required_preservations
    print(f'{action}:')
    print(f'  violates: {violates}')
    print(f'  unauth_violations (violates ∩ required_preservations): {unauth_violations}')
    print(f'  → forbidden: {bool(unauth_violations)}')
    print()
