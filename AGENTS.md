# Contributor Guidelines

The root of this repository contains utilities for analysing Excel shift schedules. When modifying code or documentation, follow these rules.

## Programmatic checks
Run the following commands from the repository root after your changes:

```bash
ruff check .
pytest -q
```

Fix any lint or test failures before committing.

## Pull request notes
* Summarise your changes in English.
* Cite modified files and line numbers using the `F:<file_path>` format.
* Include the results of the programmatic checks.
* Add a Notes section if anything could not be completed.
