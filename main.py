from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
import pandas as pd


def main():
    call_data = {
        'time': [0, 1],
        'id': ["a", "b"],
        "source": [2, 5],
        "dest": [0, 10]
    }
    input_df = pd.DataFrame(data=call_data)
    building_elevator_system_simulator = BuildingElevatorSystemSimulator(
        building=Building(
            min_floor=0,
            max_floor=10,
            number_of_elevators=1
        ),
        input_df=input_df,
    )
    building_elevator_system_simulator.run_simulation()


class Building:
    def __init__(self, min_floor: int, max_floor: int, number_of_elevators: int) -> None:
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.number_of_elevators = number_of_elevators


class Elevator:
    class ElevatorState(Enum):
        idle = "idle"
        moving_upwards_to_pickup = "moving_upwards_to_pickup"
        moving_upwards_to_dropoff = "moving_upwards_to_dropoff"
        moving_downwards_to_pickup = "moving_downwards_to_pickup"
        moving_downwards_to_dropoff = "moving_downwards_to_dropoff"
        unavailable = "unavailable"  # for maintenance or other special reasons

    def __init__(self, state: ElevatorState, name: str,
                 current_floor: int, **kwargs: Any) -> None:
        self.state = state
        self.name = name
        self.current_floor = current_floor
        self.destination = self.current_floor
        self.passengers = []

        # Other Properties for extension
        # self.speed = ...
        # self.acceleration = ...
        # self.pickup_delay = ...
        # self.dropoff_delay = ...


    @property
    def is_idle(self) -> bool:
        return self.state == Elevator.ElevatorState.idle

    def move_towards_destination(self) -> None:
        if self.current_floor < self.destination:
            self.current_floor += 1
        elif self.current_floor > self.destination:
            self.current_floor -= 1

    @property
    def pickup_in_progress(self) -> bool:
        return self.state in [Elevator.ElevatorState.moving_downwards_to_pickup, Elevator.ElevatorState.moving_upwards_to_pickup]

    @property
    def dropoff_in_progress(self) -> bool:
        return self.state in [Elevator.ElevatorState.moving_downwards_to_dropoff,
                              Elevator.ElevatorState.moving_upwards_to_dropoff]


@dataclass
class CallRequest:
    time: int
    id: str
    source_floor: int
    target_floor: int


class ElevatorDispatcher:
    class DispatchAlgos(Enum):
        FCFS = "FCFS"

    def __init__(self, algo: DispatchAlgos = DispatchAlgos.FCFS):
        self.algo = algo

    def dispatch_elevator_for_request(self, elevators:list[Elevator], request: CallRequest) -> Optional[Elevator]:
        dispatcher = self.get_dispatcher_method()
        return dispatcher(elevators, request)

    def get_dispatcher_method(self):
        if self.algo == self.DispatchAlgos.FCFS:
            return self._fcfs_dispatcher
        else:
            raise Exception("Dispatcher Not Set")

    def _fcfs_dispatcher(self, elevators: list[Elevator],
                        request: CallRequest) -> Optional[Elevator]:
        idle_elevators: list[Elevator] = list(
            filter(lambda elevator: elevator.is_idle, elevators))
        if not idle_elevators:
            return None
        return self._find_elevator_closest_to_floor(
            elevators=idle_elevators, floor=request.source_floor)

    def _find_elevator_closest_to_floor(self,
            elevators: list[Elevator], floor) -> Elevator:
        distance_map: dict[Elevator, int] = {elevator: abs(
            elevator.current_floor - floor) for elevator in elevators}
        # returns first match, if multiple found
        return min(distance_map, key=distance_map.get)


class ElevatorRequest:
    def __init__(self, elevator: Elevator, request: CallRequest):
        self.elevator = elevator
        self.request = request
        self.is_complete: bool = False
        self.initiate_pickup()

    def initiate_pickup(self):
        if self.request.source_floor > self.elevator.current_floor:
            self.elevator.destination = self.request.source_floor
            self.elevator.state = Elevator.ElevatorState.moving_upwards_to_pickup

        elif self.request.source_floor < self.elevator.current_floor:
            self.elevator.destination = self.request.source_floor
            self.elevator.state = Elevator.ElevatorState.moving_downwards_to_pickup

        else:
            self.initiate_dropoff()

    def complete_elevator_request(self):
        self.is_complete = True
        self.elevator.state = Elevator.ElevatorState.idle

    def progress_request(self):
        if self.elevator.pickup_in_progress:
            self.elevator.move_towards_destination()
            if self.elevator.current_floor == self.elevator.destination:
                self.initiate_dropoff()
        elif self.elevator.dropoff_in_progress:
            self.elevator.move_towards_destination()
            if self.elevator.current_floor == self.elevator.destination:
                self.complete_elevator_request()

    def initiate_dropoff(self):
        self.elevator.destination = self.request.target_floor
        if self.request.target_floor > self.elevator.current_floor:
            self.elevator.state = Elevator.ElevatorState.moving_upwards_to_dropoff
        elif self.request.target_floor < self.elevator.current_floor:
            self.elevator.state = Elevator.ElevatorState.moving_downwards_to_dropoff

    def __str__(self):
        return f"{self.elevator.name} currently on {self.elevator.current_floor} : {self.elevator.state} " \
               f" -- Request: {self.request}" \
               f" -- Status: {'Complete' if self.is_complete else 'Not Complete'}"


class BuildingElevatorSystemSimulator:
    def __init__(self, building: Building, input_df: pd.DataFrame, elevator_dispatcher: ElevatorDispatcher = ElevatorDispatcher()):
        self.building = building
        self.elevators = [Elevator(
            state=Elevator.ElevatorState.idle,
            name=f"Ele {i+1}",
            current_floor = self.building.min_floor,
        ) for i in range(self.building.number_of_elevators)]
        self.elevator_dispatcher = elevator_dispatcher
        self.time = -1
        self.call_queue = deque()
        self.elevator_requests = []
        self.input_df = input_df
        self.elevator_log_df = pd.DataFrame(columns=[f"{ele.name} Floor" for ele in self.elevators] + [f"{ele.name} Status" for ele in self.elevators])
        self.elevator_log_df.reindex(sorted(self.elevator_log_df.columns), axis=1)

    def list_in_progress_elevator_requests(self) -> list[ElevatorRequest]:
        return [elevator_request for elevator_request in self.elevator_requests if not elevator_request.is_complete]

    @property
    def max_time(self) -> int:
        return self.input_df["time"].max()

    def tick_time(self):
        self.time += 1
        calls = self.fetch_call_requests_at_time_t()
        self.call_queue.extend(calls)
        exit_flag = False
        while self.call_queue and not exit_flag:
            call_request = self.call_queue.popleft()
            elevator = self.elevator_dispatcher.dispatch_elevator_for_request(self.elevators, call_request)
            if elevator:
                self.elevator_requests.append(ElevatorRequest(elevator=elevator, request=call_request))
            else:
                self.call_queue.appendleft(call_request)
                exit_flag = True

        for elevator_request in self.list_in_progress_elevator_requests():
            elevator_request.progress_request()

    def update_elevator_log(self):
        for elevator in self.elevators:
            self.elevator_log_df._set_value(self.time, f"{elevator.name} Floor", elevator.current_floor)
            self.elevator_log_df._set_value(self.time, f"{elevator.name} Status", elevator.state.value)


    def run_simulation(self):
        while self.time < self.max_time or self.list_in_progress_elevator_requests() or self.call_queue:
            self.tick_time()
            self.update_elevator_log()

        print(f"\n\n------ Total Time taken: {self.time} ------")
        print(f"\n\n {self.elevator_log_df}")

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


if __name__ == "__main__":
    main()
