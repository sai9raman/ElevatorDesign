from typing import Optional

import numpy as np

from errors import DispatchError
from models import Elevator, CallRequest, ElevatorStop


class ElevatorDispatcher:
    """
    The Dispatcher Algorithm for coordinating elevator requests.

    Attributes:
    elevators (list[Elevator]): List of elevators to manage.

    Algo --
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
        """
        Initializes the ElevatorDispatcher with a list of elevators.

        Args:
            elevators (list[Elevator]): List of elevators to manage.
        """
        self.elevators = elevators

    def get_elevator_and_updated_plan_for_request(self, request: CallRequest) -> tuple[Elevator, list[ElevatorStop]]:
        """
        Finds the elevator with the shortest total time for the given request and returns it along with the
        updated plan.

        Args:
            request (CallRequest): The call request to assign to an elevator.

        Returns:
            tuple[Elevator, list[ElevatorStop]]: The selected elevator and its updated plan.
        """
        elevator_time_mapping: dict[Elevator, int] = {}
        elevator_plan_mapping: dict[Elevator, list[ElevatorStop]] = {}
        for elevator in self.elevators:
            new_elevator_plan = self.build_updated_elevator_plan_for_request_in_elevator(elevator, request)
            elevator_time_mapping[elevator] = self.get_total_time_for_request(
                current_floor=elevator.current_floor,
                elevator_plan=new_elevator_plan,
                request=request,
            )
            elevator_plan_mapping[elevator] = new_elevator_plan

        elevator_with_least_total_time: Elevator = min(elevator_time_mapping, key=elevator_time_mapping.get)
        chosen_new_elevator_plan = elevator_plan_mapping[elevator_with_least_total_time]
        updated_new_elevator_plan = self.put_request_id_in_elevator_plan(request, chosen_new_elevator_plan)
        return elevator_with_least_total_time, updated_new_elevator_plan

    def put_request_id_in_elevator_plan(self, request: CallRequest, elevator_plan: list[ElevatorStop]):
        i = len(elevator_plan) - 1
        target_index = None
        while i >= 0:
            if elevator_plan[i].floor == request.target_floor:
                elevator_plan[i].dropoff_requests.append(request)
                target_index = i
                break
            i -= 1
        if not target_index:
            raise DispatchError("Could not find target floor in new plan")

        i = target_index
        while i >= 0:
            if elevator_plan[i].floor == request.source_floor:
                elevator_plan[i].pickup_requests.append(request)
                break
            i -= 1
        return elevator_plan

    def get_total_time_for_request(
            self, current_floor: int, elevator_plan: list[ElevatorStop], request: CallRequest,
    ) -> int:
        """
        Calculates the total time for a CallRequest.

        Args:
            current_floor (int): The current floor of the elevator.
            elevator_plan (list[ElevatorStop]): The elevator's plan.
            request (CallRequest): The CallRequest.

        Returns:
            int: The total time for the CallRequest.
        """
        return self.get_wait_time_for_request(
            request=request, elevator_plan=elevator_plan, current_floor=current_floor
        ) + self.get_travel_time_for_request(request=request, elevator_plan=elevator_plan)

    def get_wait_time_for_request(
            self, request: CallRequest, elevator_plan: list[ElevatorStop], current_floor: int,
    ) -> int:
        """
        Calculates the waiting time for a CallRequest within an elevator's plan.

        Args:
            request (CallRequest): The CallRequest to calculate wait time for.
            elevator_plan (list[ElevatorStop]): The elevator's plan.
            current_floor (int): The current floor of the elevator.

        Returns:
            int: The waiting time for the CallRequest.

        Raises:
            DispatchError: If the source floor of the CallRequest is not found in the elevator's plan.
        """
        total_wait_time = 0
        i = 0

        # Iterate through the elevator plan to calculate wait time
        while i < len(elevator_plan):
            prev_floor = current_floor if i == 0 else elevator_plan[i - 1].floor

            # Calculate the floor-to-floor travel time
            total_wait_time += abs(elevator_plan[i].floor - prev_floor)

            # Check if the current floor matches the source floor of the request
            if elevator_plan[i].floor == request.source_floor:
                return total_wait_time

            i += 1

            # Add stop wait time (1 unit) for each floor
            total_wait_time += 1

        # If the source floor is not found, raise a DispatchError
        raise DispatchError("Source floor not found in elevator's plan")

    def get_travel_time_for_request(
            self, request: CallRequest, elevator_plan: list[ElevatorStop]
    ) -> int:
        """
        Calculates the travel time for a CallRequest within an elevator's plan.

        Args:
            request (CallRequest): The CallRequest to calculate travel time for.
            elevator_plan (list[ElevatorStop]): The elevator's plan.

        Returns:
            int: The travel time for the CallRequest.

        Raises:
            DispatchError: If the target floor of the CallRequest is not found in the elevator's plan.
        """
        total_travel_time = 0
        i = 0
        pickup_done = False

        # Iterate through the elevator plan to calculate travel time
        while i < len(elevator_plan):
            if pickup_done:
                # Calculate the floor-to-floor travel time and add stop time for other floors
                total_travel_time += abs(elevator_plan[i].floor - elevator_plan[i - 1].floor)
                total_travel_time += 1  # Stop time for other floors

            # Check if the current floor matches the target floor of the request
            if elevator_plan[i].floor == request.target_floor:
                # Remove the stop time from the target floor and return the total travel time
                total_travel_time -= 1
                return total_travel_time

            # Check if the current floor matches the source floor of the request
            if elevator_plan[i].floor == request.source_floor:
                pickup_done = True

            i += 1

        # If the target floor is not found, raise a DispatchError
        raise DispatchError("Target floor not found in elevator's plan")

    def build_updated_elevator_plan_for_request_in_elevator(
            self, elevator: Elevator, request: CallRequest,
    ) -> list[ElevatorStop]:
        """
        Builds an updated elevator plan considering a new CallRequest for a specific elevator.

        Args:
            elevator (Elevator): The elevator to build the updated plan for.
            request (CallRequest): The CallRequest to add to the plan.

        Returns:
            list[ElevatorStop]: The updated elevator plan with the added request.

        """

        # Create ElevatorStops for the source and target floors of the request
        source_stop = ElevatorStop(
            floor=request.source_floor,
            pickup_requests=[],
            dropoff_requests=[],
        )
        target_stop = ElevatorStop(
            floor=request.target_floor,
            pickup_requests=[],
            dropoff_requests=[],
        )

        if not elevator.elevator_plan:
            # If the elevator plan is empty, create a new plan with the source and target stops
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
            # If the elevator plan has only one stop and the current floor is the first stop,
            # append the source and target stops to the existing plan
            new_elevator_plan = elevator.elevator_plan + [
                source_stop, target_stop,
            ]
            return new_elevator_plan

        if not current_floor_is_first_stop:
            current_elevator_plan = current_floor_stop_repr + elevator.elevator_plan
        else:
            current_elevator_plan = elevator.elevator_plan

        request_dir = np.sign(request.target_floor - request.source_floor)

        # Slice the plan into ordered subplans based on direction
        sorted_subplans = self.split_plan_into_ordered_subplans(current_elevator_plan)

        # Evaluate each subplan to assess if the request can be worked into it
        matching_subplan, matching_subplan_loc = self.find_matching_subplan_for_request(
            sorted_subplans=sorted_subplans, request=request
        )

        # If no appropriate subplan is found, append the request to the end of the plan
        if not matching_subplan:
            new_elevator_plan = elevator.elevator_plan + [source_stop, target_stop]
            self.coalesce_plan(elevator_plan=new_elevator_plan)
            return new_elevator_plan

        # If a matching subplan is found, insert the request into that subplan
        matching_subplan += [source_stop, target_stop]

        # Sort the subplan in the elevator's travel direction
        matching_subplan.sort(reverse=True if request_dir == -1 else False, key=lambda stop: stop.floor)

        # Coalesce the subplan to combine duplicate floors
        self.coalesce_plan(elevator_plan=matching_subplan)  # This does it in place

        # Create the new full elevator plan by rejoining subplans
        new_elevator_plan = []
        for i, subplan in enumerate(sorted_subplans):
            new_elevator_plan += matching_subplan if i == matching_subplan_loc else subplan

        # Coalesce the updated full elevator plan
        self.coalesce_plan(elevator_plan=new_elevator_plan)

        # Remove the current floor repr from the plan if present
        if current_floor_stop_repr\
                and new_elevator_plan[0] == current_floor_stop_repr[0] \
                and not (source_stop.floor == current_floor_stop_repr[0].floor):  # rethink this condition
            new_elevator_plan = new_elevator_plan[1:]

        # Check if the elevator's capacity is exceeded with the new plan
        if not self.check_capacity(elevator=elevator, new_elevator_plan=new_elevator_plan):
            # If capacity is exceeded, revert to the previous plan (before adding the request)
            new_elevator_plan = elevator.elevator_plan + [source_stop, target_stop]
            self.coalesce_plan(elevator_plan=new_elevator_plan)

        return new_elevator_plan

    @staticmethod
    def coalesce_plan(elevator_plan: list[ElevatorStop]) -> list[ElevatorStop]:
        """
        Combines elevator stops with the same floor, reducing duplicate stops.

        Args:
            elevator_plan (list[ElevatorStop]): The elevator's plan to coalesce.

        Returns:
            list[ElevatorStop]: The coalesced elevator plan with merged pickup and dropoff requests.
        """
        indices_to_remove = []
        i = 0

        # Iterate through the elevator plan to find and merge stops with the same floor
        while i < len(elevator_plan) - 1:
            if elevator_plan[i].floor == elevator_plan[i + 1].floor:
                # Merge pickup and dropoff requests for stops with the same floor
                elevator_plan[i].pickup_requests = list(
                    set(elevator_plan[i].pickup_requests).union(set(elevator_plan[i + 1].pickup_requests))
                )
                elevator_plan[i].dropoff_requests = list(
                    set(elevator_plan[i].dropoff_requests).union(set(elevator_plan[i + 1].dropoff_requests))
                )

                # Mark the next stop for removal
                indices_to_remove.append(i + 1)
                i += 1
            i += 1

        # Remove the marked stops in reverse order to avoid index issues
        for index in indices_to_remove[::-1]:
            del elevator_plan[index]

        return elevator_plan

    @staticmethod
    def check_capacity(elevator: Elevator, new_elevator_plan: list[ElevatorStop]) -> bool:
        """
        Checks if adding new elevator stops to the plan exceeds the elevator's capacity.

        Args:
            elevator (Elevator): The elevator to check capacity for.
            new_elevator_plan (list[ElevatorStop]): The new elevator plan with added stops.

        Returns:
            bool: True if adding the new stops does not exceed the elevator's capacity, False otherwise.
        """
        current_passenger_count = len(elevator.passengers)

        # Calculate the updated passenger count by considering added pickup and dropoff requests
        for stop in new_elevator_plan:
            current_passenger_count += (len(stop.pickup_requests) - len(stop.dropoff_requests))

            # If the updated passenger count exceeds the elevator's capacity, return False
            if current_passenger_count > elevator.capacity:
                return False

        # If the loop completes without exceeding the capacity, return True
        return True

    @staticmethod
    def split_plan_into_ordered_subplans(elevator_plan: list[ElevatorStop]) -> list[list[ElevatorStop]]:
        """
        Splits an elevator plan into ordered subplans based on direction.

        Args:
            elevator_plan (list[ElevatorStop]): The elevator's plan to split into subplans.

        Returns:
            list[list[ElevatorStop]]: A list of ordered subplans, where each subplan consists of consecutive stops
            in the same direction.

        Raises:
            DispatchError: If the elevator plan has less than two stops (too small to split).
        """
        if len(elevator_plan) < 2:
            raise DispatchError("Plan is too small to split")

        inflection_points = []  # Stores indices where the direction changes
        elevator_direction = np.sign(elevator_plan[1].floor - elevator_plan[0].floor)

        # Find inflection points where direction changes
        for i in range(1, len(elevator_plan) - 1):
            if np.sign(elevator_plan[i + 1].floor - elevator_plan[i].floor) != elevator_direction:
                inflection_points.append(i + 1)
                elevator_direction = np.sign(elevator_plan[i + 1].floor - elevator_plan[i].floor)

        inflection_points.append(len(elevator_plan))
        sorted_subplans = []  # List to store ordered subplans
        start = 0

        # Create subplans based on inflection points
        for ind in inflection_points:
            sorted_subplans.append(elevator_plan[start:ind])
            start = ind - 1

        return sorted_subplans

    def find_matching_subplan_for_request(
            self, sorted_subplans: list[list[ElevatorStop]], request: CallRequest
    ) -> tuple[Optional[list[ElevatorStop]], Optional[int]]:
        """
        Finds a matching subplan for a CallRequest.

        Args:
            sorted_subplans (list[list[ElevatorStop]]): A list of sorted subplans.
            request (CallRequest): The CallRequest.

        Returns:
            tuple[Optional[list[ElevatorStop]], Optional[int]]:
                A tuple containing the matching subplan and its index in the sorted_subplans list.
                Returns None if no matching subplan is found.
        """
        request_dir = np.sign(request.target_floor - request.source_floor)
        for i, subplan in enumerate(sorted_subplans):
            subplan_dir = np.sign(subplan[-1].floor - subplan[0].floor)
            subplan_set = set(range(subplan[0].floor, subplan[-1].floor, subplan_dir))
            request_set = set(range(request.source_floor, request.target_floor, request_dir))
            if subplan_dir == request_dir and request_set.issubset(subplan_set):
                return subplan, i
        return None, None
