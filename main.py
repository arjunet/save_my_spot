from kivy_garden.mapview import MapView
from kivy.uix.screenmanager import Screen

from carbonkivy.app import App

from plyer import gps

class Home(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        try:
            self.get_location()
            gps.configure(on_location=self.on_location)
            gps.start()
            print("GPS started successfully.")

        except NotImplementedError:
            print("GPS coordinates not supported on this device...... using fake coordinates")
            self.lat = 28.5384
            self.lon = -81.3789
        
        # Api Url
        mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiYXJqdW5ldCIsImEiOiJjbW5jZTlpYjMxN2Q4Mm9vbnN6cXloZHc3In0.6mFjQz4XT7ghwW2Rc8Kcxw"
        
        # Create the MapView
        self.mapview = MapView(zoom=15, lat=self.lat, lon=self.lon)
        self.mapview.map_source.url = mapbox_url
        
        # Add the map to the Screen
        self.add_widget(self.mapview)
        
    def get_location(self):
        gps.configure(on_location=self.print_location)
        # 2. Start the GPS
        gps.start(minTime=1000, minDistance=1)
        print("GPS Started. Waiting for signal...")
        
        return None
    
    def print_location(self, **kwargs):
        # This function runs every time the GPS updates
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        print(f"Lat: {lat}, Lon: {lon}")

    def on_location(self, **kwargs):
        self.lat = kwargs.get('lat')
        self.lon = kwargs.get('lon')
        print(f"Current Position: {self.lat}, {self.lon}")


class CarFinderApp(App):
    def build(self):
        return Home()

if __name__ == "__main__":
    CarFinderApp().run()