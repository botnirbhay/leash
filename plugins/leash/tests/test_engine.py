import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.engine import Observation, evaluate
from scripts.codex_hook import control
class EngineTests(unittest.TestCase):
    def test_scope_and_high_risk_changes_block(self):
        self.assertEqual(evaluate(Observation("apply_patch", ("docs/test.md",)), {"scope": ["src/**"]}).rule, "outside-scope")
        self.assertEqual(evaluate(Observation("apply_patch", (".github/workflows/ci.yml",)), {"scope": [".github/**"]}).rule, "high-risk-config")
    def test_dependency_and_threshold_block(self):
        self.assertEqual(evaluate(Observation("Bash", command="npm install left-pad"), {}).rule, "dependency-install")
        self.assertEqual(evaluate(Observation("apply_patch", ("six.py",)), {"touched": ["one.py", "two.py", "three.py", "four.py", "five.py"]}).rule, "file-threshold")
    def test_plain_scope_and_off_commands(self):
        state = {"enabled": True, "scope": []}
        control({"prompt": "leash scope src/**"}, state)
        self.assertEqual(state["scope"], ["src/**"])
        control({"prompt": "leash off"}, state)
        self.assertFalse(state["enabled"])
if __name__ == "__main__": unittest.main()
