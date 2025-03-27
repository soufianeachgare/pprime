# simulator/simulator.py

import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer

# Configuration Kafka
KAFKA_BROKER = 'localhost:29092'  # selon la config Docker
TOPIC = 'capteurs'

# Producteur Kafka
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Valeurs possibles
chambres = ['CH1', 'CH2', 'CH3']
conserv_modes = ['NORMAL', 'SURGELÉ', 'HUMIDE']
forcage_modes = ['AUTO', 'MANUEL']
etat_binaire = [True, False]  # pour portes, ventilateurs, etc.

def generer_donnees():
    return {
        "doorSign": random.choice(etat_binaire),
        "ethylene": round(random.uniform(0.0, 10.0), 2),
        "chambre": random.choice(chambres),
        "conservMode": random.choice(conserv_modes),
        "TempConsign": round(random.uniform(-20.0, 5.0), 2),
        "forcageMode": random.choice(forcage_modes),
        "FanontSign": random.choice(etat_binaire),
        "FaninSign": random.choice(etat_binaire),
        "humConsigne": round(random.uniform(30.0, 90.0), 2),
        "humSign": round(random.uniform(30.0, 90.0), 2),
        "CO2Consigne": round(random.uniform(300.0, 1000.0), 2),
        "CO2": round(random.uniform(300.0, 1000.0), 2),
        "ethConsign": round(random.uniform(0.0, 10.0), 2),
        "ethSign": round(random.uniform(0.0, 10.0), 2),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print(f"🚀 Simulation démarrée. Envoi des données au topic Kafka '{TOPIC}'...")

    while True:
        data = generer_donnees()
        producer.send(TOPIC, value=data)
        print(f"✅ Données envoyées : {data}")
        time.sleep(5)  # délai entre chaque envoi
