from flask import Flask, jsonify
from google.cloud import bigquery

app = Flask(__name__)
client = bigquery.Client()

@app.route("/get_anomalies", methods=["GET"])
def get_anomalies(request):
    """Fetch anomalies detected by the BigQuery ML model."""
    try:
        query = """
            SELECT 
                timestamp,
                latency,
                is_anomaly,
                anomaly_probability
            FROM ML.DETECT_ANOMALIES(
                MODEL `metrics_dataset.latency_anomalies`,
                STRUCT(0.01 AS anomaly_prob_threshold),
                (
                    SELECT 
                        TIMESTAMP_SECONDS(timestamp) AS timestamp,  
                        latency
                    FROM `metrics_dataset.metrics_table`
                )
            )
            ORDER BY timestamp DESC
            LIMIT 100;
        """
        
        query_job = client.query(query)
        results = [dict(row) for row in query_job]

        return jsonify(results), 200

    except Exception as e:
        print(f"Error fetching anomalies: {e}")
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
