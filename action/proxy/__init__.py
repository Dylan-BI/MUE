"""
action/proxy/__init__.py
MUE Learner Proxy — swappable learner behavior for the action/ workspace.

To swap in the real learner web interface:
    1. Create action/proxy/web_interface.py implementing LearnerProxy
    2. Change the import below:
         from .dummy import DummyLearner as ActiveLearner
       to:
         from .web_interface import WebLearner as ActiveLearner
    3. Everything downstream stays unchanged.
"""
from action.proxy.interface import LearnerProxy
from action.proxy.dummy import DummyLearner

# ── SWAP POINT: Change this import when the real interface is ready ──
ActiveLearner = DummyLearner

__all__ = ['LearnerProxy', 'DummyLearner', 'ActiveLearner']
