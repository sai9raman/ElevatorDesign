## Elevator Dispatcher

A Python-based elevator simulation for studying elevator dispatching algorithms and analyzing performance metrics.

### Overview

This elevator simulation project simulates the operation of multiple elevators in a building, handles passenger
requests, and calculates performance metrics. This assumes an elevator style called "Destination Dispatch" elevators. In
this style, the source and the destination of the request is known before an elevator is dispatched to serve the
request.

### Dispatcher Algorithm

This dispatcher uses an algorithm where new requests do not alter the existing direction of the elevator.

**Definitions**

- Call request: A request for one passenger to go from a source floor to a target floor
- Elevator Plan: List of stops an elevator has to make in a sequential order

**Algorithm**

1. For a given call request, for each elevator in the building, find where the source floor and the destination floor
   can be worked into the elevator's travel plan.
2. Compare the "total time" taken by each elevator to serve that request
3. Pick the elevator whose total time for that request is the least

**Simplifications and drawbacks**

- The call request will be worked into the elevator's existing plan. It would not alter the directional plan of the
  elevator. _This ensures that every request is eventually completed._
- If no insertion point is found it will add the request to the end of the elevator's plan
- This algorithm is finding a local minima for that request. The wait times and travel times for the other requests
  already on the elevator's plan are not re-calculated and further optimized. _This prevents request starvation._

**Example**

Imagine a 25-floor building where there are two elevators. 

Elevator 1

- Current Floor: 3
- Current Plan: [3, 4, 6, 8, 2] : Making stops at floors 3, 4, 6, 8 and 2

Elevator 2 (Idle)

- Current Floor: 13
- Current Plan: []

Call request:

- Source Floor: 5
- Target Floor: 7

The algorithm will pick Elevator 1 to serve the request and update elevator 1's plan as follows:
[3, 4, **_5_**, 6, **_7_**, 8, 2]

**_Rationale_**
Even though elevator 2 is idle, the total time to serve the request with elevator 2 is higher than that of elevator 1.

Total time for elevator 1 = 3 [Wait time] + 3 [Travel Time] = 6

Total time for elevator 2 = 8 [Wait time] + 2 [Travel Time] = 10

### Primary goals

1. Pick up and drop off all persons calling it
2. Minimize `total time` defined as (`wait_time` + `travel_time`)

### Assumptions

1. It takes any elevator 1 time unit to move by 1 floor in either the up or down direction.
2. A stop takes 1 unit of time for an elevator
3. Each request refers to only one passenger

### Installation

To clone and set up this project, follow these steps:

1. Clone the repository to your local machine
   `git clone https://github.com/sai9raman/ElevatorDesign.git`
2. Setup the venv
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   ```
4. Run the simulation by following the instructions in the Usage section

### Usage

1. Prepare a CSV file with passenger call requests. The CSV file should have the following columns: time, id, source,
   and dest. Here's an example:
    ```csv
    time,id,source,dest
    0,1,2,7
    1,2,4,1
    2,3,7,3
    3,4,1,5
    ```

2. Run the simulation with the following command, specifying the path to your CSV file and the additional parameters

   Command: `python main.py <your parameters>` for example `python3 main.py -i  "input_call_requests.csv" `

   ```bash
   python3 main.py --help
   usage: main.py [-h] -i INPUT_CSV_PATH [-bf BUILDING_FLOORS] [-be BUILDING_ELEVATORS] [-ec ELEVATOR_CAPACITY]
   
   optional arguments:
   -h, --help            show this help message and exit
   -i INPUT_CSV_PATH, --input_csv_path INPUT_CSV_PATH
                        Path for the csv file (default: None)
   -bf BUILDING_FLOORS, --building_floors BUILDING_FLOORS
                        Number of floors in the building (default: 100)
   -be BUILDING_ELEVATORS, --building_elevators BUILDING_ELEVATORS
                        Number of elevators in the building (default: 10)
   -ec ELEVATOR_CAPACITY, --elevator_capacity ELEVATOR_CAPACITY
                        Capacity of Elevator in number of passengers (default: 10)
   ```

### Outputs

The outputs have three sections written to a csv file. 
1. Status of each elevator at each point of time 
2. Request Details
3. Metrics summary 

![Screen Shot 2023-10-09 at 10 02 23 PM](https://github.com/sai9raman/ElevatorDesign/assets/31806207/cb778d9e-254f-4a57-a026-4d238ff2d908)
![Screen Shot 2023-10-09 at 10 02 28 PM](https://github.com/sai9raman/ElevatorDesign/assets/31806207/897fd4ec-211e-4550-b289-265c4f04fcd7)


### Next steps

1. Improve logging to show passengers being dropped off and picked up
2. Add to testing - engine, helper methods
3. Refactors to reduce complexity
4. Create a reasonable front end to input and output results (consider _flask_)

### Contributing

Contributions are welcome! Please feel free to open issues or pull requests if you have suggestions, bug reports, or
improvements to the project.
