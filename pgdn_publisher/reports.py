"""
Report publishing functionality for PGDN Publisher.
"""

import json
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from .config import PublisherConfig


class ReportError(Exception):
    """Custom exception for report publishing errors."""
    pass


@dataclass
class PublishResult:
    """Result of a report publishing operation."""
    success: bool
    destination: str
    identifier: Optional[str] = None  # file path, walrus hash, etc.
    error: Optional[str] = None


class ReportPublisher:
    """Publisher for scan reports to various destinations."""
    
    def __init__(self, config: PublisherConfig):
        """Initialize report publisher."""
        self.config = config
    
    def _format_report(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format scan data into standardized report structure."""
        scan_id = scan_data.get('scan_id', scan_data.get('id', 'unknown'))
        
        # Create unique identifier for this report
        report_uid = f"depin_scan_{scan_id}_{int(datetime.now().timestamp())}"
        
        return {
            'uid': report_uid,
            'report_type': 'depin_validator_scan',
            'version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'scan_metadata': {
                'scan_id': scan_id,
                'host_uid': scan_data.get('host_uid', 'unknown'),
                'validator_id': scan_data.get('validator_id', 'unknown'),
                'scan_timestamp': scan_data.get('scan_time', datetime.now().isoformat()),
                'ip_address': scan_data.get('ip_address', 'unknown')
            },
            'security_assessment': {
                'trust_score': scan_data.get('trust_score', 0),
                'risk_level': self._calculate_risk_level(scan_data.get('trust_score', 0)),
                'open_ports': scan_data.get('open_ports', []),
                'services_detected': scan_data.get('services', []),
                'vulnerabilities': scan_data.get('vulnerabilities', []),
                'ssl_assessment': scan_data.get('ssl_info', {}),
                'scan_type': scan_data.get('scan_type', 'unknown')
            },
            'technical_details': {
                'network_scan': scan_data.get('network_scan', {}),
                'service_banners': scan_data.get('banners', {}),
                'web_technologies': scan_data.get('web_tech', {}),
                'docker_exposure': scan_data.get('docker_api', {})
            },
            'recommendations': self._generate_recommendations(scan_data),
            'raw_scan_data': scan_data
        }
    
    def _calculate_risk_level(self, trust_score: int) -> str:
        """Calculate risk level based on trust score."""
        if trust_score >= 80:
            return 'LOW'
        elif trust_score >= 60:
            return 'MEDIUM'
        elif trust_score >= 40:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def _generate_recommendations(self, scan_data: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []
        
        open_ports = scan_data.get('open_ports', [])
        if 22 in open_ports:
            recommendations.append("Ensure SSH is properly secured with key-based authentication")
        if 2375 in open_ports:
            recommendations.append("CRITICAL: Docker API exposed without authentication - secure immediately")
        
        vulnerabilities = scan_data.get('vulnerabilities', [])
        if vulnerabilities:
            recommendations.append(f"Address {len(vulnerabilities)} identified vulnerabilities")
        
        ssl_info = scan_data.get('ssl_info', {})
        if ssl_info.get('expired', False):
            recommendations.append("Renew expired SSL certificates")
        
        trust_score = scan_data.get('trust_score', 0)
        if trust_score < 70:
            recommendations.append("Overall security posture needs improvement")
        
        return recommendations
    
    def publish_to_walrus(self, report: Dict[str, Any]) -> PublishResult:
        """Publish report to Walrus decentralized storage."""
        if not self.config.walrus_api_key:
            return PublishResult(
                success=False,
                destination='walrus',
                error='Walrus API key not configured'
            )
        
        try:
            # Prepare data for Walrus
            report_json = json.dumps(report, default=str)
            
            headers = {
                'Authorization': f'Bearer {self.config.walrus_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Upload to Walrus
            response = requests.put(
                f"{self.config.walrus_api_url}/v1/store",
                data=report_json,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                walrus_hash = result.get('newlyCreated', {}).get('blobId')
                
                if walrus_hash:
                    return PublishResult(
                        success=True,
                        destination='walrus',
                        identifier=walrus_hash
                    )
                else:
                    return PublishResult(
                        success=False,
                        destination='walrus',
                        error='No blob ID returned from Walrus'
                    )
            else:
                return PublishResult(
                    success=False,
                    destination='walrus',
                    error=f'HTTP {response.status_code}: {response.text}'
                )
                
        except requests.exceptions.Timeout:
            return PublishResult(
                success=False,
                destination='walrus',
                error='Request timeout'
            )
        except Exception as e:
            return PublishResult(
                success=False,
                destination='walrus',
                error=str(e)
            )
    
    def publish_to_local_file(self, report: Dict[str, Any]) -> PublishResult:
        """Publish report to local file system."""
        try:
            # Create reports directory
            os.makedirs(self.config.reports_dir, exist_ok=True)
            
            # Generate filename
            scan_id = report['scan_metadata']['scan_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_report_{scan_id}_{timestamp}.json"
            filepath = os.path.join(self.config.reports_dir, filename)
            
            # Write report to file
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Verify file was written
            if os.path.exists(filepath):
                return PublishResult(
                    success=True,
                    destination='local_file',
                    identifier=filepath
                )
            else:
                return PublishResult(
                    success=False,
                    destination='local_file',
                    error='File was not created'
                )
                
        except Exception as e:
            return PublishResult(
                success=False,
                destination='local_file',
                error=str(e)
            )
    
    def publish(self, scan_data: Dict[str, Any], destinations: Optional[List[str]] = None) -> Dict[str, PublishResult]:
        """
        Publish report to specified destinations.
        
        Args:
            scan_data: Scan data to format and publish
            destinations: List of destinations ('walrus', 'local_file'). Defaults to both.
        
        Returns:
            Dictionary mapping destination names to PublishResult objects
        """
        if destinations is None:
            destinations = ['walrus', 'local_file']
        
        # Format the report
        report = self._format_report(scan_data)
        
        results = {}
        
        for destination in destinations:
            if destination == 'walrus':
                results['walrus'] = self.publish_to_walrus(report)
            elif destination == 'local_file':
                results['local_file'] = self.publish_to_local_file(report)
            else:
                results[destination] = PublishResult(
                    success=False,
                    destination=destination,
                    error=f'Unknown destination: {destination}'
                )
        
        return results
    
    def retrieve_from_walrus(self, walrus_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a report from Walrus storage."""
        if not self.config.walrus_api_key:
            raise ReportError("Walrus API key not configured")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.config.walrus_api_key}'
            }
            
            response = requests.get(
                f"{self.config.walrus_api_url}/v1/{walrus_hash}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise ReportError(f'HTTP {response.status_code}: {response.text}')
                
        except Exception as e:
            raise ReportError(f'Failed to retrieve from Walrus: {e}')


def publish_report(scan_data: Dict[str, Any], 
                  destinations: Optional[List[str]] = None,
                  config: Optional[PublisherConfig] = None) -> Dict[str, PublishResult]:
    """
    Convenience function to publish a scan report.
    
    Args:
        scan_data: Scan data to publish
        destinations: List of destinations to publish to
        config: Publisher configuration (defaults to environment config)
    
    Returns:
        Dictionary mapping destination names to PublishResult objects
    """
    if config is None:
        config = PublisherConfig.from_env()
    
    publisher = ReportPublisher(config)
    return publisher.publish(scan_data, destinations)