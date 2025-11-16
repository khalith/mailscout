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
  tags = ["mailscout/backend:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "worker" {
  context = "."
  dockerfile = "worker/Dockerfile"
  tags = ["mailscout/worker:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "frontend" {
  context = "frontend"
  dockerfile = "Dockerfile"
  tags = ["mailscout/frontend:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "autoscaler" {
  context = "autoscaler"
  dockerfile = "Dockerfile"
  tags = ["mailscout/autoscaler:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
}
