import argparse

import numpy as np
import pandas as pd

from building_elevator_engine import BuildingElevatorEngine
from errors import CallRequestError


def positive_int(value):
    """
    Custom argument parser function to ensure the value is a positive integer.

    Args:
        value (str): The input value to be parsed as an integer.

    Returns:
        int: The parsed integer value if it's greater than 0.

    Raises:
        argparse.ArgumentTypeError: If the value is not a positive integer.
    """
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid int value; value needs to be grtr than 0: " % value)
    return ivalue


def arg_parser() -> dict[str, any]:
    """
    Sets up the command-line arguments needed to run the Elevator Simulator.

    Returns:
        dict: A dictionary containing the parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_csv_path", help="Path for the csv file", required=True)
    parser.add_argument("-bf", "--building_floors", help="Number of floors in the building", default=100, type=positive_int)
    parser.add_argument("-be", "--building_elevators", help="Number of elevators in the building", default=3, type=positive_int)
    parser.add_argument(
        "-ec", "--elevator_capacity", help="Capacity of Elevator in number of passengers", default=5,
        type=positive_int
    )
    args = vars(parser.parse_args())
    return args


def compute_metrics_from_request_log(request_log: pd.DataFrame) -> pd.DataFrame:
    """
    Computes metrics (min, max, mean) from the request log DataFrame.

    Args:
        request_log (pd.DataFrame): DataFrame containing request log data.

    Returns:
        pd.DataFrame: DataFrame with computed metrics.
    """
    metrics_df = pd.DataFrame(columns=["Wait Times", "Total Times"])
    metrics_df.loc["Min"] = [min(request_log["Wait Time"]), min(request_log["Total Time"]), ]
    metrics_df.loc["Max"] = [max(request_log["Wait Time"]), max(request_log["Total Time"]), ]
    metrics_df.loc["Mean"] = [np.mean(request_log["Wait Time"]), np.mean(request_log["Total Time"]), ]
    return metrics_df


def validate_call_requests(input_df: pd.DataFrame) -> None:
    """
    Validates the input DataFrame for call requests.

    Args:
        input_df (pd.DataFrame): DataFrame containing call request data.

    Raises:
        CallRequestError: If any validation checks fail.
    """
    if input_df.empty:
        raise CallRequestError("No Call Requests Found")
    if not input_df["id"].is_unique:
        raise CallRequestError("Passenger ids must be unique")
    if not (input_df["time"] >= 0).all():
        raise CallRequestError("Time must be non-negative int")
    if not (input_df["source"] > 0).all() or not (input_df["source"] > 0).all():
        raise CallRequestError("Floors must be positive int")
    if ((input_df["source"] - input_df["dest"]) == 0).any():
        raise CallRequestError("Source and Dest floor cannot be the same")


def main():
    args = arg_parser()
    input_df = pd.read_csv(args["input_csv_path"], usecols=["time", "id", "source", "dest"])
    validate_call_requests(input_df=input_df)
    building_elevator_engine = BuildingElevatorEngine(
        number_of_floors=args["building_floors"],
        number_of_elevators=args["building_elevators"],
        max_capacity_of_elevator=args["elevator_capacity"],
        input_df=input_df,
    )
    elevator_log, request_log = building_elevator_engine.run_simulation()

    metrics_df = compute_metrics_from_request_log(request_log=request_log)

    with open('output_df.csv', 'w') as f:
        elevator_log.to_csv(f)
        f.write("\n\n")
        request_log.to_csv(f)
        f.write("\n\n")
        metrics_df.to_csv(f)


if __name__ == "__main__":
    main()
