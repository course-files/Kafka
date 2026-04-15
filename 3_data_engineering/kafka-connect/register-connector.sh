#!/bin/bash

# -----------------------------------------------------------------------------
# REGISTER THE DEBEZIUM POSTGRESQL CONNECTOR
# -----------------------------------------------------------------------------
# This script registers the Debezium connector with Kafka Connect by sending
# the connector configuration to the Kafka Connect REST API.
#
# The REST API is the only way to manage connectors in Kafka Connect.
# There is no configuration file you edit directly — everything is done
# through HTTP requests to port 8083.
#
# Run this script AFTER docker-compose up has completed and all services
# are healthy. Specifically, kafka-connect must be fully started before
# this script will succeed.
#
# Usage:
#   chmod +x register-connector.sh
#   ./register-connector.sh
# -----------------------------------------------------------------------------

CONNECT_URL="http://localhost:8083/connectors"
CONFIG_FILE="$(dirname "$0")/connector-config.json"

echo "Waiting for Kafka Connect to be ready..."

# Poll the Kafka Connect REST API until it responds.
# Kafka Connect can take up to 60 seconds to fully initialise.
until curl -sf "$CONNECT_URL" > /dev/null 2>&1; do
  echo "  Kafka Connect is not ready yet. Retrying in 5 seconds..."
  sleep 5
done

echo "Kafka Connect is ready."
echo ""
echo "Registering Debezium PostgreSQL connector..."

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$CONNECT_URL" \
  -H "Content-Type: application/json" \
  -d @"$CONFIG_FILE")

if [ "$RESPONSE" -eq 201 ]; then
  echo "✅ Connector registered successfully (HTTP 201)."
  echo ""
  echo "You can verify the connector status with:"
  echo "  curl http://localhost:8083/connectors/orders-postgres-connector/status"
elif [ "$RESPONSE" -eq 409 ]; then
  echo "⚠  Connector already exists (HTTP 409). No changes made."
  echo "   To reconfigure it, delete it first:"
  echo "   curl -X DELETE http://localhost:8083/connectors/orders-postgres-connector"
else
  echo "❌ Unexpected response: HTTP $RESPONSE"
  echo "   Check that Kafka Connect is running: curl http://localhost:8083/"
  exit 1
fi