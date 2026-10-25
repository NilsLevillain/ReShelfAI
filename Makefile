# Reshelf task runner. Planned targets arrive week by week (see docs/war_plan.md section 7).
# Python runs from apps/api. Set UV_PROJECT_ENVIRONMENT to keep the venv outside a synced folder.

API := apps/api
SCENARIOS := default luxury_protection

.PHONY: demo-data test lint

demo-data:
	@for s in $(SCENARIOS); do \
		(cd $(API) && PYTHONPATH=../../data/generator uv run python -m reshelf_datagen \
			--scenario ../../data/scenarios/$$s.yaml --out ../../data/generated/$$s) || exit 1; \
	done

test:
	cd $(API) && uv run pytest -q

lint:
	cd $(API) && uv run ruff check . ../../data/generator \
		&& uv run ruff format --check . ../../data/generator \
		&& uv run mypy . ../../data/generator
