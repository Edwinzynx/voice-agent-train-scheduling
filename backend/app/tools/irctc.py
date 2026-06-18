import random
from datetime import datetime

# In-memory database of bookings to allow stateful search/cancel during a session.
# Keys are PNRs (10-digit strings).
BOOKINGS_DB = {
    "4829384729": {
        "pnr": "4829384729",
        "train_no": "12626",
        "train_name": "Kerala Express",
        "src": "New Delhi",
        "dst": "Ernakulam",
        "date": "2026-06-25",
        "class_code": "3A",
        "passengers": [{"name": "John Doe", "age": 32, "gender": "M"}],
        "status": "CNF",
        "coach": "B1",
        "berth": "14",
        "price": 1450.0
    }
}

# Standard mock trains
MOCK_TRAINS = [
    {"no": "12626", "name": "Kerala Express", "src": "Delhi", "dst": "Mumbai", "dep": "20:10", "arr": "14:20", "duration": "18h 10m", "classes": ["1A", "2A", "3A", "SL"]},
    {"no": "12952", "name": "Mumbai Rajdhani", "src": "Delhi", "dst": "Mumbai", "dep": "16:55", "arr": "08:35", "duration": "15h 40m", "classes": ["1A", "2A", "3A"]},
    {"no": "12002", "name": "Shatabdi Express", "src": "Delhi", "dst": "Bhopal", "dep": "06:00", "arr": "14:40", "duration": "8h 40m", "classes": ["CC", "EC"]},
    {"no": "22436", "name": "Vande Bharat Express", "src": "Delhi", "dst": "Varanasi", "dep": "06:00", "arr": "14:00", "duration": "8h 00m", "classes": ["CC", "EC"]},
    {"no": "12926", "name": "Paschim Express", "src": "Delhi", "dst": "Mumbai", "dep": "16:30", "arr": "14:55", "duration": "22h 25m", "classes": ["1A", "2A", "3A", "SL"]}
]

def find_trains(src: str, dst: str, date: str) -> dict:
    """
    Search trains between src and dst.
    """
    src_clean = src.strip().lower()
    dst_clean = dst.strip().lower()
    
    # Simple station mapping to make mock responses feel real
    matching = []
    for train in MOCK_TRAINS:
        t_src = train["src"].lower()
        t_dst = train["dst"].lower()
        
        # Approximate matching
        if (src_clean in t_src or t_src in src_clean) and (dst_clean in t_dst or t_dst in dst_clean):
            matching.append(train)
            
    # If no direct match, return a couple of random ones renamed to look matching
    if not matching:
        for i, train in enumerate(MOCK_TRAINS[:2]):
            matching.append({
                "no": f"{10000 + random.randint(1000, 9999)}",
                "name": f"{src.title()} - {dst.title()} Express",
                "src": src.title(),
                "dst": dst.title(),
                "dep": train["dep"],
                "arr": train["arr"],
                "duration": train["duration"],
                "classes": train["classes"]
            })
            
    return {
        "success": True,
        "trains": matching,
        "src": src,
        "dst": dst,
        "date": date
    }

def check_seat_availability(train_no: str, date: str, class_code: str, quota: str = "GN") -> dict:
    """
    Check seat availability for a given train, class, and quota.
    """
    # Find train or assume default
    train_name = "Express Train"
    for train in MOCK_TRAINS:
        if train["no"] == train_no:
            train_name = train["name"]
            break
            
    # Deterministic but mock-random seats based on train_no and date
    seed = sum(ord(c) for c in (train_no + date + class_code))
    random.seed(seed)
    
    seats = random.randint(0, 45)
    wl_seats = random.randint(1, 10)
    
    price = 350.0
    if class_code == "1A":
        price = 2800.0
        seats = random.randint(0, 5)
    elif class_code == "2A":
        price = 1650.0
        seats = random.randint(0, 12)
    elif class_code == "3A":
        price = 1180.0
        seats = random.randint(2, 25)
    elif class_code == "CC":
        price = 850.0
        seats = random.randint(1, 30)
    elif class_code == "EC":
        price = 1800.0
        seats = random.randint(0, 8)
    elif class_code == "SL":
        price = 450.0
        seats = random.randint(0, 80)
        
    status = "AVAILABLE" if seats > 0 else f"WL{wl_seats}"
    
    return {
        "success": True,
        "train_no": train_no,
        "train_name": train_name,
        "date": date,
        "class_code": class_code,
        "quota": quota,
        "seats_available": seats,
        "status": status,
        "price": price
    }

def book_ticket(train_no: str, date: str, class_code: str, passengers: list, payment_confirmed: bool = False) -> dict:
    """
    Book a ticket and return PNR.
    """
    if not payment_confirmed:
        return {
            "success": False,
            "error": "Payment confirmation required."
        }
        
    # Generate random 10-digit PNR
    pnr = "".join([str(random.randint(0, 9)) for _ in range(10)])
    
    train_name = "Express Train"
    for train in MOCK_TRAINS:
        if train["no"] == train_no:
            train_name = train["name"]
            break
            
    # Calculate price
    availability = check_seat_availability(train_no, date, class_code)
    price_per_passenger = availability["price"]
    total_price = price_per_passenger * len(passengers)
    
    booking = {
        "pnr": pnr,
        "train_no": train_no,
        "train_name": train_name,
        "src": availability.get("src", "Delhi"),
        "dst": availability.get("dst", "Mumbai"),
        "date": date,
        "class_code": class_code,
        "passengers": passengers,
        "status": "CNF" if availability["seats_available"] > 0 else "WL",
        "coach": f"S{random.randint(1, 6)}" if class_code == "SL" else f"B{random.randint(1, 3)}" if class_code == "3A" else f"A{random.randint(1, 2)}",
        "berth": str(random.randint(1, 64)),
        "price": total_price
    }
    
    BOOKINGS_DB[pnr] = booking
    
    return {
        "success": True,
        "booking": booking
    }

def cancel_ticket(pnr: str) -> dict:
    """
    Cancel a ticket by PNR.
    """
    if pnr in BOOKINGS_DB:
        booking = BOOKINGS_DB[pnr]
        if booking["status"] == "CAN":
            return {
                "success": False,
                "error": "Ticket is already cancelled."
            }
        booking["status"] = "CAN"
        refund_amount = booking["price"] * 0.8  # 20% cancellation charges
        return {
            "success": True,
            "pnr": pnr,
            "message": "Ticket successfully cancelled.",
            "refund_amount": refund_amount,
            "refund_status": "PROCESSED"
        }
    return {
        "success": False,
        "error": f"PNR {pnr} not found."
    }

def get_pnr_status(pnr: str) -> dict:
    """
    Fetch PNR status.
    """
    if pnr in BOOKINGS_DB:
        return {
            "success": True,
            "booking": BOOKINGS_DB[pnr]
        }
    return {
        "success": False,
        "error": f"PNR {pnr} not found."
    }

def get_live_train_info(train_no: str) -> dict:
    """
    Get live running status for a train.
    """
    train_name = "Express Train"
    for train in MOCK_TRAINS:
        if train["no"] == train_no:
            train_name = train["name"]
            break
            
    # Mock current station & delay
    stations = ["Delhi Cantt", "Gurgaon", "Jaipur", "Ajmer", "Ahmedabad", "Vadodara", "Mumbai Central"]
    current_station = random.choice(stations)
    delay_mins = random.choice([0, 5, 15, 30, 45, 60])
    
    status_msg = "Running on time" if delay_mins == 0 else f"Running late by {delay_mins} minutes"
    
    return {
        "success": True,
        "train_no": train_no,
        "train_name": train_name,
        "current_station": current_station,
        "delay_minutes": delay_mins,
        "status_message": status_msg,
        "last_updated": datetime.now().strftime("%H:%M:%S")
    }
