from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
import pandas as pd


def main():
    call_data = {
        'time': [0, 12, 11],
        'id': ["a", "b", 'D'],
        "source": [3, 3, 7],
        "dest": [7, 8, 18]
    }
    input_df = pd.DataFrame(data=call_data)
    building_elevator_system_simulator = BuildingElevatorSystemSimulator(
        building=Building(
            number_of_floors=100,
            number_of_elevators=2
        ),
        input_df=input_df,
    )
    building_elevator_system_simulator.run_simulation()


class Building:
    def __init__(self, number_of_floors: int,
                 number_of_elevators: int) -> None:
        self.floors = number_of_floors
        self.number_of_elevators = number_of_elevators


class Elevator:
    class ElevatorState(Enum):
        idle = "idle"
        moving_upwards_to_pickup = "moving_upwards_to_pickup"
        moving_upwards_to_dropoff = "moving_upwards_to_dropoff"
        moving_downwards_to_pickup = "moving_downwards_to_pickup"
        moving_downwards_to_dropoff = "moving_downwards_to_dropoff"
        picking_up = "picking_up"
        dropping_off = "dropping_off"
        unavailable = "unavailable"  # for maintenance or other special reasons

    def __init__(self, state: ElevatorState, name: str,
                 current_floor: int, max_number_of_passengers: int, **kwargs: Any) -> None:
        self.state = state
        self.name = name
        self.current_floor = current_floor
        self.destination = self.current_floor
        self.passengers = []
        self.capacity = max_number_of_passengers

        # Other Properties for extension
        # self.speed = ...
        # self.acceleration = ...
        # self.pickup_delay = ...
        # self.dropoff_delay = ...

    @property
    def is_available(self) -> bool:
        return self.state in [Elevator.ElevatorState.idle,
                              Elevator.ElevatorState.dropping_off]

    def move_towards_destination(self) -> None:
        if self.current_floor < self.destination:
            self.current_floor += 1
        elif self.current_floor > self.destination:
            self.current_floor -= 1

    @property
    def towards_pickup(self) -> bool:
        return self.state in [Elevator.ElevatorState.moving_downwards_to_pickup,
                              Elevator.ElevatorState.moving_upwards_to_pickup]

    @property
    def towards_dropoff(self) -> bool:
        return self.state in [Elevator.ElevatorState.moving_downwards_to_dropoff,
                              Elevator.ElevatorState.moving_upwards_to_dropoff]

    @property
    def is_elevator_at_capacity(self) -> bool:
        return len(self.passengers) == self.capacity


@dataclass
class CallRequest:
    time: int
    id: str
    source_floor: int
    target_floor: int
    pickup_time: int = -1
    dropoff_time: int = -1


class ElevatorDispatcher:
    class DispatchAlgos(Enum):
        FCFS = "FCFS"

    def __init__(self, algo: DispatchAlgos = DispatchAlgos.FCFS):
        self.algo = algo

    def dispatch_elevator_for_request(
            self, elevators: list[Elevator], request: CallRequest) -> Optional[Elevator]:
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
            filter(lambda elevator: elevator.is_available, elevators))
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
    def __init__(self, elevator: Elevator, request: CallRequest, time: int):
        self.elevator = elevator
        self.request = request
        self.is_complete: bool = False
        self.initiate_pickup(time)

    def initiate_pickup(self, time):
        if self.request.source_floor > self.elevator.current_floor:
            self.elevator.destination = self.request.source_floor
            self.elevator.state = Elevator.ElevatorState.moving_upwards_to_pickup

        elif self.request.source_floor < self.elevator.current_floor:
            self.elevator.destination = self.request.source_floor
            self.elevator.state = Elevator.ElevatorState.moving_downwards_to_pickup

        else:
            self.elevator.state = Elevator.ElevatorState.picking_up
            self.request.pickup_time = time

    def initiate_dropoff(self):
        self.elevator.destination = self.request.target_floor
        if self.request.target_floor > self.elevator.current_floor:
            self.elevator.state = Elevator.ElevatorState.moving_upwards_to_dropoff
        elif self.request.target_floor < self.elevator.current_floor:
            self.elevator.state = Elevator.ElevatorState.moving_downwards_to_dropoff

    def complete_elevator_request(self):
        self.is_complete = True

    def progress_request(self, time: int):
        if self.elevator.towards_pickup:
            self.elevator.move_towards_destination()
            if self.elevator.current_floor == self.elevator.destination:
                self.elevator.state = Elevator.ElevatorState.picking_up
                self.request.pickup_time = time
        elif self.elevator.towards_dropoff:
            self.elevator.move_towards_destination()
            if self.elevator.current_floor == self.elevator.destination:
                self.elevator.state = Elevator.ElevatorState.dropping_off
                self.request.dropoff_time = time
                self.complete_elevator_request()
        elif self.elevator.state == Elevator.ElevatorState.dropping_off:
            self.elevator.state = Elevator.ElevatorState.idle
        elif self.elevator.state == Elevator.ElevatorState.picking_up:
            self.initiate_dropoff()

    def __str__(self):
        return f"{self.elevator.name} currently on {self.elevator.current_floor} : {self.elevator.state} " \
               f" -- Request: {self.request}" \
               f" -- Status: {'Complete' if self.is_complete else 'Not Complete'}"


class BuildingElevatorSystemSimulator:
    def __init__(self, building: Building, input_df: pd.DataFrame,
                 elevator_dispatcher: ElevatorDispatcher = ElevatorDispatcher()):
        self.building = building
        self.elevators = [Elevator(
            state=Elevator.ElevatorState.idle,
            name=f"Ele {i+1}",
            current_floor=1,
            max_number_of_passengers=10,
        ) for i in range(self.building.number_of_elevators)]
        self.elevator_dispatcher = elevator_dispatcher
        self.time = -1
        self.call_queue = deque()
        self.elevator_requests = []
        self.input_df = input_df
        self.elevator_log_df = pd.DataFrame(
            columns=[
                f"{ele.name} Floor" for ele in self.elevators] + [
                f"{ele.name} Status" for ele in self.elevators])
        self.elevator_log_df.reindex(
            sorted(self.elevator_log_df.columns), axis=1)
        self.request_log_df = pd.DataFrame(
            columns=[
                "Call Time",
                "Pickup Time",
                "Dropoff Time",
                "Wait Time",
                "Total Time"])

    def list_in_progress_elevator_requests(self) -> list[ElevatorRequest]:
        return [elevator_request for elevator_request in self.elevator_requests if not elevator_request.is_complete]

    @property
    def max_time(self) -> int:
        return self.input_df["time"].max()

    def tick_time(self):
        self.time += 1
        new_elevator_requests = []
        calls = self.fetch_call_requests_at_time_t()
        self.call_queue.extend(calls)
        exit_flag = False
        while self.call_queue and not exit_flag:
            call_request = self.call_queue.popleft()
            elevator = self.elevator_dispatcher.dispatch_elevator_for_request(
                self.elevators, call_request)
            if elevator:
                new_elevator_request = ElevatorRequest(
                    elevator=elevator, request=call_request, time=self.time)
                self.elevator_requests.append(new_elevator_request)
                new_elevator_requests.append(new_elevator_request)
            else:
                self.call_queue.appendleft(call_request)
                exit_flag = True

        active_elevators = []
        for elevator_request in self.list_in_progress_elevator_requests():
            active_elevators.append(elevator_request.elevator)
            if elevator_request not in new_elevator_requests:
                elevator_request.progress_request(time=self.time)

        for elevator in self.elevators:
            if elevator not in active_elevators:
                elevator.state = Elevator.ElevatorState.idle

    def update_elevator_log(self):
        for elevator in self.elevators:
            self.elevator_log_df._set_value(
                self.time, f"{elevator.name} Floor", elevator.current_floor)
            self.elevator_log_df._set_value(
                self.time, f"{elevator.name} Status", elevator.state.value)

    def run_simulation(self) -> pd.DataFrame:
        while self.time < self.max_time or self.list_in_progress_elevator_requests() or self.call_queue:
            self.update_elevator_log()
            self.tick_time()
        self.update_elevator_log()

        self.create_request_log()
        print(f"\n\n------ Total Time taken: {self.time} ------")
        print(f"\n\n {self.elevator_log_df}")
        print(f"\n\n {self.request_log_df}")
        return self.elevator_log_df

    def create_request_log(self):
        for elevator_request in self.elevator_requests:
            call_request = elevator_request.request
            self.request_log_df.loc[call_request.id] = [
                call_request.time,
                call_request.pickup_time,
                call_request.dropoff_time,
                call_request.pickup_time - call_request.time,
                call_request.dropoff_time - call_request.time
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


if __name__ == "__main__":
    main()
