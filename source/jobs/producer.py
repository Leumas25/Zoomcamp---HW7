from dataclasses import dataclass
import dataclasses
import json
import time
import sys
from pathlib import Path
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from kafka import KafkaProducer

@dataclass
class Ride:
    lpep_pickup_datetime: int
    lpep_dropoff_datetime: int
    PULocationID: int
    DOLocationID: int
    passenger_count: int
    trip_distance: float
    tip_amount: float
    total_amount: float

def clean_int(value):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0
        return int(value)

def ride_from_row(row):
    return Ride(
        lpep_pickup_datetime=int(row['lpep_pickup_datetime'].timestamp() * 1000),
        lpep_dropoff_datetime=int(row['lpep_dropoff_datetime'].timestamp() * 1000),
        PULocationID=int(row['PULocationID']),
        DOLocationID=int(row['DOLocationID']),
        passenger_count=clean_int(row['passenger_count']),
        trip_distance=float(row['trip_distance']),
        tip_amount=float(row['tip_amount']),
        total_amount=float(row['total_amount']),
    )


URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-10.parquet"
columns = ['lpep_pickup_datetime', 'lpep_dropoff_datetime',  'PULocationID', 'DOLocationID', 'passenger_count', 'trip_distance', 'tip_amount', 'total_amount']
df = pd.read_parquet(URL, columns=columns)

def ride_serializer(ride):
    ride_dict = dataclasses.asdict(ride)
    json_str = json.dumps(ride_dict)
    return json_str.encode('utf-8')


server = 'localhost:9092'

producer = KafkaProducer(bootstrap_servers=[server], value_serializer=ride_serializer)

t0 = time.time()

topic_name = 'green_trips'

for _, row in df.iterrows():
    ride = ride_from_row(row)
    producer.send(topic_name, value=ride)
    print(f"Sent {ride} ")

producer.flush()

t1 = time.time()
print(f"Time taken: {t1 - t0:.2f} seconds")