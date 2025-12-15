#!/bin/bash
cd /home/kavia/workspace/code-generation/freelancer-time-tracker-and-analytics-186558-186568/time_tracking_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

