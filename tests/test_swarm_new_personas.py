import unittest
import json
from pathlib import Path
from core.swarm import Swarm, Persona

class TestSwarmNewPersonas(unittest.TestCase):
    def setUp(self):
        self.swarm = Swarm()
        
    def test_personas_loaded(self):
        persona_names = [p.name for p in self.swarm.personas]
        self.assertIn("Ethics Researcher", persona_names)
        self.assertIn("Privacy Officer", persona_names)

    def test_weighted_scoring_ethics(self):
        ethics_persona = next(p for p in self.swarm.personas if p.name == "Ethics Researcher")
        report_text = """
        Fair – with Harmful Bias Managed Score: 80/100
        Explainable and Interpretable Score: 90/100
        """
        result = self.swarm.calculate_weighted_score(ethics_persona, report_text)
        
        # Expected: 80 * 0.7 + 90 * 0.3 = 56 + 27 = 83.0
        self.assertAlmostEqual(result["final_score"], 83.0)

    def test_weighted_scoring_privacy(self):
        privacy_persona = next(p for p in self.swarm.personas if p.name == "Privacy Officer")
        report_text = """
        Privacy-Enhanced Score: 70/100
        Accountable and Transparent Score: 100/100
        """
        result = self.swarm.calculate_weighted_score(privacy_persona, report_text)
        
        # Expected: 70 * 0.8 + 100 * 0.2 = 56 + 20 = 76.0
        self.assertAlmostEqual(result["final_score"], 76.0)

if __name__ == "__main__":
    unittest.main()
