import time

def control_gate(is_registered: bool):
    """
    Simulates the physical gate controller behavior.
    
    Args:
        is_registered (bool): True if the vehicle is registered, False otherwise.
    """
    if is_registered:
        print("🚪 Gate OPENING")
        # Simulate physical movement delay of 5 seconds
        time.sleep(5)
        print("Gate CLOSED")
    else:
        print("🚫 ACCESS DENIED")
