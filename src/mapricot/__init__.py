"""Official client for the Mapricot API: geocoding, places, routing, and IP geolocation."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Literal, NotRequired, Sequence, TypedDict

__version__ = "0.9.0"

__all__ = [
    "Account",
    "Address",
    "Attribution",
    "GeocodingService",
    "IpGeolocationService",
    "IpLocation",
    "Isochrone",
    "Isochrones",
    "Leg",
    "LineString",
    "Mapricot",
    "MapricotError",
    "Place",
    "PlaceResult",
    "Places",
    "PlacesService",
    "Point",
    "Route",
    "Routes",
    "RoutingService",
    "Step",
]


class Point(TypedDict):
    lat: float
    lon: float


class Attribution(TypedDict):
    source: str
    text: str
    url: str


class Address(TypedDict, total=False):
    houseNumber: str
    street: str
    postalCode: str
    locality: str
    region: str
    regionCode: str
    country: str
    countryCode: str


class Place(TypedDict):
    id: str
    type: str
    name: str
    label: str
    lat: float
    lon: float
    address: NotRequired[Address]
    categories: NotRequired[list[str]]
    phones: NotRequired[list[str]]
    websites: NotRequired[list[str]]
    socials: NotRequired[list[str]]
    brand: NotRequired[str]
    openingHours: NotRequired[str]
    distanceMeters: NotRequired[int]
    source: str


class Places(TypedDict):
    results: list[Place]
    attribution: list[Attribution]


class PlaceResult(TypedDict):
    result: Place
    attribution: list[Attribution]


class Step(TypedDict):
    """One maneuver, and the stretch from it to the next."""

    instruction: str
    distanceMeters: int
    durationSeconds: int
    lat: float
    """Where the maneuver is, on the route's path."""
    lon: float


class Leg(TypedDict):
    distanceMeters: int
    durationSeconds: int
    steps: NotRequired[list[Step]]
    """Turn-by-turn directions, in order, when the route was asked for with steps=True. The last step is the arrival."""


class LineString(TypedDict):
    type: Literal["LineString"]
    coordinates: list[list[float]]
    """[longitude, latitude] pairs."""


class Route(TypedDict):
    distanceMeters: int
    durationSeconds: int
    polyline: NotRequired[str]
    """Encoded polyline, with five decimal places unless geometries was polyline6. Absent for geojson."""
    geometry: NotRequired[LineString]
    """The path as GeoJSON, when geometries was geojson."""
    legs: list[Leg]


class Routes(TypedDict):
    routes: list[Route]
    attribution: NotRequired[list[Attribution]]


class IsochroneProperties(TypedDict):
    minutes: int


class Polygon(TypedDict):
    type: Literal["Polygon", "MultiPolygon"]
    coordinates: list[Any]
    """[longitude, latitude] rings, as GeoJSON."""


class Isochrone(TypedDict):
    type: Literal["Feature"]
    properties: IsochroneProperties
    geometry: Polygon


class Isochrones(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[Isochrone]
    """One area per time, largest first. Empty when there is no road near the location."""
    attribution: NotRequired[list[Attribution]]


class IpLocation(TypedDict):
    ip: str
    found: bool
    continentCode: NotRequired[str]
    countryCode: NotRequired[str]
    countryName: NotRequired[str]
    regionCode: NotRequired[str]
    regionName: NotRequired[str]
    city: NotRequired[str]
    location: NotRequired[Point]
    source: str
    attributionUrl: str
    licenseUrl: str
    datasetRelease: str


class Account(TypedDict):
    id: str
    name: str
    status: str
    createdAt: str


class MapricotError(Exception):
    """An error response from the API, with its HTTP status, error code, and request ID."""

    def __init__(self, status: int, code: str, message: str, request_id: str | None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id


class Mapricot:
    """A client for https://api.mapricot.com that authenticates with a Mapricot key."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.mapricot.com",
        timeout: float = 30,
        max_retries: int = 2,
    ):
        if not api_key:
            raise ValueError("Pass api_key, a Mapricot key.")
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self.geocoding = GeocodingService(self._request)
        self.places = PlacesService(self._request)
        self.routing = RoutingService(self._request)
        self.ip_geolocation = IpGeolocationService(self._request)

    def account(self) -> Account:
        """The key's account. Not billed, so it checks a key for free."""
        return self._request("GET", "/account")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None, **params: Any) -> Any:
        query = urllib.parse.urlencode({name: _format(value) for name, value in params.items() if value is not None})
        url = self._base_url + path + (f"?{query}" if query else "")
        headers = {"Authorization": f"Bearer {self._api_key}", "User-Agent": f"mapricot-python/{__version__}"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()

        attempt = 0
        while True:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return json.load(response)
            except urllib.error.HTTPError as response:
                with response:
                    error = _error_from(response)
            if attempt >= self._max_retries or not _retryable(error):
                raise error
            time.sleep(0.5 * 2**attempt)
            attempt += 1


class GeocodingService:
    """client.geocoding: the /geocoding/v1 endpoints."""

    def __init__(self, request: Callable[..., Any]):
        self._request = request

    def search(
        self,
        q: str,
        *,
        focus: Point | None = None,
        country: str | Sequence[str] | None = None,
        limit: int | None = None,
        lang: str | None = None,
    ) -> Places:
        """Find addresses and places matching free text."""
        return self._request("GET", "/geocoding/v1/search", q=q, focus=focus, country=country, limit=limit, lang=lang)

    def autocomplete(
        self,
        q: str,
        *,
        focus: Point | None = None,
        country: str | Sequence[str] | None = None,
        limit: int | None = None,
        lang: str | None = None,
    ) -> Places:
        """Suggest addresses and places as someone types."""
        return self._request("GET", "/geocoding/v1/autocomplete", q=q, focus=focus, country=country, limit=limit, lang=lang)

    def reverse(self, lat: float, lon: float, *, limit: int | None = None, lang: str | None = None) -> Places:
        """Find the address nearest a coordinate, or the area around it."""
        return self._request("GET", "/geocoding/v1/reverse", lat=lat, lon=lon, limit=limit, lang=lang)


class PlacesService:
    """client.places: the /places/v1 endpoints."""

    def __init__(self, request: Callable[..., Any]):
        self._request = request

    def nearby(
        self,
        lat: float,
        lon: float,
        *,
        category: str | Sequence[str] | None = None,
        radius: int | None = None,
        limit: int | None = None,
        lang: str | None = None,
    ) -> Places:
        """List places around a coordinate, optionally by category."""
        return self._request(
            "GET", "/places/v1/nearby", lat=lat, lon=lon, category=category, radius=radius, limit=limit, lang=lang
        )

    def get(self, id: str, *, lang: str | None = None) -> PlaceResult:
        """Look up one place by its Mapricot ID."""
        return self._request("GET", f"/places/v1/{urllib.parse.quote(id, safe='')}", lang=lang)


class RoutingService:
    """client.routing: the /routing/v1 endpoints."""

    def __init__(self, request: Callable[..., Any]):
        self._request = request

    def route(
        self,
        waypoints: Sequence[Point],
        *,
        mode: Literal["drive", "walk", "bicycle"] | None = None,
        geometries: Literal["polyline", "polyline6", "geojson"] | None = None,
        steps: bool = False,
        lang: str | None = None,
    ) -> Routes:
        """Find a route through 2 to 20 waypoints."""
        body: dict[str, Any] = {"waypoints": list(waypoints)}
        if mode:
            body["mode"] = mode
        if geometries:
            body["geometries"] = geometries
        if steps:
            body["steps"] = True
        if lang:
            body["lang"] = lang
        return self._request("POST", "/routing/v1/route", body=body)

    def isochrone(
        self, location: Point, minutes: Sequence[int], *, mode: Literal["drive", "walk", "bicycle"] | None = None
    ) -> Isochrones:
        """The areas reachable from a location within 1 to 4 times, each 1 to 60 minutes."""
        body: dict[str, Any] = {"location": location, "minutes": list(minutes)}
        if mode:
            body["mode"] = mode
        return self._request("POST", "/routing/v1/isochrone", body=body)


class IpGeolocationService:
    """client.ip_geolocation: the /ip-geolocation/v1 endpoints."""

    def __init__(self, request: Callable[..., Any]):
        self._request = request

    def lookup(self, ip: str) -> IpLocation:
        """Approximate location of a public IP address."""
        return self._request("GET", f"/ip-geolocation/v1/{urllib.parse.quote(ip, safe='')}")


def _format(value: Any) -> str:
    if isinstance(value, dict):
        return f"{value['lat']},{value['lon']}"
    if isinstance(value, (list, tuple)):
        return ",".join(value)
    return str(value)


def _error_from(response: urllib.error.HTTPError) -> MapricotError:
    request_id = response.headers.get("X-Request-Id")
    try:
        error = json.load(response)["error"]
        return MapricotError(response.code, error["code"], error["message"], request_id)
    except (ValueError, KeyError, TypeError):
        return MapricotError(response.code, "unknown", f"HTTP {response.code}", request_id)


def _retryable(error: MapricotError) -> bool:
    return error.status == 503 or error.code == "concurrency_exceeded"
