from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import numpy as np
import pandas as pd

from building_elevator_engine import BuildingElevatorEngine


def arg_parser() -> dict[str, any]:
    """
    Sets up the arguments needed to be inputted to run the Elevator Simulator
    :return: args dict
    """
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_csv_path", help="Path for the csv file", required=True)
    parser.add_argument("-bf", "--building_floors", help="Number of floors in the building", default=100, type=int)
    parser.add_argument("-be", "--building_elevators", help="Number of elevators in the building", default=10, type=int)
    parser.add_argument(
        "-ec", "--elevator_capacity", help="Capacity of Elevator in number of passengers", default=10,
        type=int
    )
    args = vars(parser.parse_args())
    return args


def get_request_metrics(request_log: pd.DataFrame) -> pd.DataFrame:
    metrics_df = pd.DataFrame(columns=["Wait Times", "Total Times"])
    metrics_df.loc["Min"] = [min(request_log["Wait Time"]), min(request_log["Total Time"]), ]
    metrics_df.loc["Max"] = [max(request_log["Wait Time"]), max(request_log["Total Time"]), ]
    metrics_df.loc["Mean"] = [np.mean(request_log["Wait Time"]), np.mean(request_log["Total Time"]), ]
    return metrics_df


def main():
    args = arg_parser()
    input_df = pd.read_csv(args["input_csv_path"])
    building_elevator_engine = BuildingElevatorEngine(
        number_of_floors=args["building_floors"],
        number_of_elevators=args["building_elevators"],
        max_capacity_of_elevator=args["elevator_capacity"],
        input_df=input_df,
    )
    elevator_log, request_log = building_elevator_engine.run_simulation()
    metrics_df = get_request_metrics(request_log=request_log)

    with open('output_df.csv', 'w') as f:
        elevator_log.to_csv(f)
        f.write("\n\n")
        request_log.to_csv(f)
        f.write("\n\n")
        metrics_df.to_csv(f)


if __name__ == "__main__":
    main()
