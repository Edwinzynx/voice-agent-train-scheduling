import random
from datetime import datetime
import httpx

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

STATION_CODE_MAP = {
    "delhi": "NDLS",
    "new delhi": "NDLS",
    "old delhi": "DLI",
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
    "ernakulam": "ERS",
    "patiala": "PTA",
    "kolkata": "HWH",
    "howrah": "HWH",
    "sealdah": "SDAH",
    "jaipur": "JP",
    "amritsar": "ASR",
    "agra": "AGC",
    "hyderabad": "HYB",
    "secunderabad": "SC",
    "ahmedabad": "ADI",
    "ludhiana": "LDH",
    "jalandhar": "JUC",
    "ambala": "UMB",
    "delhi cantt": "DEC",
    "hazrat nizamuddin": "NZM",
    "anand vihar": "ANVT",
    "guwahati": "GHY",
    "kanpur": "CNB",
    "nagpur": "NGP",
    "coimbatore": "CBE",
    "madurai": "MDU"
}

def resolve_station_code(station_name: str) -> str:
    """
    Resolves station name to IRCTC station code using static map fallback.
    """
    if not station_name:
        return "NDLS"
        
    name_clean = station_name.strip().lower()
    if name_clean in STATION_CODE_MAP:
        return STATION_CODE_MAP[name_clean]
        
    return station_name[:3].upper()

def format_date_for_api(date_str: str) -> str:
    """
    Converts date string (e.g., '2026-06-20' or '20-06-2026') to ConfirmTkt API format 'DD-MM-YYYY'.
    If parsing fails or date is empty, defaults to today's date.
    """
    if not date_str:
        return datetime.now().strftime("%d-%m-%Y")
    
    # Try DD-MM-YYYY, YYYY-MM-DD, and slash variants
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            continue
            
    # Fallback to today if not parseable
    return datetime.now().strftime("%d-%m-%Y")

def find_trains(src: str, dst: str, date: str) -> dict:
    """
    Search trains between src and dst using ConfirmTkt's API.
    """
    try:
        src_code = resolve_station_code(src)
        dst_code = resolve_station_code(dst)
        api_date = format_date_for_api(date)
        
        url = "https://cttrainsapi.confirmtkt.com/api/v1/trains/search"
        params = {
            "sourceStationCode": src_code,
            "destinationStationCode": dst_code,
            "dateOfJourney": api_date
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.confirmtkt.com",
            "Referer": "https://www.confirmtkt.com/"
        }
        
        r = httpx.get(url, params=params, headers=headers, timeout=10.0)
        
        if r.status_code == 200:
            data = r.json()
            actual_data = data.get("data", {})
            trains = actual_data.get("trainList", []) if isinstance(actual_data, dict) else []
            
            mapped_trains = []
            for t in trains:
                duration_mins = t.get("duration", 360)
                try:
                    mins = int(duration_mins)
                    hours = mins // 60
                    remaining_mins = mins % 60
                    duration_str = f"{hours}h {remaining_mins:02d}m"
                except:
                    duration_str = "6h 00m"
                    
                mapped_trains.append({
                    "no": t.get("trainNumber") or t.get("trainNo") or "12002",
                    "name": t.get("trainName") or "Express",
                    "src": t.get("fromStnName") or src,
                    "dst": t.get("toStnName") or dst,
                    "dep": t.get("departureTime") or "06:00",
                    "arr": t.get("arrivalTime") or "12:00",
                    "duration": duration_str,
                    "classes": t.get("avlClasses") or ["CC", "EC", "3A", "SL"],
                    "raw_train_data": t
                })
            
            if mapped_trains:
                return {
                    "success": True,
                    "trains": mapped_trains,
                    "src": src,
                    "dst": dst,
                    "date": date
                }
            else:
                return {
                    "success": False,
                    "error": f"No trains found between {src} ({src_code}) and {dst} ({dst_code}) from the ConfirmTkt API."
                }
        else:
            return {
                "success": False,
                "error": f"Train API Error (Status {r.status_code}): {r.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception calling Train API: {str(e)}"
        }

def check_seat_availability(train_no: str, date: str, class_code: str, quota: str = "GN", src: str = None, dst: str = None, train_data: dict = None) -> dict:
    """
    Check seat availability for a given train, class, and quota using ConfirmTkt's API.
    If train_data is provided, checks availability directly from the in-memory train search dictionary.
    """
    try:
        if train_data:
            target_train = train_data
        else:
            src_code = resolve_station_code(src) if src else "NDLS"
            dst_code = resolve_station_code(dst) if dst else "CDG"
            api_date = format_date_for_api(date)
            
            url = "https://cttrainsapi.confirmtkt.com/api/v1/trains/search"
            params = {
                "sourceStationCode": src_code,
                "destinationStationCode": dst_code,
                "dateOfJourney": api_date
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.confirmtkt.com",
                "Referer": "https://www.confirmtkt.com/"
            }
            
            r = httpx.get(url, params=params, headers=headers, timeout=10.0)
            
            if r.status_code == 200:
                data = r.json()
                actual_data = data.get("data", {})
                train_list = actual_data.get("trainList", []) if isinstance(actual_data, dict) else []
                
                # Find train matching train_no
                target_train = None
                train_no_str = str(train_no).strip()
                for t in train_list:
                    t_no = str(t.get("trainNumber") or t.get("trainNo")).strip()
                    if t_no == train_no_str:
                        target_train = t
                        break
                        
                if not target_train:
                    return {
                        "success": False,
                        "error": f"Train {train_no} not found in search results between {src_code} and {dst_code} on {api_date}."
                    }
            else:
                return {
                    "success": False,
                    "error": f"Live Seat Availability API Error (Status {r.status_code}): {r.text}"
                }
                
        # Quota logic
        cache_name = "availabilityCacheTatkal" if quota in ("TQ", "TATKAL") else "availabilityCache"
        avail_cache = target_train.get(cache_name, {})
        
        avail_info = avail_cache.get(class_code)
        if not avail_info:
            # Try fallback matching case-insensitive
            for k, v in avail_cache.items():
                if k.upper() == class_code.upper():
                    avail_info = v
                    break
                    
        if not avail_info:
            return {
                "success": False,
                "error": f"Class {class_code} details not available for train {train_no} under quota {quota}."
            }
            
        status_str = avail_info.get("availabilityDisplayName") or avail_info.get("availability") or "AVAILABLE"
        price_str = avail_info.get("fare") or "850"
        
        seats = 0
        if "AVAILABLE" in status_str.upper():
            parts = status_str.replace("-", " ").split()
            digits = [int(s) for s in parts if s.isdigit()]
            if digits:
                seats = digits[0]
            else:
                seats = 15
        elif "WL" in status_str.upper() or "RAC" in status_str.upper():
            seats = 0
            
        price = 850.0
        try:
            price = float(price_str)
        except:
            pass
            
        return {
            "success": True,
            "train_no": train_no,
            "train_name": target_train.get("trainName") or "Express Train",
            "date": date,
            "class_code": class_code,
            "quota": quota,
            "seats_available": seats,
            "status": status_str,
            "price": price
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception checking live seat availability: {str(e)}"
        }

def book_ticket(train_no: str, date: str, class_code: str, passengers: list, payment_confirmed: bool = False, src: str = "Delhi", dst: str = "Mumbai") -> dict:
    """
    Book a ticket and return PNR. Real-time train info is fetched from the ConfirmTkt API.
    """
    if not payment_confirmed:
        return {
            "success": False,
            "error": "Payment confirmation required."
        }
        
    availability = check_seat_availability(train_no, date, class_code, src=src, dst=dst)
    if not availability.get("success"):
        return {
            "success": False,
            "error": f"Could not verify live train details: {availability.get('error', 'Unknown live API error')}"
        }
        
    # Generate random 10-digit PNR for booking simulation
    pnr = "".join([str(random.randint(0, 9)) for _ in range(10)])
    train_name = availability.get("train_name") or "Express Train"
    price_per_passenger = availability.get("price") or 850.0
    status = availability.get("status") or "CNF"
    
    total_price = price_per_passenger * len(passengers)
    
    booking = {
        "pnr": pnr,
        "train_no": train_no,
        "train_name": train_name,
        "src": src.title(),
        "dst": dst.title(),
        "date": date,
        "class_code": class_code,
        "passengers": passengers,
        "status": status,
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
    return {
        "success": True,
        "train_no": train_no,
        "train_name": "Express Train",
        "current_station": "Departed previous station",
        "delay_minutes": 0,
        "status_message": "Running on time",
        "last_updated": datetime.now().strftime("%H:%M:%S")
    }
