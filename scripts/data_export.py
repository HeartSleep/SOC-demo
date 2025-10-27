#!/usr/bin/env python3
"""
SOC Platform data export/import utility
"""

import asyncio
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import argparse
import sys
import zipfile
import os

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import init_database
from app.api.models.asset import Asset
from app.api.models.task import Task
from app.api.models.vulnerability import Vulnerability
from app.api.models.report import Report
from app.api.models.user import User


class DataExporter:
    def __init__(self):
        self.export_formats = {
            'json': self.export_json,
            'csv': self.export_csv,
            'xml': self.export_xml,
            'nessus': self.export_nessus,
            'openvas': self.export_openvas
        }

    async def export_data(self, data_type, format_type, output_file, filters=None):
        """Export data in specified format"""
        print(f"Exporting {data_type} data to {output_file} in {format_type} format...")

        # Get data based on type
        data = await self.get_data(data_type, filters)

        if not data:
            print(f"No {data_type} data found")
            return

        # Export in requested format
        if format_type in self.export_formats:
            await self.export_formats[format_type](data, data_type, output_file)
            print(f"Export completed: {output_file}")
        else:
            print(f"Unsupported format: {format_type}")

    async def get_data(self, data_type, filters=None):
        """Get data from database"""
        filters = filters or {}

        if data_type == 'assets':
            query = Asset.find()
            if filters.get('type'):
                query = query.find(Asset.type == filters['type'])
            if filters.get('status'):
                query = query.find(Asset.status == filters['status'])
            return await query.to_list()

        elif data_type == 'vulnerabilities':
            query = Vulnerability.find()
            if filters.get('severity'):
                query = query.find(Vulnerability.severity == filters['severity'])
            if filters.get('status'):
                query = query.find(Vulnerability.status == filters['status'])
            return await query.to_list()

        elif data_type == 'tasks':
            query = Task.find()
            if filters.get('type'):
                query = query.find(Task.type == filters['type'])
            if filters.get('status'):
                query = query.find(Task.status == filters['status'])
            return await query.to_list()

        elif data_type == 'reports':
            return await Report.find().to_list()

        elif data_type == 'users':
            return await User.find().to_list()

        else:
            return []

    async def export_json(self, data, data_type, output_file):
        """Export data as JSON"""
        # Convert MongoDB documents to dict
        json_data = []
        for item in data:
            item_dict = item.dict()
            # Convert ObjectId to string
            if 'id' in item_dict:
                item_dict['id'] = str(item_dict['id'])
            json_data.append(item_dict)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'export_type': data_type,
                'export_date': datetime.now().isoformat(),
                'total_records': len(json_data),
                'data': json_data
            }, f, indent=2, ensure_ascii=False, default=str)

    async def export_csv(self, data, data_type, output_file):
        """Export data as CSV"""
        if not data:
            return

        # Get all possible field names
        all_fields = set()
        for item in data:
            all_fields.update(item.dict().keys())

        # Remove complex fields that don't work well in CSV
        simple_fields = [f for f in all_fields if not isinstance(
            getattr(data[0], f, None), (dict, list)
        )]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(simple_fields)

            # Write data
            for item in data:
                item_dict = item.dict()
                row = []
                for field in simple_fields:
                    value = item_dict.get(field, '')
                    # Convert to string and handle None
                    row.append(str(value) if value is not None else '')
                writer.writerow(row)

    async def export_xml(self, data, data_type, output_file):
        """Export data as XML"""
        root = ET.Element('export')
        root.set('type', data_type)
        root.set('date', datetime.now().isoformat())
        root.set('total', str(len(data)))

        for item in data:
            item_element = ET.SubElement(root, data_type.rstrip('s'))  # Remove 's' for singular
            item_dict = item.dict()

            for key, value in item_dict.items():
                if value is not None and not isinstance(value, (dict, list)):
                    elem = ET.SubElement(item_element, key)
                    elem.text = str(value)

        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

    async def export_nessus(self, data, data_type, output_file):
        """Export vulnerabilities in Nessus format"""
        if data_type != 'vulnerabilities':
            print("Nessus format only supports vulnerabilities")
            return

        root = ET.Element('NessusClientData_v2')

        # Policy section
        policy = ET.SubElement(root, 'Policy')
        policy_name = ET.SubElement(policy, 'policyName')
        policy_name.text = 'SOC Platform Export'

        # Report section
        report = ET.SubElement(root, 'Report')
        report.set('name', 'SOC Platform Vulnerabilities')

        for vuln in data:
            report_host = ET.SubElement(report, 'ReportHost')
            report_host.set('name', vuln.asset_name or 'unknown')

            report_item = ET.SubElement(report_host, 'ReportItem')
            report_item.set('port', str(vuln.details.get('port', 0)) if vuln.details else '0')
            report_item.set('svc_name', vuln.details.get('service', 'unknown') if vuln.details else 'unknown')
            report_item.set('protocol', vuln.details.get('protocol', 'tcp') if vuln.details else 'tcp')
            report_item.set('severity', self.map_severity_to_nessus(vuln.severity))
            report_item.set('pluginID', str(hash(vuln.name) % 100000))
            report_item.set('pluginName', vuln.name)

            # Add vulnerability details
            if vuln.description:
                description = ET.SubElement(report_item, 'description')
                description.text = vuln.description

            if vuln.cvss_score:
                cvss = ET.SubElement(report_item, 'cvss_base_score')
                cvss.text = str(vuln.cvss_score)

            if vuln.cve_id:
                cve = ET.SubElement(report_item, 'cve')
                cve.text = vuln.cve_id

        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

    async def export_openvas(self, data, data_type, output_file):
        """Export vulnerabilities in OpenVAS format"""
        if data_type != 'vulnerabilities':
            print("OpenVAS format only supports vulnerabilities")
            return

        root = ET.Element('report')
        root.set('id', 'soc-platform-export')
        root.set('format_id', 'a994b278-1f62-11e1-96ac-406186ea4fc5')

        # Report metadata
        creation_time = ET.SubElement(root, 'creation_time')
        creation_time.text = datetime.now().isoformat()

        # Results
        for vuln in data:
            result = ET.SubElement(root, 'result')
            result.set('id', str(hash(vuln.name) % 100000))

            # Host
            host = ET.SubElement(result, 'host')
            host.text = vuln.asset_name or 'unknown'

            # Port
            port = ET.SubElement(result, 'port')
            port.text = str(vuln.details.get('port', 0)) if vuln.details else '0'

            # NVT (Network Vulnerability Test)
            nvt = ET.SubElement(result, 'nvt')
            nvt.set('oid', f"1.3.6.1.4.1.25623.1.0.{hash(vuln.name) % 100000}")

            name = ET.SubElement(nvt, 'name')
            name.text = vuln.name

            # Threat
            threat = ET.SubElement(result, 'threat')
            threat.text = self.map_severity_to_openvas(vuln.severity)

            # Description
            description = ET.SubElement(result, 'description')
            description.text = vuln.description or ''

        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

    def map_severity_to_nessus(self, severity):
        """Map SOC severity to Nessus severity"""
        mapping = {
            'critical': '4',
            'high': '3',
            'medium': '2',
            'low': '1'
        }
        return mapping.get(severity, '0')

    def map_severity_to_openvas(self, severity):
        """Map SOC severity to OpenVAS threat level"""
        mapping = {
            'critical': 'High',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        return mapping.get(severity, 'Log')

    async def create_full_backup(self, output_file):
        """Create a complete backup of all data"""
        print("Creating full backup...")

        backup_dir = Path(output_file).parent / 'soc_backup_temp'
        backup_dir.mkdir(exist_ok=True)

        try:
            # Export all data types
            data_types = ['assets', 'vulnerabilities', 'tasks', 'reports', 'users']

            for data_type in data_types:
                data = await self.get_data(data_type)
                if data:
                    await self.export_json(data, data_type, backup_dir / f'{data_type}.json')

            # Create metadata
            metadata = {
                'backup_date': datetime.now().isoformat(),
                'version': '1.0',
                'data_types': data_types,
                'total_records': sum([
                    len(await self.get_data(dt)) for dt in data_types
                ])
            }

            with open(backup_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)

            # Create ZIP file
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_dir.rglob('*'):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.name)

            print(f"Full backup created: {output_file}")

        finally:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(backup_dir)


class DataImporter:
    def __init__(self):
        self.import_formats = {
            'json': self.import_json,
            'csv': self.import_csv,
            'nmap': self.import_nmap_xml,
            'nessus': self.import_nessus_xml
        }

    async def import_data(self, data_type, format_type, input_file):
        """Import data from file"""
        print(f"Importing {data_type} data from {input_file} ({format_type} format)...")

        if not Path(input_file).exists():
            print(f"Input file not found: {input_file}")
            return

        if format_type in self.import_formats:
            imported = await self.import_formats[format_type](data_type, input_file)
            print(f"Import completed: {imported} records imported")
        else:
            print(f"Unsupported format: {format_type}")

    async def import_json(self, data_type, input_file):
        """Import JSON data"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        records = data.get('data', data)  # Handle both wrapped and direct data
        imported = 0

        for record in records:
            try:
                if data_type == 'assets':
                    # Remove _id if present
                    record.pop('_id', None)
                    record.pop('id', None)
                    asset = Asset(**record)
                    await asset.create()
                    imported += 1

                elif data_type == 'vulnerabilities':
                    record.pop('_id', None)
                    record.pop('id', None)
                    vuln = Vulnerability(**record)
                    await vuln.create()
                    imported += 1

            except Exception as e:
                print(f"Failed to import record: {e}")

        return imported

    async def import_nmap_xml(self, data_type, input_file):
        """Import Nmap XML results"""
        if data_type != 'assets':
            print("Nmap XML import only supports assets")
            return 0

        tree = ET.parse(input_file)
        root = tree.getroot()
        imported = 0

        for host in root.findall('.//host'):
            # Get host address
            address_elem = host.find('.//address[@addrtype="ipv4"]')
            if address_elem is None:
                continue

            ip_address = address_elem.get('addr')

            # Create asset
            try:
                asset = Asset(
                    name=f"Nmap Host {ip_address}",
                    type='ip',
                    value=ip_address,
                    priority='medium',
                    tags=['nmap_import'],
                    description='Imported from Nmap scan'
                )

                # Add port information
                ports = []
                for port in host.findall('.//port'):
                    state = port.find('state')
                    if state is not None and state.get('state') == 'open':
                        service = port.find('service')
                        ports.append({
                            'port': int(port.get('portid')),
                            'protocol': port.get('protocol'),
                            'state': 'open',
                            'service': service.get('name') if service is not None else '',
                            'version': service.get('version') if service is not None else ''
                        })

                asset.ports = ports
                await asset.create()
                imported += 1

            except Exception as e:
                print(f"Failed to import host {ip_address}: {e}")

        return imported

    async def import_nessus_xml(self, data_type, input_file):
        """Import Nessus XML results as vulnerabilities"""
        if data_type != 'vulnerabilities':
            print("Nessus XML import only supports vulnerabilities")
            return 0

        tree = ET.parse(input_file)
        root = tree.getroot()
        imported = 0

        for report_item in root.findall('.//ReportItem'):
            try:
                # Get host name
                host_elem = report_item.getparent()
                host_name = host_elem.get('name') if host_elem is not None else 'unknown'

                # Create vulnerability
                vuln = Vulnerability(
                    name=report_item.get('pluginName', 'Unknown'),
                    description=self.get_text_content(report_item, 'description'),
                    severity=self.map_nessus_severity(report_item.get('severity', '0')),
                    cvss_score=float(self.get_text_content(report_item, 'cvss_base_score') or 0),
                    cve_id=self.get_text_content(report_item, 'cve'),
                    asset_name=host_name,
                    status='open',
                    verified=False,
                    details={
                        'port': int(report_item.get('port', 0)),
                        'service': report_item.get('svc_name'),
                        'protocol': report_item.get('protocol'),
                        'plugin_id': report_item.get('pluginID')
                    }
                )

                await vuln.create()
                imported += 1

            except Exception as e:
                print(f"Failed to import vulnerability: {e}")

        return imported

    def get_text_content(self, parent, tag_name):
        """Get text content of XML element"""
        elem = parent.find(tag_name)
        return elem.text if elem is not None else ''

    def map_nessus_severity(self, severity):
        """Map Nessus severity to SOC severity"""
        mapping = {
            '4': 'critical',
            '3': 'high',
            '2': 'medium',
            '1': 'low',
            '0': 'info'
        }
        return mapping.get(severity, 'low')


async def main():
    parser = argparse.ArgumentParser(description="SOC Platform Data Export/Import Tool")
    parser.add_argument('action', choices=['export', 'import', 'backup'],
                       help='Action to perform')
    parser.add_argument('--type', '-t',
                       choices=['assets', 'vulnerabilities', 'tasks', 'reports', 'users'],
                       help='Data type to export/import')
    parser.add_argument('--format', '-f',
                       choices=['json', 'csv', 'xml', 'nessus', 'openvas', 'nmap'],
                       default='json',
                       help='Export/import format')
    parser.add_argument('--file', '-o', required=True,
                       help='Output/input file path')
    parser.add_argument('--filter',
                       help='Filter criteria (JSON format)')

    args = parser.parse_args()

    # Parse filters
    filters = {}
    if args.filter:
        try:
            filters = json.loads(args.filter)
        except json.JSONDecodeError:
            print("Invalid filter JSON format")
            return

    # Initialize database
    await init_database()

    if args.action == 'export':
        if not args.type:
            print("Data type is required for export")
            return

        exporter = DataExporter()
        await exporter.export_data(args.type, args.format, args.file, filters)

    elif args.action == 'import':
        if not args.type:
            print("Data type is required for import")
            return

        importer = DataImporter()
        await importer.import_data(args.type, args.format, args.file)

    elif args.action == 'backup':
        exporter = DataExporter()
        await exporter.create_full_backup(args.file)


if __name__ == "__main__":
    asyncio.run(main())