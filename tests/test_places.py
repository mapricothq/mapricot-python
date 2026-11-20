import unittest

from mapricot import Mapricot


class PlacesTest(unittest.TestCase):
    def test_get_refuses_an_empty_id(self):
        with self.assertRaises(ValueError):
            Mapricot("k").places.get("")


if __name__ == "__main__":
    unittest.main()
