import json
import uuid
import math
import os

# --- Booking System Logic ---
LOCATIONS = ["PUP Main", "CEA", "Hasmin", "iTech", "COC", "PUP LHS", "Condotel"]

DISTANCE_MATRIX = {
    ("PUP Main", "CEA"): 2.0,
    ("PUP Main", "Hasmin"): 1.5,
    ("PUP Main", "iTech"): 1.2,
    ("PUP Main", "COC"): 1.0,
    ("PUP Main", "PUP LHS"): 1.7,
    ("PUP Main", "Condotel"): 1.5,
    ("CEA", "Hasmin"): 2.0,
    ("CEA", "iTech"): 5.0,
    ("CEA", "COC"): 4.5,
    ("CEA", "PUP LHS"): 4.0,
    ("CEA", "Condotel"): 4.5,
    ("Hasmin", "iTech"): 4.0,
    ("Hasmin", "COC"): 3.5,
    ("Hasmin", "PUP LHS"): 0.5,
    ("Hasmin", "Condotel"): 1.5,
    ("iTech", "COC"): 0.5,
    ("iTech", "PUP LHS"): 2.5,
    ("iTech", "Condotel"): 0.5,
    ("COC", "PUP LHS"): 2.0,
    ("COC", "Condotel"): 1.0,
    ("PUP LHS", "Condotel"): 2.0,
}

ROUTE_IMAGE_MAP = {
    ("PUP Main", "CEA"): "pup_main_to_cea.png",
    ("CEA", "PUP Main"): "pup_main_to_cea.png",
    ("PUP Main", "Hasmin"): "pup_main_to_hasmin.png",
    ("Hasmin", "PUP Main"): "pup_main_to_hasmin.png",
    ("PUP Main", "iTech"): "pup_main_to_itech.png",
    ("iTech", "PUP Main"): "pup_main_to_itech.png",
    ("PUP Main", "COC"): "pup_main_to_coc.png",
    ("COC", "PUP Main"): "pup_main_to_coc.png",
    ("PUP Main", "PUP LHS"): "pup_main_to_pup_lhs.png",
    ("PUP LHS", "PUP Main"): "pup_main_to_pup_lhs.png",
    ("PUP Main", "Condotel"): "pup_main_to_condotel.png",
    ("Condotel", "PUP Main"): "pup_main_to_condotel.png",
    ("CEA", "Hasmin"): "cea_to_hasmin.png",
    ("Hasmin", "CEA"): "cea_to_hasmin.png",
    ("CEA", "iTech"): "cea_to_itech.png",
    ("iTech", "CEA"): "cea_to_itech.png",
    ("CEA", "COC"): "cea_to_coc.png",
    ("COC", "CEA"): "cea_to_coc.png",
    ("CEA", "PUP LHS"): "cea_to_pup_lhs.png",
    ("PUP LHS", "CEA"): "cea_to_pup_lhs.png",
    ("CEA", "Condotel"): "cea_to_condotel.png",
    ("Condotel", "CEA"): "cea_to_condotel.png",
    ("Hasmin", "iTech"): "hasmin_to_itech.png",
    ("iTech", "Hasmin"): "hasmin_to_itech.png",
    ("Hasmin", "COC"): "hasmin_to_coc.png",
    ("COC", "Hasmin"): "hasmin_to_coc.png",
    ("Hasmin", "PUP LHS"): "hasmin_to_pup_lhs.png",
    ("PUP LHS", "Hasmin"): "hasmin_to_pup_lhs.png",
    ("Hasmin", "Condotel"): "hasmin_to_condotel.png",
    ("Condotel", "Hasmin"): "hasmin_to_condotel.png",
    ("iTech", "COC"): "itech_to_coc.png",
    ("COC", "iTech"): "itech_to_coc.png",
    ("iTech", "PUP LHS"): "itech_to_pup_lhs.png",
    ("PUP LHS", "iTech"): "itech_to_pup_lhs.png",
    ("iTech", "Condotel"): "itech_to_condotel.png",
    ("Condotel", "iTech"): "itech_to_condotel.png",
    ("COC", "PUP LHS"): "coc_to_pup_lhs.png",
    ("PUP LHS", "COC"): "coc_to_pup_lhs.png",
    ("COC", "Condotel"): "coc_to_condotel.png",
    ("Condotel", "COC"): "coc_to_condotel.png",
    ("PUP LHS", "Condotel"): "pup_lhs_to_condotel.png",
    ("Condotel", "PUP LHS"): "pup_lhs_to_condotel.png",
}

def get_distance(start, end):
    """Calculates distance between two locations."""
    if (start, end) in DISTANCE_MATRIX:
        return DISTANCE_MATRIX[(start, end)]
    elif (end, start) in DISTANCE_MATRIX:
        return DISTANCE_MATRIX[(end, start)]
    else:
        return 0.0

class Booking:
    def __init__(self, vehicle_type, start, end, distance, cost, payment_method, status="booked", booking_id=None):
        self.id = booking_id if booking_id else str(uuid.uuid4())[:8]
        self.vehicle_type = vehicle_type
        self.start = start
        self.end = end
        self.distance = distance
        self.cost = cost
        self.payment_method = payment_method
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_type": self.vehicle_type,
            "start": self.start,
            "end": self.end,
            "distance": self.distance,
            "cost": self.cost,
            "payment_method": self.payment_method,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["vehicle_type"],
            data["start"],
            data["end"],
            data["distance"],
            data["cost"],
            data["payment_method"],
            data["status"],
            data["id"]
        )

class BookingSystem:
    BASE_FARE = 40.0
    RATE_PER_KM_ENA_VROOM = 10.0
    RATE_PER_KM_ENACAR_4_SEATER = 40.0
    RATE_PER_KM_ENACAR_6_SEATER = 60.0

    def __init__(self, file="bookings.json", log_file="booking_log.txt"):
        self.file = file
        self.log_file = log_file
        self.bookings = []

    def calculate_cost(self, vehicle_type, distance):
        cost = self.BASE_FARE
        if vehicle_type == "Enavroom-vroom":
            cost += distance * self.RATE_PER_KM_ENA_VROOM
        elif vehicle_type == "Car (4-seater)":
            cost += distance * self.RATE_PER_KM_ENACAR_4_SEATER
        elif vehicle_type == "Car (6-seater)":
            cost += distance * self.RATE_PER_KM_ENACAR_6_SEATER
        return round(cost, 2)

    def book(self, vehicle_type, start, end, payment_method):
        distance = get_distance(start, end)
        if distance == 0.0 and start != end:
            print(f"ERROR: Route from {start} to {end} not defined.")
            return None
        cost = self.calculate_cost(vehicle_type, distance)
        booking = Booking(vehicle_type, start, end, distance, cost, payment_method)
        self.bookings.append(booking)
        self.save()
        self.log_to_txt(booking, action="Booked")
        return booking

    def cancel(self, booking_id):
        for booking in self.bookings:
            if booking.id == booking_id:
                booking.status = "cancelled"
                self.save()
                self.log_to_txt(booking, action="Cancelled")
                return True
        return False

    def save(self):
        with open(self.file, "w") as f:
            json.dump([b.to_dict() for b in self.bookings], f, indent=2)

    def log_to_txt(self, booking, action="Booked"):
        log_entry = (
            f"{action.upper()} | ID: {booking.id} | "
            f"{booking.vehicle_type} | {booking.start} → {booking.end} | "
            f"{booking.distance:.1f} km | ₱{booking.cost:.2f} | "
            f"{booking.payment_method} | STATUS: {booking.status}\n"
        )
        with open(self.log_file, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

    def load(self):
        self.bookings = []
        try:
            if os.path.exists(self.file):
                with open(self.file, "r") as f:
                    data = json.load(f)
                    for item in data:
                        self.bookings.append(Booking.from_dict(item))
            else:
                print(f"DEBUG: {self.file} not found. Starting with empty bookings.")
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not decode JSON from {self.file}: {e}. Starting with empty bookings.")
        # Optionally load from log file as a fallback (not recommended for primary data)
        # This would require parsing log entries back into Booking objects, which is complex
        # For now, we'll stick to bookings.json as the source of truth

    def clear_all(self):
        """Clears all bookings and the booking log file."""
        self.bookings = []
        self.save()
        if os.path.exists(self.log_file):
            open(self.log_file, "w").close()
            print(f"DEBUG: {self.log_file} has been cleared.")