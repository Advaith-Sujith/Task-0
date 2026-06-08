'''
The whole code has comments for reference. I will do my best to explain each process in these comments,
if anything is not clear in these comments, feel free to email me at 4dvaith.s@gmail.com for any
clarifications.
'''

#IMPORTS
import logging
import sys
from io import StringIO
import json
import pandas as pd
import os
import argparse
import yaml
import time
import numpy as np


#Defining output and version as a backup to avoid unnecessary errors
output = "metrics.json"
version = "unknown"

#Running try block to catch any errors before execution
try:
    #Using parser to take CLI arguments
    parser = argparse.ArgumentParser(description="MLOps Data Signal Production System")

    parser.add_argument("--input", required=True, type=str, help="Dataset file path")
    parser.add_argument("--config", required=True, type=str, help="Config file path")
    parser.add_argument("--output", required=True, type=str, help="Output metrics file path")
    parser.add_argument("--log-file", required=True, type=str, help="Log file path")

    args = parser.parse_args()

    input_file = args.input
    config = args.config
    output = args.output
    log = args.log_file

    #Starting log with basic format definition

    logging.basicConfig(
        filename=log,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    #Noting start time for latency
    start_time = time.perf_counter()

    logging.info("Job Started")

    #Checking if config file exists
    if not os.path.exists(config):
        raise FileNotFoundError("Config file path does not exist")

    #Confirming that config format is correct. Raising error if not
    with open(config, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError:
            raise ValueError("Incorrect YAML file format")
        
    #Verifying config structure
    if not isinstance(data, dict):
        raise ValueError("Invalid config structure")

    #Checking if required values are provided in config
    required = ["seed", "window", "version"]

    for key in required:
        if key not in data:
            raise ValueError(f"Missing config field: {key}")

    seed = data["seed"]
    window = data["window"]
    version = data["version"]

    #Checking datatype of values provided in config
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")

    if not isinstance(window, int) or window <= 0:
        raise ValueError("window must be a positive integer")

    if not isinstance(version, str):
        raise ValueError("version must be a string")

    #Logging validity of config
    logging.info(
        "Config loaded and validated | "
        f"seed={seed} window={window} version={version}"
    )

    #Checking if dataset input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError("Dataset file path does not exist")

    #Defining project seed
    np.random.seed(seed)

    #Reading and formatting input data as the provided data is in incorrect format
    with open(input_file, "r") as inp:
        csv_data = inp.read().replace('"','')

    #Checking csv format one last time
    try:
        dt = pd.read_csv(StringIO(csv_data), on_bad_lines="error")
    except pd.errors.ParserError as err:
        raise ValueError(f"Invalid CSV format: {err}")
    except Exception as err:
        raise err

    #Checking if dataset is empty
    if dt.empty:
        raise ValueError("Dataset is empty")

    #Checking for important "close" column in csv dataset
    if 'close' not in dt.columns:
        raise ValueError("Close column is missing")
    
    #Raises exception on invalid values
    dt["close"] = pd.to_numeric(dt["close"], errors="raise")
    
    #Logging validity of dataset
    logging.info(
        "Dataset Validated | "
        f"Rows loaded: {len(dt)}"
    )

    logging.info(
        "Computing rolling mean"
    )
    
    #Calculating rolling mean with window
    dt["rolling_mean"] = dt["close"].rolling(window).mean()

    logging.info(
        "Generating signals"
    )

    #Generating signal based on close and rolling mean column
    dt["signal"] = (dt["close"]>dt["rolling_mean"]).astype(int)

    rows_processed = len(dt)

    #Checking signal rate
    signal_rate = dt["signal"].mean()

    #Checking latency of job
    latency_ms = round((time.perf_counter()-start_time)*1000)

    #Noting metrics for JSON
    metrics = {
        "version": version,
        "rows_processed": rows_processed,
        "metric": "signal_rate",
        "value": float(signal_rate),
        "latency_ms": latency_ms,
        "seed": seed,
        "status": "success"
    }

    #Writing JSON metrics to metrics.json file
    with open(output, "w") as f:
        json.dump(metrics, f, indent=4)

    #Printing metrics output
    print(json.dumps(metrics, indent=4))

    #Logging processed Metrics
    logging.info(
        "Metrics summary | "
        f"Rows processed: {rows_processed} | "
        f"Signal rate: {signal_rate:.4f} | "
        f"Latency in ms: {latency_ms} | "
    )

    logging.info("Job completed successfully")
    
#Handling errors that occur before job starts
except Exception as e:
    #Noting errors for json
    error_metrics = {
        "version": version if "version" in locals() else "unknown",
        "status": "error",
        "error_message": str(e)
    }
    
    #Logging error
    if "log" in locals() and log:
        logging.exception(str(e))

    #Writing error to metrics.json
    with open(output, "w") as f:
        json.dump(error_metrics, f, indent=4)

    #Printing error to console
    print(json.dumps(error_metrics, indent=4))

    #Exiting system with error code 1
    sys.exit(1)