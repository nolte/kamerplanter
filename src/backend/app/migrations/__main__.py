"""``python -m app.migrations`` — dispatch to the framework CLI (NFR-016 O-2)."""

import sys

from app.migrations.framework.cli import main

if __name__ == "__main__":
    sys.exit(main())
