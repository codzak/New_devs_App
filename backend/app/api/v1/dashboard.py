from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.services.reservations import calculate_monthly_revenue
from app.core.auth import authenticate_request as get_current_user
from decimal import Decimal, ROUND_HALF_UP

router = APIRouter()


def _tenant_id(current_user) -> str:
    return getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"


def _summary_response(revenue_data: Dict[str, Any]) -> Dict[str, Any]:
    total_revenue_decimal = Decimal(str(revenue_data['total'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": float(total_revenue_decimal),
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    revenue_data = await get_revenue_summary(property_id, _tenant_id(current_user))
    return _summary_response(revenue_data)


@router.get("/dashboard/monthly")
async def get_dashboard_monthly(
    property_id: str,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=2100),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    revenue_data = await calculate_monthly_revenue(property_id, _tenant_id(current_user), month, year)
    return _summary_response(revenue_data)
