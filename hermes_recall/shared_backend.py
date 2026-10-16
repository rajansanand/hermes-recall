"""Process-local, profile-isolated ownership of embedded memory resources."""

import hashlib
import json
import os
from pathlib import Path
from threading import RLock

from .ownership import WriterBusyError

_lock = RLock()
_backends = {}


def acquire(home, cfg, factory):
    """Borrow matching resources; reject changed live settings before opening storage."""
    key = (
        os.path.normcase(str(Path(home).resolve())),
        cfg["qdrant"]["path"],
        cfg["qdrant"]["collection"],
    )
    signature = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    with _lock:
        backend = _backends.get(key)
        fresh = backend is None
        if fresh:
            backend = factory()
            backend.key, backend.signature = key, signature
            backend.active = 0
            _backends[key] = backend
        elif backend.active == 0:
            raise WriterBusyError("Memory writer is still draining its last chat.")
        elif backend.signature != signature:
            raise RuntimeError(
                "Memory writer settings changed; close existing chats before reopening."
            )
        backend.refs += 1
        backend.active += 1
        return backend, fresh


def retire(backend):
    """Reject replacement owners while the last chat's worker is still draining."""
    with _lock:
        backend.active -= 1


def release(backend, *, retired=False):
    """Keep the OS writer lease until every borrowing chat has drained its worker."""
    with _lock:
        if not retired:
            backend.active -= 1
        backend.refs -= 1
        if backend.refs == 0:
            backend.resources.close()
            del _backends[backend.key]
