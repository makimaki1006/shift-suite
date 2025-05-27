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
  time‑series models. Each run appends the selected model and MAPE to
  `forecast_history.csv` and holiday dates can be passed as exogenous inputs.
- **`fairness`** – Evaluates fairness in shift allocation across staff members.
- **`rl`** – Experimental reinforcement‑learning module for generating
  optimised rosters.
- **`hire_plan`** – Estimates the number of hires required to meet forecast
  demand.
- **`h2hire`** – Converts shortage hours into required FTE hires.
- **`cluster`** – Groups staff automatically by shift pattern.
- **`fatigue`** – Trains a simple model and outputs fatigue scores per staff.
- **`skill_nmf`** – Estimates a latent skill matrix using non‑negative matrix factorisation.
- **`anomaly`** – Detects irregular shift patterns via IsolationForest.
- **`cost_benefit`** – Simulates labour costs and hiring scenarios.
- **`ppt`** – Builds a PowerPoint report summarising heatmaps, shortage metrics
  and cost simulations (requires the optional `python-pptx` library).
- **`leave_analyzer`** – Summarises paid and requested leave days.
- **`cli_bridge`** – Lightweight CLI for `leave_analyzer` based on CSV input.

## Usage

1. Install dependencies (requires Python 3.12 or later):

   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` file pins `scikit-learn` to `1.4.1.post1` for
   compatibility with Python 3.12.
   It also installs `streamlit-plotly-events` so the leave analysis charts
   can respond to clicks and selections.

2. To use the GUI, run:

   ```bash
   streamlit run app.py
   ```

   Follow the on-screen instructions to upload your shift spreadsheet and
   execute the desired analyses. Separate upload fields are provided for
   global and local holiday calendars if you wish to factor them into the
   shortage analysis and forecasts.

3. To use the CLI, run:

   ```bash
   python cli.py <excel.xlsx> <out_dir> [--slot MIN] [--header ROW] [--zip] \
       [--holidays-global FILE] [--holidays-local FILE]
   ```

   - `<excel.xlsx>`: path to the source Excel file
   - `<out_dir>`: directory where results will be written
   - `--slot`: time slot length in minutes (default: 30)
   - `--header`: header row number in the shift sheets (default: 2)
   - `--zip`: optionally compress the output directory
   - `--holidays-global`: CSV/JSON with nationally observed holidays
   - `--holidays-local`: CSV/JSON with site-specific holidays

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

Some modules require extra libraries such as `prophet` for forecasting or
`stable-baselines3` and `torch` for reinforcement learning.  PowerPoint report
generation uses `python-pptx`, which is optional.  Install these via
`pip install -r requirements.txt` before running `app.py` or the CLIs if you
need the related features.

### Example output

Running the bridge command on a CSV with `staff`, `ds` (timestamp) and
`holiday_type` columns produces a CSV like the following:

```text
date,staff,leave_type,leave_day_flag
2024-04-01,Alice,希望休,1
2024-04-01,Bob,有給,1
```

The GUI displays the same data interactively under the **Leave Analysis** tab.

### 勤務予定人数と希望休取得者数 chart

Within the **Leave Analysis** tab there is a line chart labelled “勤務予定人数と希望休取得者数”.
It plots the total scheduled staff, the number requesting leave and the
remaining staff available each day.  This chart is generated by the
`display_leave_analysis_tab` function in `app.py`.

### Leave concentration graphs

The tab also shows line charts for days where leave requests exceed the
concentration threshold. Hovering over the points reveals the staff names who
requested leave. A second chart plots the share of requesting staff
(`leave_applicants_count ÷ total_staff`) for those days.

You can click or lasso points on this chart to select specific dates. The
selected staff members are listed below, together with a bar chart showing how
frequently each person appears within the chosen dates.

### Shortage → Hire plan workflow

After `shortage_role.xlsx` is generated, the application now calls
`h2hire.build_hire_plan` to convert shortage hours into required FTE counts.
The resulting `hire_plan.xlsx` is stored in the same output folder and the
**Shortage** tab displays these FTE numbers per role.

The CLI additionally runs a cost/benefit simulation once the hire plan has
been created. `analyze_cost_benefit(out_dir)` writes `cost_benefit.xlsx`
to the same folder. You can customise the calculation with optional
parameters:

- `wage_direct` – hourly cost of direct employees (default `1500`)
- `wage_temp` – hourly cost for temporary staff (default `2200`)
- `hiring_cost_once` – one‑time cost per hire (default `180000`)
- `penalty_per_lack_h` – penalty per uncovered hour (default `4000`)

If a `leave_analysis.csv` is also present in the output folder you can call
`merge_shortage_leave(out_dir)` to create `shortage_leave.xlsx`. This file
combines the per-slot shortage counts with daily leave applicants and adds a
`net_shortage` column. The Streamlit dashboard automatically visualises this
table under the **Shortage** tab.
