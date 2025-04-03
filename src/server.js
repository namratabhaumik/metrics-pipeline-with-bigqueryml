const express = require("express");
const { PubSub } = require("@google-cloud/pubsub");
const { MetricServiceClient } = require("@google-cloud/monitoring");

const app = express();
const pubSubClient = new PubSub();
const monitoring = new MetricServiceClient();

const topicName = "metrics-topic";
const projectId = "nimble-analyst-402215";

app.use(express.json());

async function recordMetric(metricType, value) {
  const dataPoint = {
    interval: {
      endTime: {
        seconds: Math.floor(Date.now() / 1000),
      },
    },
    value: {
      doubleValue: value,
    },
  };

  const timeSeriesData = {
    metric: {
      type: `custom.googleapis.com/${metricType}`,
    },
    resource: {
      type: "generic_node",
      labels: {
        project_id: projectId,
        location: "us-central1",
        namespace: "default",
        node_id: "metrics-api-node",
      },
    },
    points: [dataPoint],
  };

  const request = {
    name: monitoring.projectPath(projectId),
    timeSeries: [timeSeriesData],
  };

  try {
    await monitoring.createTimeSeries(request);
    console.log(`Recorded metric ${metricType} with value ${value}`);
  } catch (error) {
    console.error("Error recording metric:", error.details || error.message);
  }
}

app.post("/metrics", async (req, res) => {
  const startTime = Date.now(); // Start latency measurement

  try {
    const messageBuffer = Buffer.from(JSON.stringify(req.body));
    await pubSubClient.topic(topicName).publish(messageBuffer);

    const latency = Date.now() - startTime; // Calculate latency

    // Record custom metrics
    await recordMetric("metrics_pipeline/ingestion_rate", 1); // Increment by 1 for each request
    await recordMetric("metrics_pipeline/latency", latency); // Record latency in milliseconds

    res.status(200).send("Metrics received and sent to Pub/Sub.");
  } catch (error) {
    console.error("Error publishing message:", error);
    res.status(500).send("Error processing metrics.");
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`Server running on port ${PORT}`);
});
