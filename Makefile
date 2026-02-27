.PHONY: help build clean test fmt vet install \
        run-frames run-frames-a4 run-catalog \
        add-ec2 add-lambda \
        list-services list-compute list-analytics list-database \
        list-networking list-security list-storage list-ai \
        sample-web3tier sample-serverless

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

list-compute: build ## List Compute category services
	$(BINARY) list services --category Compute

list-analytics: build ## List Analytics category services
	$(BINARY) list services --category Analytics

list-database: build ## List Database category services
	$(BINARY) list services --category Database

list-networking: build ## List Networking-Content-Delivery category services
	$(BINARY) list services --category "Networking & Content Delivery"

list-security: build ## List Security-Identity-Compliance category services
	$(BINARY) list services --category "Security, Identity, & Compliance"

list-storage: build ## List Storage category services
	$(BINARY) list services --category Storage

list-ai: build ## List AI/ML category services
	$(BINARY) list services --category "Machine Learning"

# ── Sample architecture diagrams ──────────────────────────────────────────────
# Step 1: generate → creates output file (open in Excalidraw)
# Step 2: add service → pushes icons to the running canvas server (localhost:3000)

sample-web3tier: build ## [Sample] 3-tier web: generate A4 frame + add services to canvas
	@echo "=== Step 1: generate A4 landscape frame ==="
	$(BINARY) generate frames --size A4 --output output/samples/web3tier/
	@echo ""
	@echo "=== Step 2: add services to canvas (canvas server must be running) ==="
	@echo "--- Row 1: DNS / CDN (y=80) ---"
	$(BINARY) add service --name "Route 53"             --x 100 --y  80 --legend-x 900 --legend-y  80
	$(BINARY) add service --name "CloudFront"           --x 300 --y  80 --legend-x 900 --legend-y 116
	@echo "--- Row 2: Load Balancer (y=240) ---"
	$(BINARY) add service --name "Elastic Load Balancing" --x 200 --y 240 --legend-x 900 --legend-y 152
	@echo "--- Row 3: Compute (y=400) ---"
	$(BINARY) add service --name "EC2 Auto Scaling"     --x 100 --y 400 --legend-x 900 --legend-y 188
	$(BINARY) add service --name "EC2"                  --x 300 --y 400 --legend-x 900 --legend-y 224
	$(BINARY) add service --name "S3"                   --x 500 --y 400 --legend-x 900 --legend-y 260
	@echo "--- Row 4: Data (y=560) ---"
	$(BINARY) add service --name "RDS"                  --x 100 --y 560 --legend-x 900 --legend-y 296
	$(BINARY) add service --name "ElastiCache"          --x 300 --y 560 --legend-x 900 --legend-y 332
	$(BINARY) add service --name "CloudWatch"           --x 500 --y 560 --legend-x 900 --legend-y 368
	@echo ""
	@echo "Done. Open output/samples/web3tier/A4-landscape.excalidraw in Excalidraw."

sample-serverless: build ## [Sample] Serverless: generate A4 frame + add services to canvas
	@echo "=== Step 1: generate A4 landscape frame ==="
	$(BINARY) generate frames --size A4 --output output/samples/serverless/
	@echo ""
	@echo "=== Step 2: add services to canvas (canvas server must be running) ==="
	@echo "--- Row 1: Edge (y=80) ---"
	$(BINARY) add service --name "Route 53"             --x 100 --y  80 --legend-x 900 --legend-y  80
	$(BINARY) add service --name "CloudFront"           --x 300 --y  80 --legend-x 900 --legend-y 116
	$(BINARY) add service --name "Cognito"              --x 500 --y  80 --legend-x 900 --legend-y 152
	@echo "--- Row 2: API (y=240) ---"
	$(BINARY) add service --name "API Gateway"          --x 200 --y 240 --legend-x 900 --legend-y 188
	$(BINARY) add service --name "WAF"                  --x 400 --y 240 --legend-x 900 --legend-y 224
	@echo "--- Row 3: Compute (y=400) ---"
	$(BINARY) add service --name "Lambda"               --x 100 --y 400 --legend-x 900 --legend-y 260
	$(BINARY) add service --name "Step Functions"       --x 300 --y 400 --legend-x 900 --legend-y 296
	$(BINARY) add service --name "EventBridge"          --x 500 --y 400 --legend-x 900 --legend-y 332
	@echo "--- Row 4: Data / Observability (y=560) ---"
	$(BINARY) add service --name "DynamoDB"             --x 100 --y 560 --legend-x 900 --legend-y 368
	$(BINARY) add service --name "S3"                   --x 300 --y 560 --legend-x 900 --legend-y 404
	$(BINARY) add service --name "CloudWatch"           --x 500 --y 560 --legend-x 900 --legend-y 440
	@echo ""
	@echo "Done. Open output/samples/serverless/A4-landscape.excalidraw in Excalidraw."

.DEFAULT_GOAL := help

