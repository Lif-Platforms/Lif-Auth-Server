from app.database import connections
from typing import Literal, Optional, Tuple, cast

def submit_report(user: str, service: str, reason: str, content: str) -> None:
    """
    Submit a report.

    Parameters:
        user (str): User who submitted the report.
        service (str): Service the report was submitted from.
        reason (str): Reason for the report.
        content (str): Content being reported.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Add report to database
    cursor.execute(
        """INSERT INTO reports (user, service, reason, content, resolved) 
        VALUES (%s, %s, %s, %s, %s)""", 
        (user, service, reason, content, False,)
    )
    conn.commit()
    conn.close()

def get_reports(
    search_filter: Optional[Literal["unresolved", "resolved"]] = None,
    limit: int = 100
) -> list:
    """
    Get a list of reports.

    Parameters:
        search_filter (Literal["unresolved", "resolved"]): Filter between resolved and unresolved reports.
        limit (int): Specify a limit to how many reports are returned.
    
    Returns:
        out (list): List of reports.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    filter = True if search_filter == "resolved" else False
    
    # Check filter and execute correct SQL query
    if search_filter:
        cursor.execute("SELECT * FROM reports WHERE resolved = %s LIMIT %s", (filter, limit))
    else:
        cursor.execute("SELECT * FROM reports LIMIT %s", (limit,))

    reportsRAW = cursor.fetchall()
    reports = cast(list[Tuple], reportsRAW) if reportsRAW else []
    conn.close()

    return reports

def get_report(report_id: int) -> Optional[Tuple]:
    """
    Get a report by id.

    Parameters:
        report_id (int): The id of the report.

    Returns:
        out (Optional[Tuple]): The report or None if not found.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
    report = cast(Optional[Tuple], cursor.fetchone())
    conn.close()

    return report

def resolve_report(report_id: int) -> None:
    """
    Mark a report as resolved.

    Parameters:
        report_id (int): Id of the report.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE reports SET resolved = %s WHERE id = %s", (True, report_id))
    conn.commit()
    conn.close()
