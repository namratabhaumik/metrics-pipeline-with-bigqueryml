# Cloud-Native Backend System for Real-Time Data Ingestion and Anomaly Detection

## Project Overview

This project implements a cloud-native backend system to process real-time data, detect anomalies, and monitor metrics using various GCP services and Terraform for Infrastructure as Code (IaC). The pipeline includes:

- **Data Ingestion**: Real-time data ingestion using **Google Cloud Pub/Sub**.
- **Processing and Storage**: Cloud Run service to process metrics and store them in **BigQuery**.
- **Anomaly Detection**: Anomaly detection using **BigQuery ML**.
- **Deployment and Automation**: Terraform for automated provisioning and **GitHub CI/CD** for continuous integration and deployment.

## Prerequisites

1. **Google Cloud Platform (GCP)**:
   - Enable required APIs: `Cloud Run`, `Pub/Sub`, `BigQuery`, `IAM`.
   - Set up a **service account** with necessary permissions (Pub/Sub Admin, BigQuery Admin, Cloud Run Admin).
   - Install `gcloud` CLI.
2. **Terraform**:
   - Install Terraform (>=1.5).
   - Set up and initialize Terraform using terraform init, plan and apply.
3. **Docker**:
   - Install Docker to build and deploy the Cloud Run service.
4. **GitHub Actions**:
   - For CI/CD pipeline automation.

## Setup Instructions

### Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Google Cloud Platform Setup

1. Enable the following APIs:

   - Cloud Run
   - BigQuery
   - Pub/Sub
   - Cloud Functions
   - Monitoring & Logging

2. Create the required BigQuery dataset and table:

```sql
CREATE SCHEMA `metrics_dataset`;
CREATE TABLE `metrics_dataset.metrics_table` (
    timestamp INT64,
    latency FLOAT64,
    cpu INT64
);
```

3. Create a service account with appropriate roles:
   - `BigQuery Data Editor`
   - `Cloud Run Invoker`
   - `Pub/Sub Publisher`
   - `Viewer` (for logging)

## Deployment Steps

### Terraform

- Store all Terraform files in the `terraform/` folder.
- Run the following commands to deploy infrastructure:

```bash
terraform init
terraform apply
```

### GitHub CI/CD

- Ensure you have added the `GCP_SA_KEY` secret in your GitHub repository settings.
- Push your code to trigger automatic deployment.

### Step 2: Deploy Cloud Run Manually (Alternate)

If Terraform is not used:

1. Build the Docker image:
   ```bash
   docker build -t gcr.io/your-project-id/processmetrics cloud_run/
   ```
2. Push to GCR:
   ```bash
   docker push gcr.io/your-project-id/processmetrics
   ```
3. Deploy the container:
   ```bash
   gcloud run deploy processmetrics \
       --image gcr.io/your-project-id/processmetrics \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated
   ```

### Step 3: CI/CD with GitHub Actions

- The pipeline will automatically build and deploy the Cloud Run service on every push to the `master` branch.

## Usage Guide

### Cloud Run Services (Functional Pipeline)

- processmetrics: https://processmetrics-876160330159.us-central1.run.app
  This is triggered via pub/sub when a message is in the queue. See the next Ingesting Metrics step to send a message to the Pub/Sub.
- get_anomalies: https://get-anomalies-876160330159.us-central1.run.app
  This is used as a GET endpoint to get the anomalies from bigquery

### Ingesting Metrics

Send metrics using the Cloud Run endpoint:

```plaintext
POST https://metrics-api-876160330159.us-central1.run.app/metrics
Content-Type: application/json

{
    "timestamp": 1743548330,
    "latency": 312.0,
    "cpu": 100
}
```

### Retrieving Anomalies

Fetch detected anomalies using:

```plaintext
GET https://processmetrics-876160330159.us-central1.run.app/get_anomalies
```

### BigQuery Model Creation

```sql
CREATE MODEL `metrics_dataset.latency_anomalies`
OPTIONS(model_type='ARIMA_PLUS', time_series_data_col='latency', time_series_timestamp_col='timestamp') AS
SELECT
  TIMESTAMP_SECONDS(timestamp) AS timestamp,
  latency
FROM `metrics_dataset.metrics_table`
WHERE TIMESTAMP_SECONDS(timestamp) > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 730 DAY);
```

### Model Evaluation Query

```sql
SELECT *
FROM ML.EVALUATE(
    MODEL `metrics_dataset.latency_anomalies`,
    (
        SELECT
            TIMESTAMP_SECONDS(timestamp) AS timestamp,
            latency
        FROM `metrics_dataset.metrics_table`
    )
);
```

### Retrieve Anomalies

Query anomalies from BigQuery:

```sql
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
```

### Monitoring

- Google Cloud Monitoring was used to monitor the Cloud Run services and Pub/Sub message processing.
- Alerts were configured to track metrics such as ingestion rate and latency. Alerts were configured to be notified via email.
- Metrics are stored in **BigQuery** and can be accessed via the BigQuery UI or API.
- Anomaly detection results are automatically populated after the ML model runs.

## Alternate Approaches

- Used **GitHub Actions** instead of **GitLab CI/CD** for faster setup and easier integration.
- Switched to **manual Cloud Run deployment** during initial testing to debug issues faster.

## Known Issues and Limitations

1. **Uniform Data Issue**: The anomaly detection model might fail if the data lacks variance.
2. **Docker Build Issues**: Inconsistent dependencies may lead to build failures.

## Troubleshooting

- Check **Cloud Run logs** for errors:
  ```bash
  gcloud logs read --platform run
  ```
- Verify **BigQuery table schema** for any mismatches.
