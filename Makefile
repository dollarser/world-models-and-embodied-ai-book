.PHONY: check check-local check-strict docs-build docs-serve ch02-smoke ch02-smoke-local ch02-test-local ch03-smoke ch03-smoke-local ch03-test-local ch04-smoke ch04-smoke-local ch04-test-local ch05-smoke ch05-smoke-local ch05-test-local ch06-smoke ch06-smoke-local ch06-test-local ch07-smoke ch07-smoke-local ch07-test-local ch09-smoke ch09-smoke-local ch09-test-local ch10-smoke ch10-smoke-local ch10-test-local ch11-smoke ch11-smoke-local ch11-test-local ch12-smoke ch12-smoke-local ch12-test-local ch13-smoke ch13-smoke-local ch13-test-local ch14-smoke ch14-smoke-local ch14-test-local ch15-smoke ch15-smoke-local ch15-test-local ch16-smoke ch16-smoke-local ch16-test-local ch17-smoke ch17-smoke-local ch17-test-local ch19-smoke ch19-smoke-local ch19-test-local ch20-smoke ch20-smoke-local ch20-test-local ch21-smoke ch21-smoke-local ch21-test-local

check-local:
	python3 scripts/check_book.py
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch02-system-cards/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-c-spatial/ch03-geometry-control/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch04-data-audit/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch05-generative-foundations/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch06-rssm/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch07-model-planning/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch09-evaluation/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-c-spatial/ch10-jepa-probing/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-c-spatial/ch11-action-video/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-c-spatial/ch12-actionable-space/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-b-policy/ch13-imitation/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-b-policy/ch14-generative-actions/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-b-policy/ch15-vla-contract/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-b-policy/ch16-cross-embodiment/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch17-policy-utility/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-a-world-model-control/ch19-sim-gap/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-b-policy/ch20-evaluation/experiment-card.json
	python3 scripts/validate_experiment_card.py labs/track-b-policy/ch21-deployment-gate/experiment-card.json

check-strict:
	python3 scripts/docker_compose.py run --rm checks

check: check-local check-strict

docs-build:
	python3 scripts/docker_compose.py run --rm docs

docs-serve:
	python3 scripts/docker_compose.py run --rm --service-ports docs mkdocs serve --dev-addr=0.0.0.0:8000

ch02-smoke:
	python3 scripts/docker_compose.py run --rm ch02-smoke

ch02-smoke-local:
	python3 labs/track-a-world-model-control/ch02-system-cards/scripts/smoke.py

ch02-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch02-system-cards/tests -p 'test_*.py'

ch03-smoke:
	python3 scripts/docker_compose.py run --rm ch03-smoke

ch03-smoke-local:
	python3 labs/track-c-spatial/ch03-geometry-control/scripts/smoke.py

ch03-test-local:
	python3 -m unittest discover -s labs/track-c-spatial/ch03-geometry-control/tests -p 'test_*.py'

ch04-smoke:
	python3 scripts/docker_compose.py run --rm ch04-smoke

ch04-smoke-local:
	python3 labs/track-a-world-model-control/ch04-data-audit/scripts/smoke.py

ch04-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch04-data-audit/tests -p 'test_*.py'

ch05-smoke:
	python3 scripts/docker_compose.py run --rm ch05-smoke

ch05-smoke-local:
	python3 labs/track-a-world-model-control/ch05-generative-foundations/scripts/smoke.py

ch05-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch05-generative-foundations/tests -p 'test_*.py'

ch06-smoke:
	python3 scripts/docker_compose.py run --rm ch06-smoke

ch06-smoke-local:
	python3 labs/track-a-world-model-control/ch06-rssm/scripts/smoke.py

ch06-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch06-rssm/tests -p 'test_*.py'

ch07-smoke:
	python3 scripts/docker_compose.py run --rm ch07-smoke

ch07-smoke-local:
	python3 labs/track-a-world-model-control/ch07-model-planning/scripts/smoke.py

ch07-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch07-model-planning/tests -p 'test_*.py'

ch09-smoke:
	python3 scripts/docker_compose.py run --rm ch09-smoke

ch09-smoke-local:
	python3 labs/track-a-world-model-control/ch09-evaluation/scripts/smoke.py

ch09-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch09-evaluation/tests -p 'test_*.py'

ch10-smoke:
	python3 scripts/docker_compose.py run --rm ch10-smoke

ch10-smoke-local:
	python3 labs/track-c-spatial/ch10-jepa-probing/scripts/smoke.py

ch10-test-local:
	python3 -m unittest discover -s labs/track-c-spatial/ch10-jepa-probing/tests -p 'test_*.py'

ch11-smoke:
	python3 scripts/docker_compose.py run --rm ch11-smoke

ch11-smoke-local:
	python3 labs/track-c-spatial/ch11-action-video/scripts/smoke.py

ch11-test-local:
	python3 -m unittest discover -s labs/track-c-spatial/ch11-action-video/tests -p 'test_*.py'

ch12-smoke:
	python3 scripts/docker_compose.py run --rm ch12-smoke

ch12-smoke-local:
	python3 labs/track-c-spatial/ch12-actionable-space/scripts/smoke.py

ch12-test-local:
	python3 -m unittest discover -s labs/track-c-spatial/ch12-actionable-space/tests -p 'test_*.py'

ch13-smoke:
	python3 scripts/docker_compose.py run --rm ch13-smoke

ch13-smoke-local:
	python3 labs/track-b-policy/ch13-imitation/scripts/smoke.py

ch13-test-local:
	python3 -m unittest discover -s labs/track-b-policy/ch13-imitation/tests -p 'test_*.py'

ch14-smoke:
	python3 scripts/docker_compose.py run --rm ch14-smoke

ch14-smoke-local:
	python3 labs/track-b-policy/ch14-generative-actions/scripts/smoke.py

ch14-test-local:
	python3 -m unittest discover -s labs/track-b-policy/ch14-generative-actions/tests -p 'test_*.py'

ch15-smoke:
	python3 scripts/docker_compose.py run --rm ch15-smoke

ch15-smoke-local:
	python3 labs/track-b-policy/ch15-vla-contract/scripts/smoke.py

ch15-test-local:
	python3 -m unittest discover -s labs/track-b-policy/ch15-vla-contract/tests -p 'test_*.py'

ch16-smoke:
	python3 scripts/docker_compose.py run --rm ch16-smoke

ch16-smoke-local:
	python3 labs/track-b-policy/ch16-cross-embodiment/scripts/smoke.py

ch16-test-local:
	python3 -m unittest discover -s labs/track-b-policy/ch16-cross-embodiment/tests -p 'test_*.py'

ch17-smoke:
	python3 scripts/docker_compose.py run --rm ch17-smoke

ch17-smoke-local:
	python3 labs/track-a-world-model-control/ch17-policy-utility/scripts/smoke.py

ch17-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch17-policy-utility/tests -p 'test_*.py'

ch19-smoke:
	python3 scripts/docker_compose.py run --rm ch19-smoke

ch19-smoke-local:
	python3 labs/track-a-world-model-control/ch19-sim-gap/scripts/smoke.py

ch19-test-local:
	python3 -m unittest discover -s labs/track-a-world-model-control/ch19-sim-gap/tests -p 'test_*.py'

ch20-smoke:
	python3 scripts/docker_compose.py run --rm ch20-smoke

ch20-smoke-local:
	python3 labs/track-b-policy/ch20-evaluation/scripts/smoke.py

ch20-test-local:
	python3 -m unittest discover -s labs/track-b-policy/ch20-evaluation/tests -p 'test_*.py'

ch21-smoke:
	python3 scripts/docker_compose.py run --rm ch21-smoke

ch21-smoke-local:
	python3 labs/track-b-policy/ch21-deployment-gate/scripts/smoke.py

ch21-test-local:
	python3 -m unittest discover -s labs/track-b-policy/ch21-deployment-gate/tests -p 'test_*.py'
