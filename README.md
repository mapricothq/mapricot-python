# Mapricot for Python

The official Python client for the [Mapricot API](https://mapricot.com/): address and place search, reverse geocoding, nearby places, routing, and IP geolocation, with 250,000 free requests every month.

```sh
pip install mapricot
```

It needs Python 3.11 or later and has no dependencies.

## Quick start

Create a server key in the [dashboard](https://app.mapricot.com/) and set it as `MAPRICOT_KEY`:

```sh
export MAPRICOT_KEY="mapricot_sk_…"
```

```python
from mapricot import Mapricot

client = Mapricot()

data = client.search("128 SW 3rd Ave, Portland", limit=1)
place = data["results"][0]
print(place["label"], place["lat"], place["lon"])
```

Pass the key yourself with `Mapricot("mapricot_sk_…")`.

## Methods

Each method returns the API's JSON as a typed dict, with the same field names as the [API reference](https://mapricot.com/api-reference/).

| Method | Endpoint |
| --- | --- |
| `client.search(q, focus=, country=, limit=, lang=)` | [`GET /v1/search`](https://mapricot.com/docs/geocoding/#find-an-address) |
| `client.autocomplete(q, focus=, country=, limit=, lang=)` | [`GET /v1/autocomplete`](https://mapricot.com/docs/places/#suggest-as-people-type) |
| `client.reverse(lat, lon, limit=, lang=)` | [`GET /v1/reverse`](https://mapricot.com/docs/geocoding/#find-the-address-at-a-point) |
| `client.nearby(lat, lon, category=, radius=, limit=, lang=)` | [`GET /v1/nearby`](https://mapricot.com/docs/places/#list-places-around-a-point) |
| `client.place(id, lang=)` | [`GET /v1/places/{id}`](https://mapricot.com/docs/places/#look-up-a-saved-place) |
| `client.route(waypoints, mode=)` | [`POST /v1/route`](https://mapricot.com/docs/routing/#get-a-route) |
| `client.ip(address)` | [`GET /v1/ip/{ip}`](https://mapricot.com/docs/ip-geolocation/#look-up-an-address) |
| `client.account()` | `GET /v1/account`, which checks a key and is never billed |

`focus` and each waypoint are `{"lat": …, "lon": …}`. `country` and `category` take a list or a comma-separated string.

```python
nearby = client.nearby(45.52, -122.68, category=["food:coffee_shop"], radius=1000)
route = client.route([{"lat": 45.5189, "lon": -122.6793}, {"lat": 45.5214, "lon": -122.6828}], mode="walk")
print(route["routes"][0]["durationSeconds"])
```

A route's `polyline` is encoded with six decimal places. Decode it with precision 6, as [decoding a route polyline](https://mapricot.com/docs/polyline/) shows.

If your app shows results, show the credits in each response's `attribution`.

## Errors and retries

An error response raises `MapricotError`, with the HTTP `status`, the API's error `code`, a `message`, and the `request_id`:

```python
from mapricot import MapricotError

try:
    client.search("")
except MapricotError as error:
    print(error.status, error.code, error.message)  # 400 invalid_request The service rejected the request.
```

The client retries `503` responses and `429 concurrency_exceeded`, up to twice, waiting longer each time. Errors aren't billed. Set `max_retries=` and `timeout=` (seconds) on `Mapricot(...)` to change this. The [API reference](https://mapricot.com/api-reference/#errors) lists every status.

## Links

- [Mapricot](https://mapricot.com/)
- [Python docs](https://mapricot.com/docs/python/)
- [API reference](https://mapricot.com/api-reference/)
- [Pricing](https://mapricot.com/pricing/)
