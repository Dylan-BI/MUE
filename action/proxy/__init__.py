"""
action/proxy/__init__.py
MUE Learner Proxy — swappable learner behavior for the action/ workspace.

The real learner web interface is now active. To swap back to the dummy:
    1. Change the import below:
         from .web_interface import WebLearner as ActiveLearner
       to:
         from .dummy import DummyLearner as ActiveLearner
    2. Everything downstream stays unchanged.
"""
from action.proxy.interface import LearnerProxy
from action.proxy.web_interface import WebLearner

# ── SWAP POINT: Change this import to switch implementations ──
ActiveLearner = WebLearner

__all__ = ['LearnerProxy', 'WebLearner', 'ActiveLearner']
