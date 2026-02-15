"""
AxionAgent — Entry Point

Run via: cd src/axionic_rsa/RSA-0 && python -m axionagent
"""

import os
import sys
from pathlib import Path

# RSA-0 root is the parent of the axionagent/ package
RSA0_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RSA0_ROOT))


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no external dependency)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    # Load .env from Axio project root
    axio_root = RSA0_ROOT.parent.parent.parent  # /home/david/Axio
    _load_dotenv(axio_root / ".env")

    from axionagent.agent import AxionAgent

    agent = AxionAgent(repo_root=RSA0_ROOT)
    agent.run()


if __name__ == "__main__":
    main()
