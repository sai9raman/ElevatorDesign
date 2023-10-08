import pytest
from pytest_unordered import unordered

from elevator_dispatcher import ElevatorDispatcher
from models import ElevatorStop, CallRequest, Elevator


class TestSplitPlanIntoOrderedSubplans:
    def test_bad_input_raises_error(self):
        plan_with_too_few_stops = [
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[], )
        ]
        empty_plan = []
        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.split_plan_into_ordered_subplans(
                empty_plan
            )
        assert exc_info.value.args[0] == "Plan is too small to split; logical inconsistency"

        with pytest.raises(Exception) as exc_info:
            ElevatorDispatcher.split_plan_into_ordered_subplans(
                plan_with_too_few_stops
            )
        assert exc_info.value.args[0] == "Plan is too small to split; logical inconsistency"

    def test_single_infection(self):
        plan_with_single_inflection = [
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
        ]
        subplans = ElevatorDispatcher.split_plan_into_ordered_subplans(
            plan_with_single_inflection
        )
        expected_subplans = [
            [
                ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ],
            [
                ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
            ],
        ]

        assert subplans == expected_subplans

    def test_multiple_infections(self):
        plan_with_multiple_inflections = [
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=9, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=14, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=12, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=10, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=1, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[]),
        ]
        subplans = ElevatorDispatcher.split_plan_into_ordered_subplans(
            plan_with_multiple_inflections
        )

        expected_subplans = [
            [
                ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[]),
            ],
            [
                ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=9, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=14, pickup_requests=[], dropoff_requests=[]),
            ],
            [
                ElevatorStop(floor=14, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=12, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=10, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=1, pickup_requests=[], dropoff_requests=[]),
            ],
            [
                ElevatorStop(floor=1, pickup_requests=[], dropoff_requests=[]),
                ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[]),
            ],
        ]

        assert subplans == expected_subplans


class TestCoalescePlan:

    def test_plan_with_no_duplicates(self):
        plan = [
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
        ]
        new_plan = ElevatorDispatcher.coalesce_plan(elevator_plan=plan)

        assert new_plan == plan

    def test_plan_with_one_duplicates(self):
        call_req_a = CallRequest(
            source_floor=3, target_floor=5, time=10, id="A"
        )
        call_req_b = CallRequest(
            source_floor=43, target_floor=9, time=10, id="B"
        )
        call_req_c = CallRequest(
            source_floor=7, target_floor=19, time=10, id="C"
        )

        plan = [
            ElevatorStop(floor=2, pickup_requests=[call_req_a], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[call_req_c], dropoff_requests=[call_req_b]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
        ]

        ElevatorDispatcher.coalesce_plan(elevator_plan=plan)

        assert plan == [
            ElevatorStop(floor=2, pickup_requests=[call_req_a, call_req_c], dropoff_requests=[call_req_b]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[]),
        ]

    def test_coalesce_multiple_duplicates(self):
        call_req_a = CallRequest(
            source_floor=3, target_floor=5, time=10, id="A"
        )
        call_req_b = CallRequest(
            source_floor=43, target_floor=9, time=10, id="B"
        )
        call_req_c = CallRequest(
            source_floor=7, target_floor=19, time=10, id="C"
        )
        call_req_d = CallRequest(
            source_floor=7, target_floor=19, time=10, id="D"
        )
        call_req_e = CallRequest(
            source_floor=7, target_floor=19, time=10, id="E"
        )
        call_req_f = CallRequest(
            source_floor=7, target_floor=19, time=10, id="F"
        )
        plan = [
            ElevatorStop(floor=2, pickup_requests=[call_req_a], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[call_req_c], dropoff_requests=[call_req_b]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[call_req_a]),
            ElevatorStop(floor=6, pickup_requests=[call_req_d], dropoff_requests=[call_req_c]),
            ElevatorStop(floor=7, pickup_requests=[call_req_e], dropoff_requests=[call_req_d]),
            ElevatorStop(floor=7, pickup_requests=[call_req_f], dropoff_requests=[]),
        ]

        ElevatorDispatcher.coalesce_plan(elevator_plan=plan)

        assert plan == unordered(
            [
                ElevatorStop(floor=2, pickup_requests=[call_req_a, call_req_c], dropoff_requests=[call_req_b]),
                ElevatorStop(floor=6, pickup_requests=[call_req_d], dropoff_requests=[call_req_a, call_req_c]),
                ElevatorStop(floor=7, pickup_requests=[call_req_e, call_req_f], dropoff_requests=[call_req_d]),
            ]
        )


class TestCheckCapacity:
    @pytest.fixture()
    def setUp(self):
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=[
                Elevator(
                    state=Elevator.ElevatorState.moving_upwards,
                    name="Ele 1",
                    current_floor=3,
                    max_capacity_of_elevator=2,
                ),
                Elevator(
                    state=Elevator.ElevatorState.idle,
                    name="Ele 2",
                    current_floor=13,
                    max_capacity_of_elevator=5,
                )
            ]
        )
        self.mock_request = CallRequest(
            source_floor=5,
            target_floor=3,
            id='pass_test',
            time=10,
        )
        self.elevator = self.elevator_dispatcher.elevators[0]

    def test_check_capacity_within_capacity(self, setUp):
        # Test when the elevator has enough capacity for the new plan
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[self.mock_request, self.mock_request, self.mock_request], dropoff_requests=[self.mock_request]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        result = self.elevator_dispatcher.check_capacity(self.elevator, elevator_plan)
        assert result is True

    def test_check_capacity_exceeds_capacity(self, setUp):
        # Test when the new plan exceeds the elevator's capacity
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[self.mock_request, ], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[self.mock_request, self.mock_request, self.mock_request], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        result = self.elevator_dispatcher.check_capacity(self.elevator, elevator_plan)
        assert result is False

    def test_check_capacity_empty_plan(self, setUp):
        # Test when the elevator plan is empty (no passengers)
        elevator_plan = []

        result = self.elevator_dispatcher.check_capacity(self.elevator, elevator_plan)
        assert result is True



class TestFindMatchingSubplanForRequest:
    pass


class TestBuildUpdatedPlanForRequestInElevator:
    @pytest.fixture()
    def setUp(self):
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=[
                Elevator(
                    state=Elevator.ElevatorState.moving_upwards,
                    name="Ele 1",
                    current_floor=3,
                    max_capacity_of_elevator=5,
                ),
                Elevator(
                    state=Elevator.ElevatorState.idle,
                    name="Ele 2",
                    current_floor=13,
                    max_capacity_of_elevator=5,
                )
            ]
        )

    def test_updated_plan_in_between(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]
        self.elevator_dispatcher.elevators[0].elevator_plan = elevator_plan
        request = CallRequest(
            source_floor=5,
            target_floor=3,
            id='pass_test',
            time=10,
        )
        updated_plan = self.elevator_dispatcher.build_updated_elevator_plan_for_request_in_elevator(
            elevator=self.elevator_dispatcher.elevators[0],
            request=request,
        )

        assert updated_plan == [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=5, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[request]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

    def test_updated_plan_source_same_as_current_floor(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]
        self.elevator_dispatcher.elevators[0].elevator_plan = elevator_plan
        request = CallRequest(
            source_floor=3,
            target_floor=7,
            id='pass_test',
            time=10,
        )
        updated_plan = self.elevator_dispatcher.build_updated_elevator_plan_for_request_in_elevator(
            elevator=self.elevator_dispatcher.elevators[0],
            request=request,
        )

        assert updated_plan == [
            ElevatorStop(floor=3, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[request]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

    def test_updated_plan_at_end_of_plan(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]
        self.elevator_dispatcher.elevators[0].elevator_plan = elevator_plan
        request = CallRequest(
            source_floor=1,
            target_floor=7,
            id='pass_test',
            time=10,
        )
        updated_plan = self.elevator_dispatcher.build_updated_elevator_plan_for_request_in_elevator(
            elevator=self.elevator_dispatcher.elevators[0],
            request=request,
        )

        assert updated_plan == [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=1, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[request]),
        ]


class TestGetTravelTimeForRequest:
    @pytest.fixture()
    def setUp(self):
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=[
                Elevator(
                    state=Elevator.ElevatorState.moving_upwards,
                    name="Ele 1",
                    current_floor=3,
                    max_capacity_of_elevator=5,
                ),
                Elevator(
                    state=Elevator.ElevatorState.idle,
                    name="Ele 2",
                    current_floor=13,
                    max_capacity_of_elevator=5,
                )
            ]
        )

    def test_travel_time_correct_current_floor_is_first_stop_and_source_floor(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        request = CallRequest(
            source_floor=3,
            target_floor=2,
            id='pass_test',
            time=10,
        )

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan,
            request=request
        )

        assert travel_time == 9

        request = CallRequest(
            source_floor=3,
            target_floor=4,
            id='pass_test',
            time=10,
        )

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan,
            request=request
        )

        assert travel_time == 1

    def test_wait_time_correct_general(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        request = CallRequest(
            source_floor=6,
            target_floor=2,
            id='pass_test',
            time=10,
        )

        travel_time = self.elevator_dispatcher.get_travel_time_for_request(
            elevator_plan=elevator_plan,
            request=request
        )

        assert travel_time == 4


class TestGetWaitTimeForRequest:
    @pytest.fixture()
    def setUp(self):
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=[
                Elevator(
                    state=Elevator.ElevatorState.moving_upwards,
                    name="Ele 1",
                    current_floor=3,
                    max_capacity_of_elevator=5,
                ),
                Elevator(
                    state=Elevator.ElevatorState.idle,
                    name="Ele 2",
                    current_floor=13,
                    max_capacity_of_elevator=5,
                )
            ]
        )

    def test_wait_time_correct_current_floor_is_first_stop(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        request = CallRequest(
            source_floor=6,
            target_floor=2,
            id='pass_test',
            time=10,
        )

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan,
            current_floor=3,
            request=request
        )

        assert wait_time == 5

        request = CallRequest(
            source_floor=3,
            target_floor=6,
            id='pass_test',
            time=10,
        )

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan,
            current_floor=3,
            request=request
        )

        assert wait_time == 0

    def test_wait_time_correct_general(self, setUp):
        elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        request = CallRequest(
            source_floor=6,
            target_floor=2,
            id='pass_test',
            time=10,
        )

        wait_time = self.elevator_dispatcher.get_wait_time_for_request(
            elevator_plan=elevator_plan,
            current_floor=2,
            request=request
        )

        assert wait_time == 6


class TestGetElevatorAndUpdatedPlanForRequest:
    @pytest.fixture()
    def setUp(self):
        self.elevator_dispatcher = ElevatorDispatcher(
            elevators=[
                Elevator(
                    state=Elevator.ElevatorState.moving_upwards,
                    name="Ele 1",
                    current_floor=3,
                    max_capacity_of_elevator=5,
                ),
                Elevator(
                    state=Elevator.ElevatorState.idle,
                    name="Ele 2",
                    current_floor=13,
                    max_capacity_of_elevator=5,
                )
            ]
        )
        self.elevator_dispatcher.elevators[0].elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]
        self.elevator_dispatcher.elevators[1].elevator_plan = []

    def test_gets_elevator_with_least_time_for_idle(self, setUp):
        request = CallRequest(
            source_floor=11,
            target_floor=3,
            id='pass_test',
            time=10,
        )
        elevator, updated_plan = self.elevator_dispatcher.get_elevator_and_updated_plan_for_request(request=request)

        assert elevator == self.elevator_dispatcher.elevators[1]
        assert updated_plan == [
            ElevatorStop(floor=11, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[request]),
        ]

    def test_gets_elevator_with_least_time_for_moving(self, setUp):
        request = CallRequest(
            source_floor=5,
            target_floor=7,
            id='pass_test',
            time=10,
        )
        elevator, updated_plan = self.elevator_dispatcher.get_elevator_and_updated_plan_for_request(request=request)

        assert elevator == self.elevator_dispatcher.elevators[0]
        assert updated_plan == [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=5, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=7, pickup_requests=[], dropoff_requests=[request]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

    def test_elevator_choice_switches_with_change_of_elevator_plan(self, setUp):
        self.elevator_dispatcher.elevators[0].elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        request = CallRequest(
            source_floor=1,
            target_floor=5,
            id='pass_test',
            time=10,
        )

        elevator, updated_plan = self.elevator_dispatcher.get_elevator_and_updated_plan_for_request(request=request)

        assert elevator == self.elevator_dispatcher.elevators[0]
        assert updated_plan == [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=1, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[request]),
        ]

        self.elevator_dispatcher.elevators[0].elevator_plan = [
            ElevatorStop(floor=3, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=4, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=6, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=8, pickup_requests=[], dropoff_requests=[]),
            ElevatorStop(floor=2, pickup_requests=[], dropoff_requests=[]),
        ]

        elevator, updated_plan = self.elevator_dispatcher.get_elevator_and_updated_plan_for_request(request=request)

        assert elevator == self.elevator_dispatcher.elevators[1]
        assert updated_plan == [
            ElevatorStop(floor=1, pickup_requests=[request], dropoff_requests=[]),
            ElevatorStop(floor=5, pickup_requests=[], dropoff_requests=[request]),
        ]
