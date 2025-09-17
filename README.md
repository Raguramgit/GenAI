# GenAI

Save working files of my Gen AI study.

[![Repository Size](https://img.shields.io/github/repo-size/Raguramgit/GenAI)](https://github.com/Raguramgit/GenAI)
[![Top language](https://img.shields.io/github/languages/top/Raguramgit/GenAI)](https://github.com/Raguramgit/GenAI)


## Overview

GenAI is a collection of working files, experiments, and notes for personal study and exploration of generative AI techniques. The repository primarily contains Python notebooks, scripts, and supporting code used to learn, prototype, and document ideas related to machine learning, deep learning, and generative models.

This repository is intended as a personal study log rather than a packaged library or production project. Use the material for learning and experimentation; confirm and adapt code before using in production.


## Repository structure (conventions)

The repository may contain the following top-level folders (some may not exist yet):

- notebooks/         - Jupyter notebooks for experiments and exploration
- experiments/      - Experiment runs, scripts, and logs
- models/           - Trained or checkpointed model files (gitignored)
- data/             - Small example datasets or download scripts (large data should be stored externally)
- src/              - Reusable modules and helper code
- scripts/          - Utility scripts for preprocessing, training, and evaluation
- docs/             - Documentation, notes, and write-ups
- tests/            - Unit/integration tests


## Getting started

Prerequisites
- Python 3.8+ (3.10+ recommended)
- pip or poetry
- Git

Quick setup (virtualenv + pip)
```bash
git clone https://github.com/Raguramgit/GenAI.git
cd GenAI
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install --upgrade pip
# If a requirements.txt exists, install dependencies:
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
```

Or using poetry
```bash
pip install poetry
poetry install
poetry shell
```

Running notebooks
```bash
# Install Jupyter if needed
pip install jupyterlab
jupyter lab
# or
jupyter notebook
```


## Typical workflows

- Explore and prototype in notebooks/.
- Move stable or reusable code into src/ and scripts/.
- Save experiments under experiments/ with clear notes about hyperparameters and environment.
- Keep large datasets and model checkpoints out of the repo; reference download instructions or use .gitignore for models/ and data/


## Tips for reproducibility

- Add a requirements.txt or environment.yml to pin dependency versions.
- Record random seeds, library versions, and GPU/CPU details in experiment notes.
- Use small example datasets for demos and link to full datasets via scripts or docs.


## Contributing

This repository is primarily a personal study space. Contributions are welcome as suggestions or improvements via issues and pull requests. If you share code, please:

- Provide a clear description and purpose for your change
- Keep changes small and focused
- Add tests for core functionality where feasible


## License

No license is specified for this repository. If you want to make this project open-source, add a LICENSE file (for example, the MIT License). Without a license, others have limited rights to reuse the code.


## Acknowledgements & Resources

- OpenAI, Hugging Face, and numerous tutorials and academic papers that inspired experiments here.
- Helpful libraries: PyTorch / TensorFlow, Hugging Face Transformers, scikit-learn, Jupyter


## Contact

Repository owner: Raguramgit
