# main.py

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.lang import Builder
from kivy_garden.mapview import MapView, MapMarker
from kivy.core.window import Window

from plyer import gps, camera
import requests
import threading

import kivy
print(kivy.__version__)

# Load the KV file
Builder.load_file('main.kv')

# Set the window size (useful for desktop testing)
Window.size = (360, 640)

# Backend API URL
API_URL = 'https://your-backend-api.com/reports/'  # Replace with your actual backend URL
LOGIN_URL = 'https://your-backend-api.com/login/'  # Replace with your actual login API URL
REGISTER_URL = 'https://your-backend-api.com/register/'  # Replace with your actual registration API URL

# class LoginScreen(Screen):
#     username = ObjectProperty(None)
#     password = ObjectProperty(None)
#     error_message = StringProperty('')

#     def login(self):
#         username = self.username.text
#         password = self.password.text
#         data = {'username': username, 'password': password}

#         threading.Thread(target=self._login, args=(data,)).start()

#     def _login(self, data):
#         try:
#             response = requests.post(LOGIN_URL, data=data)
#             if response.status_code == 200:
#                 user_data = response.json()
#                 if user_data['role'] == 'admin':
#                     self.manager.current = 'admin_dashboard'
#                 else:
#                     self.manager.current = 'user_dashboard'
#             else:
#                 self.error_message = 'Invalid credentials'
#         except Exception as e:
#             print('Error during login:', e)
#             self.error_message = 'Login failed'

# class RegistrationScreen(Screen):
#     username = ObjectProperty(None)
#     password = ObjectProperty(None)
#     confirm_password = ObjectProperty(None)
#     registration_message = StringProperty('')

#     def register(self):
#         username = self.username.text
#         password = self.password.text
#         confirm_password = self.confirm_password.text

#         if password != confirm_password:
#             self.registration_message = 'Passwords do not match'
#             return

#         data = {'username': username, 'password': password}
#         threading.Thread(target=self._register, args=(data,)).start()

#     def _register(self, data):
#         try:
#             response = requests.post(REGISTER_URL, data=data)
#             if response.status_code == 201:
#                 self.registration_message = 'Registration successful'
#                 self.manager.current = 'login'
#             else:
#                 self.registration_message = 'Registration failed'
#         except Exception as e:
#             print('Error during registration:', e)
#             self.registration_message = 'Registration error'

class UserDashboard(Screen):
    def on_enter(self):
        # Fetch user-specific data if needed
        pass

class AdminDashboard(Screen):
    reports_list = ObjectProperty(None)

    def on_enter(self):
        threading.Thread(target=self.load_reports).start()

    def load_reports(self):
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                reports = response.json()
                self.display_reports(reports)
            else:
                print('Failed to load reports:', response.text)
        except Exception as e:
            print('Error loading reports:', e)

    def display_reports(self, reports):
        self.reports_list.clear_widgets()
        for report in reports:
            item = ReportItem(report=report)
            self.reports_list.add_widget(item)

class ReportItem(BoxLayout):
    report = ObjectProperty(None)

    def __init__(self, report, **kwargs):
        super().__init__(**kwargs)
        self.report = report
        self.ids.description.text = report.get('description', 'No description')
        self.ids.location.text = f"Lat: {report['latitude']}, Lon: {report['longitude']}"

class ReportScreen(Screen):
    location_label = StringProperty('Getting location...')
    image_path = StringProperty('')
    description_input = StringProperty('')
    lat = None
    lon = None

    def on_pre_enter(self):
        self.get_location()

    def get_location(self):
        try:
            gps.configure(on_location=self.on_location, on_status=self.on_status)
            gps.start(minTime=1000, minDistance=0)
        except NotImplementedError:
            self.location_label = "GPS not implemented on this platform"

    def on_location(self, **kwargs):
        self.lat = kwargs.get('lat')
        self.lon = kwargs.get('lon')
        self.location_label = f"Latitude: {self.lat}, Longitude: {self.lon}"

    def on_status(self, stype, status):
        pass

    def take_picture(self):
        threading.Thread(target=self._take_picture).start()

    def _take_picture(self):
        try:
            camera.take_picture(filename='photo.jpg', on_complete=self.on_camera_complete)
        except NotImplementedError:
            print("Camera not implemented on this platform")

    def on_camera_complete(self, filepath):
        self.image_path = filepath
        print(f"Photo saved to: {filepath}")

    def submit_report(self):
        if not self.lat or not self.lon:
            self.location_label = "Location not available"
            return

        report_data = {
            'latitude': self.lat,
            'longitude': self.lon,
            'description': self.description_input.text,
        }

        files = {}
        if self.image_path:
            files['image'] = open(self.image_path, 'rb')

        threading.Thread(target=self._send_report, args=(report_data, files)).start()

    def _send_report(self, data, files):
        try:
            response = requests.post(API_URL, data=data, files=files)
            if response.status_code == 201:
                print('Report submitted successfully')
                self.reset_form()
                self.manager.current = 'user_dashboard'
            else:
                print('Failed to submit report:', response.text)
        except Exception as e:
            print('Error submitting report:', e)

    def reset_form(self):
        self.description_input.text = ''
        self.image_path = ''
        self.location_label = 'Getting location...'
    
    def go_back(self):
        # Check if user is admin or not
        if self.is_admin:
            self.manager.current = 'admin_dashboard'
        else:
            self.manager.current = 'user_dashboard'

class FireReportApp(App):
    def build(self):
        sm = ScreenManager()
        # sm.add_widget(LoginScreen(name='login'))
        # sm.add_widget(RegistrationScreen(name='register'))
        sm.add_widget(UserDashboard(name='user_dashboard'))
        sm.add_widget(AdminDashboard(name='admin_dashboard'))
        sm.add_widget(ReportScreen(name='report'))
        return sm

if __name__ == '__main__':
    FireReportApp().run()