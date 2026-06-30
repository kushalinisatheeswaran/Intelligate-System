import logging
from typing import Dict, Any

logger = logging.getLogger("anpr.decision")

class DecisionEngine:
    """
    Evaluates detected plates against database records and rules,
    and decides whether to grant access.
    """
    def __init__(self, get_db_session_func=None):
        # We inject a function that returns a db session context manager
        self.get_db_session = get_db_session_func

    async def evaluate(self, plate_number: str) -> Dict[str, Any]:
        """
        Checks the plate against the DB (simulated or real).
        Returns a dict with access decision.
        """
        if not self.get_db_session:
            # Fallback for testing without DB
            dummy_db = {
                "ABC1234": {"owner": "Karthi", "status": "allowed"},
                "TEST123": {"owner": "Admin", "status": "allowed"}
            }
            record = dummy_db.get(plate_number)
        else:
            # Real DB query logic here using SQLAlchemy async
            # Example:
            # async with self.get_db_session() as session:
            #     vehicle = await session.execute(select(Vehicle).where(Vehicle.plate_number == plate_number))
            #     record = vehicle.scalar_one_or_none()
            pass
            record = None  # Placeholder until DB is fully wired

        if record:
            logger.info(f"Access GRANTED for {plate_number}")
            return {
                "granted": True,
                "reason": "Registered vehicle",
                "details": record
            }
        else:
            logger.info(f"Access DENIED for {plate_number}")
            return {
                "granted": False,
                "reason": "Unregistered vehicle",
                "details": None
            }
