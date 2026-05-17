from kivy_garden.mapview import MapView, MapMarker, MapLayer
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.graphics import Line, Color

from carbonkivy.app import CarbonApp
from carbonkivy.uix.modal import CModal

from plyer import gps
import weakref
import threading
import requests

# Load the KV file:
Builder.load_file('SaveMySpot.kv')
# ------------------------------------------------------------------------
# API KEYS:
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjY1NjAxM2Q2ZTI2OTRlOTdiM2Q5M2IxOTdkZTJlZGM2IiwiaCI6Im11cm11cjY0In0="
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Api Url:
        mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiYXJqdW5ldCIsImEiOiJjbW5jZTlpYjMxN2Q4Mm9vbnN6cXloZHc3In0.6mFjQz4XT7ghwW2Rc8Kcxw"

        if platform == 'android':
            # Request location permissions on Android:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION, Permission.CAMERA], self.permissions_callback)

        else:
            # For non-Android platforms, we can skip permission requests and use fake coordinates:
            print("Non-Android platform detected. Using fake coordinates.")
            self.start_gps()

        # Default Vars:
        self.has_centered = False
        self.current_location_marker = None
        self.parked_car_marker = None
        self.route_layer = None

        # Default coordinates (Orlando, FL) in case GPS is not available:
        self.lat = 28.5384
        self.lon = -81.3789

        # Add the mapview:
        self.mapview = MapView(zoom=25, lat=self.lat, lon=self.lon)
        self.mapview.map_source.url = mapbox_url
        Clock.schedule_once(self.add_ui_elements, 2)

    def permissions_callback(self, permissions, grants):
        if all(grants):
            self.start_gps()

        else:
            print("Location permissions denied. Using fake coordinates.")
            self.start_gps()

    def start_gps(self):
        try:
            # Configure and start GPS
            gps.configure(on_location=self.on_location)
            gps.start(minTime=1000, minDistance=1)

        # Handle cases where GPS is not supported or available
        except (NotImplementedError, ModuleNotFoundError):
            print("GPS not supported on this device. Using fake coordinates.")

    @mainthread # Ensure UI updates happen on the main thread
    def on_location(self, **kwargs):
        self.lat = kwargs.get('lat')
        self.lon = kwargs.get('lon')
        
        # Update the map's center to follow your location
        print(f"Updated Position: {self.lat}, {self.lon}")

    def add_ui_elements(self, dt):
        self.ids.main_layout.add_widget(self.mapview, index=len(self.ids.main_layout.children))
        store = JsonStore('./session.json')
        if store.exists('location'):
            data = store.get('location')
            # Use a tiny delay to ensure the MapView has initialized its bounds
            Clock.schedule_once(lambda dt: self.load_saved_car_marker(data['lat'], data['lon']), 0.5)

    def load_saved_car_marker(self, lat, lon):
        self.parked_car_marker = MapMarker(lat=lat, lon=lon, source='./images/car_marker.png')
        self.parked_car_marker.size = (50, 50)
        self.parked_car_marker.allow_stretch = True
        self.parked_car_marker.keep_ratio = True
        self.mapview.add_widget(self.parked_car_marker)
        self.mapview.center_on(lat, lon)
        self.has_centered = True

    def add_car_marker(self):
        if hasattr(self, 'parked_car_marker') and self.parked_car_marker:
            modal = ChangeParkedLocationModal(lat=self.lat, lon=self.lon, mapview=self.mapview, marker=self.parked_car_marker, home_screen=self)
            self._modal_ref = weakref.ref(modal)
            modal.open()
            self._modal_ref = None
            modal = None
            
        else:
            self.parked_car_marker = MapMarker(lat=self.lat, lon=self.lon, source='./images/car_marker.png')
            self.parked_car_marker.size = (50, 50)  # Set a reasonable size for the marker
            self.parked_car_marker.allow_stretch = True
            self.parked_car_marker.keep_ratio = True
            self.mapview.add_widget(self.parked_car_marker)
            JsonStore('./session.json').put('location', lat=self.lat, lon=self.lon)

    def find_car(self):
        self.start_gps()  # Ensure GPS is running to get the latest location

        # Add current location marker:
        if self.current_location_marker:
            self.mapview.remove_widget(self.current_location_marker)

        self.current_location_marker = MapMarker(lat=self.lat, lon=self.lon, source='./images/current_marker.png')
        self.current_location_marker.size = (50, 50)  # Set a reasonable size for the marker
        self.current_location_marker.allow_stretch = True
        self.current_location_marker.keep_ratio = True
        self.mapview.add_widget(self.current_location_marker)

        # Zoom out and center:
        self.mapview.center_on(self.lat, self.lon)
        self.has_centered = True
        self.mapview.zoom = 15

        # Add the route line:
        threading.Thread(
            target=self.get_route,
            daemon=True
        ).start()

    def get_route(self):
        response = requests.post(
            "https://api.openrouteservice.org/v2/directions/foot-walking/geojson",
            headers={
                "Authorization": ORS_API_KEY,
                "Content-Type": "application/json"
                },
            
            json={
                "coordinates": [
                    [self.lon, self.lat],  # ORS uses lon,lat order
                    [self.parked_car_marker.lon, self.parked_car_marker.lat]
                ]
            }
        )

        if response.status_code == 200:
            coords = response.json()["features"][0]["geometry"]["coordinates"]
            Clock.schedule_once(lambda dt: self.draw_route(coords))
        else:
            print(f"ORS ERROR: {response.text}")

    @mainthread
    def draw_route(self, coords):
        # Remove old route if exists
        if self.route_layer:
            self.mapview.remove_layer(self.route_layer)

        self.route_layer = RouteLayer(coords)
        self.mapview.add_layer(self.route_layer)
# ------------------------------------------------------------------------
class ChangeParkedLocationModal(CModal):
    def __init__(self, lat, lon, mapview, marker, home_screen, **kwargs):
        super().__init__(**kwargs)
        self.lat = lat
        self.lon = lon
        self.mapview = mapview
        self.parked_car_marker = marker
        self.home_screen = home_screen

    def change_parked_loc(self):
        self.mapview.remove_widget(self.parked_car_marker)

        self.new_parked_car_marker = MapMarker(lat=self.lat, lon=self.lon, source='./images/car_marker.png')
        self.new_parked_car_marker.size = (50, 50)  # Set a reasonable size for the marker
        self.new_parked_car_marker.allow_stretch = True
        self.new_parked_car_marker.keep_ratio = True
        self.mapview.add_widget(self.new_parked_car_marker)
        JsonStore('./session.json').put('location', lat=self.lat, lon=self.lon)
        self.home_screen.parked_car_marker = self.new_parked_car_marker
        self.dismiss()
# ------------------------------------------------------------------------
class RouteLayer(MapLayer):
    def __init__(self, coords, **kwargs):
        super().__init__(**kwargs)
        self.coords = coords  # list of [lon, lat]
        self.drawn_points = []

    def reposition(self):
        self.canvas.clear()
        if not self.coords or not self.parent:
            return
        with self.canvas:
            Color(0, 0.47, 1, 1)  # blue
            points = []
            for lon, lat in self.coords:
                x, y = self.parent.get_window_xy_from(lat, lon, self.parent.zoom)
                points.extend([x, y])
            if len(points) >= 4:
                Line(points=points, width=3)

class SaveMySpot(CarbonApp):
    def build(self):
        return HomeScreen()

if __name__ == "__main__":
    SaveMySpot().run()