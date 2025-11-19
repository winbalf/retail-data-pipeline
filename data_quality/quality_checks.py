"""
Data quality checks for the retail data pipeline.
Performs various validations on the transformed data in PostgreSQL.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from shared.database import get_postgres_engine

class QualityCheckResult:
    """Result of a quality check."""
    def __init__(self, check_name: str, passed: bool, message: str, details: Optional[Dict[str, Any]] = None):
        self.check_name = check_name
        self.passed = passed
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'check_name': self.check_name,
            'passed': self.passed,
            'message': self.message,
            'details': self.details
        }

class DataQualityChecker:
    """Performs data quality checks on the star schema."""
    
    def __init__(self):
        self.engine = get_postgres_engine()
    
    def check_record_count(self, date_str: str) -> QualityCheckResult:
        """
        Check if expected number of records exist for the date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            QualityCheckResult
        """
        try:
            with self.engine.begin() as conn:
                # Count fact records for the date
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) as count
                        FROM fact_sales fs
                        JOIN dim_date dd ON fs.date_id = dd.date_id
                        WHERE dd.date = :date
                    """),
                    {"date": date_str}
                )
                row = result.fetchone()
                record_count = row[0] if row else 0
                
                # Check if we have at least some records (minimum threshold: 1)
                passed = record_count > 0
                message = f"Record count check: {record_count} records found for {date_str}"
                
                return QualityCheckResult(
                    check_name="record_count",
                    passed=passed,
                    message=message,
                    details={"record_count": record_count, "date": date_str}
                )
        except Exception as e:
            return QualityCheckResult(
                check_name="record_count",
                passed=False,
                message=f"Error checking record count: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_data_completeness(self, date_str: str) -> QualityCheckResult:
        """
        Check for null values in critical fields.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            QualityCheckResult
        """
        try:
            with self.engine.begin() as conn:
                # Check for nulls in critical fields
                result = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_records,
                            SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) as null_quantity,
                            SUM(CASE WHEN unit_price IS NULL THEN 1 ELSE 0 END) as null_unit_price,
                            SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END) as null_total_amount,
                            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) as null_product_id,
                            SUM(CASE WHEN retailer_id IS NULL THEN 1 ELSE 0 END) as null_retailer_id
                        FROM fact_sales fs
                        JOIN dim_date dd ON fs.date_id = dd.date_id
                        WHERE dd.date = :date
                    """),
                    {"date": date_str}
                )
                row = result.fetchone()
                
                if not row or row[0] == 0:
                    return QualityCheckResult(
                        check_name="data_completeness",
                        passed=False,
                        message=f"No records found for {date_str}",
                        details={"total_records": 0}
                    )
                
                total_records = row[0]
                null_quantity = row[1]
                null_unit_price = row[2]
                null_total_amount = row[3]
                null_product_id = row[4]
                null_retailer_id = row[5]
                
                # Check if any critical fields have nulls
                has_nulls = (null_quantity > 0 or null_unit_price > 0 or 
                           null_total_amount > 0 or null_product_id > 0 or null_retailer_id > 0)
                
                passed = not has_nulls
                message = f"Data completeness check: {total_records} records, "
                if has_nulls:
                    message += f"Found nulls - quantity: {null_quantity}, unit_price: {null_unit_price}, "
                    message += f"total_amount: {null_total_amount}, product_id: {null_product_id}, "
                    message += f"retailer_id: {null_retailer_id}"
                else:
                    message += "No null values in critical fields"
                
                return QualityCheckResult(
                    check_name="data_completeness",
                    passed=passed,
                    message=message,
                    details={
                        "total_records": total_records,
                        "null_quantity": null_quantity,
                        "null_unit_price": null_unit_price,
                        "null_total_amount": null_total_amount,
                        "null_product_id": null_product_id,
                        "null_retailer_id": null_retailer_id
                    }
                )
        except Exception as e:
            return QualityCheckResult(
                check_name="data_completeness",
                passed=False,
                message=f"Error checking data completeness: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_business_rules(self, date_str: str) -> QualityCheckResult:
        """
        Check business rule validations (e.g., total_amount = quantity * unit_price).
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            QualityCheckResult
        """
        try:
            with self.engine.begin() as conn:
                # Check if total_amount matches quantity * unit_price (with small tolerance for rounding)
                result = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_records,
                            SUM(CASE 
                                WHEN ABS(total_amount - (quantity * unit_price)) > 0.01 
                                THEN 1 ELSE 0 
                            END) as rule_violations
                        FROM fact_sales fs
                        JOIN dim_date dd ON fs.date_id = dd.date_id
                        WHERE dd.date = :date
                    """),
                    {"date": date_str}
                )
                row = result.fetchone()
                
                if not row or row[0] == 0:
                    return QualityCheckResult(
                        check_name="business_rules",
                        passed=False,
                        message=f"No records found for {date_str}",
                        details={"total_records": 0}
                    )
                
                total_records = row[0]
                rule_violations = row[1]
                
                passed = rule_violations == 0
                message = f"Business rules check: {total_records} records, {rule_violations} violations found"
                if rule_violations > 0:
                    message += " (total_amount != quantity * unit_price)"
                
                return QualityCheckResult(
                    check_name="business_rules",
                    passed=passed,
                    message=message,
                    details={
                        "total_records": total_records,
                        "rule_violations": rule_violations
                    }
                )
        except Exception as e:
            return QualityCheckResult(
                check_name="business_rules",
                passed=False,
                message=f"Error checking business rules: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_referential_integrity(self, date_str: str) -> QualityCheckResult:
        """
        Check referential integrity (foreign keys point to valid dimension records).
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            QualityCheckResult
        """
        try:
            with self.engine.begin() as conn:
                # Check for orphaned records (foreign keys that don't exist in dimensions)
                # Filter by date first, then check if foreign keys exist
                result = conn.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_records,
                            SUM(CASE WHEN dp.product_id IS NULL THEN 1 ELSE 0 END) as orphaned_product,
                            SUM(CASE WHEN dr.retailer_id IS NULL THEN 1 ELSE 0 END) as orphaned_retailer
                        FROM fact_sales fs
                        JOIN dim_date dd ON fs.date_id = dd.date_id AND dd.date = :date
                        LEFT JOIN dim_product dp ON fs.product_id = dp.product_id
                        LEFT JOIN dim_retailer dr ON fs.retailer_id = dr.retailer_id
                    """),
                    {"date": date_str}
                )
                row = result.fetchone()
                
                if not row or row[0] == 0:
                    return QualityCheckResult(
                        check_name="referential_integrity",
                        passed=False,
                        message=f"No records found for {date_str}",
                        details={"total_records": 0}
                    )
                
                total_records = row[0]
                orphaned_product = row[1]
                orphaned_retailer = row[2]
                
                has_orphans = (orphaned_product > 0 or orphaned_retailer > 0)
                
                passed = not has_orphans
                message = f"Referential integrity check: {total_records} records"
                if has_orphans:
                    message += f", Found orphaned records - product: {orphaned_product}, retailer: {orphaned_retailer}"
                else:
                    message += ", All foreign keys valid"
                
                return QualityCheckResult(
                    check_name="referential_integrity",
                    passed=passed,
                    message=message,
                    details={
                        "total_records": total_records,
                        "orphaned_product": orphaned_product,
                        "orphaned_retailer": orphaned_retailer
                    }
                )
        except Exception as e:
            return QualityCheckResult(
                check_name="referential_integrity",
                passed=False,
                message=f"Error checking referential integrity: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_data_freshness(self, date_str: str) -> QualityCheckResult:
        """
        Check if data is recent (within expected time window).
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            QualityCheckResult
        """
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            days_diff = (today - target_date).days
            
            # Data should be within last 7 days (reasonable for daily pipeline)
            max_days_old = 7
            passed = days_diff <= max_days_old
            
            message = f"Data freshness check: Data is {days_diff} days old"
            if not passed:
                message += f" (exceeds maximum of {max_days_old} days)"
            
            return QualityCheckResult(
                check_name="data_freshness",
                passed=passed,
                message=message,
                details={
                    "target_date": date_str,
                    "days_old": days_diff,
                    "max_days_old": max_days_old
                }
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="data_freshness",
                passed=False,
                message=f"Error checking data freshness: {str(e)}",
                details={"error": str(e)}
            )
    
    def run_all_checks(self, date_str: str) -> Dict[str, Any]:
        """
        Run all quality checks for a given date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Dictionary with all check results
        """
        print(f"🔍 Running data quality checks for date: {date_str}")
        
        checks = {
            'record_count': self.check_record_count(date_str),
            'data_completeness': self.check_data_completeness(date_str),
            'business_rules': self.check_business_rules(date_str),
            'referential_integrity': self.check_referential_integrity(date_str),
            'data_freshness': self.check_data_freshness(date_str)
        }
        
        # Summary
        total_checks = len(checks)
        passed_checks = sum(1 for result in checks.values() if result.passed)
        failed_checks = total_checks - passed_checks
        
        print(f"\n📊 Quality Check Summary:")
        print(f"   Total checks: {total_checks}")
        print(f"   Passed: {passed_checks}")
        print(f"   Failed: {failed_checks}")
        
        for check_name, result in checks.items():
            status = "✅" if result.passed else "❌"
            print(f"   {status} {result.check_name}: {result.message}")
        
        return {
            'date': date_str,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'all_passed': failed_checks == 0,
            'checks': {k: v.to_dict() for k, v in checks.items()}
        }

