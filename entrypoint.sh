#!/bin/bash
# entrypoint.sh
# Downloads model weights from S3 before starting the API server.
# Called by ECS instead of CMD when weights need to be fetched.
#
# Required environment variables (set in ECS task definition):
#   S3_BUCKET   — e.g. mahjong-reviewer-models
#   S3_KEY      — e.g. weights/cnn_weights.pt
#   MODEL_PATH  — local path to write weights, e.g. data/models/cnn_weights.pt

set -e

echo "Downloading model weights from s3://${S3_BUCKET}/${S3_KEY}..."
mkdir -p "$(dirname "$MODEL_PATH")"
aws s3 cp "s3://${S3_BUCKET}/${S3_KEY}" "$MODEL_PATH"
echo "Weights downloaded to $MODEL_PATH"

echo "Starting API server..."
exec uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
