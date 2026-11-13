# Attrition Rate Script

Calculates employee attrition (turnover) rates from an HR roster
and optionally exports the results to [CSV / Excel / etc.].

## Features

- Calculates attrition rates by monthly or annual timeframes with optional filters for department, state, or employment type
- Exports results via `exporters.py`

## Requirements

- charset-normalizer==3.5.2
- numpy==2.5.4
- pandas==3.1.1
- pillow==13.0.0
- python-dateutil==4.0.0
- reportlab==5.1.0
- tzdata==2026.6
- python==3.x

## Installation

- git clone https://github.com/mknudson2/hr_tools-attrition_rate.git
- cd hr_tools-attrition_rate
- pip install -r requirements.txt

## Usage

python run_attrition.py --[filters]

### Filters

| **Filter**        | **Required?** | **Description**                                                           |
| ----------------- | ------------- | ------------------------------------------------------------------------- |
| --file            | [optional]    | file path to data; default to "employee_roster.csv"                       |
| --years           | [required]    | determines which years you want to focus the attrition rate               |
| --department      | [optional]    | filter results by a specific department                                   |
| --state           | [optional]    | filter results by employees in a specific state                           |
| --employment-type | [optional]    | filter results by a specific employment type (Full-time, Part-time, etc.) |
| --monthly         | [optional]    | provides the month-by-month table as well                                 |
| --export          | [optional]    | save results to a .csv or .pdf file (type chosen by extension)            |
| --overwrite       | [optional]    | allows --export to replace an existing file                               |

### Example output:

python3 run_attrition.py --years 2020 2021 2022

```
2020 (all employees): 3.64% total, 0.00% voluntary, 3.64% involuntary
2021 (all employees): 5.74% total, 2.30% voluntary, 3.44% involuntary
2022 (all employees): 5.35% total, 4.01% voluntary, 1.34% involuntary
```

python3 run_attrition.py --years 2020 2021 2022 --monthly

```
2020 (all employees): 3.64% total, 0.00% voluntary, 3.64% involuntary
  month  start_hc  end_hc  avg_hc  terminations  voluntary  involuntary
2020-01         2       5     3.5             0          0            0
2020-02         5      10     7.5             0          0            0
2020-03        10      13    11.5             0          0            0
2020-04        13      16    14.5             0          0            0
2020-05        16      19    17.5             0          0            0
2020-06        19      27    23.0             0          0            0
2020-07        27      34    30.5             0          0            0
2020-08        34      37    35.5             0          0            0
2020-09        37      43    40.0             0          0            0
2020-10        43      45    44.0             1          0            1
2020-11        45      52    48.5             0          0            0
2020-12        52      56    54.0             0          0            0

2021 (all employees): 5.74% total, 2.30% voluntary, 3.44% involuntary
  month  start_hc  end_hc  avg_hc  terminations  voluntary  involuntary
2021-02        60      63    61.5             0          0            0
2021-03        63      70    66.5             0          0            0
2021-04        70      76    73.0             0          0            0
2021-05        76      82    79.0             0          0            0
2021-06        82      89    85.5             1          1            0
2021-07        89      91    90.0             1          0            1
2021-08        91      99    95.0             0          0            0
2021-01        56      60    58.0             0          0            0
2021-09        99     103   101.0             0          0            0
2021-10       103     111   107.0             0          0            0
2021-11       111     114   112.5             2          1            1
2021-12       114     119   116.5             1          0            1

2022 (all employees): 5.35% total, 4.01% voluntary, 1.34% involuntary
  month  start_hc  end_hc  avg_hc  terminations  voluntary  involuntary
2022-01       119     127   123.0             0          0            0
2022-02       127     129   128.0             0          0            0
2022-03       129     136   132.5             0          0            0
2022-04       136     137   136.5             1          0            1
2022-05       137     143   140.0             0          0            0
2022-06       143     148   145.5             1          0            1
2022-07       148     152   150.0             1          1            0
2022-08       152     158   155.0             1          1            0
2022-09       158     167   162.5             1          1            0
2022-10       167     174   170.5             0          0            0
2022-11       174     175   174.5             3          3            0
2022-12       175     179   177.0             0          0            0
```

## Input data format

The script expects `employee_roster.csv` by default with the following columns expected:

| Column           | Description                                                                            |
| ---------------- | -------------------------------------------------------------------------------------- |
| employee_id      | Unique ID                                                                              |
| hire_date        | YYYY-MM-DD                                                                             |
| termination_date | YYYY-MM-DD, blank if active                                                            |
| termination_type | description of termination ("Voluntary", "Involuntary", "Retirement"), blank if active |

By default, the script has the following constants found in attrition.py. Adjust as needed for your own process or report structure:

- REQUIRED_COLUMNS = ["employee_id", "hire_date", "termination_date", "termination_type"]
- VALID_TERM_TYPES = {"Voluntary", "Involuntary", "Retirement"}

## Attrition formula

Attrition rate = (separations during period ÷ average headcount
during period) × 100

## Project structure

- `attrition.py` – calculation logic
- `exporters.py` – output formatting
- `run_attrition.py` – entry point

## Data privacy

`employee_roster.csv` contains fake employee data and is excluded
via `.gitignore`. Never commit real employee data to this repository.

## Author

Michael Knudson, PHR – Norrœna Solutions
