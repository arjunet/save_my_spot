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
        mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=sk.eyJ1IjoiYXJqdW5ldCIsImEiOiJjbW5jOWl6bTEwYW15Mm9vemxibWdxbmVuIn0.rx64yPcodhv0WtFe3cU7jg"
        
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
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        print(f"Current Position: {lat}, {lon}")


class CarFinderApp(App):
    def build(self):
        return Home()

if __name__ == "__main__":
    CarFinderApp().run()