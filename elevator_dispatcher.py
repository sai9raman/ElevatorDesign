from typing import Optional

import numpy as np

from errors import DispatchError
from models import Elevator, CallRequest, ElevatorStop


class ElevatorDispatcher:
    """
    The Dispatcher Algorithm.

    Input: CallRequest, Elevators

    1. Finds the "optimal point" where the given call-request can be worked into each elevator's plan
        - The main simplification made here is that the call request will be tried to work into
        the existing elevator's directional plan. It would not alter the direction switches in the elevator's
        plan.
        - If no insertion point is found it will add the request to the end of the elevator's plan

    2. Compare the total-times for the request amongst all the elevators and pick the quickest elevator
        - Note that this is finding a local maxima. The wait times for the other requests already on the
        elevator's plan are not re-calculated and further optimized.
        - This prevents starvation

    """

    def __init__(self, elevators: list[Elevator]):
        self.elevators = elevators

    def get_elevator_and_updated_plan_for_request(self, request: CallRequest) -> tuple[Elevator, list[ElevatorStop]]:
        elevator_total_time_mapping: dict[Elevator, int] = {}
        elevator_and_updated_plan_mapping: dict[Elevator, list[ElevatorStop]] = {}
        for elevator in self.elevators:
            new_elevator_plan = self.build_updated_elevator_plan_for_request_in_elevator(elevator, request)
            elevator_total_time_mapping[elevator] = self.get_total_time_for_request(
                current_floor=elevator.current_floor,
                elevator_plan=new_elevator_plan,
                request=request,
            )
            elevator_and_updated_plan_mapping[elevator] = new_elevator_plan

        elevator_with_least_total_time: Elevator = min(elevator_total_time_mapping, key=elevator_total_time_mapping.get)

        return elevator_with_least_total_time, elevator_and_updated_plan_mapping[elevator_with_least_total_time]

    def get_total_time_for_request(
            self, current_floor: int, elevator_plan: list[ElevatorStop], request: CallRequest,
    ) -> int:
        return self.get_wait_time_for_request(
            request=request, elevator_plan=elevator_plan, current_floor=current_floor
        ) + self.get_travel_time_for_request(request=request, elevator_plan=elevator_plan)

    def get_wait_time_for_request(
            self, request: CallRequest, elevator_plan: list[ElevatorStop], current_floor: int,
    ) -> int:
        wait_time = 0
        i = 0
        while i < len(elevator_plan):
            prev_floor = current_floor if i == 0 else elevator_plan[i - 1].floor
            wait_time += abs(elevator_plan[i].floor - prev_floor)
            if elevator_plan[i].floor == request.source_floor:
                return wait_time
            i += 1
            wait_time += 1  # for the stop wait time

        raise DispatchError("Source floor not found in elevator's plan")

    def get_travel_time_for_request(
            self, request: CallRequest, elevator_plan: list[ElevatorStop]
    ) -> int:
        travel_time = 0
        i = 0
        pickup_done = False
        while i < len(elevator_plan):
            if pickup_done:
                travel_time += abs(elevator_plan[i].floor - elevator_plan[i - 1].floor)
                travel_time += 1  # stop time for other floors
            if elevator_plan[i].floor == request.target_floor:
                travel_time -= 1  # remove stop time from target floor
                return travel_time
            if elevator_plan[i].floor == request.source_floor:
                pickup_done = True
            i += 1

        raise DispatchError("Target floor not found in elevator's plan")

    def build_updated_elevator_plan_for_request_in_elevator(
            self, elevator: Elevator, request: CallRequest,
    ) -> list[ElevatorStop]:
        """
        :param elevator_plan: list of stops
        :param request: Call request
        :return:
        """

        source_stop = ElevatorStop(
            floor=request.source_floor,
            pickup_requests=[request],
            dropoff_requests=[],
        )
        target_stop = ElevatorStop(
            floor=request.target_floor,
            pickup_requests=[],
            dropoff_requests=[request],
        )

        if not elevator.elevator_plan:
            new_elevator_plan = [
                source_stop, target_stop,
            ]
            return new_elevator_plan

        if elevator.current_floor == elevator.elevator_plan[0].floor:
            current_floor_is_first_stop = True
            current_floor_stop_repr = []
        else:
            current_floor_is_first_stop = False
            current_floor_stop_repr = [ElevatorStop(
                floor=elevator.current_floor,
                pickup_requests=[],
                dropoff_requests=[],
            )]

        if len(elevator.elevator_plan) == 1 and current_floor_is_first_stop:
            new_elevator_plan = elevator.elevator_plan + [
                source_stop, target_stop,
            ]
            return new_elevator_plan

        if not current_floor_is_first_stop:
            current_elevator_plan = current_floor_stop_repr + elevator.elevator_plan
        else:
            current_elevator_plan = elevator.elevator_plan

        request_dir = np.sign(request.target_floor - request.source_floor)

        # Slice the plan into ordered subplans
        sorted_subplans = self.split_plan_into_ordered_subplans(current_elevator_plan)

        # evaluate each subplan to assess if the request can be worked into it
        matching_subplan, matching_subplan_loc = self.find_matching_subplan_for_request(
            sorted_subplans=sorted_subplans, request=request
        )

        # if no appropriate subplan is found, tack this request to the end of the plan
        if not matching_subplan:
            new_elevator_plan = elevator.elevator_plan + [source_stop, target_stop]
            return new_elevator_plan

        # if subplan is found, then insert this request into that subplan
        matching_subplan += [source_stop, target_stop]
        matching_subplan.sort(reverse=True if request_dir == -1 else False, key=lambda stop: stop.floor)

        # coalesce the subplan - combine duplicate floors
        self.coalesce_plan(elevator_plan=matching_subplan)  # this does it in place

        # create the new full elevator plan  by rejoining subplans
        new_elevator_plan = []
        for i, subplan in enumerate(sorted_subplans):
            new_elevator_plan += matching_subplan if i == matching_subplan_loc else subplan

        # Coalesce the updated full elevator plan
        self.coalesce_plan(elevator_plan=new_elevator_plan)

        # Remove the current floor repr from the plan
        if new_elevator_plan[0] == current_floor_stop_repr:
            new_elevator_plan = new_elevator_plan[1:]

        # Check capacity
        if not self.check_capacity(elevator=elevator, new_elevator_plan=new_elevator_plan):
            new_elevator_plan = elevator.elevator_plan + [source_stop, target_stop]
            return new_elevator_plan

        return new_elevator_plan

    @staticmethod
    def coalesce_plan(elevator_plan: list[ElevatorStop]) -> list[ElevatorStop]:
        indices_to_remove = []
        i = 0
        while i < len(elevator_plan) - 1:
            if elevator_plan[i].floor == elevator_plan[i + 1].floor:
                elevator_plan[i].pickup_requests = list(
                    set(elevator_plan[i].pickup_requests).union(set(elevator_plan[i + 1].pickup_requests))
                )
                elevator_plan[i].dropoff_requests = list(
                    set(elevator_plan[i].dropoff_requests).union(set(elevator_plan[i + 1].dropoff_requests))
                )
                indices_to_remove.append(i + 1)
                i += 1
            i += 1

        for index in indices_to_remove[::-1]:
            del elevator_plan[index]

        return elevator_plan

    @staticmethod
    def check_capacity(elevator: Elevator, new_elevator_plan: list[ElevatorStop]) -> bool:
        current_passenger_count = len(elevator.passengers)
        for stop in new_elevator_plan:
            current_passenger_count += (len(stop.pickup_requests) - len(stop.dropoff_requests))
            if current_passenger_count > elevator.capacity:
                return False
        return True

    @staticmethod
    def split_plan_into_ordered_subplans(elevator_plan: list[ElevatorStop]) -> list[list[ElevatorStop]]:
        if len(elevator_plan) < 2:
            raise DispatchError("Plan is too small to split")

        inflection_points = []
        elevator_direction = np.sign(elevator_plan[1].floor - elevator_plan[0].floor)
        for i in range(1, len(elevator_plan) - 1):
            if np.sign(elevator_plan[i + 1].floor - elevator_plan[i].floor) != elevator_direction:
                inflection_points.append(i + 1)
                elevator_direction = np.sign(elevator_plan[i + 1].floor - elevator_plan[i].floor)
        inflection_points.append(len(elevator_plan))
        sorted_subplans = []
        start = 0
        for ind in inflection_points:
            sorted_subplans.append(elevator_plan[start:ind])
            start = ind - 1

        return sorted_subplans

    def find_matching_subplan_for_request(
            self, sorted_subplans: list[list[ElevatorStop]], request: CallRequest
    ) -> tuple[Optional[list[ElevatorStop]], Optional[int]]:
        request_dir = np.sign(request.target_floor - request.source_floor)
        for i, subplan in enumerate(sorted_subplans):
            subplan_dir = np.sign(subplan[-1].floor - subplan[0].floor)
            subplan_set = set(range(subplan[0].floor, subplan[-1].floor, subplan_dir))
            request_set = set(range(request.source_floor, request.target_floor, request_dir))
            if subplan_dir == request_dir and request_set.issubset(subplan_set):
                return subplan, i
        return None, None
