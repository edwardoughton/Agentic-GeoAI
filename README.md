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

https://github.com/edwardoughton/GeoAI/blob/main/00_01_ggs662_local_setup.ipynb

Week 1 notebook link can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/01_01_ggs662_agentic_geoai_intro.ipynb

Week 2 notebook link can be found here:

https://colab.research.google.com/github/edwardoughton/Agentic-GeoAI/blob/main/02_01_ggs662_agentic_geoai_problem_formulation.ipynb

Week 2 local environment
========================

From PowerShell in the repository root:

```powershell
python -m venv .venv-week2
.\.venv-week2\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-week2.txt
```

In VS Code, open the Week 2 notebook and select the `.venv-week2` Python kernel.

