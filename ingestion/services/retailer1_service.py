"""
Service to ingest data from Retailer 1.
"""
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from ingestion.models.retailer_data import SalesRecord

class Retailer1Service:
    """Service for Retailer 1 API integration."""
    
    def __init__(self):
        # Use local API URL if not set (for Docker network)
        self.api_url = os.getenv('RETAILER_1_API_URL', 'http://retailer1-api:5001')
        self.api_key = os.getenv('RETAILER_1_API_KEY', 'retailer1_api_key_123')
        self.retailer_id = 'retailer_1'
    
    def fetch_sales_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Fetch sales data from Retailer 1 API.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of sales records as dictionaries
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        try:
            response = requests.get(
                f"{self.api_url}/sales",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Retailer 1: {e}")
            return []
    
    def normalize_sales_record(self, raw_record: Dict[str, Any]) -> SalesRecord:
        """
        Normalize Retailer 1 data format to common SalesRecord structure.
        
        Args:
            raw_record: Raw record from Retailer 1 API
            
        Returns:
            Normalized SalesRecord
        """
        return SalesRecord(
            retailer_id=self.retailer_id,
            transaction_id=str(raw_record.get('order_id', '')),
            product_id=str(raw_record.get('sku', '')),
            product_name=raw_record.get('product_name', ''),
            category=raw_record.get('category', ''),
            quantity=int(raw_record.get('quantity', 0)),
            unit_price=float(raw_record.get('price', 0)),
            total_amount=float(raw_record.get('total', 0)),
            transaction_date=datetime.fromisoformat(raw_record.get('order_date', datetime.now().isoformat())),
            customer_id=raw_record.get('customer_id'),
            store_id=raw_record.get('store_id'),
            raw_data=raw_record
        )

