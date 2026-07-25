# Imports
from carbonkivy.uix.screen import CScreen
from carbonkivy.app import App
from carbonkivy.uix.screenmanager import CScreenManager

from kivy.properties import StringProperty

from kivy.utils import platform
from kivy.core.window import Window

from plyer import gps
# ----------------------------------------------------------
# KEYS:
PUBLIC_KEY = "pk.eyJ1IjoiYXJqdW5ldCIsImEiOiJjbW5jZTlpYjMxN2Q4Mm9vbnN6cXloZHc3In0.6mFjQz4XT7ghwW2Rc8Kcxw"
MAPBOX_TILE_URL = "https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/512/{z}/{x}/{y}@2x?access_token=" + PUBLIC_KEY
# ----------------------------------------------------------
class HomeScreen(CScreen):
    mapbox_url = StringProperty(MAPBOX_TILE_URL)

    def on_enter(self):
        self.startup()

    def startup(self):
        if platform == "android":
            from android.permissions import request_permissions, Permission

            def callback(permissions, results):
                # Ensure all requested permissions were granted
                if all(results):
                    print("Permissions granted. Starting GPS...")
                    self.start_gps()
                else:
                    print("Location permissions were denied by the user.")

            request_permissions([
                Permission.ACCESS_COARSE_LOCATION,
                Permission.ACCESS_FINE_LOCATION
            ], callback)

        else:
            # Fallback or simulator logic for desktop development
            print("USING FAKE CORRDINATES AS PLATFORM DOES NOT SUPPORT GPS HANDELING")

    def start_gps(self):
        try:
            gps.configure(
                on_location = self.update_location,
                on_status = self.on_status
            )

            gps.start(minTime=1000, minDistance=1)
            print("GPS STARTED")

        except NotImplementedError:
            print("USING FAKE CORRDINATES AS PLATFORM DOES NOT SUPPORT GPS HANDELING")

    def update_location(self, **kwargs):
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')

        if lat and lon:
            # Access the MapView created in KV via ids
            self.ids.map.center_on(lat, lon)

class MainApp(App):
    def __init__(self, *args, **kwargs) -> None:
        self.defaults = False
        super().__init__(*args, **kwargs)
        
    def build(self):
        # Set light mode
        Window.clearcolor = (1, 1, 1, 1)

        # Set up screen manager
        self.sm = CScreenManager()
        self.sm.add_widget(HomeScreen(name='Home'))
        return self.sm

if __name__ == "__main__":
    MainApp().run()


