# OctoPing

This repository contains a simple Dockerized service that polls the GitHub Notifications API and relays new notifications to a webhook URL.

## Install

Deploy with the following Docker command or use the provided Docker Compose file.

```bash
docker run -d \
  --name octoping \
  -e GITHUB_TOKEN=ghp_xxxxxxxxx \
  -e WEBHOOK_URL=https://example.com/webhook \
  -e POLL_INTERVAL=60 \
  -v ./data:/data \
  ghcr.io/kieranlane/octoping:latest
```

## Environment Variables
- `GITHUB_TOKEN`: GitHub token with `notifications` scope.
- `WEBHOOK_URL`: Your destination webhook URL.
- `POLL_INTERVAL`: (Optional) Polling interval in seconds, default `60`.
- `STATE_FILE`: (Optional) Path to store last seen timestamp, default `/data/state.json`.

## Build

1. Build the Docker image:
```bash
docker build -t octoping .
```

2. Run the container:
```bash
docker run -d \
  --name octoping \
  -e GITHUB_TOKEN=ghp_xxxxxxxxx \
  -e WEBHOOK_URL=https://example.com/webhook \
  -e POLL_INTERVAL=60 \
  -v ./data:/data \
  octoping
```