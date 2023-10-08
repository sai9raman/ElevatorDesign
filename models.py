from dataclasses import dataclass
from enum import Enum


@dataclass()
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

    def __hash__(self):
        return hash((self.time, self.id, self.source_floor, self.target_floor))

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
            self, state: ElevatorState, name: str, current_floor: int, max_capacity_of_elevator: int
    ) -> None:
        self.state = state
        self.name = name
        self.current_floor = current_floor
        self.passengers: list[str] = []  # list of passenger ids in the elevator
        self.capacity = max_capacity_of_elevator
        self.elevator_plan: list[ElevatorStop] = []

    def remove_current_floor_from_plan(self, time: int) -> None:
        completed_stop = self.elevator_plan[0]
        for pickup_request in completed_stop.pickup_requests:
            pickup_request.pickup_time = time
            self.passengers.append(pickup_request.id)
        for dropoff_request in completed_stop.dropoff_requests:
            dropoff_request.dropoff_time = time
            self.passengers.remove(dropoff_request.id)

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

    def update_plan(self, updated_plan: list[ElevatorStop]):
        self.elevator_plan = updated_plan


class Building:
    """
    The Building class which defines the floors and number of elevators in the system
    """

    def __init__(
            self,
            number_of_floors: int,
            number_of_elevators: int,
            max_capacity_of_elevator: int,
    ) -> None:
        self.floors = number_of_floors
        self.number_of_elevators = number_of_elevators
        self.elevators = [
            Elevator(
                state=Elevator.ElevatorState.idle,
                name=f"Ele {i + 1}", current_floor=1,
                max_capacity_of_elevator=max_capacity_of_elevator,
            ) for i in range(self.number_of_elevators)
        ]

