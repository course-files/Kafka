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
# are healthy. Specifically, kafka-connect must be fully started so that
# this script can succeed.
#
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(dirname "$0")"
CONNECT_URL="http://localhost:8083/connectors"
CONFIG_FILE="$SCRIPT_DIR/connector-config.json"

# -----------------------------------------------------------------------------
# Load environment variables from .env
# -----------------------------------------------------------------------------
# We use `source <(sed 's/\r$//' "$ENV_FILE")` rather than `source "$ENV_FILE"`
# directly. On Windows, .env files are often saved with CRLF line endings
# (\r\n). Without stripping the \r, every variable value would contain a
# trailing carriage return, silently corrupting passwords and usernames.
#
# The <(...) syntax is process substitution: it runs the `sed` command and
# feeds its output to source as if it were a file.
#
# set -a / set +a ensures every variable loaded here is exported to child
# processes (like the render_template function below).
# -----------------------------------------------------------------------------
echo "Script directory = $SCRIPT_DIR"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env file not found at $ENV_FILE"
  echo "   Copy .env.example to .env and fill in the correct credentials."
  exit 1
fi

set -a
source <(sed 's/\r$//' "$ENV_FILE")
set +a

# -----------------------------------------------------------------------------
# Template rendering — pure bash replacement for envsubst
# -----------------------------------------------------------------------------
# envsubst (from the gettext package) is the standard Unix tool for
# substituting ${VAR} placeholders in text. However, it is not available
# on macOS without Homebrew, and it is not included in Git Bash on Windows.
#
# This function replicates its behaviour using bash's built-in string
# substitution syntax: ${variable//find/replace}
# It should work identically on Linux, macOS, and Git Bash.
# -----------------------------------------------------------------------------
render_template() {
    local content
    content=$(cat "$1")
    content="${content//\$\{POSTGRES_USER\}/$POSTGRES_USER}"
    content="${content//\$\{POSTGRES_PASSWORD\}/$POSTGRES_PASSWORD}"
    content="${content//\$\{POSTGRES_DB\}/$POSTGRES_DB}"
    printf '%s' "$content"
}

echo "Waiting for Kafka Connect to be ready..."

until curl -sf "$CONNECT_URL" > /dev/null 2>&1; do
  echo "  Kafka Connect is not ready yet. Retrying in 5 seconds..."
  sleep 5
done

echo "Kafka Connect is ready."
echo ""
echo "Registering Debezium PostgreSQL connector..."

RESPONSE=$(render_template "$CONFIG_FILE" | curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$CONNECT_URL" \
  -H "Content-Type: application/json" \
  -d @-)

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