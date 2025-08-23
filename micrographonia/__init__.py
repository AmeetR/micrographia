"""Compatibility wrapper exposing the ``symphonia`` package as ``micrographonia``.

This allows documentation examples like ``python -m micrographonia.finetune.cli``
to work while the underlying package is still named ``symphonia``.
"""
from symphonia import *  # noqa: F401,F403
import sys as _sys
import symphonia as symphonia
import symphonia.finetune as _finetune
import symphonia.sdk as _sdk
import symphonia.registry as _registry
import symphonia.training as _training
import symphonia.tools as _tools
import symphonia.runtime as _runtime

# Re-export common subpackages so ``micrographonia.<mod>`` maps to
# ``symphonia.<mod>``.
_sys.modules[__name__ + ".finetune"] = _finetune
_sys.modules[__name__ + ".sdk"] = _sdk
_sys.modules[__name__ + ".registry"] = _registry
_sys.modules[__name__ + ".training"] = _training
_sys.modules[__name__ + ".tools"] = _tools
_sys.modules[__name__ + ".runtime"] = _runtime
