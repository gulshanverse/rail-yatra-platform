# AI stream timeout

The backend keeps the upstream AI SSE fetch alive for 65 seconds by default, configurable with `AI_SERVICE_TIMEOUT_MS` (10-120 seconds). The AI workflow itself has a 45-second execution timeout, so the backend must not abort the fetch before that workflow can complete.