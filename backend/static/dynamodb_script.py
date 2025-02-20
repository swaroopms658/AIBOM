import json
import boto3
import paho.mqtt.client as mqtt

# AWS DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table = dynamodb.Table('IotData')  # Replace with your DynamoDB table name

# MQTT settings
mqtt_broker = "51.20.85.183" # Replace with your broker IP
mqtt_port = 1883 # Replace with your broker port
mqtt_topic = "test"  # Replace with your topic

# Callback function to handle incoming MQTT messages
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    
    # Assuming message is in JSON format
    message = json.loads(msg.payload.decode())
    
    # Insert data into DynamoDB
    response = table.put_item(
        Item={
            'DeviceID': message['DeviceID'],  # Adjust according to your message structure
            'Timestamp': message['Timestamp'],
            'Data': message['Data']
        }
    )
    print(f"Data inserted into DynamoDB: {response}")

# Set up MQTT client
client = mqtt.Client()
client.on_message = on_message

# Connect to MQTT broker
client.connect(mqtt_broker, mqtt_port)


# Subscribe to topic
client.subscribe(mqtt_topic)

# Start the loop to listen for messages
client.loop_forever()
