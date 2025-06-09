# Shift-Suite

Shift-Suite is a collection of utilities for analysing and visualising Excel
shift schedules.  It offers both a graphical interface built with Streamlit
and a lightweight command line tool for batch execution.

## Quickstart

Clone the repository and install the dependencies with the provided setup
script:

```bash
./setup.sh
```

Run the linter and test suite locally to ensure everything is working:

```bash
ruff check .
pytest -q
```

Once the tests pass you can explore the modules described below.

## Logging

All commands log to ``shift_suite.log`` in the current directory in addition to
printing to the console.  Set ``SHIFT_SUITE_LOG_FILE`` to override the path.

## Main modules

- **`app.py`** – Launches the Streamlit based GUI.  The application guides you
  through uploading an Excel file, selecting sheets and running various
  analyses such as heatmap generation and shortage detection.
- **`cli.py`** – Provides a command line interface for running a subset of the
  analysis pipeline without the GUI.  It ingests an Excel file, builds a
  heatmap, runs shortage analysis and summarises the results.
- New in v0.9.0: the GUI includes an **Optimization Analysis** tab that visualises
  surplus capacity and margin to upper limits and outputs an optimisation score
  per time slot.

The `shift_suite/tasks` package holds the analysis modules listed below. They
are automatically imported by `shift_suite/__init__.py`, so you can simply
`import shift_suite` and access them as attributes (e.g. `shift_suite.heatmap`).

- **`heatmap`** – Generates time-slot heatmaps and calculates required staff
  numbers from shift records.
- **`shortage`** – Computes staff shortages based on heatmap data and outputs
  summary spreadsheets.
- **`weekday_timeslot_summary` / `monthperiod_timeslot_summary`** –
  Return average shortage counts by weekday or month period for each time slot
  so you can create heatmaps highlighting recurring issues.
- **`build_stats`** – Aggregates KPIs and produces overall and monthly
  statistics.
 - **`forecast`** – Builds demand series and forecasts future staffing needs via
   time‑series models. Each run appends the selected model and MAPE to
   `forecast_history.csv` and holiday dates can be passed as exogenous inputs.
   If the average MAPE of the last few runs exceeds 0.25, the function
   automatically switches to an ARIMA model and uses multiplicative seasonality.
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

The GUI caches the uploaded workbook using `load_excelfile_cached()` with
`st.cache_resource`, as `pd.ExcelFile` objects cannot be pickled.

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
   shortage analysis and forecasts. Use the **Forecast days** field in the
   sidebar to specify how many days ahead the Need forecast module should
   predict (default: 30).

   You can skip the file uploader by setting the environment variable
   `SHIFT_SUITE_DEFAULT_EXCEL` to the path of your workbook before launching
   the GUI:

   ```bash
   SHIFT_SUITE_DEFAULT_EXCEL=./shifts.xlsx streamlit run app.py
   ```

   The wizard will pre-load this file so you can immediately select the
   relevant sheets.

3. To use the CLI, run:

   ```bash
   python cli.py <excel.xlsx> <out_dir> [--slot MIN] [--header ROW] [--zip] \
       [--holidays-global FILE] [--holidays-local FILE] [--safety-factor NUM]
   ```

   - `<excel.xlsx>`: path to the source Excel file
   - `<out_dir>`: directory where results will be written
   - `--slot`: time slot length in minutes (default: 30)
   - `--header`: header row number in the shift sheets (default: 2)
   - `--zip`: optionally compress the output directory
   - `--holidays-global`: CSV/JSON with nationally observed holidays
   - `--holidays-local`: CSV/JSON with site-specific holidays

   - `--safety-factor`: multiplier applied to shortage hours when automatically
     generating a hire plan (default: 1.0)

   Each shift sheet should include columns for staff name, role and employment
   type. The employment type must be one of `正社員`, `パート`, `派遣`, `スポット`
   or `その他`.

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

### Reinforcement learning

`learn_roster` optionally loads a saved PPO model. If the model cannot
be deserialised, an error is logged and the function returns `None`
instead of raising an exception.

### Example output

Running the bridge command on a CSV with `staff`, `ds` (timestamp) and
`holiday_type` columns produces a CSV like the following:

```text
date,staff,leave_type,leave_day_flag
2024-04-01,Alice,希望休,1
2024-04-01,Bob,有給,1
```

The GUI displays the same data interactively under the **Leave Analysis** tab.

`summarize_leave_by_day_count` aggregates these daily flags by a chosen period
and writes `leave_analysis.csv` when ``period="date"``.  The CSV now contains
the following columns:

- ``date`` (aggregation unit)
- ``leave_type``
- ``total_leave_days``
- ``num_days_in_period_unit`` – number of unique dates in each period
- ``avg_leave_days_per_day`` – ``total_leave_days`` divided by
  ``num_days_in_period_unit``

### 勤務予定人数と希望休取得者数 chart

Within the **Leave Analysis** tab there is a line chart labelled “勤務予定人数と希望休取得者数”.
It plots the total scheduled staff, the number requesting leave and the
remaining staff available each day.  This chart is generated by the
`display_leave_analysis_tab` function in `app.py`.

### Leave concentration graphs

The tab now shows a bar chart of daily leave applicants. Days that exceed the
concentration threshold are highlighted with red diamond markers. Hovering over
these points reveals the staff names who requested leave. A second line chart
plots the share of requesting staff (`leave_applicants_count ÷ total_staff`) for
those days.

Another bar chart visualises the distribution of requested and paid leave by
month period (early/mid/late) and weekday. The underlying data is written to
`leave_ratio_breakdown.csv`.

You can click or lasso points on this chart to select specific dates. Multiple
dates accumulate across clicks, and the selected staff members are listed below,
together with a bar chart showing how frequently each person appears within the
chosen range. Use the **選択をクリア** button to reset the selection.

### Custom leave codes via remarks

`load_shift_patterns` now checks the remarks column first when reading the
"勤務区分" sheet.  If keywords such as "希望休" or "有給" are found, the code in
that row is treated as a leave code even if it is not listed in
`LEAVE_CODES`. The shift time for that pattern becomes zero, letting you define
ad‑hoc leave markers directly in Excel without modifying the source code.

### Shortage → Hire plan workflow

After `shortage_role.xlsx` is generated, the application automatically runs
`h2hire.build_hire_plan` to convert shortage hours into required FTE counts.
The *Safety factor* slider is also applied here (default `0.0`). The resulting `hire_plan.xlsx` is stored in the same output folder and
the **Shortage** tab displays these FTE numbers per role.

If you select the optional **Hire plan** module, the application instead calls
`tasks.hire_plan.build_hire_plan`. This function honours the current value of
the *Safety factor* slider found under **Cost & Hire Parameters** (range
`0.00–2.00`, default `0.0`).

The CLI additionally runs a cost/benefit simulation once the hire plan has
been created. `analyze_cost_benefit(out_dir)` writes `cost_benefit.xlsx`
to the same folder. You can customise the calculation with optional
parameters:

- `wage_direct` – hourly cost of direct employees (default `1500`)
- `wage_temp` – hourly cost for temporary staff (default `2200`)
- `hiring_cost_once` – one‑time cost per hire (default `180000`)
- `penalty_per_lack_h` – penalty per uncovered hour (default `4000`)
- `safety_factor` – multiplier applied when running
`tasks.hire_plan.build_hire_plan` (default `0.0`). This same value is passed to
`h2hire.build_hire_plan` when shortage results are converted automatically.
  The value can also be set via the `--safety-factor` CLI option.

If a `leave_analysis.csv` is also present in the output folder you can call
`merge_shortage_leave(out_dir)` to create `shortage_leave.xlsx`. This file
combines the per-slot shortage counts with daily leave applicants and adds a
`net_shortage` column. The Streamlit dashboard automatically visualises this
table under the **Shortage** tab.

For a step-by-step explanation of how shortage and excess numbers are
calculated, see [docs/shortage_excess_example.md](docs/shortage_excess_example.md).

### Uploading ZIP archives

You can inspect past results without rerunning the analyses by uploading a
compressed ``out`` folder. Use the **Dashboard (Upload ZIP)** section of the GUI
to drop a ZIP file containing the results. The archive must include at least
``heat_ALL.xlsx`` and ``leave_analysis.csv`` so the **Leave Analysis** tab can
render correctly. If ``staff_balance_daily.csv`` or
``concentration_requested.csv`` are also present they will be loaded directly.
When these extra files are missing the application reconstructs the
``staff_balance_daily`` and ``concentration_requested`` tables from
``leave_analysis.csv`` and ``heat_ALL.xlsx``.

### Running tests

Install the dependencies first:

```bash
./setup.sh  # or pip install -r requirements.txt
```

Then execute the test suite with:

```bash
pytest -q
```

To generate a coverage report, install ``pytest-cov`` and run:

```bash
pytest --cov=shift_suite --cov-report=term-missing
```

### Linting

Check code style with [ruff](https://docs.astral.sh/ruff/):

```bash
ruff check .
```

### Configuration and localisation

Runtime settings and translation strings are stored in separate files under
`shift_suite/`:

- `config.json` – default values such as the forecast period.
- `resources/strings_ja.json` – Japanese UI labels.

Modify these files to tweak behaviour or update translations without touching
the Python source.

### Troubleshooting

When launching the GUI, Streamlit will raise `StreamlitAPIException: Expanders may not be nested inside other expanders` if an `st.expander` is created within another expander.  The code avoids this by replacing the inner expander for **Leave Analysis** with a simple Markdown heading.  If you encounter this error, check that your local copy reflects this structure or remove the nested expander.

If you see repeated messages like `Examining the path of torch.classes raised` on
Windows, set `STREAMLIT_WATCHER_TYPE=poll` before running the app to disable the
default file watcher:

```bash
STREAMLIT_WATCHER_TYPE=poll streamlit run app.py
```
