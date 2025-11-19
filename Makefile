.PHONY: help setup up down logs clean test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Generate .env file and prepare environment
	@echo "Setting up environment..."
	@python3 scripts/generate_env.py
	@echo "✅ Setup complete! Please edit .env with your credentials."

up: ## Start all services
	docker-compose up -d
	@echo "✅ Services started. Airflow UI: http://localhost:8080"

up-services: ## Start all services including ingestion/transformation
	docker-compose --profile services up -d

down: ## Stop all services
	docker-compose down

down-volumes: ## Stop all services and remove volumes (⚠️ deletes data)
	docker-compose down -v

recreate-network: ## Recreate Docker network (fixes network configuration issues)
	docker-compose down
	docker network prune -f
	docker-compose up -d

logs: ## Show logs from all services
	docker-compose logs -f

logs-airflow: ## Show Airflow logs
	docker-compose logs -f airflow-webserver airflow-scheduler

logs-postgres: ## Show PostgreSQL logs
	docker-compose logs -f postgres

build: ## Rebuild Docker images
	docker-compose build

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

test-ingestion: ## Test ingestion service manually (optionally pass DATE=YYYY-MM-DD)
	@bash scripts/run_ingestion.sh $(if $(DATE),$(DATE),)

test-transformation: ## Test transformation service manually (optionally pass DATE=YYYY-MM-DD)
	@bash scripts/run_with_fallback.sh transformation python -m transformation.main $(if $(DATE),$(DATE),)

test-s3: ## Test S3 bucket connectivity and list uploaded files
	@bash scripts/run_with_fallback.sh ingestion python scripts/test_s3.py

psql: ## Connect to PostgreSQL
	docker-compose exec postgres psql -U retail_user -d retail_analytics

health-check: ## Run comprehensive pipeline health check
	@bash scripts/check_pipeline_health.sh

add-sample-data: ## Add sample data for a specific date (usage: make add-sample-data DATE=2024-01-16)
	@bash scripts/add_sample_data.sh $(DATE)

