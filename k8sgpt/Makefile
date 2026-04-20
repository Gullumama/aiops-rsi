.PHONY: help build push deploy clean test

REGISTRY ?= k8sgpt
TAG ?= latest
IMAGE := $(REGISTRY):$(TAG)

help:
	@echo "K8sGPT Build Commands:"
	@echo "  make build       - Build K8sGPT Docker image"
	@echo "  make push        - Push image to registry"
	@echo "  make deploy      - Deploy to Kubernetes"
	@echo "  make clean       - Remove Docker image"
	@echo "  make test        - Test the image"

build:
	@echo "Building K8sGPT image: $(IMAGE)"
	docker build -t $(IMAGE) -f k8sgpt/Dockerfile .
	@echo "✓ Build complete"

push:
	@echo "Pushing image to registry..."
	docker push $(IMAGE)
	@echo "✓ Push complete"

deploy:
	@echo "Deploying K8sGPT to Kubernetes..."
	kubectl apply -f k8sgpt/deployment.yaml
	@echo "✓ Deployment complete"
	@echo "Waiting for pod to be ready..."
	kubectl rollout status deployment/k8sgpt -n aiops

clean:
	@echo "Removing Docker image: $(IMAGE)"
	docker rmi $(IMAGE) || true
	@echo "✓ Cleanup complete"

test:
	@echo "Testing K8sGPT image..."
	docker run --rm $(IMAGE) version || docker run --rm $(IMAGE) --help
	@echo "✓ Test complete"

logs:
	kubectl logs -f -n aiops deployment/k8sgpt

shell:
	kubectl exec -it -n aiops deployment/k8sgpt -- /bin/bash