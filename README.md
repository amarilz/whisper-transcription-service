# Whisper Transcription Service

## Run locally with Docker Compose

The `whisper` service in `docker-compose.yaml` must define:

```yaml
image: whisper-transcription-service:${APP_VERSION:-dev}
```

Build and start the service using the version in `VERSION`:

```bash
APP_VERSION="$(cat VERSION)" docker compose up -d --build
```

Check the service:

```bash
curl http://localhost:8000/health
```

Stop it with `docker compose down`.

## Run all tests locally

Stop the running service first to free memory for the real Whisper integration test:

```bash
docker compose stop whisper

docker compose run --rm --no-deps \
  -v "$PWD:/workspace" -w /workspace whisper \
  sh -c "pip install -r requirements-dev.txt && python -m pytest"
```

This runs all 8 tests, including the real audio transcription test. To run only the 7 API tests, replace `python -m pytest` with `python -m pytest -m 'not integration'`.

## Build Docker image from `main`

```bash
git switch main
git pull --ff-only origin main
docker build --platform linux/arm64 -t "whisper-transcription-service:$(cat VERSION)" .
```

## Create a release

1. Update `VERSION` (for example, `0.2.0`) and run all tests locally as shown above.
2. Commit and push the version change:

```bash
git add VERSION
git commit -m "Release $(cat VERSION)"
git push origin main
```

3. Create and push the matching Git tag:

```bash
VERSION="$(cat VERSION)"
git tag -a "v${VERSION}" -m "Release ${VERSION}"
git push origin "v${VERSION}"
```

Pushing the tag triggers GitHub Actions to validate the version, run the API tests, build the ARM64 Docker image, and create a GitHub Release. The image is **not** published to a container registry.
