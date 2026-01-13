"""Selector v1.1

Reuses v100 selectors unchanged.
Selector must remain blind to predicted fields.
"""

# Just re-export v100 selectors
try:
    from ...v100.selector.blind import BlindActionSelectorV100, ASBNullSelectorV100
except ImportError:
    from rsa_poc.v100.selector.blind import BlindActionSelectorV100, ASBNullSelectorV100

# v1.1 uses same selectors as v1.0 (selector blindness maintained)
BlindActionSelectorV110 = BlindActionSelectorV100
ASBNullSelectorV110 = ASBNullSelectorV100
