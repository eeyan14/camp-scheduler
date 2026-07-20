# camp-scheduler

Script and helpful stuff for scheduling activities during free time blocks at camp.

## Local development

### Frontend

Install Node dependencies with `yarn install`.

To start the UI, run `yarn serve`, then open up http://localhost:8000/ui. You will need to refresh the page to see new changes.

### GitHub Pages deployment

The repository includes a GitHub Actions workflow that builds the UI and publishes the generated site to the `gh-pages` branch whenever changes land on `main`.

To enable GitHub Pages:

1. Open the repository's Settings > Pages.
2. Set the source to "Deploy from a branch".
3. Choose the `gh-pages` branch and the `/ (root)` folder.
4. Save the settings.

The workflow will then publish the built UI automatically on every push to `main`.

### Python

Create a virtual Python environment using `uv venv`, then run `source .venv/bin/activate`. Install packages with `uv sync`.

Tests can be run with `python -m unittest discover -s tests -v`