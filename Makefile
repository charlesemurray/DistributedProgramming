venv: TARGET

TARGET:
	@if [ ! -d "venv" ]; then \
		virtualenv -p python3.6 venv; \
	else echo "Virtualenv Already exists"; \
	fi
