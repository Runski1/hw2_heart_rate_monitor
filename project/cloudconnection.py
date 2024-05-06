import urequests as requests
import ujson
import network
from time import sleep
from hrv_analysis import basic_hrv_analysis


class Kubios:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.connected = False
        self.connect()

    def connect(self):
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        wifi.connect(self.ssid, self.password)
        count = 0
        wait = 20
        while not wifi.isconnected():
            print("Connecting...")
            sleep(1)
            count += 1

        if wait > count:  # if connection isn't timed out, set "connected" to True
            self.connected = True
        else:
            self.connected = False

    def request(self, intervals):
        APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
        CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
        CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"
        LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
        TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
        REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"
        response = requests.post(
            url=TOKEN_URL,
            data="grant_type=client_credentials&client_id={}".format(CLIENT_ID),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(CLIENT_ID, CLIENT_SECRET),
        )
        response = response.json()  # Parse JSON response into a python dictionary
        access_token = response["access_token"]  # Parse access token

        # Creating dataset
        dataset = {"type": "RRI", "data": intervals, "analysis": {"type": "readiness"}}

        # Make the readiness analysis with the given data
        response = requests.post(
            url="https://analysis.kubioscloud.com/v2/analytics/analyze",
            headers={
                "Authorization": "Bearer {}".format(access_token),
                "X-Api-Key": APIKEY,
            },
            json=dataset,
        )
        response = response.json()

        results = {
            "timestamp": response["analysis"]["create_timestamp"][
                :16
            ],  # OH NO IM SLICING
            "mean_hr": round(response["analysis"]["mean_hr_bpm"], 1),
            "mean_ppi": round(response["analysis"]["mean_rr_ms"]),
            "rmssd": round(response["analysis"]["rmssd_ms"], 1),
            "sdnn": round(response["analysis"]["sdnn_ms"], 1),
            "sns": round(response["analysis"]["sns_index"], 2),
            "pns": round(response["analysis"]["pns_index"], 2),
        }

        return results


def connect_to_kubios(rri_list):
    print("Connecting to wlan")
    wlan_creds = open("./wlan_creds.txt")
    ssid = wlan_creds.readline().strip()
    pwd = wlan_creds.readline().strip()
    wlan_creds.close()
    print("WLAN credentials read")
    kubios = Kubios(ssid, pwd)  # Initialize Kubios connection
    if kubios.connected:  # Check if the wifi is connected
        results = kubios.request(
            rri_list
        )  # send request to the kubios. Returns dictionary with needed values
        print("Kubios results:")
        print(results)
        return results
    else:
        print("not connected")
        return False
