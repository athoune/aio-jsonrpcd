test:
	poetry run pytest --cov jsonrpcd

.venv:
	poetry install
