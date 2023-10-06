import pytest

from elevator_dispatcher import ElevatorDispatcher
from models import ElevatorStop, CallRequest, Building


class TestSplitPlanIntoOrderedSubplans:
    def setup_method(self):
        self.empty_plan = []
        self.plan_with_too_few_stops = [4]
        self.plan_with_single_inflection = [2, 4, 6, 8, 7]
        self.plan_with_multiple_inflections = [8, 5, 7, 9, 14, 12, 10, 1, 5]

    def test_bad_input_raises_error(self):
        self.setup_method()
        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.split_plan_into_ordered_subplans(
                self.empty_plan
            )
        assert exc_info.value.args[0] == "Plan is too small to split; logical inconsistency"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.split_plan_into_ordered_subplans(
                self.plan_with_too_few_stops
            )
        assert exc_info.value.args[0] == "Plan is too small to split; logical inconsistency"

    def test_single_infection(self):
        self.setup_method()
        subplans = ElevatorDispatcher.split_plan_into_ordered_subplans(
            self.plan_with_single_inflection
        )

        expected_subplans = [
            [2, 4, 6, 8],
            [8, 7],
        ]

        assert subplans == expected_subplans

    def test_multiple_infections(self):
        self.setup_method()
        subplans = ElevatorDispatcher.split_plan_into_ordered_subplans(
            self.plan_with_multiple_inflections
        )

        expected_subplans = [
            [8, 5, ],
            [5, 7, 9, 14, ],
            [14, 12, 10, 1, ],
            [1, 5, ],
        ]

        assert subplans == expected_subplans


class TestFindInsertionPointsInArray:
    def test_raises_if_dir_is_improperly_set(self):
        unsorted_plan = [8, 5, 7, 9, 14, 12, 10, 1, 5]
        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=unsorted_plan,
                source_floor=1,
                target_floor=4,
                dir=-5
            )

        assert exc_info.value.args[0] == "Unknown direction"

    def test_raises_if_subplan_not_sorted(self):
        unsorted_plan = [8, 5, 7, 9, 14, 12, 10, 1, 5]
        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=unsorted_plan,
                source_floor=1,
                target_floor=4,
                dir=-1
            )

        assert exc_info.value.args[0] == "Subplan is not sorted"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=unsorted_plan,
                source_floor=1,
                target_floor=4,
                dir=1
            )

        assert exc_info.value.args[0] == "Subplan is not sorted"

    def test_raises_if_source_floor_not_in_subplan_range(self):
        sorted_asc_plan = [5, 7, 9, 14]
        sorted_desc_plan = [14, 12, 10, 3]
        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=sorted_asc_plan,
                source_floor=1,
                target_floor=4,
                dir=1
            )

        assert exc_info.value.args[0] == "Logic Failing - source floor not in subplan range"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=sorted_asc_plan,
                source_floor=15,
                target_floor=25,
                dir=1
            )

        assert exc_info.value.args[0] == "Logic Failing - source floor not in subplan range"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=sorted_desc_plan,
                source_floor=15,
                target_floor=10,
                dir=-1
            )

        assert exc_info.value.args[0] == "Logic Failing - source floor not in subplan range"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=sorted_desc_plan,
                source_floor=2,
                target_floor=1,
                dir=-1
            )

        assert exc_info.value.args[0] == "Logic Failing - source floor not in subplan range"

    def test_raises_if_target_floor_not_in_subplan_range(self):
        sorted_asc_plan = [5, 7, 9, 14]
        sorted_desc_plan = [14, 12, 10, 3]
        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=sorted_asc_plan,
                source_floor=8,
                target_floor=15,
                dir=1
            )

        assert exc_info.value.args[0] == "Logic Failing - target floor not in subplan range"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.find_insertion_points_in_array(
                sorted_subplan=sorted_desc_plan,
                source_floor=15,
                target_floor=10,
                dir=-1
            )

        assert exc_info.value.args[0] == "Logic Failing - source floor not in subplan range"

    def test_correct_returned_indices_for_asc_plan(self):
        sorted_asc_plan_1 = [5, 7, 9, 14]
        sorted_asc_plan_2 = [5, 9]
        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_asc_plan_1,
            source_floor=8,
            target_floor=14,
            dir=1
        )
        assert source_index == 2
        assert target_index == 4

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_asc_plan_1,
            source_floor=7,
            target_floor=14,
            dir=1
        )
        assert source_index == 1
        assert target_index == 3

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_asc_plan_2,
            source_floor=6,
            target_floor=7,
            dir=1
        )
        assert source_index == 1
        assert target_index == 2

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_asc_plan_2,
            source_floor=5,
            target_floor=7,
            dir=1
        )
        assert source_index == 0
        assert target_index == 1

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_asc_plan_2,
            source_floor=5,
            target_floor=9,
            dir=1
        )
        assert source_index == 0
        assert target_index == 1

    def test_correct_returned_indices_for_desc_plan(self):
        sorted_desc_plan_1 = [29, 14, 13, 1]
        sorted_desc_plan_2 = [14, 1]
        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_desc_plan_1,
            source_floor=16,
            target_floor=8,
            dir=-1
        )
        assert source_index == 1
        assert target_index == 4

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_desc_plan_1,
            source_floor=14,
            target_floor=13,
            dir=-1
        )
        assert source_index == 1
        assert target_index == 2

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_desc_plan_2,
            source_floor=7,
            target_floor=5,
            dir=-1
        )
        assert source_index == 1
        assert target_index == 2

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_desc_plan_2,
            source_floor=7,
            target_floor=1,
            dir=-1
        )
        assert source_index == 1
        assert target_index == 2

        source_index, target_index = ElevatorDispatcher.find_insertion_points_in_array(
            sorted_subplan=sorted_desc_plan_2,
            source_floor=14,
            target_floor=7,
            dir=-1
        )
        assert source_index == 0
        assert target_index == 1


class TestGetWaitTimeForRequest:
    def setup_method(self):
        self.building = Building(
            number_of_floors=25,
            number_of_elevators=3,
            max_capacity_of_elevator=10,
        )
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=self.building.elevators,
            request=CallRequest(
                time=10,
                id="test",
                source_floor=3,
                target_floor=5,
            )
        )

        self.elevator_dispatcher_2 = ElevatorDispatcher(
            elevators=self.building.elevators,
            request=CallRequest(
                time=10,
                id="test_2",
                source_floor=14,
                target_floor=5,
            )
        )

    def test_elevator_already_at_stop(self):
        elevator_plan = []
        current_floor = 3
        source_index = 0  # New plan: (curr_floor: 3), 3

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )

        assert wait_time == 0

    def test_calculates_wait_time_correctly(self):
        elevator_plan = [
            ElevatorStop(5, [], []),
            ElevatorStop(7, [], []),
            ElevatorStop(9, [], []),
            ElevatorStop(8, [], []),
            ElevatorStop(13, [], []),
            ElevatorStop(2, [], []),
            ElevatorStop(5, [], []),
        ]  # len: 7
        current_floor = 3
        source_index = 6  # New plan: (curr_floor: 3), 5, 7, 9, 8, 13, 2, ->3<-, 5

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )
        assert wait_time == 30

        current_floor = 3
        source_index = 7  # New plan: (curr_floor: 3), 5, 7, 9, 8, 13, 2, 5, ->3<-

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )
        assert wait_time == 35

        current_floor = 3
        source_index = 0  # New plan: (curr_floor: 3), ->3<-, 5, 7, 9, 8, 13, 2, 5

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )
        assert wait_time == 0

    def test_calculates_wait_time_correctly_2(self):
        elevator_plan = [
            ElevatorStop(9, [], []),
        ]
        current_floor = 3
        source_index = 1  # New plan: (curr_floor: 3),  9, ->14<-

        wait_time = self.elevator_dispatcher_2.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )
        assert wait_time == 12

        elevator_plan.append(
            ElevatorStop(25, [], []),
        )
        current_floor = 3
        source_index = 1  # New plan: (curr_floor: 3),  9, ->14<-, 25
        wait_time = self.elevator_dispatcher_2.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )
        assert wait_time == 12

        current_floor = 9
        source_index = 1  # New plan: (curr_floor: 9),  9, ->14<-, 25
        wait_time = self.elevator_dispatcher_2.get_wait_time_for_request(
            elevator_plan=elevator_plan, current_floor=current_floor, source_index=source_index
        )
        assert wait_time == 6


class TestGetTravelTimeForRequest:
    def setup_method(self):
        self.building = Building(
            number_of_floors=25,
            number_of_elevators=3,
            max_capacity_of_elevator=10,
        )
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=self.building.elevators,
            request=CallRequest(
                time=10,
                id="test",
                source_floor=3,
                target_floor=5,
            )
        )

        self.elevator_dispatcher_2 = ElevatorDispatcher(
            elevators=self.building.elevators,
            request=CallRequest(
                time=10,
                id="test_2",
                source_floor=14,
                target_floor=5,
            )
        )

    def test_elevator_already_at_stop(self):
        elevator_plan = []
        source_index = 0
        target_index = 1  # New plan: (curr_floor: 3), 3, 5
        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )

        assert travel_time == 2

    def test_calculates_travel_time_correctly(self):
        elevator_plan = [
            ElevatorStop(5, [], []),
            ElevatorStop(7, [], []),
            ElevatorStop(9, [], []),
            ElevatorStop(8, [], []),
            ElevatorStop(13, [], []),
            ElevatorStop(2, [], []),
            ElevatorStop(5, [], []),
        ]  # len: 7
        source_index = 5
        target_index = 7  # New plan: (curr_floor: 3), 5, 7, 9, 8, 13, ->3<-, 2, ->5<-

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert 5 == travel_time

        source_index = 7
        target_index = 8  # New plan: (curr_floor: 3), 5, 7, 9, 8, 13, 2, 5, ->3<-, ->5<-

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert 2 == travel_time

        source_index = 0
        target_index = 1  # New plan: (curr_floor: 3) ->3<-, ->5<-, 7, 9, 8, 13, 2,

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert 2 == travel_time

        source_index = 2
        target_index = 5  # New plan: (curr_floor: 3) 5, 7, ->3<-, 9, 8, 13, ->5<-,  2,

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert travel_time == 23

        source_index = 2
        target_index = 6  # New plan: (curr_floor: 3) 5, 7, ->3<-, 9, 8, 13, 2, ->5<-

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert travel_time == 30

    def test_calculates_travel_time_correctly_2(self):
        elevator_plan = [
            ElevatorStop(9, [], []),
        ]
        source_index = 1
        target_index = 2  # New plan: 9, =>14<=, =>5<=,

        travel_time = self.elevator_dispatcher_2.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert travel_time == 9

        elevator_plan.append(
            ElevatorStop(25, [], []),
        )
        source_index = 1
        target_index = 3  # New plan: 9, =>14<=, 25, =>5<=
        travel_time = self.elevator_dispatcher_2.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert travel_time == 32

        source_index = 0
        target_index = 2  # New plan: =>14<=, 9, =>5<=, 25
        travel_time = self.elevator_dispatcher_2.get_travel_time_for_request(
            elevator_plan=elevator_plan, source_index=source_index, target_index=target_index
        )
        assert travel_time == 10
