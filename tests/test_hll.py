import unittest

from cardapi import Counter
from hll import Distinct


class TestDistinct(unittest.TestCase):
    def test_add_counts(self):
        self.assertEqual(Distinct().add("a")["count"], 1)

    def test_estimate_of_sparse(self):
        counter = Distinct()
        counter.add("a")
        counter.add("a")
        self.assertEqual(counter.estimate(), 1)

    def test_stats_shape(self):
        self.assertIn("precision", Distinct().stats())

    def test_mode_initial(self):
        self.assertEqual(Distinct().stats()["mode"], "sparse")

    def test_counter_wraps(self):
        counter = Counter()
        counter.add("a")
        self.assertEqual(counter.counter.stats()["seen"], 1)


if __name__ == "__main__":
    unittest.main()
