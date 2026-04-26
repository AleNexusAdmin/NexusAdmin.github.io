#!/usr/bin/env bash
set -euo pipefail

OUTPUT="NexusAdmin.github.io.zip"

zip -r "$OUTPUT" . \
  -x '.git/*' \
     '__pycache__/*' \
     '*.pyc' \
     '*.zip'

echo "Arquivo gerado: $OUTPUT"
