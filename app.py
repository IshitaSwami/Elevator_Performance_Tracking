from fastapi import FastAPI
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI()

# Elevator states
current_floor = 0
direction = "idle"  # "up", "down", "idle"
door_open = False

# Prometheus metrics
floor_gauge = Gauge("elevator_current_floor", "Current floor of the elevator")
direction_counter = Counter("elevator_direction_changes", "Number of direction changes", ['direction'])
door_state_gauge = Gauge("elevator_door_open", "Elevator door open status (1=open, 0=closed)")

# Track last direction for changes
last_direction = "idle"

@app.get("/")
def root():
    return {
        "floor": current_floor,
        "direction": direction,
        "door_open": door_open
    }

@app.post("/move/{new_direction}")
def move(new_direction: str):
    global direction, last_direction, current_floor
    
    if new_direction not in ["up", "down", "idle"]:
        return {"error": "Invalid direction"}
    
    direction = new_direction
    if direction != last_direction:
        direction_counter.labels(direction=direction).inc()
        last_direction = direction

    if direction == "up":
        current_floor += 1
    elif direction == "down":
        current_floor -= 1

    floor_gauge.set(current_floor)

    return {"floor": current_floor, "direction": direction}

@app.post("/door/{state}")
def door(state: str):
    global door_open

    if state == "open":
        door_open = True
        door_state_gauge.set(1)
    elif state == "close":
        door_open = False
        door_state_gauge.set(0)
    else:
        return {"error": "Invalid door state"}

    return {"door_open": door_open}

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
