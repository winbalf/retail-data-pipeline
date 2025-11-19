"""
Data models for retailer data structures.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class SalesRecord:
    """Generic sales record structure."""
    retailer_id: str
    transaction_id: str
    product_id: str
    product_name: str
    category: str
    quantity: int
    unit_price: float
    total_amount: float
    transaction_date: datetime
    customer_id: Optional[str] = None
    store_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

