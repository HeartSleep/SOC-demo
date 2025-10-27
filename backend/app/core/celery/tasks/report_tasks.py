from datetime import datetime
from typing import Dict, Any, List
import os
from pathlib import Path
import json
import jinja2

from celery import current_task
from app.core.celery.celery_app import celery_app
from app.api.models.report import Report, ReportStatus, ReportType, ReportFormat
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True)
def generate_report_task(self, report_id: str, report_config: Dict[str, Any]):
    """Generate report task"""
    try:
        logger.info(f"Starting report generation: {report_id}")

        # Update report status
        update_report_status(report_id, ReportStatus.GENERATING, {"progress": 0})

        # Load report configuration
        report_type = report_config.get("type", ReportType.VULNERABILITY_REPORT)
        report_format = report_config.get("format", ReportFormat.PDF)

        # Gather data for report
        update_report_status(report_id, ReportStatus.GENERATING, {
            "progress": 20,
            "message": "Gathering report data"
        })

        report_data = gather_report_data(report_config)

        # Generate report based on type and format
        update_report_status(report_id, ReportStatus.GENERATING, {
            "progress": 50,
            "message": "Generating report content"
        })

        if report_format == ReportFormat.PDF:
            file_path = generate_pdf_report(report_id, report_data, report_config)
        elif report_format == ReportFormat.HTML:
            file_path = generate_html_report(report_id, report_data, report_config)
        elif report_format == ReportFormat.EXCEL:
            file_path = generate_excel_report(report_id, report_data, report_config)
        elif report_format == ReportFormat.JSON:
            file_path = generate_json_report(report_id, report_data, report_config)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

        # Complete report generation
        update_report_status(report_id, ReportStatus.COMPLETED, {
            "progress": 100,
            "message": "Report generated successfully",
            "file_path": file_path,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        })

        logger.info(f"Report generation completed: {report_id}")

        return {
            "status": "success",
            "file_path": file_path,
            "report_id": report_id
        }

    except Exception as e:
        logger.error(f"Report generation failed for {report_id}: {str(e)}")
        update_report_status(report_id, ReportStatus.FAILED, {
            "error": str(e),
            "message": f"Report generation failed: {str(e)}"
        })
        raise


@celery_app.task(bind=True)
def scheduled_report_task(self, report_config: Dict[str, Any]):
    """Execute scheduled report generation"""
    try:
        logger.info("Starting scheduled report generation")

        # Create new report instance
        report_id = create_scheduled_report(report_config)

        # Generate the report
        result = generate_report_task(report_id, report_config)

        # Send report if email is configured
        if report_config.get("auto_email", False):
            send_report_email(report_id, report_config)

        return result

    except Exception as e:
        logger.error(f"Scheduled report generation failed: {str(e)}")
        raise


def gather_report_data(report_config: Dict[str, Any]) -> Dict[str, Any]:
    """Gather data for report generation"""
    data = {
        "generation_time": datetime.utcnow().isoformat(),
        "assets": [],
        "vulnerabilities": [],
        "scan_tasks": [],
        "statistics": {}
    }

    try:
        # Apply filters from report config
        filters = report_config.get("filters", {})

        # Gather assets data
        if report_config.get("include_assets", True):
            data["assets"] = get_assets_data(filters.get("asset_filters", {}))

        # Gather vulnerabilities data
        if report_config.get("include_vulnerabilities", True):
            data["vulnerabilities"] = get_vulnerabilities_data(filters.get("vulnerability_filters", {}))

        # Gather scan tasks data
        if report_config.get("include_scan_tasks", False):
            data["scan_tasks"] = get_scan_tasks_data(filters.get("task_filters", {}))

        # Calculate statistics
        data["statistics"] = calculate_statistics(data)

    except Exception as e:
        logger.error(f"Failed to gather report data: {str(e)}")
        raise

    return data


def generate_pdf_report(report_id: str, report_data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate PDF report"""
    try:
        # First generate HTML
        html_content = render_report_template(report_data, config, "html")

        # Convert HTML to PDF using weasyprint or similar
        output_path = os.path.join(settings.UPLOAD_DIR, "reports", f"report_{report_id}.pdf")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # For now, just write HTML content (you'd use weasyprint in real implementation)
        with open(output_path.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Placeholder for PDF generation
        # import weasyprint
        # weasyprint.HTML(string=html_content).write_pdf(output_path)

        return output_path

    except Exception as e:
        logger.error(f"Failed to generate PDF report: {str(e)}")
        raise


def generate_html_report(report_id: str, report_data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate HTML report"""
    try:
        html_content = render_report_template(report_data, config, "html")

        output_path = os.path.join(settings.UPLOAD_DIR, "reports", f"report_{report_id}.html")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    except Exception as e:
        logger.error(f"Failed to generate HTML report: {str(e)}")
        raise


def generate_excel_report(report_id: str, report_data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate Excel report"""
    try:
        import pandas as pd

        output_path = os.path.join(settings.UPLOAD_DIR, "reports", f"report_{report_id}.xlsx")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Assets sheet
            if report_data.get("assets"):
                assets_df = pd.DataFrame(report_data["assets"])
                assets_df.to_excel(writer, sheet_name='Assets', index=False)

            # Vulnerabilities sheet
            if report_data.get("vulnerabilities"):
                vulns_df = pd.DataFrame(report_data["vulnerabilities"])
                vulns_df.to_excel(writer, sheet_name='Vulnerabilities', index=False)

            # Statistics sheet
            stats_data = []
            for key, value in report_data.get("statistics", {}).items():
                stats_data.append({"Metric": key, "Value": value})

            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)

        return output_path

    except Exception as e:
        logger.error(f"Failed to generate Excel report: {str(e)}")
        raise


def generate_json_report(report_id: str, report_data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate JSON report"""
    try:
        output_path = os.path.join(settings.UPLOAD_DIR, "reports", f"report_{report_id}.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        return output_path

    except Exception as e:
        logger.error(f"Failed to generate JSON report: {str(e)}")
        raise


def render_report_template(report_data: Dict[str, Any], config: Dict[str, Any], format_type: str) -> str:
    """Render report using template"""
    try:
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "reports")
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

        # Select template based on report type and format
        report_type = config.get("type", "vulnerability_report")
        template_name = f"{report_type}_{format_type}.html"

        try:
            template = env.get_template(template_name)
        except jinja2.TemplateNotFound:
            # Fall back to default template
            template = env.get_template(f"default_{format_type}.html")

        # Render template
        content = template.render(
            report_data=report_data,
            config=config,
            generation_time=datetime.utcnow()
        )

        return content

    except Exception as e:
        logger.error(f"Failed to render report template: {str(e)}")
        # Return basic HTML structure as fallback
        return f"""
        <html>
        <head><title>Security Report</title></head>
        <body>
        <h1>Security Report</h1>
        <p>Generated: {datetime.utcnow().isoformat()}</p>
        <pre>{json.dumps(report_data, indent=2, default=str)}</pre>
        </body>
        </html>
        """


def get_assets_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get assets data for report"""
    # This would query the database with filters
    # For now, return mock data
    return [
        {
            "name": "example.com",
            "type": "domain",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]


def get_vulnerabilities_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get vulnerabilities data for report"""
    # This would query the database with filters
    # For now, return mock data
    return [
        {
            "title": "SQL Injection",
            "severity": "high",
            "target": "https://example.com/login",
            "status": "open",
            "discovered_at": "2024-01-01T00:00:00Z"
        }
    ]


def get_scan_tasks_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get scan tasks data for report"""
    # This would query the database with filters
    return []


def calculate_statistics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate report statistics"""
    stats = {}

    # Asset statistics
    assets = data.get("assets", [])
    stats["total_assets"] = len(assets)
    stats["assets_by_type"] = {}

    for asset in assets:
        asset_type = asset.get("type", "unknown")
        stats["assets_by_type"][asset_type] = stats["assets_by_type"].get(asset_type, 0) + 1

    # Vulnerability statistics
    vulnerabilities = data.get("vulnerabilities", [])
    stats["total_vulnerabilities"] = len(vulnerabilities)
    stats["vulnerabilities_by_severity"] = {}

    for vuln in vulnerabilities:
        severity = vuln.get("severity", "unknown")
        stats["vulnerabilities_by_severity"][severity] = stats["vulnerabilities_by_severity"].get(severity, 0) + 1

    return stats


def update_report_status(report_id: str, status: ReportStatus, metadata: Dict[str, Any]):
    """Update report status"""
    # This would update the report in the database
    logger.info(f"Report {report_id} status: {status}, metadata: {metadata}")


def create_scheduled_report(config: Dict[str, Any]) -> str:
    """Create a new report for scheduled generation"""
    # This would create a new report record in the database
    import uuid
    return str(uuid.uuid4())


def send_report_email(report_id: str, config: Dict[str, Any]):
    """Send report via email"""
    # This would implement email sending functionality
    logger.info(f"Sending report {report_id} via email")
    pass