#!/usr/bin/env python3
"""
OpenAPI Documentation Generator
Generates OpenAPI 3.0 specification from FastAPI endpoints
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import ast
import re

class OpenAPIGenerator:
    def __init__(self):
        self.backend_dir = Path("backend")
        self.spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "SOC Security Platform API",
                "version": "1.0.0",
                "description": "Enterprise Security Operations Center Platform API",
                "contact": {
                    "name": "API Support",
                    "email": "api@soc-platform.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                },
                {
                    "url": "https://api.soc-platform.com",
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                },
                "schemas": {}
            },
            "security": [
                {"bearerAuth": []}
            ],
            "tags": []
        }

    def extract_endpoints_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract endpoint definitions from a Python file"""
        endpoints = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Find router definitions
            router_pattern = r'@router\.(get|post|put|delete|patch)\("([^"]+)".*?\)'
            matches = re.findall(router_pattern, content, re.DOTALL)

            for method, path in matches:
                # Extract function name and docstring
                func_pattern = rf'@router\.{method}\("{re.escape(path)}".*?\)\s*async def (\w+).*?"""(.*?)"""'
                func_match = re.search(func_pattern, content, re.DOTALL)

                if func_match:
                    func_name = func_match.group(1)
                    docstring = func_match.group(2).strip()

                    endpoints.append({
                        "method": method.upper(),
                        "path": f"/api/v1{path}",
                        "function": func_name,
                        "description": docstring.split('\n')[0] if docstring else "",
                        "file": file_path.name
                    })

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return endpoints

    def generate_path_spec(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI path specification for an endpoint"""
        operation = {
            "summary": endpoint.get("function", "").replace("_", " ").title(),
            "description": endpoint.get("description", ""),
            "operationId": endpoint.get("function", ""),
            "tags": [endpoint.get("file", "").replace(".py", "")],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/SuccessResponse"
                            }
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "404": {
                    "description": "Not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                }
            }
        }

        # Add request body for POST/PUT/PATCH
        if endpoint["method"] in ["POST", "PUT", "PATCH"]:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": f"#/components/schemas/{endpoint['function'].title()}Request"
                        }
                    }
                }
            }

        # Add parameters for GET endpoints
        if endpoint["method"] == "GET" and "{" in endpoint["path"]:
            # Extract path parameters
            params = re.findall(r'\{(\w+)\}', endpoint["path"])
            operation["parameters"] = [
                {
                    "name": param,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": f"{param} parameter"
                }
                for param in params
            ]

        # Add common query parameters for list endpoints
        if endpoint["method"] == "GET" and endpoint["path"].endswith("/"):
            operation["parameters"] = operation.get("parameters", []) + [
                {
                    "name": "page",
                    "in": "query",
                    "schema": {"type": "integer", "default": 1},
                    "description": "Page number"
                },
                {
                    "name": "size",
                    "in": "query",
                    "schema": {"type": "integer", "default": 20},
                    "description": "Page size"
                },
                {
                    "name": "search",
                    "in": "query",
                    "schema": {"type": "string"},
                    "description": "Search query"
                }
            ]

        return operation

    def add_common_schemas(self):
        """Add common schema definitions"""
        self.spec["components"]["schemas"].update({
            "SuccessResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {"type": "object"},
                    "message": {"type": "string"}
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "status": {"type": "integer"},
                    "errors": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "PaginatedResponse": {
                "type": "object",
                "properties": {
                    "items": {"type": "array", "items": {}},
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "size": {"type": "integer"},
                    "pages": {"type": "integer"}
                }
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "full_name": {"type": "string"},
                    "role": {"type": "string"},
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "Asset": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "asset_type": {
                        "type": "string",
                        "enum": ["domain", "ip", "url"]
                    },
                    "status": {"type": "string"},
                    "domain": {"type": "string"},
                    "ip_address": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "criticality": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"]
                    },
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "LoginRequest": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"}
                }
            },
            "LoginResponse": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "token_type": {"type": "string"},
                    "expires_in": {"type": "integer"},
                    "user": {"$ref": "#/components/schemas/User"}
                }
            }
        })

    def generate_spec(self):
        """Generate complete OpenAPI specification"""
        print("🔍 Scanning API endpoints...")

        endpoints_dir = self.backend_dir / "app" / "api" / "endpoints"

        if endpoints_dir.exists():
            all_endpoints = []
            tags_set = set()

            for file_path in endpoints_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    endpoints = self.extract_endpoints_from_file(file_path)
                    all_endpoints.extend(endpoints)

                    # Add tag
                    tag_name = file_path.name.replace(".py", "")
                    tags_set.add(tag_name)

            # Add tags to spec
            self.spec["tags"] = [
                {"name": tag, "description": f"{tag.title()} operations"}
                for tag in sorted(tags_set)
            ]

            # Process endpoints
            for endpoint in all_endpoints:
                path = endpoint["path"]
                method = endpoint["method"].lower()

                if path not in self.spec["paths"]:
                    self.spec["paths"][path] = {}

                self.spec["paths"][path][method] = self.generate_path_spec(endpoint)

            print(f"✅ Found {len(all_endpoints)} endpoints")

        # Add common schemas
        self.add_common_schemas()

    def generate_postman_collection(self):
        """Generate Postman collection from OpenAPI spec"""
        collection = {
            "info": {
                "name": self.spec["info"]["title"],
                "description": self.spec["info"]["description"],
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [],
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "token",
                    "value": "",
                    "type": "string"
                }
            ],
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{token}}",
                        "type": "string"
                    }
                ]
            }
        }

        # Group requests by tag
        folders = {}

        for path, methods in self.spec["paths"].items():
            for method, operation in methods.items():
                tag = operation.get("tags", ["default"])[0]

                if tag not in folders:
                    folders[tag] = {
                        "name": tag.title(),
                        "item": []
                    }

                # Create request
                request = {
                    "name": operation.get("summary", path),
                    "request": {
                        "method": method.upper(),
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "url": {
                            "raw": "{{baseUrl}}" + path,
                            "host": ["{{baseUrl}}"],
                            "path": path.strip("/").split("/")
                        }
                    }
                }

                # Add auth header
                if path != "/api/v1/auth/login":
                    request["request"]["header"].append({
                        "key": "Authorization",
                        "value": "Bearer {{token}}"
                    })

                # Add request body for POST/PUT/PATCH
                if method.upper() in ["POST", "PUT", "PATCH"]:
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps({
                            "example": "data"
                        }, indent=2)
                    }

                folders[tag]["item"].append(request)

        # Add folders to collection
        collection["item"] = list(folders.values())

        return collection

    def save_documentation(self):
        """Save generated documentation"""
        # Create docs directory
        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Save OpenAPI JSON
        openapi_json = docs_dir / "openapi.json"
        with open(openapi_json, 'w') as f:
            json.dump(self.spec, f, indent=2)
        print(f"✅ OpenAPI JSON: {openapi_json}")

        # Save OpenAPI YAML
        openapi_yaml = docs_dir / "openapi.yaml"
        with open(openapi_yaml, 'w') as f:
            yaml.dump(self.spec, f, default_flow_style=False, sort_keys=False)
        print(f"✅ OpenAPI YAML: {openapi_yaml}")

        # Generate and save Postman collection
        postman_collection = self.generate_postman_collection()
        postman_file = docs_dir / "postman_collection.json"
        with open(postman_file, 'w') as f:
            json.dump(postman_collection, f, indent=2)
        print(f"✅ Postman Collection: {postman_file}")

        # Generate HTML documentation
        self.generate_html_docs()

    def generate_html_docs(self):
        """Generate HTML API documentation"""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.spec['info']['title']}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
        }}
        #swagger-ui {{
            margin: 20px auto;
            max-width: 1200px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self.spec['info']['title']}</h1>
        <p>{self.spec['info']['description']}</p>
        <p>Version: {self.spec['info']['version']}</p>
    </div>
    <div id="swagger-ui"></div>

    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const spec = {json.dumps(self.spec)};

            const ui = SwaggerUIBundle({{
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});

            window.ui = ui;
        }}
    </script>
</body>
</html>"""

        html_file = Path("docs/api/index.html")
        with open(html_file, 'w') as f:
            f.write(html_content)
        print(f"✅ HTML Documentation: {html_file}")

        # Generate Markdown documentation
        self.generate_markdown_docs()

    def generate_markdown_docs(self):
        """Generate Markdown API documentation"""
        md_content = [
            f"# {self.spec['info']['title']}",
            f"\n{self.spec['info']['description']}",
            f"\nVersion: {self.spec['info']['version']}",
            "\n## Base URLs",
            ""
        ]

        for server in self.spec["servers"]:
            md_content.append(f"- {server['description']}: `{server['url']}`")

        md_content.extend([
            "\n## Authentication",
            "\nThis API uses JWT Bearer tokens for authentication.",
            "\n```http",
            "Authorization: Bearer <token>",
            "```",
            "\n## Endpoints",
            ""
        ])

        # Group endpoints by tag
        endpoints_by_tag = {}
        for path, methods in sorted(self.spec["paths"].items()):
            for method, operation in methods.items():
                tag = operation.get("tags", ["default"])[0]
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append({
                    "path": path,
                    "method": method.upper(),
                    "operation": operation
                })

        # Generate documentation for each tag
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            md_content.append(f"\n### {tag.title()}")
            md_content.append("")

            for endpoint in endpoints:
                md_content.append(f"#### {endpoint['method']} {endpoint['path']}")
                md_content.append("")

                operation = endpoint['operation']
                if operation.get('description'):
                    md_content.append(operation['description'])
                    md_content.append("")

                # Parameters
                if operation.get('parameters'):
                    md_content.append("**Parameters:**")
                    md_content.append("")
                    for param in operation['parameters']:
                        md_content.append(f"- `{param['name']}` ({param['in']}): {param.get('description', '')}")
                    md_content.append("")

                # Request body
                if operation.get('requestBody'):
                    md_content.append("**Request Body:**")
                    md_content.append("```json")
                    md_content.append("{")
                    md_content.append("  // Request schema")
                    md_content.append("}")
                    md_content.append("```")
                    md_content.append("")

                # Responses
                md_content.append("**Responses:**")
                md_content.append("")
                for code, response in operation['responses'].items():
                    md_content.append(f"- `{code}`: {response['description']}")
                md_content.append("")

        md_file = Path("docs/api/API_REFERENCE.md")
        with open(md_file, 'w') as f:
            f.write("\n".join(md_content))
        print(f"✅ Markdown Documentation: {md_file}")

    def run(self):
        """Run the documentation generation process"""
        print("=" * 60)
        print("📚 OpenAPI Documentation Generator")
        print("=" * 60)

        # Generate OpenAPI spec
        self.generate_spec()

        # Save documentation
        self.save_documentation()

        print("\n" + "=" * 60)
        print("✅ Documentation generation complete!")
        print("=" * 60)
        print("\nGenerated files:")
        print("  • docs/api/openapi.json - OpenAPI specification")
        print("  • docs/api/openapi.yaml - YAML format")
        print("  • docs/api/postman_collection.json - Postman collection")
        print("  • docs/api/index.html - Interactive HTML docs")
        print("  • docs/api/API_REFERENCE.md - Markdown reference")
        print("\nView interactive docs:")
        print("  • Open docs/api/index.html in browser")
        print("  • Or visit http://localhost:8000/docs (FastAPI)")


def main():
    generator = OpenAPIGenerator()
    generator.run()


if __name__ == "__main__":
    main()