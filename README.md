# camp-scheduler

Script and helpful stuff for scheduling activities during free time blocks at camp.

## Local development

### Frontend

Install Node dependencies with `yarn install`.

To start the UI, run `yarn serve`, then open up http://localhost:8000/ui. You will need to refresh the page to see new changes.

### Python

Create a virtual Python environment using `uv venv`, then run `source .venv/bin/activate`. Install packages with `uv sync`.

Tests can be run with `python -m unittest discover -s tests -v`