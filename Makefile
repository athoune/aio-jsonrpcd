test:
	poetry run pytest --cov jsonrpcd

.venv:
	poetry install

hello: .venv
	poetry run python -m jsonrpcd.ws.hello
