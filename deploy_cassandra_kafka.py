import os
import time
import json
import threading
import random
import logging
import signal
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# CONFIG
# ============================
CASSANDRA_CONTAINER = "cassandra_node"
TOPIC_NAME = "capteurs"
BROKER_HOST = "localhost:29092"  # listener exposé depuis kafka
KEYSPACE = "pfe"
TABLE = "capteurs"

# ============================
# 1. DOCKER-COMPOSE + DÉPLOIEMENT
# ============================
def deploy_docker():
    print("\n🚀 Déploiement de Cassandra + Kafka (Confluent stack)...")

    # Docker Compose avec Confluent Kafka
    compose_content = """version: '2'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.4
    ports:
      - 22181:2181
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.4.4
    depends_on:
      - zookeeper
    ports:
      - 29092:29092
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  cassandra_node:
    image: cassandra:latest
    ports:
      - 9042:9042
    networks:
      - default
    environment:
      CASSANDRA_CLUSTER_NAME: PFECluster
    volumes:
      - cassandra_data:/var/lib/cassandra

volumes:
  cassandra_data:
"""

    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)

    os.system("docker-compose down")
    os.system("docker-compose up -d")
    time.sleep(20)  # Attente initiale

# ============================
# 2. WAIT FOR KAFKA
# ============================
def wait_for_kafka(timeout=60):
    print("⏳ Attente de Kafka (max 60s)...")
    for _ in range(timeout):
        try:
            KafkaAdminClient(bootstrap_servers=BROKER_HOST)
            logger.info("✅ Kafka is ready.")
            return
        except KafkaError:
            time.sleep(1)
    raise Exception("❌ Kafka ne s'est pas lancé à temps.")

# ============================
# 3. WAIT FOR CASSANDRA
# ============================
def wait_for_cassandra(timeout=90):
    print("⏳ Attente de Cassandra (max 90s)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            cluster = Cluster(['localhost'])
            session = cluster.connect()
            session.execute("SELECT now() FROM system.local")
            print("✅ Cassandra est prêt.")
            return
        except Exception:
            time.sleep(2)
    raise Exception("❌ Cassandra ne s'est pas lancé à temps.")

# ============================
# 4. CREATE TOPIC
# ============================
def create_kafka_topic():
    print("📌 Création du topic Kafka...")
    admin_client = KafkaAdminClient(bootstrap_servers=BROKER_HOST)
    topic = NewTopic(name=TOPIC_NAME, num_partitions=3, replication_factor=1)
    try:
        admin_client.create_topics([topic])
        print(f"✅ Topic '{TOPIC_NAME}' créé.")
    except TopicAlreadyExistsError:
        print(f"ℹ️ Topic '{TOPIC_NAME}' existe déjà.")

# ============================
# 5. CONFIG CASSANDRA
# ============================
def setup_cassandra():
    print("📌 Configuration de Cassandra...")
    cluster = Cluster(['localhost'])
    session = cluster.connect()

    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
    """)
    session.set_keyspace(KEYSPACE)

    session.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id UUID PRIMARY KEY,
            timestamp TIMESTAMP,
            doorSign BOOLEAN,
            ethylene FLOAT,
            chambre TEXT,
            conservMode TEXT,
            TempConsign FLOAT,
            forcageMode TEXT,
            FanontSign BOOLEAN,
            FaninSign BOOLEAN,
            humConsigne FLOAT,
            humSign FLOAT,
            CO2Consigne FLOAT,
            CO2 FLOAT,
            ethConsign FLOAT,
            ethSign FLOAT
        );
    """)
    print(f"✅ Table {KEYSPACE}.{TABLE} prête.")

# ============================
# 6. CONSUMER KAFKA → CASSANDRA
# ============================
stop_event = threading.Event()

def signal_handler(sig, frame):
    print("Shutting down...")
    stop_event.set()

signal.signal(signal.SIGINT, signal_handler)

def start_consumer():
    print("📡 Démarrage du consumer Kafka...")

    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=BROKER_HOST,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    cluster = Cluster(['localhost'])
    session = cluster.connect(KEYSPACE)

    while not stop_event.is_set():
        for message in consumer:
            if stop_event.is_set():
                break
            data = message.value

            try:
                # Validate the data
                validate_data(data)

                # Insert validated data into Cassandra
                session.execute(
                    f"""
                    INSERT INTO {TABLE} (
                        id, timestamp, temperature, humidity, pressure, doorSign, ethylene,
                        chambre, conservMode, TempConsign, forcageMode, FanontSign, FaninSign,
                        humConsigne, humSign, CO2Consigne, CO2, ethConsign, ethSign
                    )
                    VALUES (
                        uuid(), toTimestamp(now()), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        data["temperature"], data["humidity"], data["pressure"],
                        data["doorSign"], data["ethylene"], data["chambre"],
                        data["conservMode"], data["TempConsign"], data["forcageMode"],
                        data["FanontSign"], data["FaninSign"], data["humConsigne"],
                        data["humSign"], data["CO2Consigne"], data["CO2"],
                        data["ethConsign"], data["ethSign"]
                    )
                )
                print(f"✅ Donnée insérée : {data}")
            except ValueError as e:
                print(f"❌ Invalid data: {e}")
            except Exception as e:
                print(f"❌ Failed to insert data into Cassandra: {e}")

# ============================
# 7. PRODUCER TEST
# ============================
def send_test_data():
    print("🚀 Envoi de données de test...")

    producer = KafkaProducer(
        bootstrap_servers=BROKER_HOST,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    test_data = {"temperature": 6.5, "humidity": 40, "pressure": 1013}
    try:
        producer.send(TOPIC_NAME, test_data).get(timeout=10)
    except KafkaError as e:
        print(f"❌ Failed to send data to Kafka: {e}")
    print(f"✅ Données envoyées à Kafka : {test_data}")

# ============================
# 8. SELECT FROM CASSANDRA
# ============================
def check_cassandra_data():
    print("🔍 Vérification dans Cassandra...")

    cluster = Cluster(['localhost'])
    session = cluster.connect(KEYSPACE)

    rows = session.execute(f"SELECT * FROM {TABLE} LIMIT 5")
    for row in rows:
        print("📊", row)

# ============================
# RETRY WITH BACKOFF
# ============================
def retry_with_backoff(func, retries=5, backoff_in_seconds=1):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            wait_time = backoff_in_seconds * (2 ** i) + random.uniform(0, 1)
            print(f"Retrying in {wait_time:.2f}s due to error: {e}")
            time.sleep(wait_time)
    raise Exception("Max retries reached")

# ============================
# DATA VALIDATION
# ============================
def validate_data(data):
    required_keys = {
        "doorSign", "ethylene", "chambre", "conservMode", "TempConsign",
        "forcageMode", "FanontSign", "FaninSign", "humConsigne", "humSign",
        "CO2Consigne", "CO2", "ethConsign", "ethSign", "timestamp"
    }
    missing_keys = required_keys - data.keys()
    if missing_keys:
        raise ValueError(f"Invalid data format: Missing keys: {missing_keys}")

# ============================
# EXECUTION
# ============================
if __name__ == "__main__":
    deploy_docker()
    wait_for_kafka()
    wait_for_cassandra()
    create_kafka_topic()
    setup_cassandra()

    # Lancer le Consumer dans un thread
    threading.Thread(target=start_consumer).start()

    # Envoi de la donnée + Vérification
    send_test_data()
    time.sleep(5)
    check_cassandra_data()

    print("\n🎯 Tout est opérationnel !")
