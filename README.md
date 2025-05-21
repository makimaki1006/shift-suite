# Shift-Suite

Shift-Suite is a collection of utilities for analysing and visualising Excel
shift schedules.  It offers both a graphical interface built with Streamlit
and a lightweight command line tool for batch execution.

## Main modules

- **`app.py`** – Launches the Streamlit based GUI.  The application guides you
  through uploading an Excel file, selecting sheets and running various
  analyses such as heatmap generation and shortage detection.
- **`cli.py`** – Provides a command line interface for running a subset of the
  analysis pipeline without the GUI.  It ingests an Excel file, builds a
  heatmap, runs shortage analysis and summarises the results.

The `shift_suite/tasks` package holds the analysis modules listed below. They
are automatically imported by `shift_suite/__init__.py`, so you can simply
`import shift_suite` and access them as attributes (e.g. `shift_suite.heatmap`).

- **`heatmap`** – Generates time-slot heatmaps and calculates required staff
  numbers from shift records.
- **`shortage`** – Computes staff shortages based on heatmap data and outputs
  summary spreadsheets.
- **`build_stats`** – Aggregates KPIs and produces overall and monthly
  statistics.
- **`forecast`** – Builds demand series and forecasts future staffing needs via
  time‑series models.
- **`fairness`** – Evaluates fairness in shift allocation across staff members.
- **`rl`** – Experimental reinforcement‑learning module for generating
  optimised rosters.
- **`hire_plan`** – Estimates the number of hires required to meet forecast
  demand.
- **`cluster`** – Groups staff automatically by shift pattern.
- **`fatigue`** – Trains a simple model and outputs fatigue scores per staff.
- **`skill_nmf`** – Estimates a latent skill matrix using non‑negative matrix factorisation.
- **`anomaly`** – Detects irregular shift patterns via IsolationForest.
- **`cost_benefit`** – Simulates labour costs and hiring scenarios.
- **`ppt`** – Generates a PowerPoint report (requires `python-pptx`).
- **`leave_analyzer`** – Summarises paid and requested leave days.
- **`cli_bridge`** – Lightweight CLI for `leave_analyzer` based on CSV input.

## Usage

1. Install dependencies (Python 3.10+):

   ```bash
   pip install -r requirements.txt
   ```

2. To use the GUI, run:

   ```bash
   streamlit run app.py
   ```

   Follow the on-screen instructions to upload your shift spreadsheet and
   execute the desired analyses.

3. To use the CLI, run:

   ```bash
   python cli.py <excel.xlsx> <out_dir> [--slot MIN] [--zip]
   ```

   - `<excel.xlsx>`: path to the source Excel file
   - `<out_dir>`: directory where results will be written
   - `--slot`: time slot length in minutes (default: 30)
   - `--zip`: optionally compress the output directory

4. To run the leave analysis pipeline with a simple CSV file use the helper
   CLI:

   ```bash
   python shift_suite/tasks/cli_bridge.py shifts.csv --out results
   ```

   The command produces `results/leave_analysis.csv` summarising leave days per
   staff member.

The analysis code lives under the `shift_suite/tasks` package.  Results are
written to the specified output directory or displayed directly in the GUI.

### Additional dependencies

Some modules require optional libraries such as `prophet` for forecasting,
`stable-baselines3` and `torch` for reinforcement learning, and `python-pptx`
to build PowerPoint reports.  Install them via `pip install -r requirements.txt`
before running `app.py` or the CLIs.

### Example output

Running the bridge command on a CSV with `staff`, `ds` (timestamp) and
`holiday_type` columns produces a CSV like the following:

```text
date,staff,leave_type,leave_day_flag
2024-04-01,Alice,希望休,1
2024-04-01,Bob,有給,1
```

The GUI displays the same data interactively under the **Leave Analysis** tab.
