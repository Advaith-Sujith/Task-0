# MLOps Data Signal Production System

## Overview

This project implements a simple MLOps-style batch processing pipeline that:

* Loads configuration from a YAML file
* Reads OHLCV market data from a CSV file
* Computes a rolling mean on the `close` column
* Generates a binary trading signal
* Produces machine-readable metrics
* Writes detailed execution logs
* Runs both locally and inside Docker

---

## Project Structure

```text
.
├── run.py
├── config.yaml
├── data.csv
├── requirements.txt
├── Dockerfile
├── README.md
├── metrics.json
└── run.log
```

---

## Local Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python run.py \
  --input data.csv \
  --config config.yaml \
  --output metrics.json \
  --log-file run.log
```

---

## Docker Usage

### Build Image

```bash
docker build -t mlops-task .
```

### Run Container

```bash
docker run --rm mlops-task
```

The container will:

* Read `data.csv`
* Read `config.yaml`
* Generate `metrics.json`
* Generate `run.log`
* Print the final metrics JSON to stdout

---

## Configuration

Example `config.yaml`

```yaml
seed: 42
window: 5
version: "v1"
```

| Field   | Description                             |
| ------- | --------------------------------------- |
| seed    | Random seed for deterministic execution |
| window  | Rolling mean window size                |
| version | Pipeline version identifier             |

---

## Signal Generation Logic

Rolling mean is calculated using the configured window size:

```python
rolling_mean = close.rolling(window).mean()
```

Signal generation:

```python
signal = 1 if close > rolling_mean
signal = 0 otherwise
```

---

## Handling Initial Rows (window - 1)

For the first `window - 1` rows, a rolling mean cannot be computed because there are insufficient historical observations.

Example with:

```yaml
window: 5
```

The first 4 rows will have:

```text
rolling_mean = NaN
```

When signals are generated:

```python
(close > rolling_mean).astype(int)
```

comparisons against `NaN` evaluate to `False`, producing:

```text
signal = 0
```

Therefore:

* No rows are removed
* No values are filled
* Initial rows contribute a signal value of 0

This behavior is deterministic and consistent across executions.

---

## Metrics Output

Successful execution produces:

```json
{
    "version": "v1",
    "rows_processed": 10000,
    "metric": "signal_rate",
    "value": 0.4990,
    "latency_ms": 127,
    "seed": 42,
    "status": "success"
}
```

### Fields

| Field          | Description              |
| -------------- | ------------------------ |
| version        | Pipeline version         |
| rows_processed | Number of rows processed |
| metric         | Metric name              |
| value          | Signal rate              |
| latency_ms     | Runtime in milliseconds  |
| seed           | Configured random seed   |
| status         | Success status           |

---

## Error Handling

The pipeline validates:

* Missing configuration file
* Invalid YAML format
* Invalid configuration structure
* Missing required configuration fields
* Missing dataset file
* Invalid CSV format
* Empty dataset
* Missing `close` column
* Invalid data types in `close`

On failure, an error metrics file is still written:

```json
{
    "version": "v1",
    "status": "error",
    "error_message": "Description of failure"
}
```

---

## Logging

Execution logs are written to `run.log`.

Logged events include:

* Job start
* Configuration validation
* Dataset loading
* Row count
* Rolling mean computation
* Signal generation
* Metrics summary
* Job completion
* Exceptions and validation failures

---

## Reproducibility

The pipeline sets a deterministic NumPy seed from the configuration:

```python
np.random.seed(seed)
```

Although the current processing flow contains no stochastic operations, setting the seed ensures reproducibility if future random operations are introduced.
