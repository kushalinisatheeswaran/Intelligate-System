import re

# Plate format: 2-3 letters, dash, 4 digits e.g. ABC-1234
PLATE_PATTERN   = re.compile(r"^[A-Z0-9\s-]{3,15}$")

# Student number format: numeric-only unique ID e.g. 113113
STUDENT_PATTERN = re.compile(r"^\d+$")


def validate_identifier(id_type: str, value: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    Adjust patterns to match your university's actual formats.
    """
    if id_type == "plate":
        if not PLATE_PATTERN.match(value):
            return False, f"Invalid plate format: {value}. Expected e.g. ABC-1234"
        return True, ""

    if id_type == "barcode":
        if not STUDENT_PATTERN.match(value):
            return False, f"Invalid student ID format: {value}. Expected numeric ID e.g. 113113"
        return True, ""

    return False, f"Unknown type: {id_type}. Use 'plate' or 'barcode'"