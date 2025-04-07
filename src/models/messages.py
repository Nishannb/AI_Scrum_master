"""
Message models for agent communication in the Fetch.ai Agentverse.
"""

from typing import Dict, Any, Optional, List
from uagents import Model

class StatusRequest(Model):
    """Request for agent status"""
    type: str = "status_request"

class StatusResponse(Model):
    """Response with agent status"""
    type: str = "status_response"
    status: str
    details: Optional[Dict[str, Any]] = None

class DataRequest(Model):
    """Request to collect sprint data"""
    type: str = "collect_data"
    sprint_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class DataResponse(Model):
    """Response with collected sprint data"""
    type: str = "data_response"
    status: str
    sprint_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AnalysisRequest(Model):
    """Request to analyze sprint data"""
    type: str = "analyze_data"
    sprint_data: Dict[str, Any]

class AnalysisResponse(Model):
    """Response with analysis results"""
    type: str = "analysis_response"
    status: str
    analysis_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ReportRequest(Model):
    """Request to generate sprint report"""
    type: str = "generate_report"
    analysis_results: Dict[str, Any]

class ReportResponse(Model):
    """Response with report status"""
    type: str = "report_response"
    status: str
    report_url: Optional[str] = None
    error: Optional[str] = None 