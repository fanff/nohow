from datetime import datetime, timezone


def format_timestamp(timestamp: float) -> str:
    """Convert a Unix timestamp into a string in human-readable format.

    Args:
        timestamp: The Unix timestamp.

    Returns:
        The string timestamp in the format "%Y-%m-%d %H:%M:%S".
    """
    utc_dt = datetime.fromtimestamp(timestamp, timezone.utc)
    local_dt = utc_dt.astimezone()
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")
