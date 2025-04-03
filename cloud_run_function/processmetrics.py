from flask import Flask, request
from google.cloud import bigquery
import json
import base64

app = Flask(__name__)
client = bigquery.Client()
table_id = "nimble-analyst-402215.metrics_dataset.metrics_table"

@app.route("/", methods=["POST"])
def process_metrics(request):
    """Receives messages from Pub/Sub and stores metrics in BigQuery."""
    try:
        envelope = request.get_json()
        if not envelope or "message" not in envelope:
            return "Bad Request: No Pub/Sub message found", 400

        pubsub_message = envelope["message"]
        data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        message = json.loads(data)

        rows_to_insert = [{
            "timestamp": message.get("timestamp"),
            "latency": message.get("latency"),
            "cpu": message.get("cpu")
        }]

        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            print(f"Error inserting rows: {errors}")
            return "Error inserting data", 500
        else:
            print("Metrics successfully stored in BigQuery.")
            return "Success", 200

    except Exception as e:
        print(f"Error processing message: {e}")
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(debug=True)
