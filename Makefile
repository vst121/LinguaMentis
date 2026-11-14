.PHONY: help dev test test-backend test-frontend test-e2e test-eval lint clean

help: ## Zeigt alle verfügbaren Make-Befehle
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

dev: ## Startet Backend (FastAPI) und Frontend (Next.js) im Devcontainer
	./scripts/dev.sh

test: test-backend test-frontend ## Führt alle Backend- und Frontend-Tests aus

test-backend: ## Führt Backend Unit-, Integrations- und Offline-Eval-Tests aus
	cd backend && uv run pytest

test-frontend: ## Führt Frontend Unit-, Komponenten- und Seitentests (Vitest) aus
	cd frontend && pnpm test

test-e2e: ## Führt End-to-End-Browser-Tests (Playwright) aus
	cd frontend && pnpm run test:e2e

test-eval: ## Führt das AI-Evaluation-Harness live gegen Gemini aus
	cd backend && RUN_AI_EVALUATION=1 uv run pytest -m evaluation

lint: ## Prüft Code-Qualität und Typen in Backend und Frontend
	cd backend && uv run ruff check src tests
	cd frontend && pnpm run lint && pnpm exec tsc --noEmit

clean: ## Entfernt temporäre Test-, Linter- und Build-Caches
	rm -rf backend/.pytest_cache backend/.ruff_cache frontend/.next frontend/test-results frontend/playwright-report frontend/tsconfig.tsbuildinfo
	find backend -type d -name "__pycache__" -exec rm -rf {} +
