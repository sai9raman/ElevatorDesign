import operator
from typing import Optional

import numpy as np

from models import Elevator, CallRequest, PlanUpdate, ElevatorStop


class ElevatorDispatcher:
    """
    The Dispatcher Algorithm.

    Input: CallRequest, Elevators

    1. Finds the optimal point where the given call-request can be worked into each elevator
        - The main simplification made here is that the call request will be tried to work into
        the existing elevator's directional plan. It would not alter the direction switches in the elevator's
        plan.
        - If no insertion point is found it will add the request to the end of the elevator's plan

    2. Compare the total-times for the request amongst all the elevators and pick the quickest elevator
        - Note that this is finding a local maxima. The wait times for the other requests already on the
        elevator's plan are not re-calculated and further optimized.
        This prevents starvation

    """

    def __init__(self, elevators: list[Elevator], request: CallRequest):
        self.elevators = elevators
        self.request = request

    def get_elevator_and_plan_update_for_request(self) -> tuple[Elevator, PlanUpdate]:
        total_time_dict: dict[Elevator, int] = {}
        elevator_plan_update: dict[Elevator, PlanUpdate] = {}
        for elevator in self.elevators:
            source_ind, target_ind = self.get_indices_in_elevator_plan_for_request(
                elevator.current_floor,
                elevator.elevator_plan,
            )
            total_time_dict[elevator] = self.get_total_time_for_request(
                elevator.current_floor, elevator.elevator_plan,
                source_ind, target_ind
            )
            elevator_plan_update[elevator] = PlanUpdate(source_index=source_ind, target_index=target_ind)
        best_elevator: Elevator = min(total_time_dict, key=total_time_dict.get)
        return best_elevator, elevator_plan_update[best_elevator]

    def get_total_time_for_request(
            self, current_floor: int, elevator_plan: list[ElevatorStop], source_index: int,
            target_index: int
    ) -> int:
        return self.get_wait_time_for_request(
            current_floor, elevator_plan, source_index
        ) + self.get_travel_time_for_request(
            elevator_plan,
            source_index, target_index
        )

    def get_wait_time_for_request(
            self, current_floor: int, elevator_plan: list[ElevatorStop], source_index: int
    ) -> int:
        wait_time = 0
        for i, stop in enumerate(elevator_plan[:source_index]):
            wait_time += abs(stop.floor - (elevator_plan[i - 1].floor if i > 0 else current_floor))
        return wait_time + abs(
            self.request.source_floor - (elevator_plan[source_index - 1].floor if source_index > 0 else current_floor)
        )

    def get_travel_time_for_request(
            self, elevator_plan: list[ElevatorStop], source_index: int, target_index: int
    ) -> int:
        travel_time = abs(
            (elevator_plan[source_index + 1].floor if source_index < len(
                elevator_plan
            ) - 1 else
             self.request.target_floor) - self.request.source_floor
        )
        for i, stop in enumerate(elevator_plan[source_index + 1:target_index]):
            travel_time += abs(stop.floor - elevator_plan[i - 1].floor)
        return travel_time + abs(
            self.request.target_floor - (
                elevator_plan[target_index - 1].floor if target_index < len(
                    elevator_plan
                ) else self.request.target_floor)
        )

    def get_indices_in_elevator_plan_for_request(
            self, current_floor: int, elevator_plan: list[ElevatorStop],
    ) -> tuple[int, int]:
        """
        :param elevator_plan: list of stops
        :param request: Call request
        :return:
        """
        request_diff = self.request.target_floor - self.request.source_floor
        request_dir = np.sign(request_diff)
        if elevator_plan and current_floor == elevator_plan[0].floor:
            current_floor_is_first_stop = True
            elevator_floor_plan = [stop.floor for stop in elevator_plan]
        else:
            current_floor_is_first_stop = False
            elevator_floor_plan = [current_floor] + [stop.floor for stop in elevator_plan]

        if len(elevator_floor_plan) <= 1:
            return 0, 1  # add to beginning of plan,

        # Slice the plan into ordered subplans (this includes current floor)
        sorted_subplans = self._split_plan_into_ordered_subplans(elevator_floor_plan)

        # evaluate each subplan to assess if the request can be worked into it
        current_floor_adj = -1 if not current_floor_is_first_stop else 0
        matching_subplan, index_delta = self._find_matching_subplan_for_request(
            index_delta=current_floor_adj, sorted_subplans=sorted_subplans
        )

        # if no appropriate subplan is found, tack this request to the end of the plan
        if not matching_subplan:
            return len(elevator_floor_plan) + current_floor_adj, len(elevator_floor_plan) + current_floor_adj + 1

            # if subplan is found, then correctly insert this request into that elevator's plan
        source_index, target_index = self.find_insertion_points_in_array(
            sorted_subplan=matching_subplan,
            source_floor=self.request.source_floor,
            target_floor=self.request.target_floor,
            dir=request_dir
        )
        source_index += index_delta
        target_index += index_delta

        # ToDo: Capacity Check - Check if request can work into elevator's capacity constraints

        return source_index, target_index

    @staticmethod
    def find_insertion_points_in_array(
            sorted_subplan: list[int], source_floor: int, target_floor: int, dir: int,
    ) -> tuple[int, int]:
        if dir == 1:
            comparison_operator = operator.le
        elif dir == -1:
            comparison_operator = operator.ge
        else:
            raise Exception("Unknown direction")

        source_index = None
        target_index = None
        source_already_in_plan_flag = False
        for i in range(len(sorted_subplan)):
            if comparison_operator(source_floor, sorted_subplan[i]):
                source_index = i
                if source_floor == sorted_subplan[i]:
                    source_already_in_plan_flag = True
                break

        if source_index is None:
            raise Exception("Logic Failing")

        for i in range(source_index - 1, len(sorted_subplan)):
            if comparison_operator(target_floor, sorted_subplan[i]):
                target_index = i

        if target_index is None:
            raise Exception("Logic Failing")

        if not source_already_in_plan_flag:
            target_index += 1  # adjusting for the adding of the source floor

        return source_index, target_index

    @staticmethod
    def _split_plan_into_ordered_subplans(plan: list[int]) -> list[list]:
        inflection_points = []
        dir = np.sign(plan[1] - plan[0])
        for i in range(1, len(plan) - 1):
            if np.sign(plan[i + 1] - plan[i]) != dir:
                inflection_points.append(i + 1)
                dir = np.sign(plan[i + 1] - plan[i])
        inflection_points.append(len(plan))
        sorted_subplans = []
        start = 0
        for ind in inflection_points:
            sorted_subplans.append(plan[start:ind])
            start = ind - 1

        return sorted_subplans

    def _find_matching_subplan_for_request(
            self, index_delta: int, sorted_subplans: list[list]
    ) -> tuple[Optional[list], int]:
        request_dir = np.sign(self.request.target_floor - self.request.source_floor)
        matching_subplan = None
        for subplan in sorted_subplans:
            subplan_dir = np.sign(subplan[-1] - subplan[0])
            if subplan_dir != request_dir:
                index_delta += len(subplan) - 1
                continue
            subplan_set = set(range(subplan[0], subplan[-1], subplan_dir))
            request_set = set(range(self.request.source_floor, self.request.target_floor, request_dir))
            if not request_set.issubset(subplan_set):
                index_delta += len(subplan) - 1
                continue
            matching_subplan = subplan
            break

        return matching_subplan, index_delta
