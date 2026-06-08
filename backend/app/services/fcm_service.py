import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Firebase app initialised once at startup
_firebase_app = None


def init_firebase():
    """
    Initialise Firebase Admin SDK.
    Called once from create_app().
    """
    global _firebase_app
    if _firebase_app:
        return  # already initialised

    enabled = os.getenv("FIREBASE_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("[FCM] Firebase disabled — stub mode active")
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        service_account_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT_PATH",
            "firebase_service_account.json"
        )

        if not os.path.exists(service_account_path):
            logger.error(
                f"[FCM] Service account file not found: {service_account_path}"
            )
            return

        cred = credentials.Certificate(service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("[FCM] Firebase Admin SDK initialised successfully")

    except Exception as e:
        logger.error(f"[FCM] Firebase init failed: {e}")


def _get_active_tokens(user_ids: list = None) -> list:
    """
    Fetch active FCM tokens from DB.
    If user_ids provided, returns tokens for those users only.
    Otherwise returns ALL active guard/admin tokens.
    """
    try:
        from app.models.device_token import DeviceToken
        from app.models.administrator import Administrator

        query = DeviceToken.query.filter_by(is_active=True)

        if user_ids:
            query = query.filter(DeviceToken.user_id.in_(user_ids))
        else:
            # Send to all admins and guards by default
            admin_user_ids = [
                a.user_id for a in Administrator.query.all()
            ]
            if admin_user_ids:
                query = query.filter(
                    DeviceToken.user_id.in_(admin_user_ids)
                )

        tokens = [dt.fcm_token for dt in query.all()]
        return tokens

    except Exception as e:
        logger.error(f"[FCM] Failed to fetch tokens: {e}")
        return []


def _send_fcm_push(tokens: list, title: str, body: str, data: dict = None) -> dict:
    """
    Core FCM send function.
    Sends to multiple device tokens using MulticastMessage.
    """
    enabled = os.getenv("FIREBASE_ENABLED", "false").lower() == "true"

    if not enabled:
        logger.info(f"[FCM STUB] Push: '{title}' → {len(tokens)} device(s)")
        return {"sent": False, "reason": "firebase_disabled"}

    if not tokens:
        logger.warning("[FCM] No active device tokens found")
        return {"sent": False, "reason": "no_tokens"}

    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            tokens       = tokens,
            notification = messaging.Notification(
                title = title,
                body  = body,
            ),
            data     = {k: str(v) for k, v in (data or {}).items()},
            android  = messaging.AndroidConfig(
                priority             = "high",
                notification         = messaging.AndroidNotification(
                    sound            = "default",
                    priority         = "max",
                    visibility       = "public",
                    channel_id       = "intelligate_alerts"
                )
            ),
            apns = messaging.APNSConfig(
                payload = messaging.APNSPayload(
                    aps = messaging.Aps(
                        sound          = "default",
                        badge          = 1,
                        content_available = True
                    )
                )
            )
        )

        response = messaging.send_each_for_multicast(message)
        logger.info(
            f"[FCM] Sent to {response.success_count}/{len(tokens)} devices"
        )

        # Deactivate tokens that are no longer valid
        if response.failure_count > 0:
            _handle_failed_tokens(tokens, response.responses)

        return {
            "sent":          True,
            "success_count": response.success_count,
            "failure_count": response.failure_count
        }

    except Exception as e:
        logger.error(f"[FCM] Send failed: {e}")
        return {"sent": False, "error": str(e)}


def _handle_failed_tokens(tokens: list, responses: list):
    """
    Deactivates invalid or expired FCM tokens in DB.
    Called automatically after every send.
    """
    try:
        from app.database import db
        from app.models.device_token import DeviceToken

        for token, response in zip(tokens, responses):
            if not response.success:
                error_code = response.exception.code if response.exception else "unknown"
                # These codes mean the token is permanently invalid
                if error_code in (
                    "registration-token-not-registered",
                    "invalid-registration-token"
                ):
                    DeviceToken.query.filter_by(
                        fcm_token=token
                    ).update({"is_active": False})
                    logger.info(f"[FCM] Deactivated invalid token: {token[:20]}...")

        db.session.commit()

    except Exception as e:
        logger.error(f"[FCM] Failed to handle token cleanup: {e}")


def send_unknown_vehicle_alert(
    identifier: str,
    id_type: str,
    pending_id: int,
    timestamp: str,
    image_url: str = None
) -> dict:
    """
    Main alert function — called by /api/verify on denied entry.
    Sends FCM push to ALL active guard/admin devices.
    """
    type_label = "Plate" if id_type == "plate" else "Student ID"
    title      = "🚨 Unknown Vehicle Detected"
    body       = f"{type_label}: {identifier} — Main Gate"

    data = {
        "type":        "unknown_vehicle",
        "identifier":  identifier,
        "id_type":     id_type,
        "pending_id":  str(pending_id),
        "timestamp":   timestamp,
        "screen":      "PendingApprovals"  # React Native navigates here on tap
    }

    tokens = _get_active_tokens()
    result = _send_fcm_push(tokens, title, body, data)

    # Save to notifications table
    _save_notification(
        identifier = identifier,
        id_type    = id_type,
        title      = title,
        body       = body,
        status     = "sent" if result.get("sent") else "failed",
        error      = result.get("error")
    )

    return result


def send_gate_alert(action: str, triggered_by: str = "system") -> dict:
    """
    Sends FCM push when gate is manually opened/closed by admin.
    """
    title = "🚪 Gate Status Update"
    body  = f"Gate {action.upper()} — triggered by {triggered_by}"
    data  = {
        "type":         "gate_status",
        "status":       action,
        "triggered_by": triggered_by,
        "screen":       "GateStatus"
    }
    tokens = _get_active_tokens()
    return _send_fcm_push(tokens, title, body, data)


def _save_notification(
    identifier: str,
    id_type: str,
    title: str,
    body: str,
    status: str,
    error: str = None
):
    """Saves notification record to PostgreSQL."""
    try:
        from app.database import db
        from app.models.notification import Notification

        notif = Notification(
            identifier = identifier,
            id_type    = id_type,
            channel    = "fcm",
            message    = f"{title}\n{body}",
            status     = status,
            error      = error,
            sent_at    = datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

    except Exception as e:
        logger.error(f"[FCM] Failed to save notification: {e}")