import sys
import time
import ttn
import datetime as dt

from influxdb import InfluxDBClient

app_id = "dekut"
access_key = "ttn-account-v2.hf5mTr75JSqOmlQ2gkLHfU1Bb_gfz29lyMnOXsLbEXY"

GTW_ID = 'iot-mashinani' # gateway of interest

db_client = InfluxDBClient(host="127.0.0.1", port="8000")
db_client.create_database('fence_project')
db_client.switch_database('fence_project')

def uplink_callback(msg, client):
    

      print("Received uplink from ", msg.dev_id)

      influxdb_entry = {}  #a dictionary like json body

      influxdb_entry['time'] = msg.metadata.time #gets the time in the thing network
      fields = {}

      fields['data_rate'] = msg.metadata.data_rate  #gets the datarate


      for gtw in msg.metadata.gateways:
        if gtw.gtw_id == GTW_ID:
          fields['rssi'] = float(gtw.rssi)
          fields['snr'] = float(gtw.snr)

      try:
        fields['Voltage'] = float(msg.payload_fields.analog_in_7)
        fields['Current'] = float(msg.payload_fields.analog_in_8)
      except:
        pass


      influxdb_entry['fields'] = fields
      influxdb_entry['measurement'] = 'Fence_project'
      influxdb_entry['tags'] = {'sensor': msg.dev_id}

      print(influxdb_entry)


      db_client.write_points([influxdb_entry])

handler = ttn.HandlerClient(app_id, access_key)

# using mqtt client
mqtt_client = handler.data()
mqtt_client.set_uplink_callback(uplink_callback)
mqtt_client.connect()

while True:
  try:
    time.sleep(60)
  except KeyboardInterrupt:
    print('Closing ...')
    mqtt_client.close()
    sys.exit(0)