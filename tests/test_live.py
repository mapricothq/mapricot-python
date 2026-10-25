import os
import unittest

from mapricot import Mapricot, MapricotError


@unittest.skipUnless(os.environ.get("MAPRICOT_KEY"), "set MAPRICOT_KEY to run tests against the live API")
class LiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Mapricot(os.environ["MAPRICOT_KEY"])

    def test_search(self):
        data = self.client.search("128 SW 3rd Ave, Portland", country=["US"], limit=1)
        self.assertEqual(data["results"][0]["address"]["locality"], "Portland")
        self.assertTrue(data["attribution"])

    def test_autocomplete(self):
        data = self.client.autocomplete("stumptown", focus={"lat": 45.52, "lon": -122.68}, limit=1)
        self.assertIn("Stumptown", data["results"][0]["name"])

    def test_reverse(self):
        data = self.client.reverse(45.5217, -122.6733, limit=1)
        self.assertIsInstance(data["results"][0]["distanceMeters"], int)

    def test_nearby(self):
        data = self.client.nearby(45.52, -122.68, category=["food:coffee_shop"], radius=1000, limit=1)
        self.assertIn("food:coffee_shop", data["results"][0]["categories"])

    def test_place(self):
        found = self.client.search("Pioneer Courthouse Square, Portland", limit=1)["results"][0]
        self.assertEqual(self.client.place(found["id"])["result"]["id"], found["id"])

    def test_route(self):
        data = self.client.route([{"lat": 43.7396, "lon": 7.4275}, {"lat": 43.734, "lon": 7.4222}], mode="walk")
        self.assertEqual(len(data["routes"][0]["legs"]), 1)
        self.assertTrue(data["routes"][0]["polyline"])

    def test_ip(self):
        data = self.client.ip("8.8.8.8")
        self.assertTrue(data["found"])
        self.assertEqual(data["countryCode"], "US")

    def test_account(self):
        self.assertEqual(self.client.account()["status"], "active")

    def test_invalid_request(self):
        with self.assertRaises(MapricotError) as caught:
            self.client.search("")
        self.assertEqual(caught.exception.status, 400)
        self.assertEqual(caught.exception.code, "invalid_request")
        self.assertTrue(caught.exception.request_id)


class BadKeyTest(unittest.TestCase):
    def test_unauthorized(self):
        with self.assertRaises(MapricotError) as caught:
            Mapricot("mapricot_sk_bad").account()
        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(caught.exception.code, "unauthorized")
