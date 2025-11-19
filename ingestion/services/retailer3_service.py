"""
Service to ingest data from Retailer 3.
"""
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from ingestion.models.retailer_data import SalesRecord

class Retailer3Service:
    """Service for Retailer 3 API integration."""
    
    def __init__(self):
        # Use local API URL if not set (for Docker network)
        self.api_url = os.getenv('RETAILER_3_API_URL', 'http://retailer3-api:5003')
        self.api_key = os.getenv('RETAILER_3_API_KEY', 'retailer3_api_key_123')
        self.retailer_id = 'retailer_3'
    
    def fetch_sales_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Fetch sales data from Retailer 3 API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of sales records as dictionaries
        """
        headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {}
        if start_date:
            payload['dateFrom'] = start_date
        if end_date:
            payload['dateTo'] = end_date
        
        try:
            response = requests.post(
                f"{self.api_url}/sales/query",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Retailer 3: {e}")
            return []
    
    def normalize_sales_record(self, raw_record: Dict[str, Any]) -> SalesRecord:
        """
        Normalize Retailer 3 data format to common SalesRecord structure.
        
        Args:
            raw_record: Raw record from Retailer 3 API
            
        Returns:
            Normalized SalesRecord
        """
        return SalesRecord(
            retailer_id=self.retailer_id,
            transaction_id=str(raw_record.get('sale_id', '')),
            product_id=str(raw_record.get('product_code', '')),
            product_name=raw_record.get('name', ''),
            category=raw_record.get('type', ''),
            quantity=int(raw_record.get('count', 0)),
            unit_price=float(raw_record.get('price_per_unit', 0)),
            total_amount=float(raw_record.get('revenue', 0)),
            transaction_date=datetime.fromisoformat(raw_record.get('timestamp', datetime.now().isoformat())),
            customer_id=raw_record.get('buyer_id'),
            store_id=raw_record.get('outlet_id'),
            raw_data=raw_record
        )

