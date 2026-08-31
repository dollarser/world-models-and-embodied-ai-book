.PHONY: check check-local check-strict docs-build docs-serve ch06-smoke ch06-smoke-local ch06-test-local ch09-smoke ch09-smoke-local ch09-test-local

check-local:
	python3 scripts/check_book.py
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch02-system-cards/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch04-data-audit/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch06-rssm/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch09-evaluation/experiment-card.json

check-strict:
	python3 scripts/docker_compose.py run --rm checks

check: check-local check-strict

docs-build:
	python3 scripts/docker_compose.py run --rm docs

docs-serve:
	python3 scripts/docker_compose.py run --rm --service-ports docs mkdocs serve --dev-addr=0.0.0.0:8000

ch06-smoke:
	python3 scripts/docker_compose.py run --rm ch06-smoke

ch06-smoke-local:
	python3 labs/track-a-world-model-control/ch06-rssm/scripts/smoke.py

ch06-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch06-rssm/tests -p 'test_*.py'

ch09-smoke:
	python3 scripts/docker_compose.py run --rm ch09-smoke

ch09-smoke-local:
	python3 labs/track-a-world-model-control/ch09-evaluation/scripts/smoke.py

ch09-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch09-evaluation/tests -p 'test_*.py'
