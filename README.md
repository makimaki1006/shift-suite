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

1. Install dependencies (requires Python 3.12):

   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` file pins `scikit-learn` to `1.4.1.post1` for
   compatibility with Python 3.12.

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

4. Run analyses directly on a CSV file using the module entry point:

   ```bash
   python -m shift_suite.tasks.cli_bridge --analysis <type> <csv> --out <dir>
   ```

   Available analysis types are `leave`, `rest`, `work`, `attendance`,
   `lowstaff`, `score` and `all`.  The `leave` option mirrors the previous
   behaviour and outputs `leave_analysis.csv`.  When using `lowstaff`, you
   may optionally pass `--threshold` to set the staff-count threshold (either
   a value or quantile).

   Example: generate combined scores with

   ```bash
   python -m shift_suite.tasks.cli_bridge --analysis score shifts.csv --out results
   ```

   Example: analyze low staff load with a custom threshold

   ```bash
   python -m shift_suite.tasks.cli_bridge --analysis lowstaff --threshold 0.2 shifts.csv --out results
   ```

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
