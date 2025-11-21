group "default" {
  targets = ["all"]
}

group "all" {
  targets = [
    "backend",
    "worker",
    "frontend",
    "autoscaler"
  ]
}

target "backend" {
  context = "backend"
  dockerfile = "Dockerfile"
  tags = ["ghcr.io/khalith/mailscout-backend:latest"]
  platforms = ["linux/amd64", "linux/arm64"]

  cache-from = ["type=local,src=.buildx-cache/backend"]
  cache-to   = ["type=local,dest=.buildx-cache/backend,mode=max"]
}

target "worker" {
  context = "."
  dockerfile = "worker/Dockerfile"
  tags = ["ghcr.io/khalith/mailscout-worker:latest"]
  platforms = ["linux/amd64", "linux/arm64"]

  cache-from = ["type=local,src=.buildx-cache/worker"]
  cache-to   = ["type=local,dest=.buildx-cache/worker,mode=max"]
}

target "frontend" {
  context = "frontend"
  dockerfile = "Dockerfile"
  tags = ["ghcr.io/khalith/mailscout-frontend:latest"]
  platforms = ["linux/amd64", "linux/arm64"]

  cache-from = ["type=local,src=.buildx-cache/frontend"]
  cache-to   = ["type=local,dest=.buildx-cache/frontend,mode=max"]
}

target "autoscaler" {
  context = "autoscaler"
  dockerfile = "Dockerfile"
  tags = ["ghcr.io/khalith/mailscout-autoscaler:latest"]
  platforms = ["linux/amd64", "linux/arm64"]

  cache-from = ["type=local,src=.buildx-cache/autoscaler"]
  cache-to   = ["type=local,dest=.buildx-cache/autoscaler,mode=max"]
}
