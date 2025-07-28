.PHONY: create dev test test-coverage type-coverage build clean install publish check-dist help update-llms-txt

# Usage targets
create:
	@echo "🛠️  Create a rule with the given diff url ..."
	# This allows: make create <diff_url>
	python -m high_taste.rules.create --debug $(filter-out $@,$(MAKECMDGOALS))

# Development targets
dev:
	@echo "🛠️  Running development checks..."
	uv run ruff check . --fix --unsafe-fixes
	uv run ruff format .
	uv run ty check .
	@echo "✅ Development checks complete!"

test:
	@echo "🧪 Running tests (last failed first)..."
	uv run pytest --lf

test-all:
	@echo "🧪 Running all tests..."
	uv run pytest -v

test-coverage:
	@echo "📊 Running tests with coverage..."
	uv run pytest --cov=. --cov-report=html --cov-report=term --durations=5

type-coverage:
	@echo "🔍 Checking type annotation coverage..."
	@echo "📊 Checking for missing return type annotations..."
	@uv run ruff check . --select ANN201 --quiet || echo "❌ Missing return type annotations found"
	@echo "📊 Checking for missing parameter type annotations..."
	@uv run ruff check . --select ANN001,ANN002,ANN003 --quiet || echo "❌ Missing parameter type annotations found"
	@echo "📊 Running comprehensive type check..."
	@uv run ty check . > /dev/null 2>&1 && echo "✅ Type checking passed - excellent coverage!" || echo "❌ Type checking failed"
	@echo "📊 Checking for Any usage (should be minimal)..."
	@uv run ruff check . --select ANN401 --quiet && echo "✅ No problematic Any usage found" || echo "⚠️  Some Any usage found (may be acceptable in tests)"
	@echo "📈 Type coverage assessment complete!"

# Package management
install:
	@echo "📦 Installing package in development mode..."
	uv pip install -e .
	@echo "✅ Package installed!"

build: clean
	@echo "🏗️  Building package..."
	uv build
	@echo "✅ Package built successfully!"
	@echo "📁 Built files:"
	@ls -la dist/

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete!"

check-dist:
	@echo "🔍 Checking distribution..."
	@echo "📊 Built files:"
	@ls -la dist/
	@echo "✅ Distribution check complete!"

# Publishing
publish-test: build check-dist
	@echo "🚀 Publishing to TestPyPI..."
	@echo "⚠️  Using token from ~/.pypirc or TWINE_PASSWORD environment variable"
	@if [ -z "$$TWINE_PASSWORD" ]; then \
		echo "📝 Reading token from ~/.pypirc..."; \
		TOKEN=$$(grep "password = " ~/.pypirc | cut -d' ' -f3); \
		uv publish dist/* --repository testpypi --username __token__ --password "$$TOKEN"; \
	else \
		uv publish dist/* --repository testpypi --username __token__; \
	fi
	@echo "✅ Published to TestPyPI!"

publish: build check-dist
	@echo "🚀 Publishing to PyPI..."
	@read -p "Are you sure you want to publish to PyPI? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "⚠️  Using token from ~/.pypirc or TWINE_PASSWORD environment variable"
	@if [ -z "$$TWINE_PASSWORD" ]; then \
		echo "📝 Reading token from ~/.pypirc..."; \
		TOKEN=$$(grep "password = " ~/.pypirc | cut -d' ' -f3); \
		uv publish dist/* --username __token__ --password "$$TOKEN"; \
	else \
		uv publish dist/* --username __token__; \
	fi
	@echo "✅ Published to PyPI!"

# Local testing
test-cli:
	@echo "🖥️  Testing CLI locally..."
	uv run high-taste --help
	uv run high-taste rules
	@echo "✅ CLI test complete!"

test-uvx:
	@echo "🌐 Testing with uvx (from built package)..."
	uvx --from ./dist/high_taste-*.whl high-taste --help
	uvx --from ./dist/high_taste-*.whl high-taste rules
	@echo "✅ uvx test complete!"

# Git operations
git-status:
	@echo "📋 Git status:"
	git status --short
	@echo "📈 Recent commits:"
	git log --oneline -5

commit:
	@echo "💾 Staging and committing changes..."
	git add .
	@read -p "Enter commit message: " msg && git commit -m "$$msg 🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

push: commit
	@echo "⬆️  Pushing to remote..."
	git push
	@echo "✅ Pushed successfully!"

# Documentation
update-llms-txt:
	@echo "📚 Updating llms/*.txt documentation files..."
	@mkdir -p llms
	@claude -p "Please update the llms/ directory with documentation for tools mentioned in Python.md. For each tool: \
	\
	1. CLI TOOLS: Run '{tool} --help' to get help output. Save to llms/{tool}.txt. \
	2. PYTHON PACKAGES: Check for official llms.txt files at common locations: \
	   - https://docs.{package}.dev/latest/llms.txt or llms-full.txt \
	   - https://{package}.readthedocs.io/llms.txt \
	   - For pydantic-ai: https://ai.pydantic.dev/llms-full.txt \
	   - For fasthtml: https://fastht.ml/docs/llms-ctx-full.txt \
	3. For each file, add a footer documenting: \
	   - Source URL or command used \
	   - Retrieval date \
	   - Method (curl, help command, etc.) \
	\
	IMPORTANT: Only update existing files or create new ones for tools in Python.md. Use curl to download llms.txt files when available. For CLI tools not installed, create placeholder noting unavailability."
	@echo "✅ llms/*.txt files updated!"

# Comprehensive workflows
ci: dev test-coverage type-coverage
	@echo "🔄 CI pipeline complete!"

release: ci build check-dist test-uvx
	@echo "🎉 Release pipeline complete! Ready to publish."
	@echo "💡 Run 'make publish-test' to publish to TestPyPI first"
	@echo "💡 Run 'make publish' to publish to PyPI"

# Help
help:
	@echo "🔧 High-Taste Development Commands:"
	@echo ""
	@echo "Development:"
	@echo "  dev              Run linting, formatting, and type checking"
	@echo "  test             Run tests (last failed first)"
	@echo "  test-all         Run all tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  type-coverage    Check type annotation coverage"
	@echo ""
	@echo "Package Management:"
	@echo "  install          Install package in development mode"
	@echo "  build            Build package (wheel + source dist)"
	@echo "  clean            Clean build artifacts"
	@echo "  check-dist       Show built distribution files"
	@echo ""
	@echo "Testing:"
	@echo "  test-cli         Test CLI commands locally"
	@echo "  test-uvx         Test package with uvx"
	@echo ""
	@echo "Publishing:"
	@echo "  publish-test     Publish to TestPyPI (auto-reads ~/.pypirc)"
	@echo "  publish          Publish to PyPI (interactive, auto-reads ~/.pypirc)"
	@echo ""
	@echo "Git Operations:"
	@echo "  git-status       Show git status and recent commits"
	@echo "  commit           Stage, commit with message"
	@echo "  push             Commit and push changes"
	@echo ""
	@echo "Workflows:"
	@echo "  ci               Run full CI pipeline"
	@echo "  release          Complete release pipeline"
	@echo ""
	@echo "Documentation:"
	@echo "  update-llms-txt  Update llms documentation"
	@echo ""
	@echo "💡 Publishing: Uses token from ~/.pypirc or TWINE_PASSWORD env var"
