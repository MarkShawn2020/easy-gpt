# ref: https://python-poetry.org/docs/basic-usage/#activating-the-virtual-environment
source $(poetry env info --path)/bin/activate

poetry install

uvicorn main:app --host localhost --port 31014 --reload
