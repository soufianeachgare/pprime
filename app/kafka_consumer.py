# backend/kafka_consumer.py

import json
import uuid
from kafka import KafkaConsumer
from cassandra.cluster import Cluster
from datetime import datetime

# --- Configuration Kafka ---
KAFKA_BROKER = 'localhost:29092'
TOPIC_NAME = 'capteurs'

# --- Connexion Cassandra ---
cluster = Cluster(['127.0.0.1'])
session = cluster.connect()
session.set_keyspace('pfe')

# --- Consumer Kafka ---
consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='capteurs-group'
)

print(f"✅ Consumer démarré sur le topic '{TOPIC_NAME}'...")

for message in consumer:
    data = message.value
    try:
        # Conversion timestamp si string
        timestamp = data['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        session.execute(f"""
            INSERT INTO capteurs (
                id, doorSign, ethylene, chambre, conservMode,
                TempConsign, forcageMode, FanontSign, FaninSign,
                humConsigne, humSign, CO2Consigne, CO2,
                ethConsign, ethSign, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            uuid.uuid4(),
            data.get('doorSign'),
            data.get('ethylene'),
            data.get('chambre'),
            data.get('conservMode'),
            data.get('TempConsign'),
            data.get('forcageMode'),
            data.get('FanontSign'),
            data.get('FaninSign'),
            data.get('humConsigne'),
            data.get('humSign'),
            data.get('CO2Consigne'),
            data.get('CO2'),
            data.get('ethConsign'),
            data.get('ethSign'),
            timestamp
        ))

        print(f"📥 Donnée insérée : {data}")

    except Exception as e:
        print(f"❌ Erreur d'insertion : {e}")
