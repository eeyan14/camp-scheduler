import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


class MainTests(unittest.TestCase):
    def test_ui_output_contains_schedule_sections(self):
        result = main.main(output="ui")

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], "ui")
        self.assertIn("master_schedule", result)
        self.assertIn("per_group", result)
        self.assertIn("per_activity", result)
        self.assertIn("B:A/J", result["per_group"])


if __name__ == "__main__":
    unittest.main()
