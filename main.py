from kivy_garden.mapview import MapView
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.utils import platform

from carbonkivy.app import App

from plyer import gps

class Home(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION], self.permissions_callback)

        else:
                print("Non-Android platform detected. Using fake coordinates.")
                self.start_gps()

        # Default Vars:
        self.has_centered = False

        # Default coordinates (Orlando, FL) in case GPS is not available
        self.lat = 28.5384
        self.lon = -81.3789

        # Api Url
        mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiYXJqdW5ldCIsImEiOiJjbW5jZTlpYjMxN2Q4Mm9vbnN6cXloZHc3In0.6mFjQz4XT7ghwW2Rc8Kcxw"
        
        # Create the MapView
        self.mapview = MapView(zoom=15, lat=self.lat, lon=self.lon)
        self.mapview.map_source.url = mapbox_url
        
        # Add the map to the Screen
        self.add_widget(self.mapview)


    def permissions_callback(self, permissions, grants):
        if all(grants):
            print("Location permissions granted.")
            self.start_gps()
        else:
            print("Location permissions denied. Using fake coordinates.")
            self.start_gps()

    def start_gps(self):
        try:
            # Configure and start GPS
            gps.configure(on_location=self.on_location)
            gps.start(minTime=1000, minDistance=1)
            print("GPS Started Successfully.")

        # Handle cases where GPS is not supported or available
        except (NotImplementedError, ModuleNotFoundError):
            print("GPS not supported on this device. Using fake coordinates.")

    @mainthread # Ensure UI updates happen on the main thread
    def on_location(self, **kwargs):
        self.lat = kwargs.get('lat')
        self.lon = kwargs.get('lon')
        
        # Update the map's center to follow your location
        print(f"Updated Position: {self.lat}, {self.lon}")

        if not self.has_centered:
            self.mapview.center_on(self.lat, self.lon)
            self.has_centered = True
            print("Initial GPS lock found. Map centered.")

class SaveMySpot(App):
    def build(self):
        return Home()

if __name__ == "__main__":
    SaveMySpot().run()