"""
Service to ingest data from Retailer 2.
"""
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from ingestion.models.retailer_data import SalesRecord

class Retailer2Service:
    """Service for Retailer 2 API integration."""
    
    def __init__(self):
        # Use local API URL if not set (for Docker network)
        self.api_url = os.getenv('RETAILER_2_API_URL', 'http://retailer2-api:5002')
        self.api_key = os.getenv('RETAILER_2_API_KEY', 'retailer2_api_key_123')
        self.retailer_id = 'retailer_2'
    
    def fetch_sales_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Fetch sales data from Retailer 2 API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of sales records as dictionaries
        """
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        params = {}
        if start_date:
            params['from'] = start_date
        if end_date:
            params['to'] = end_date
        
        try:
            response = requests.get(
                f"{self.api_url}/transactions",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('transactions', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Retailer 2: {e}")
            return []
    
    def normalize_sales_record(self, raw_record: Dict[str, Any]) -> SalesRecord:
        """
        Normalize Retailer 2 data format to common SalesRecord structure.
        
        Args:
            raw_record: Raw record from Retailer 2 API
            
        Returns:
            Normalized SalesRecord
        """
        return SalesRecord(
            retailer_id=self.retailer_id,
            transaction_id=str(raw_record.get('transaction_number', '')),
            product_id=str(raw_record.get('item_code', '')),
            product_name=raw_record.get('item_name', ''),
            category=raw_record.get('department', ''),
            quantity=int(raw_record.get('qty', 0)),
            unit_price=float(raw_record.get('unit_cost', 0)),
            total_amount=float(raw_record.get('amount', 0)),
            transaction_date=datetime.fromisoformat(raw_record.get('date', datetime.now().isoformat())),
            customer_id=raw_record.get('member_id'),
            store_id=raw_record.get('location_id'),
            raw_data=raw_record
        )

