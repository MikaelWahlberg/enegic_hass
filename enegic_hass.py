import requests
import os
import time
import json
from datetime import datetime
from paho.mqtt import client as mqtt_client

URL = "https://api.enegic.com/energydisplaydata"
USER_ID = "123456"
ITEM_ID = "1234567890123"
TOKEN ="baaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
MQTT_ADDR = "10.1.6.90"
MQTT_PORT = 1883
MQTT_USERNAME = "hass_user"
MQTT_PASSWORD = "passwordaaaaaaal"


def get_current_usage(url, user_id, item_id, token):
    try:
        response = requests.put(
            url,
            data={
                "ItemId": item_id,
                "UserId": user_id,
                "DisplayToken": token
            }
        )
    except Exception as e:
        print(e)

#    print(response.json())
    energy = dict()
    tot_kwh = 0
    kw = 0
    if response.status_code == 200:
        res = response.json()
        if len(res) == 2:
            for d in res[1].get("data", []):
                (l1, l2, l3, l4) = d["data"]["iavg"]
                kw = (l1+l2+l3)/4.38
                cur_kwh = kw/60
                tot_kwh += cur_kwh
    energy["total_kwh"] = "%0.3f" % tot_kwh
    energy["current_kw"] = "%0.3f" % kw
    return energy


def connect_mqtt(client_id):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_ADDR, MQTT_PORT)
    return client


mqtt = connect_mqtt("enegic_publisher")

while True:
    energy = get_current_usage(URL, USER_ID, ITEM_ID, TOKEN)
    print(datetime.now())
    print(energy["total_kwh"])
    print(energy["current_kw"])
    total_energy_topic = "homeassistant/sensor/enegicUsage/config"
    total_energy_config_payload = {
        "device_class": "energy",
        "unique_id": "enegic_usage_0",
        "state_class": "total_increasing",
        "name": "Enegic Energy Usage",
        "state_topic": "homeassistant/sensor/enegicUsage/state",
        "unit_of_measurement": "kWh"
    }
    current_energy_topic = "homeassistant/sensor/enegicUsageCurrent/config"
    current_energy_config_payload = {
        "device_class": "energy",
        "unique_id": "enegic_current_0",
        "state_class": "measurement",
        "name": "Enegic Current Power Usage",
        "state_topic": "homeassistant/sensor/enegicUsageCurrent/state",
        "unit_of_measurement": "kW"
    }

    try:
        res = mqtt.publish(total_energy_topic, json.dumps(total_energy_config_payload))
        res = mqtt.publish(total_energy_config_payload["state_topic"], energy["total_kwh"])
        res = mqtt.publish(current_energy_topic, json.dumps(current_energy_config_payload))
        res = mqtt.publish(current_energy_config_payload["state_topic"], energy["current_kw"])
        if res.rc != 0:
            print("Error sending, reconnecting")
            mqtt = connect_mqtt("enegic_publisher")
    except Exception:
        print("ERROR! Reconnecting")
        mqtt = connect_mqtt("enegic_publisher")
    time.sleep(60)
