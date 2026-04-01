from kivy_garden.mapview import MapView, MapMarker
from kivy.uix.screenmanager import Screen
from kivy.clock import mainthread
from kivy.utils import platform
from kivy.clock import Clock
from kivy.lang import Builder

from carbonkivy.utils import _Dict, update_system_ui
from carbonkivy.app import CarbonApp
from carbonkivy.uix.modal import CModal

from plyer import gps, camera
import weakref
import os
from os import getcwd

Builder.load_file('SaveMySpot.kv')

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION, Permission.CAMERA], self.permissions_callback)

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
        self.mapview = MapView(zoom=25, lat=self.lat, lon=self.lon)
        self.mapview.map_source.url = mapbox_url
        
        # Add the map to the Screen
        Clock.schedule_once(self.add_buttons, 2)

    def add_buttons(self, dt):
        self.ids.main_layout.add_widget(self.mapview, index=len(self.ids.main_layout.children))

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

    def add_car_marker(self):
        if hasattr(self, 'parked_car_marker') and self.parked_car_marker:
            modal = ChangeParkedLocationModal(lat=self.lat, lon=self.lon, mapview=self.mapview)
            self._modal_ref = weakref.ref(modal)
            modal.open()
            self._modal_ref = None
            modal = None
            
        else:
            self.parked_car_marker = MapMarker(lat=self.lat, lon=self.lon)
            self.mapview.add_widget(self.parked_car_marker)
            modal = TakePictureModal()
            self._modal_ref = weakref.ref(modal)
            modal.open()
            self._modal_ref = None
            modal = None

class TakePictureModal(CModal):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cwd = getcwd() + "/"
        self.ids.path_label.text = self.cwd

    def take_picture(self):
        if platform == 'android':
            filepath = self.cwd + "CarPicture.jpg"

            try:
                camera.take_picture(filename=filepath,
                                   on_complete=self.camera_callback)
            except NotImplementedError:
                print("Camera not supported on this device.")
                self.dismiss()

    def camera_callback(self, filepath):
        if filepath:
            print(f"Picture saved at: {filepath}")
        else:
            print("Failed to save picture.")
        self.dismiss()

class ChangeParkedLocationModal(CModal):
    def __init__(self, lat, lon, mapview, **kwargs):
        super().__init__(**kwargs)
        self.lat = lat
        self.lon = lon
        self.mapview = mapview

    def change(self):
        if hasattr(self, 'parked_car_marker') and self.parked_car_marker:
            self.mapview.remove_widget(self.parked_car_marker)
            
        self.parked_car_marker = MapMarker(lat=self.lat, lon=self.lon)
        self.mapview.add_widget(self.parked_car_marker)
        self.dismiss()

        modal = TakePictureModal()
        self._modal_ref = weakref.ref(modal)
        modal.open()
        self._modal_ref = None
        modal = None

class SaveMySpot(CarbonApp):
    def build(self):
        return HomeScreen()

if __name__ == "__main__":
    SaveMySpot().run()