from dataclasses import dataclass
from enum import Enum


@dataclass
class CallRequest:
    """
    A dataclass that houses each call request and its various attrs
    """
    time: int
    id: str
    source_floor: int
    target_floor: int
    pickup_time: int = -1  # Default before pickup
    dropoff_time: int = -1  # Default before dropoff
    elevator_name: str = ""  # Default before assigned elevator

    @property
    def is_complete(self):
        return self.pickup_time != -1 and self.dropoff_time != -1


@dataclass
class ElevatorStop:
    floor: int
    pickup_requests: list[CallRequest]  # list of request ids
    dropoff_requests: list[CallRequest]  # list of request ids


class Elevator:
    """
    The elevator class that houses the various parameters that are involved in the
    operation of an elevator
    """

    class ElevatorState(Enum):
        idle = "idle"
        moving_upwards = "moving_upwards"
        moving_downwards = "moving_downwards"
        at_stop = "at_stop"
        unavailable = "unavailable"  # for maintenance or other special reasons

    def __init__(
            self, state: ElevatorState, name: str, current_floor: int, max_number_of_passengers: int, ) -> None:
        self.state = state
        self.name = name
        self.current_floor = current_floor
        self.passengers = []  # not implemented: list of request ids
        self.capacity = max_number_of_passengers
        self.elevator_plan: list[ElevatorStop] = []

    @property
    def check_capacity_at_floor(self) -> bool:
        return len(self.passengers) == self.capacity

    def coalesce_plan(self):
        mark_for_removal = None
        for i, stop in enumerate(self.elevator_plan[:-1]):
            if stop.floor == self.elevator_plan[i + 1].floor:
                stop.pickup_requests += self.elevator_plan[i + 1].pickup_requests
                stop.dropoff_requests += self.elevator_plan[i + 1].dropoff_requests
                mark_for_removal = i + 1
                break
        if mark_for_removal:
            del self.elevator_plan[mark_for_removal]

    def add_stop_to_plan(self, new_stop: ElevatorStop, index: int) -> None:
        self.elevator_plan.insert(index, new_stop)
        self.coalesce_plan()

    def remove_current_floor_from_plan(self, time: int) -> None:
        completed_stop = self.elevator_plan[0]
        for pickup_request in completed_stop.pickup_requests:
            pickup_request.pickup_time = time
        for dropoff_request in completed_stop.dropoff_requests:
            dropoff_request.dropoff_time = time

        self.elevator_plan = self.elevator_plan[1:]

    def next(self, time):
        if not self.elevator_plan:
            self.state = Elevator.ElevatorState.idle
        elif self.current_floor < self.elevator_plan[0].floor:
            self.current_floor += 1
            self.state = Elevator.ElevatorState.moving_upwards
        elif self.current_floor > self.elevator_plan[0].floor:
            self.current_floor -= 1
            self.state = Elevator.ElevatorState.moving_downwards
        elif self.current_floor == self.elevator_plan[0].floor:
            self.state = Elevator.ElevatorState.at_stop
            self.remove_current_floor_from_plan(time=time)


class Building:
    """
    The Building class which defines the floors and number of elevators in the system
    """

    def __init__(
            self,
            number_of_floors: int,
            number_of_elevators: int,
            max_capacity_of_elevator: int = 10,
    ) -> None:
        self.floors = number_of_floors
        self.number_of_elevators = number_of_elevators
        self.elevators = [
            Elevator(
                state=Elevator.ElevatorState.idle,
                name=f"Ele {i + 1}", current_floor=1,
                max_number_of_passengers=max_capacity_of_elevator,
            ) for i in range(self.number_of_elevators)
        ]


@dataclass
class PlanUpdate:
    source_index: int
    target_index: int
