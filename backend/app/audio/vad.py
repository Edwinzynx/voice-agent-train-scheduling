import math
import struct

def is_silent(audio_data: bytes, threshold: float = 30.0) -> bool:
    """
    Checks if a block of 16-bit PCM audio is silent based on RMS energy threshold.
    """
    if not audio_data:
        return True
        
    try:
        # Calculate RMS energy of the audio chunk
        count = len(audio_data) // 2
        format_str = f"<{count}h"
        shorts = struct.unpack(format_str, audio_data[:count*2])
        
        sum_squares = sum(s * s for s in shorts)
        rms = math.sqrt(sum_squares / count) if count > 0 else 0
        
        return rms < threshold
    except Exception:
        # Default fallback
        return False
