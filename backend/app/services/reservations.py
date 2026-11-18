from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

from sqlalchemy import text

from app.core.database_pool import db_pool


async def _get_session():
    await db_pool.initialize()
    if not db_pool.session_factory:
        raise RuntimeError("Database pool not available")
    return db_pool.get_session()


async def get_tenant_properties(tenant_id: str) -> List[Dict[str, str]]:
    """
    Lists the properties owned by a tenant.
    """
    query = text("""
        SELECT id, name
        FROM properties
        WHERE tenant_id = :tenant_id
        ORDER BY id
    """)

    async with await _get_session() as session:
        result = await session.execute(query, {"tenant_id": tenant_id})
        return [{"id": row.id, "name": row.name} for row in result]


async def calculate_monthly_revenue(property_id: str, tenant_id: str, month: int, year: int) -> Dict[str, Any]:
    """
    Calculates revenue for a month, as the month is defined in the property's time zone.
    """
    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)

    query = text("""
        SELECT
            COALESCE(SUM(r.total_amount), 0) AS total_revenue,
            COUNT(r.id) AS reservation_count
        FROM reservations r
        JOIN properties p ON p.id = r.property_id AND p.tenant_id = r.tenant_id
        WHERE r.property_id = :property_id
        AND r.tenant_id = :tenant_id
        AND (r.check_in_date AT TIME ZONE p.timezone) >= :start_date
        AND (r.check_in_date AT TIME ZONE p.timezone) < :end_date
    """)

    async with await _get_session() as session:
        result = await session.execute(query, {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "start_date": start_date,
            "end_date": end_date
        })
        row = result.one()

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": str(Decimal(str(row.total_revenue))),
        "currency": "USD",
        "count": row.reservation_count
    }


async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database. Database failures propagate to the caller.
    """
    query = text("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS total_revenue,
            COUNT(*) AS reservation_count
        FROM reservations
        WHERE property_id = :property_id AND tenant_id = :tenant_id
    """)

    async with await _get_session() as session:
        result = await session.execute(query, {
            "property_id": property_id,
            "tenant_id": tenant_id
        })
        row = result.one()

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": str(Decimal(str(row.total_revenue))),
        "currency": "USD",
        "count": row.reservation_count
    }
