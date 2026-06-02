# AcademyOps Project

## Purpose

This repository contains the AcademyOps training project.

The objective is to provide a clean, reproducible Python development environment that can be cloned and set up by any engineer within minutes.

---

## Project Structure

```text
academyops-project/
│
├── src/        # Application source code
├── tests/      # Unit and integration tests
├── data/       # Sample and local data files
├── scripts/    # Utility scripts
│
├── README.md
├── requirements.txt
└── .gitignore
```


## Setup

Clone repository:

```bash
git clone <repository-url>
cd academyops-project
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate:

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run

Currently this project contains only the initial environment setup.

Future application code will be added to the `src/` directory.

---

## Testing

```bash
pytest
```