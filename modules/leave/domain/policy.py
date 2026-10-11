from decimal import Decimal
from datetime import date
from typing import Dict, Any

# Published RH calendar is supplied externally; validation function checks against it.
# VL conversion uses 2 VL : 1 EL ratio.

def entitlement(category: str) -> Decimal:
    """Return yearly entitlement for category."""
    ent = {
        'CL': Decimal('8'),
        'RH': Decimal('2'),
        'SCL': Decimal('15'),
        'EL': Decimal('30'),  # non-faculty
        'COL': Decimal('20'),
        'VL': Decimal('60'),  # faculty VL linked to academic vacation periods
    }
    return ent.get(category, Decimal('0'))

def requested_day_balance_validation(category: str, requested_days: Decimal, balance: Decimal) -> bool:
    """Validate requested days against balance for categories that lapse or carry forward.
    CL/RH/SCL lapse; EL/COL carry forward; VL does not carry forward.
    Returns True if request is within limits.
    """
    if category in ('CL', 'RH', 'SCL'):
        # Lapse: balance must be >= requested_days; no carry forward.
        return balance >= requested_days
    elif category == 'EL':
        # Carry forward: request <= balance (balance may be > entitlement due to carry forward)
        return requested_days <= balance
    elif category == 'COL':
        # Carry forward
        return requested_days <= balance
    elif category == 'VL':
        # VL does not carry forward; only current VL balance (if any) can be used.
        # But VL unused at year end converts to EL, not VL carry forward.
        # So request <= balance.
        return requested_days <= balance
    else:
        return False

def half_day_cl(requested_days: Decimal) -> Decimal:
    """Convert half-day CL request to day fraction (0.5)."""
    # Half day consumes 0.5 days.
    return Decimal('0.5')

def vl_conversion(unused_vl: Decimal) -> Decimal:
    """Convert unused faculty VL at year end to EL at 2 VL : 1 EL ratio.
    Returns EL days equivalent.
    """
    # 2 VL days convert to 1 EL day.
    # So EL = unused_vl / 2
    return unused_vl / Decimal('2')

def rh_calendar_validation(requested_date: date, rh_calendar: Dict[date, bool]) -> bool:
    """Validate RH request date against published RH calendar.
    rh_calendar maps date -> True if date is an applicable RH (i.e., not excluded).
    Returns True if date is in calendar.
    """
    return rh_calendar.get(requested_date, False)

# No additional prose or placeholders.
