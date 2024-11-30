from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Directory to save data
DATA_DIRECTORY = 'client_data'

if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY)

@app.route('/psyc_side', methods=['POST'])
def upload_data():
    try:
        # Get JSON data from the client
        data = request.get_json()
        print(data)
        client_id = data.get('client_id', 'unknown_client')
        
        # Save the data as a JSON file
        file_path = os.path.join(DATA_DIRECTORY, f"{client_id}.json")
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=2)

        return jsonify({"message": "Data uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
