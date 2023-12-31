import pandas as pd

from elevator_dispatcher import ElevatorDispatcher
from models import Building, CallRequest


class BuildingElevatorEngine:
    def __init__(
            self,
            number_of_floors: int,
            number_of_elevators: int,
            max_capacity_of_elevator: int,
            input_df: pd.DataFrame,
    ):
        """
        Initializes the BuildingElevatorEngine with the given parameters.

        Args:
            number_of_floors (int): The number of floors in the building.
            number_of_elevators (int): The number of elevators in the building.
            max_capacity_of_elevator (int): The maximum capacity of each elevator.
            input_df (pd.DataFrame): A DataFrame containing call request data.
        """
        self.building = Building(
            number_of_floors=number_of_floors,
            number_of_elevators=number_of_elevators,
            max_capacity_of_elevator=max_capacity_of_elevator,
        )
        self.elevator_dispatcher = ElevatorDispatcher(elevators=self.building.elevators)
        self.input_df = input_df.sort_index()  # sorted by time
        self.expected_request_count = self.input_df.shape[0]

        # Engine driving parameters
        self.time = -1
        self.elevator_requests: list[CallRequest] = []

        # For logging and output
        elevator_log_columns = []
        for elevator in self.building.elevators:
            elevator_log_columns += [f"{elevator.name} Floor", f"{elevator.name} Status", f"{elevator.name} Passengers"]
        self.elevator_log_df = pd.DataFrame(
            columns=elevator_log_columns
        )
        self.request_log_df = pd.DataFrame(
            columns=[
                "Call Time",
                "Source->Dest",
                "Pickup Time",
                "Dropoff Time",
                "Wait Time",
                "Total Time",
                "Elevator",
            ]
        )

    def list_in_progress_requests(self) -> list[CallRequest]:
        """
        Returns a list of in-progress elevator requests.

        Returns:
            list[CallRequest]: List of in-progress elevator requests.
        """
        return [request for request in self.elevator_requests if not request.is_complete]

    def run_simulation(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Runs the elevator simulation.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: A tuple of DataFrames containing elevator and request logs.
        """
        while len(self.elevator_requests) < self.expected_request_count \
                or bool(self.list_in_progress_requests()):
            self.update_elevator_log()
            self.tick_time()

        self.update_elevator_log()
        self.create_request_log()

        print(f"\n\n------ Total Time taken: {self.time} ------")

        return self.elevator_log_df, self.request_log_df

    def tick_time(self):
        """
        Advances the simulation time by one unit.
        """
        self.time += 1

        # Get all new requests at this time, process them
        new_calls = self.fetch_call_requests_at_time_t()
        while new_calls:
            call_request = new_calls.pop()
            elevator, updated_plan = self.elevator_dispatcher.get_elevator_and_updated_plan_for_request(
                request=call_request
            )
            elevator.update_plan(updated_plan=updated_plan)

            # Logging and tracking
            call_request.elevator_name = elevator.name  # Just for logging purposes
            self.elevator_requests.append(call_request)

        # Elevators are moved to their next location
        for elevator in self.building.elevators:
            elevator.next(time=self.time)  # time is sent to the elevator just for logging

    def fetch_call_requests_at_time_t(self) -> list[CallRequest]:
        """
        Fetches call requests that occur at the current simulation time.

        Returns:
            list[CallRequest]: List of call requests at the current time.
        """
        df_filtered_for_t = self.input_df[self.input_df["time"] == self.time]
        if df_filtered_for_t.empty:
            return []
        call_requests_at_t: list[CallRequest] = [CallRequest(
            time=row["time"],
            id=row["id"],
            source_floor=row["source"],
            target_floor=row["dest"],
        ) for _, row in df_filtered_for_t.iterrows()]

        return call_requests_at_t

    def update_elevator_log(self):
        """
        Updates the elevator log DataFrame with the current state of elevators.
        """
        for elevator in self.building.elevators:
            self.elevator_log_df.at[
                self.time, f"{elevator.name} Floor"] = elevator.current_floor
            self.elevator_log_df.at[
                self.time, f"{elevator.name} Status"] = elevator.state.value
            self.elevator_log_df.at[
                self.time, f"{elevator.name} Passengers"] = ", ".join(elevator.passengers)

    def create_request_log(self):
        """
        Creates a log of elevator requests and their details.
        """
        for call_request in self.elevator_requests:
            self.request_log_df.loc[call_request.id] = [
                call_request.time,
                f"{call_request.source_floor} -> {call_request.target_floor}",
                call_request.pickup_time,
                call_request.dropoff_time,
                call_request.pickup_time - call_request.time,
                call_request.dropoff_time - call_request.time,
                call_request.elevator_name,
            ]
