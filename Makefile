.PHONY: help build clean test fmt vet install run-frames run-catalog run-frames-a4 add-ec2 add-lambda

BIN_DIR := .bin
BINARY  := $(BIN_DIR)/aet

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the aet binary
	@mkdir -p $(BIN_DIR)
	go build -o $(BINARY) ./cmd
	@echo "Built: $(BINARY)"

build-all: ## Build for all platforms
	@mkdir -p $(BIN_DIR)
	GOOS=darwin  GOARCH=amd64  go build -o $(BIN_DIR)/aet-darwin-amd64   ./cmd
	GOOS=darwin  GOARCH=arm64  go build -o $(BIN_DIR)/aet-darwin-arm64   ./cmd
	GOOS=linux   GOARCH=amd64  go build -o $(BIN_DIR)/aet-linux-amd64    ./cmd
	GOOS=windows GOARCH=amd64  go build -o $(BIN_DIR)/aet-windows-amd64.exe ./cmd
	@echo "Multi-platform build complete"

clean: ## Remove build artefacts
	rm -rf $(BIN_DIR) output/

test: ## Run tests
	go test ./...

fmt: ## Format code
	go fmt ./...

vet: ## Run go vet
	go vet ./...

install: ## Install aet to $GOPATH/bin
	go install ./cmd

# ── Convenience targets ────────────────────────────────────────────────────────

run-frames: build ## Copy AWS frame templates → output/aws-frames/
	$(BINARY) generate frames

run-frames-a4: build ## Copy A4 frame templates only
	$(BINARY) generate frames --size A4

run-catalog: build ## Copy service catalog → output/service-catalog.excalidraw
	$(BINARY) generate catalog

# Canvas add examples (canvas server must be running on localhost:3000)

add-ec2: build ## Add EC2 service icon + legend to the canvas
	$(BINARY) add service --name EC2 --x 200 --y 200

add-lambda: build ## Add Lambda service icon + legend to the canvas
	$(BINARY) add service --name Lambda --x 300 --y 200

list-services: build ## List all available AWS service icons
	$(BINARY) list services

.DEFAULT_GOAL := help

