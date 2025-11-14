"""Top-level package marker for flask_backend.

Also provides a compatibility alias so imports like
`from app.services import ...` continue to work when the
package is executed as `flask_backend.app`.
"""

import sys as _sys
from . import app as _app_pkg  # noqa: F401

# Make `import app` resolve to `flask_backend.app`
_sys.modules.setdefault("app", _app_pkg)
