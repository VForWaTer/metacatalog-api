.PHONY: help build-manager build-all start stop clean dev

# Default target
help:
	@echo "Available commands:"
	@echo "  build-manager  - Build the SvelteKit manager app"
	@echo "  build-all      - Build all components"
	@echo "  start          - Build manager and start all services"
	@echo "  stop           - Stop all services"
	@echo "  clean          - Clean build artifacts"
	@echo "  dev            - Start in development mode (separate processes)"

# Build the SvelteKit manager app
build-manager:
	@echo "Building SvelteKit manager app..."
	cd metacatalog_api/apps/manager && npm install
	cd metacatalog_api/apps/manager && npm run build
	@echo "Manager app built successfully!"

# Build all components
build-all: build-manager
	@echo "All components built!"

# Start all services (build + docker-compose)
start: build-manager
	@echo "Starting all services..."
	docker compose up --build

# Stop all services
stop:
	@echo "Stopping all services..."
	docker compose down

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf metacatalog_api/apps/manager/dist
	rm -rf metacatalog_api/apps/manager/.svelte-kit
	rm -rf metacatalog_api/apps/manager/node_modules
	@echo "Clean complete!"

# Development mode - start database and run manager in dev mode
dev:
	@echo "Starting development mode..."
	@echo "Starting database..."
	docker compose up -d
	@echo "Database started. Starting manager in development mode..."
	cd metacatalog_api/apps/manager && npm run dev 