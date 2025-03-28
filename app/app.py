from flask import Flask, jsonify, render_template
from cassandra.cluster import Cluster
from datetime import datetime

app = Flask(__name__)

# Cassandra Connection
cluster = Cluster(['localhost'])
session = cluster.connect()
session.set_keyspace('pfe')

# Route to render the dashboard page
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to get the latest sensor data
@app.route('/api/sensors/latest', methods=['GET'])
def get_latest_sensors():
    try:
        # Query the latest sensor data from Cassandra
        rows = session.execute("SELECT * FROM capteurs LIMIT 10")
        data = []
        for row in rows:
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint to get 24-hour history data for all rooms
@app.route('/api/sensors/history/24', methods=['GET'])
def get_history():
    try:
        # Calculate the timestamp for the last 24 hours
        min_time = datetime.now().timestamp() * 1000 - 86400000
        # Query the sensor data for the last 24 hours
        query = "SELECT * FROM capteurs WHERE timestamp > %s ALLOW FILTERING"
        rows = session.execute(query, (datetime.fromtimestamp(min_time / 1000),))
        data = []
        for row in rows:
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint to get 24-hour history data for a specific room
@app.route('/api/sensors/history/24/<room_id>', methods=['GET'])
def get_room_history(room_id):
    try:
        # calculate the condition for the last 24 hours using python 
        min_time = datetime.now().timestamp() * 1000 - 86400000
        # Query for the last 24-hour data for a specific room
        query = "SELECT * FROM capteurs WHERE chambre = %s AND timestamp > %s ALLOW FILTERING"
        rows = session.execute(query, (room_id, datetime.fromtimestamp(min_time / 1000)))
        data = []
        for row in rows:
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to get the latest sensor data for a specific room
@app.route('/api/sensors/latest/<room_id>', methods=['GET'])
def get_latest_room(room_id):
    try:
        # Query the latest sensor data for a specific room
        query = "SELECT * FROM capteurs WHERE chambre = %s LIMIT 1 ALLOW FILTERING"
        rows = session.execute(query, (room_id,))
        data = []
        for row in rows:
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint to get the latest sensor alerts for a specific room
@app.route('/api/sensors/alerts/<room_id>', methods=['GET'])
def get_room_alerts(room_id):
    try:
        # Query the latest sensor data for a specific room
        query = "SELECT * FROM capteurs WHERE chambre = %s ALLOW FILTERING"
        rows = session.execute(query, (room_id,))
        data = []
        for row in rows:
            if row.tempconsign > 25.0:
                data.append({
                    "roomName": row.chambre,
                    "message": "Temperature exceeds threshold!",
                    "severity": "high",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.humsign < 40.0:
                data.append({
                    "roomName": row.chambre,
                    "message": "Humidity below acceptable range.",
                    "severity": "medium",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.co2 > 1000.0:
                data.append({
                    "roomName": row.chambre,
                    "message": "CO2 level exceeds threshold!",
                    "severity": "high",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.ethylene > 2.0:
                data.append({
                    "roomName": row.chambre,
                    "message": "Ethylene level exceeds threshold!",
                    "severity": "high",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.doorsign:  # Assuming doorsign is True when the door is open
                data.append({
                    "roomName": row.chambre,
                    "message": "Door is open!",
                    "severity": "medium",
                    "timestamp": row.timestamp.isoformat()
                })
            if not row.fanontsign:  # Assuming fanontsign is False when the fan is off
                data.append({
                    "roomName": row.chambre,
                    "message": "Fan is off!",
                    "severity": "medium",
                    "timestamp": row.timestamp.isoformat()
                })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint to get the sensor data for a specific room in a specific time range
@app.route('/api/sensors/history/<room_id>/<start>/<end>', methods=['GET'])
def get_room_history_range(room_id, start, end):
    try:
        # Query the sensor data for a specific room in a specific time range
        query = "SELECT * FROM capteurs WHERE chambre = %s AND timestamp >= %s AND timestamp <= %s ALLOW FILTERING"
        rows = session.execute(query, (room_id, datetime.fromisoformat(start), datetime.fromisoformat(end)))
        data = []
        for row in rows:
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to get the latest sensor data for each room
@app.route('/api/sensors/latest/all', methods=['GET'])
def get_latest_all():
    try:
        # Query the latest sensor data for each room
        query = "SELECT chambre, id, timestamp, doorsign, ethylene, conservmode, tempconsign, forcagemode, fanontsign, faninsign, humconsigne, humsign, co2consigne, co2, ethconsign, ethsign FROM capteurs"
        rows = session.execute(query)
        latest_data = {}
        for row in rows:
            if row.chambre not in latest_data or row.timestamp > latest_data[row.chambre].timestamp:
                latest_data[row.chambre] = row
        data = []
        for row in latest_data.values():
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to get alerts for all where the temperature is above the threshold or the humidity is below the threshold or the CO2 level is above the threshold or the ethylene level is above the threshold or the door is open or the fan is off then return the alerts like this example :
# {
# [
#    {
#        "roomName": "CH1",
#        "message": "Temperature exceeds threshold!",
#        "severity": "high",
#        "timestamp": "2025-03-27T01:10:59.625000"
#    },
#    {
#        "roomName": "CH2",
#        "message": "Humidity below acceptable range.",
#        "severity": "medium",
#        "timestamp": "2025-03-27T01:15:30.123000"
#    }
#]
@app.route('/api/sensors/alerts', methods=['GET'])
def get_alerts():
    try:
        # Define thresholds
        temp_threshold = 25.0  # Example temperature threshold
        hum_threshold = 40.0  # Example minimum humidity threshold
        co2_threshold = 1000.0  # Example CO2 threshold
        ethylene_threshold = 2.0  # Example ethylene threshold

        # Query all sensor data
        query = "SELECT chambre, timestamp, tempconsign, humsign, co2, ethylene, doorsign, fanontsign FROM capteurs"
        rows = session.execute(query)

        alerts = []
        for row in rows:
            if row.tempconsign > temp_threshold:
                alerts.append({
                    "roomName": row.chambre,
                    "message": "Temperature exceeds threshold!",
                    "severity": "high",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.humsign < hum_threshold:
                alerts.append({
                    "roomName": row.chambre,
                    "message": "Humidity below acceptable range.",
                    "severity": "medium",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.co2 > co2_threshold:
                alerts.append({
                    "roomName": row.chambre,
                    "message": "CO2 level exceeds threshold!",
                    "severity": "high",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.ethylene > ethylene_threshold:
                alerts.append({
                    "roomName": row.chambre,
                    "message": "Ethylene level exceeds threshold!",
                    "severity": "high",
                    "timestamp": row.timestamp.isoformat()
                })
            if row.doorsign:  # Assuming doorsign is True when the door is open
                alerts.append({
                    "roomName": row.chambre,
                    "message": "Door is open!",
                    "severity": "medium",
                    "timestamp": row.timestamp.isoformat()
                })
            if not row.fanontsign:  # Assuming fanontsign is False when the fan is off
                alerts.append({
                    "roomName": row.chambre,
                    "message": "Fan is off!",
                    "severity": "medium",
                    "timestamp": row.timestamp.isoformat()
                })

        return jsonify(alerts), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint to get temperature data for the last 24 hours for all rooms
@app.route('/api/sensors/temperature/all', methods=['GET'])
def get_temperature_all():
    try:
        # Calculate the timestamp for the last 24 hours
        min_time = datetime.now().timestamp() * 1000 - 86400000
        # Query temperature data for the last 24 hours for all rooms
        query = "SELECT chambre, timestamp, tempconsign FROM capteurs WHERE timestamp > %s ALLOW FILTERING"
        rows = session.execute(query, (datetime.fromtimestamp(min_time / 1000),))
        data = []
        for row in rows:
            data.append({
                'chambre': row.chambre,
                'timestamp': row.timestamp.isoformat(),
                'TempConsign': row.tempconsign,
            })

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/room/<room_id>')
def room_detail(room_id):
    return render_template('room_detail.html', room_id=room_id)
# Endpoint to export the sensor data for a specific room in a specific time range as csv
@app.route('/api/sensors/history/<room_id>/<start>/<end>/export', methods=['GET'])
def export_room_history_range(room_id, start, end):
    try:
        # Query the sensor data for a specific room in a specific time range
        query = "SELECT * FROM capteurs WHERE chambre = %s AND timestamp >= %s AND timestamp <= %s ALLOW FILTERING"
        rows = session.execute(query, (room_id, datetime.fromisoformat(start), datetime.fromisoformat(end)))
        data = []
        for row in rows:
            data.append({
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat(),
                'doorSign': getattr(row, 'doorsign', None),
                'ethylene': row.ethylene,
                'chambre': row.chambre,
                'conservMode': row.conservmode,
                'TempConsign': row.tempconsign,
                'forcageMode': row.forcagemode,
                'FanontSign': getattr(row, 'fanontsign', None),
                'FaninSign': getattr(row, 'faninsign', None),
                'humConsigne': row.humconsigne,
                'humSign': row.humsign,
                'CO2Consigne': row.co2consigne,
                'CO2': row.co2,
                'ethConsign': row.ethconsign,
                'ethSign': row.ethsign,
            })

        # Convert data to CSV format
        csv_data = "id,timestamp,doorSign,ethylene,chambre,conservMode,TempConsign,forcageMode,FanontSign,FaninSign,humConsigne,humSign,CO2Consigne,CO2,ethConsign,ethSign\n"
        for item in data:
            csv_data += ",".join([str(item[key]) for key in item.keys()]) + "\n"

        # Return CSV file as response
        response = jsonify(csv_data)
        response.headers["Content-Disposition"] = "attachment; filename=room_history.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
 