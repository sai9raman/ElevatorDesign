import pandas as pd

from elevator_dispatcher import ElevatorDispatcher
from models import ElevatorStop, Building, CallRequest


class BuildingElevatorEngine:
    def __init__(
            self,
            number_of_floors: int,
            number_of_elevators: int,
            max_capacity_of_elevator: int,
            input_df: pd.DataFrame,
    ):
        self.building = Building(
            number_of_floors=number_of_floors,
            number_of_elevators=number_of_elevators,
            max_capacity_of_elevator=max_capacity_of_elevator,
        )
        self.time = -1
        self.elevator_requests: list[CallRequest] = []
        self.input_df = input_df

        # For logging and output
        elevator_log_columns = []
        for ele in self.building.elevators:
            elevator_log_columns += [f"{ele.name} Floor", f"{ele.name} Status"]
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
        return [request for request in self.elevator_requests if not request.is_complete]

    @property
    def max_time(self) -> int:
        return self.input_df["time"].max()

    def tick_time(self):
        self.time += 1
        new_calls = self.fetch_call_requests_at_time_t()
        while new_calls:
            call_request = new_calls.pop()

            elevator, elevator_plan_update = ElevatorDispatcher(
                elevators=self.building.elevators,
                request=call_request
            ).get_elevator_and_plan_update_for_request()

            call_request.elevator_name = elevator.name
            self.elevator_requests.append(call_request)
            new_pickup_stop = ElevatorStop(
                floor=call_request.source_floor,
                pickup_requests=[call_request],
                dropoff_requests=[],
            )
            elevator.add_stop_to_plan(new_stop=new_pickup_stop, index=elevator_plan_update.source_index)
            new_dropoff_stop = ElevatorStop(
                floor=call_request.target_floor,
                pickup_requests=[],
                dropoff_requests=[call_request],
            )
            elevator.add_stop_to_plan(new_stop=new_dropoff_stop, index=elevator_plan_update.target_index)

        for elevator in self.building.elevators:
            elevator.next(time=self.time)

    def update_elevator_log(self):
        for elevator in self.building.elevators:
            self.elevator_log_df._set_value(
                self.time, f"{elevator.name} Floor", elevator.current_floor
            )
            self.elevator_log_df._set_value(
                self.time, f"{elevator.name} Status", elevator.state.value
            )

    def run_simulation(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        while self.time < self.max_time or bool(self.list_in_progress_requests()):
            self.update_elevator_log()
            self.tick_time()
        self.update_elevator_log()

        self.create_request_log()
        print(f"\n\n------ Total Time taken: {self.time} ------")
        print(f"\n\n {self.elevator_log_df}")
        print(f"\n\n {self.request_log_df}")
        return self.elevator_log_df, self.request_log_df

    def create_request_log(self):
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

    def fetch_call_requests_at_time_t(self) -> list[CallRequest]:
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
