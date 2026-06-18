import random
from datetime import datetime
import httpx
from ..config import config_manager

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
    {"no": "12926", "name": "Paschim Express", "src": "Delhi", "dst": "Mumbai", "dep": "16:30", "arr": "14:55", "duration": "22h 25m", "classes": ["1A", "2A", "3A", "SL"]},
    {"no": "12012", "name": "Kalka Shatabdi Express", "src": "Chandigarh", "dst": "Delhi", "dep": "06:15", "arr": "09:50", "duration": "3h 35m", "classes": ["CC", "EC"]}
]

STATION_CODE_MAP = {
    "delhi": "NDLS",
    "new delhi": "NDLS",
    "chandigarh": "CDG",
    "mumbai": "MMCT",
    "mumbai central": "MMCT",
    "bhopal": "BPL",
    "varanasi": "BSB",
    "lucknow": "LKO",
    "patna": "PNBE",
    "bangalore": "SBC",
    "chennai": "MAS",
    "pune": "PUNE",
    "ernakulam": "ERS"
}

def resolve_station_code(station_name: str) -> str:
    """
    Resolves station name to IRCTC station code. Uses local map first, with a RapidAPI search fallback.
    """
    if not station_name:
        return "NDLS"
    name_clean = station_name.strip().lower()
    if name_clean in STATION_CODE_MAP:
        return STATION_CODE_MAP[name_clean]
    
    settings = config_manager.settings
    if settings.use_real_irctc_api and settings.rapidapi_key:
        try:
            headers = {
                "x-rapidapi-key": settings.rapidapi_key,
                "x-rapidapi-host": settings.rapidapi_host or "irctc1.p.rapidapi.com"
            }
            url = f"https://{headers['x-rapidapi-host']}/api/v1/searchStation"
            r = httpx.get(url, headers=headers, params={"query": station_name}, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                stations = data.get("data", [])
                if stations:
                    return stations[0].get("code", station_name[:3].upper())
        except Exception as e:
            print(f"Error resolving station code from RapidAPI: {e}")
            
    return station_name[:3].upper()

def find_trains(src: str, dst: str, date: str) -> dict:
    """
    Search trains between src and dst. Connects to RapidAPI if configured.
    """
    settings = config_manager.settings
    if settings.use_real_irctc_api and settings.rapidapi_key:
        try:
            src_code = resolve_station_code(src)
            dst_code = resolve_station_code(dst)
            headers = {
                "x-rapidapi-key": settings.rapidapi_key,
                "x-rapidapi-host": settings.rapidapi_host or "irctc1.p.rapidapi.com"
            }
            # Check endpoint style (some versions of the API use trainBetweenStations, others trainBetweenStationsV3, etc.)
            # We will use /api/v3/trainBetweenStations as it's the standard for irctc1
            url = f"https://{headers['x-rapidapi-host']}/api/v3/trainBetweenStations"
            params = {"fromStationCode": src_code, "toStationCode": dst_code}
            r = httpx.get(url, headers=headers, params=params, timeout=8.0)
            if r.status_code == 200:
                data = r.json()
                trains = data.get("data", [])
                mapped_trains = []
                for t in trains:
                    mapped_trains.append({
                        "no": t.get("train_number") or t.get("train_no") or "12002",
                        "name": t.get("train_name") or "Express",
                        "src": t.get("from_station_name") or src,
                        "dst": t.get("to_station_name") or dst,
                        "dep": t.get("dep_time") or "06:00",
                        "arr": t.get("arr_time") or "12:00",
                        "duration": t.get("duration") or "6h 00m",
                        "classes": t.get("classes") or ["CC", "EC", "3A", "SL"]
                    })
                if mapped_trains:
                    return {
                        "success": True,
                        "trains": mapped_trains,
                        "src": src,
                        "dst": dst,
                        "date": date
                    }
        except Exception as e:
            print(f"Error calling real train search API: {e}")
            
    # Mock fallback
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

def check_seat_availability(train_no: str, date: str, class_code: str, quota: str = "GN", src: str = None, dst: str = None) -> dict:
    """
    Check seat availability for a given train, class, and quota. Connects to RapidAPI if configured.
    """
    settings = config_manager.settings
    if settings.use_real_irctc_api and settings.rapidapi_key:
        try:
            src_code = resolve_station_code(src) if src else "NDLS"
            dst_code = resolve_station_code(dst) if dst else "CDG"
            headers = {
                "x-rapidapi-key": settings.rapidapi_key,
                "x-rapidapi-host": settings.rapidapi_host or "irctc1.p.rapidapi.com"
            }
            url = f"https://{headers['x-rapidapi-host']}/api/v1/checkSeatAvailability"
            params = {
                "classType": class_code,
                "fromStationCode": src_code,
                "quota": quota,
                "toStationCode": dst_code,
                "trainNo": train_no,
                "date": date
            }
            r = httpx.get(url, headers=headers, params=params, timeout=8.0)
            if r.status_code == 200:
                res_data = r.json()
                data_list = res_data.get("data", [])
                if isinstance(data_list, list) and len(data_list) > 0:
                    avail = data_list[0]
                    # Parse status and price
                    status_str = avail.get("current_status") or avail.get("status") or "AVAILABLE"
                    # Ex: "AVAILABLE-0012" -> seats_available = 12
                    seats = 0
                    if "AVAILABLE" in status_str:
                        parts = status_str.split("-")
                        if len(parts) > 1 and parts[1].isdigit():
                            seats = int(parts[1])
                        else:
                            seats = 15 # fallback
                    elif "WL" in status_str:
                        seats = 0
                    
                    price_str = avail.get("ticket_price") or avail.get("price") or "850"
                    price = 850.0
                    try:
                        price = float(price_str)
                    except:
                        pass
                        
                    return {
                        "success": True,
                        "train_no": train_no,
                        "train_name": res_data.get("train_name") or "Express Train",
                        "date": date,
                        "class_code": class_code,
                        "quota": quota,
                        "seats_available": seats,
                        "status": status_str,
                        "price": price
                    }
        except Exception as e:
            print(f"Error checking live seat availability: {e}")

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

def book_ticket(train_no: str, date: str, class_code: str, passengers: list, payment_confirmed: bool = False, src: str = "Delhi", dst: str = "Mumbai") -> dict:
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
    availability = check_seat_availability(train_no, date, class_code, src=src, dst=dst)
    price_per_passenger = availability["price"]
    total_price = price_per_passenger * len(passengers)
    
    booking = {
        "pnr": pnr,
        "train_no": train_no,
        "train_name": train_name,
        "src": src,
        "dst": dst,
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
    Fetch PNR status. Connects to RapidAPI if configured.
    """
    settings = config_manager.settings
    if settings.use_real_irctc_api and settings.rapidapi_key:
        try:
            headers = {
                "x-rapidapi-key": settings.rapidapi_key,
                "x-rapidapi-host": settings.rapidapi_host or "irctc1.p.rapidapi.com"
            }
            url = f"https://{headers['x-rapidapi-host']}/api/v3/getPNRStatus"
            params = {"pnrNumber": pnr}
            r = httpx.get(url, headers=headers, params=params, timeout=8.0)
            if r.status_code == 200:
                res_data = r.json()
                pnr_data = res_data.get("data", {})
                if pnr_data:
                    booking = {
                        "pnr": pnr_data.get("pnr") or pnr,
                        "train_no": pnr_data.get("trainNo") or pnr_data.get("train_number") or "12002",
                        "train_name": pnr_data.get("trainName") or pnr_data.get("train_name") or "Express Train",
                        "src": pnr_data.get("source") or pnr_data.get("from_station_name") or "Delhi",
                        "dst": pnr_data.get("destination") or pnr_data.get("to_station_name") or "Mumbai",
                        "date": pnr_data.get("date") or pnr_data.get("journey_date") or "2026-06-25",
                        "class_code": pnr_data.get("class") or pnr_data.get("class_code") or "3A",
                        "passengers": [
                            {
                                "name": p.get("name") or p.get("passenger_name") or f"Passenger {i+1}",
                                "age": p.get("age") or 30,
                                "gender": p.get("gender") or "M"
                            }
                            for i, p in enumerate(pnr_data.get("passengers", []))
                        ],
                        "status": pnr_data.get("status") or pnr_data.get("booking_status") or "CNF",
                        "coach": pnr_data.get("coach") or "B1",
                        "berth": pnr_data.get("berth") or pnr_data.get("seat") or "14",
                        "price": float(pnr_data.get("price") or 1450.0)
                    }
                    BOOKINGS_DB[pnr] = booking
                    return {
                        "success": True,
                        "booking": booking
                    }
        except Exception as e:
            print(f"Error calling real getPNRStatus API: {e}")

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
