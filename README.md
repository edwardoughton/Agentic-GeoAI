# Agentic GeoAI

Welcome to **GGS 662: Agentic GeoAI**, a George Mason University course introducing the use of contemporary agentic artificial intelligence (AI) tools to automate the design, implementation, testing, debugging, refactoring, validation, and documentation of geospatial projects. By the end of the course, students will be able to develop and deploy autonomous AI agents that can design, execute, evaluate, and iteratively improve traditional GIS routines and workflows.

The course builds on foundational programming and spatial computing skills, emphasizing how AI-assisted workflows can automate traditional GIS analysis via AI agents. Particular attention is given to evaluating the correctness and reliability of AI-automated solutions, including the design of testing and validation strategies for GIS codebases, to ensure workflows behave as intended and produce reproducible results. The course also encourages critical reflection on the limitations of AI tool usage in geospatial domains.

Class meets **Mondays, 4:30pm – 7:10pm**, in **Exploratory Hall, Room 2310**.

What you will learn
====================

- Design autonomous agents that plan, reason, and act for spatial analysis.
- Integrate LLMs with geospatial tools, APIs, and data.
- Understand key concepts including ReAct (Reasoning and Acting) and MCP (Model Context Protocol).
- Build end-to-end spatial workflows across multiple data sources.
- Validate, test, and document agent outputs for spatial correctness.
- Apply responsible AI practices to ensure transparency, fairness, and reproducibility.

Notebooks
=========

Start here: local setup, Git, GitHub, command line and Python environments:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/02_01_ggs662_local_setup.ipynb

Week 1 notebook link can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/01_01_ggs662_agentic_geoai_intro.ipynb

Week 2 notebook link can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/02_02_ggs662_agentic_geoai_problem_formulation.ipynb

Week 3 notebook links can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/03_01_ggs662_route_planning_data_acquisition.ipynb
https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/03_02_ggs662_agentic_application_route_planning.ipynb 

Week 4 notebook links can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/04_01_agentic_geoai_applications.ipynb

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/04_02_agentic_geoai_verification_validation.ipynb

Week 5 notebook links can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/05_01_agentic_geoai_scientific_discovery.ipynb

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/05_02_multi_agent_geoai_lab.ipynb

Week 6 notebooks (recommended reading order):

[06_00_agentic_systems_foundations.ipynb](https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/master/06_00_agentic_systems_foundations.ipynb): ReAct, RAG, embeddings, APIs, tools, MCP, orchestration, guardrails, evaluation and cost control. Read this first.

[06_01_single_research_agent_github_voice.ipynb](https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/master/06_01_single_research_agent_github_voice.ipynb)

[06_02_remote_agent_management.ipynb](https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/master/06_02_remote_agent_management.ipynb): pair your phone with a local ChatGPT/Codex or Claude Code agent, verify local execution, and supervise research remotely.

[06_03_github_pages_actions_literature_watch.ipynb](https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/master/06_03_github_pages_actions_literature_watch.ipynb): GitHub Pages, scheduled Actions, and a bounded weekly literature watch with an accumulated review-period report. Starter files are in `week6/literature_watch/`.

The practical labs use VS Code and a phone; no notebook kernel is required. The foundations notebook includes one optional standard-library Python illustration.

Week 7 notebooks:

- [07_01_agentic_scientific_research.ipynb](07_01_agentic_scientific_research.ipynb): scientific research agents and experimental design.
- [07_02_agentic_land_cover_classification.ipynb](07_02_agentic_land_cover_classification.ipynb): a self-contained case study building on GGS416 pixel classification. Understand the inputs and labels, build and check a baseline, then hand method improvement to a coding agent. Running the notebook downloads the Landsat training data and documentation into `week7/landcover/data/` and reuses them on later runs. Downloaded data stay local and are ignored by Git; no separate runner or test files are required.
- [07_03_writing_latex_in_vscode.ipynb](07_03_writing_latex_in_vscode.ipynb): a short introduction to editing the supplied `paper_template` in VS Code and compiling it with `pdflatex`. Covers setup, basic syntax, citations and common errors; no notebook kernel is needed.

Week 9 notebook:

- [09_tower_detection_agentic_demo.ipynb](week9/notebooks/09_tower_detection_agentic_demo.ipynb): train an electricity tower detector from aerial imagery, measure a baseline, then delegate model improvement to a coding agent using fixed validation data. Includes an optional augmentation extension and a final held-out test. Run locally in VS Code; follow the [Week 9 setup instructions](week9/README.md) for dependencies and the bundled dataset (50 training / 10 validation / 50 test images).

Local setup: Windows and macOS
==============================

Follow [Getting started](GETTING_STARTED.md) for short, copy-and-paste commands for **Windows Command Prompt** and **macOS Terminal**. The guide covers creating and reusing one virtual environment, installing `requirements.txt`, selecting the notebook kernel, and common errors.

Use **64-bit Python 3.12** and the same `.venv-agentic-geoai` environment for all course notebooks. The requirements include the Week 2 analysis packages and the Week 3-4 geospatial and routing packages.
