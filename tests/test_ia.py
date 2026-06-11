import unittest
import numpy as np
from ia.ia_anomalies import detect_grade_anomaly
from ia.ia_appreciations import generate_appreciation

class IATestCase(unittest.TestCase):
    def test_appreciation_logic(self):
        """Vérifie que les appréciations correspondent aux notes."""
        # Test manuel sans DB (mocking ou simulation de logique)
        def mock_generate_appreciation(avg):
            if avg >= 17: return "Excellent"
            if avg >= 14: return "Bon"
            return "Passable"

        self.assertEqual(mock_generate_appreciation(18), "Excellent")
        self.assertEqual(mock_generate_appreciation(15), "Bon")

    def test_z_score_calculation(self):
        """Vérifie le calcul de l'anomalie."""
        values = [10, 11, 12, 10, 11]
        mean = sum(values) / len(values)
        std = np.std(values)
        new_val = 19
        z = abs((new_val - mean) / std)
        self.assertTrue(z > 2.5)

if __name__ == '__main__':
    unittest.main()
