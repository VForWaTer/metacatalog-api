.PHONY: help build-manager build-all start stop clean dev

# Default target
help:
	@echo "Available commands:"
	@echo "  build-manager  - Build the SvelteKit manager app"
	@echo "  build-all      - Build all components"
	@echo "  start          - Build manager and start all services"
	@echo "  stop           - Stop all services"
	@echo "  clean          - Clean build artifacts"
	@echo "  dev            - Start development mode (database + API + frontend in single container)"
	@echo ""
	@echo "Admin token management:"
	@echo "  create-admin-token  - Create a new admin token"
	@echo "  validate-token      - Validate a specific token (use: make validate-token TOKEN=your-token)"
	@echo "  cli-help            - Show CLI help"

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

# Development mode - start all services in single container
dev:
	@echo "Starting development mode..."
	@echo "Starting database and combined app container (API + frontend)..."
	docker compose -f docker-compose.dev.yml up

# Create admin token (requires database to be running)
create-admin-token:
	@echo "Creating admin token..."
	docker compose up -d
	METACATALOG_URI=postgresql://postgres:postgres@localhost:5433/metacatalog python -m metacatalog_api.cli --create-admin-token
	docker compose down

# Validate a specific token
validate-token:
	@echo "Validating admin token..."
	docker compose up -d
	METACATALOG_URI=postgresql://postgres:postgres@localhost:5433/metacatalog python -m metacatalog_api.cli --validate-admin-token $(TOKEN)
	docker compose down

# Show CLI help
cli-help:
	@echo "Showing CLI help..."
	python -m metacatalog_api.cli --help