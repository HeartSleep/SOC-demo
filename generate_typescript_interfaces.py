#!/usr/bin/env python3
"""
Generate TypeScript interfaces from Backend Python models
Ensures perfect type compatibility between frontend and backend
"""

import os
import re
import ast
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class TypeScriptInterfaceGenerator:
    def __init__(self):
        self.backend_dir = Path("backend")
        self.frontend_dir = Path("frontend")
        self.type_mapping = {
            # Python to TypeScript type mappings
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "datetime": "string",  # ISO format
            "date": "string",
            "UUID": "string",
            "dict": "Record<string, any>",
            "Dict": "Record<string, any>",
            "list": "any[]",
            "List": "any[]",
            "Any": "any",
            "None": "null",
            "Optional": "| null",
            "Enum": "string",
        }
        self.interfaces = {}
        self.enums = {}

    def parse_python_models(self):
        """Parse Python model files to extract type information"""
        models_dir = self.backend_dir / "app" / "api" / "models"
        schemas_dir = self.backend_dir / "app" / "api" / "schemas"

        all_models = {}

        # Parse SQLAlchemy models
        if models_dir.exists():
            for file_path in models_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    print(f"📖 Parsing model: {file_path.name}")
                    models = self.parse_file(file_path)
                    all_models.update(models)

        # Parse Pydantic schemas
        if schemas_dir.exists():
            for file_path in schemas_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    print(f"📖 Parsing schema: {file_path.name}")
                    models = self.parse_file(file_path)
                    all_models.update(models)

        return all_models

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single Python file to extract class definitions"""
        models = {}

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Extract class information
                    class_name = node.name
                    fields = {}
                    is_enum = False

                    # Check if it's an Enum
                    for base in node.bases:
                        if hasattr(base, 'attr') and base.attr == 'Enum':
                            is_enum = True
                        elif hasattr(base, 'id') and 'Enum' in base.id:
                            is_enum = True

                    if is_enum:
                        # Extract enum values
                        enum_values = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        enum_values.append(target.id)
                        self.enums[class_name] = enum_values
                    else:
                        # Extract fields from class
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign):
                                # Type annotated field
                                if isinstance(item.target, ast.Name):
                                    field_name = item.target.id
                                    field_type = self.extract_type(item.annotation)
                                    fields[field_name] = field_type

                            elif isinstance(item, ast.Assign):
                                # SQLAlchemy Column definitions
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.id
                                        # Try to infer type from Column definition
                                        field_type = self.infer_sqlalchemy_type(item.value)
                                        if field_type:
                                            fields[field_name] = field_type

                        if fields:
                            models[class_name] = fields

        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")

        return models

    def extract_type(self, annotation) -> str:
        """Extract type from AST annotation"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # Handle Optional[type], List[type], etc.
            base = annotation.value.id if hasattr(annotation.value, 'id') else 'Any'
            if base == 'Optional':
                inner_type = self.extract_type(annotation.slice)
                return f"{inner_type} | null"
            elif base == 'List':
                inner_type = self.extract_type(annotation.slice)
                ts_type = self.python_to_typescript(inner_type)
                return f"{ts_type}[]"
            elif base == 'Dict':
                return "Record<string, any>"
            return base
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        else:
            return "any"

    def infer_sqlalchemy_type(self, value) -> Optional[str]:
        """Infer type from SQLAlchemy Column definition"""
        if isinstance(value, ast.Call):
            if hasattr(value.func, 'id') and value.func.id == 'Column':
                # Look for type in arguments
                for arg in value.args:
                    if isinstance(arg, ast.Name):
                        type_name = arg.id
                        if 'String' in type_name:
                            return 'str'
                        elif 'Integer' in type_name:
                            return 'int'
                        elif 'Boolean' in type_name:
                            return 'bool'
                        elif 'DateTime' in type_name:
                            return 'datetime'
                        elif 'UUID' in type_name:
                            return 'UUID'
                    elif isinstance(arg, ast.Call) and hasattr(arg.func, 'id'):
                        type_name = arg.func.id
                        if type_name in ['String', 'Text']:
                            return 'str'
                        elif type_name in ['Integer', 'BigInteger']:
                            return 'int'
                        elif type_name == 'Boolean':
                            return 'bool'
                        elif type_name in ['DateTime', 'Date']:
                            return 'datetime'
                        elif type_name == 'UUID':
                            return 'UUID'
        return None

    def python_to_typescript(self, python_type: str) -> str:
        """Convert Python type to TypeScript type"""
        if python_type in self.type_mapping:
            return self.type_mapping[python_type]
        elif ' | null' in python_type:
            base_type = python_type.replace(' | null', '')
            ts_type = self.python_to_typescript(base_type)
            return f"{ts_type} | null"
        elif python_type.endswith('[]'):
            base_type = python_type[:-2]
            ts_type = self.python_to_typescript(base_type)
            return f"{ts_type}[]"
        elif python_type in self.enums:
            # It's an enum, use the enum name
            return python_type
        else:
            # Unknown type, use as-is or map to any
            return python_type if python_type[0].isupper() else "any"

    def generate_typescript_interfaces(self, models: Dict[str, Dict[str, str]]) -> str:
        """Generate TypeScript interface definitions"""
        output = []

        # Header
        output.append("/**")
        output.append(" * Auto-generated TypeScript interfaces from Backend Models")
        output.append(" * Generated: " + str(Path.cwd()))
        output.append(" * DO NOT EDIT MANUALLY - Use generate_typescript_interfaces.py")
        output.append(" */")
        output.append("")

        # Generate enums first
        for enum_name, values in self.enums.items():
            output.append(f"export enum {enum_name} {{")
            for value in values:
                output.append(f'  {value} = "{value}",')
            output.append("}")
            output.append("")

        # Generate interfaces
        for model_name, fields in sorted(models.items()):
            output.append(f"export interface {model_name} {{")

            for field_name, field_type in sorted(fields.items()):
                # Skip private fields
                if field_name.startswith('_'):
                    continue

                # Convert Python type to TypeScript
                ts_type = self.python_to_typescript(field_type)

                # Handle optional fields
                if ' | null' in ts_type:
                    output.append(f"  {field_name}?: {ts_type};")
                else:
                    output.append(f"  {field_name}: {ts_type};")

            output.append("}")
            output.append("")

        # Generate common response types
        output.append("// Common API Response Types")
        output.append("")
        output.append("export interface PaginatedResponse<T> {")
        output.append("  items: T[];")
        output.append("  total: number;")
        output.append("  page: number;")
        output.append("  size: number;")
        output.append("  pages: number;")
        output.append("}")
        output.append("")
        output.append("export interface ApiResponse<T> {")
        output.append("  success: boolean;")
        output.append("  data?: T;")
        output.append("  message?: string;")
        output.append("  errors?: string[];")
        output.append("  request_id?: string;")
        output.append("}")
        output.append("")
        output.append("export interface ApiError {")
        output.append("  detail: string;")
        output.append("  status?: number;")
        output.append("  errors?: string[];")
        output.append("}")
        output.append("")

        # Generate API endpoint types
        output.append("// API Endpoint Types")
        output.append("")
        output.append("export interface LoginRequest {")
        output.append("  username: string;")
        output.append("  password: string;")
        output.append("}")
        output.append("")
        output.append("export interface LoginResponse {")
        output.append("  access_token: string;")
        output.append("  token_type: string;")
        output.append("  expires_in: number;")
        output.append("  user: User;")
        output.append("}")
        output.append("")

        return "\n".join(output)

    def generate_api_client(self) -> str:
        """Generate TypeScript API client with proper types"""
        output = []

        output.append("/**")
        output.append(" * Auto-generated API Client")
        output.append(" */")
        output.append("")
        output.append("import axios, { AxiosInstance } from 'axios';")
        output.append("import * as Types from './types';")
        output.append("")
        output.append("export class APIClient {")
        output.append("  private client: AxiosInstance;")
        output.append("")
        output.append("  constructor(baseURL: string = '/api/v1') {")
        output.append("    this.client = axios.create({")
        output.append("      baseURL,")
        output.append("      timeout: 30000,")
        output.append("      headers: {")
        output.append("        'Content-Type': 'application/json',")
        output.append("      },")
        output.append("    });")
        output.append("")
        output.append("    this.setupInterceptors();")
        output.append("  }")
        output.append("")
        output.append("  private setupInterceptors() {")
        output.append("    // Request interceptor")
        output.append("    this.client.interceptors.request.use(")
        output.append("      (config) => {")
        output.append("        const token = localStorage.getItem('token');")
        output.append("        if (token) {")
        output.append("          config.headers.Authorization = `Bearer ${token}`;")
        output.append("        }")
        output.append("        return config;")
        output.append("      },")
        output.append("      (error) => Promise.reject(error)")
        output.append("    );")
        output.append("")
        output.append("    // Response interceptor")
        output.append("    this.client.interceptors.response.use(")
        output.append("      (response) => response.data,")
        output.append("      (error) => {")
        output.append("        if (error.response?.status === 401) {")
        output.append("          // Handle unauthorized")
        output.append("          localStorage.removeItem('token');")
        output.append("          window.location.href = '/login';")
        output.append("        }")
        output.append("        return Promise.reject(error);")
        output.append("      }")
        output.append("    );")
        output.append("  }")
        output.append("")
        output.append("  // Authentication")
        output.append("  async login(data: Types.LoginRequest): Promise<Types.LoginResponse> {")
        output.append("    return this.client.post('/auth/login', data);")
        output.append("  }")
        output.append("")
        output.append("  async logout(): Promise<void> {")
        output.append("    return this.client.post('/auth/logout');")
        output.append("  }")
        output.append("")
        output.append("  async getCurrentUser(): Promise<Types.User> {")
        output.append("    return this.client.get('/auth/me');")
        output.append("  }")
        output.append("")
        output.append("  // Assets")
        output.append("  async getAssets(params?: any): Promise<Types.Asset[] | Types.PaginatedResponse<Types.Asset>> {")
        output.append("    return this.client.get('/assets/', { params });")
        output.append("  }")
        output.append("")
        output.append("  async getAsset(id: string): Promise<Types.Asset> {")
        output.append("    return this.client.get(`/assets/${id}`);")
        output.append("  }")
        output.append("")
        output.append("  async createAsset(data: Partial<Types.Asset>): Promise<Types.Asset> {")
        output.append("    return this.client.post('/assets/', data);")
        output.append("  }")
        output.append("")
        output.append("  async updateAsset(id: string, data: Partial<Types.Asset>): Promise<Types.Asset> {")
        output.append("    return this.client.put(`/assets/${id}`, data);")
        output.append("  }")
        output.append("")
        output.append("  async deleteAsset(id: string): Promise<void> {")
        output.append("    return this.client.delete(`/assets/${id}`);")
        output.append("  }")
        output.append("")
        output.append("  // Users")
        output.append("  async getUsers(params?: any): Promise<Types.PaginatedResponse<Types.User>> {")
        output.append("    return this.client.get('/users/', { params });")
        output.append("  }")
        output.append("")
        output.append("  // Tasks")
        output.append("  async getTasks(params?: any): Promise<Types.PaginatedResponse<Types.Task>> {")
        output.append("    return this.client.get('/tasks/', { params });")
        output.append("  }")
        output.append("")
        output.append("  // Vulnerabilities")
        output.append("  async getVulnerabilities(params?: any): Promise<Types.PaginatedResponse<Types.Vulnerability>> {")
        output.append("    return this.client.get('/vulnerabilities/', { params });")
        output.append("  }")
        output.append("}")
        output.append("")
        output.append("// Export singleton instance")
        output.append("export default new APIClient();")
        output.append("")

        return "\n".join(output)

    def save_typescript_files(self, interfaces: str, client: str):
        """Save generated TypeScript files"""
        # Create directory if it doesn't exist
        types_dir = self.frontend_dir / "src" / "types" / "generated"
        types_dir.mkdir(parents=True, exist_ok=True)

        # Save interfaces
        interfaces_file = types_dir / "models.ts"
        with open(interfaces_file, 'w') as f:
            f.write(interfaces)
        print(f"✅ Generated TypeScript interfaces: {interfaces_file}")

        # Save API client
        client_file = types_dir / "api-client.ts"
        with open(client_file, 'w') as f:
            f.write(client)
        print(f"✅ Generated API client: {client_file}")

        # Create index file
        index_content = """/**
 * Auto-generated TypeScript definitions
 */

export * from './models';
export { APIClient, default as apiClient } from './api-client';
"""
        index_file = types_dir / "index.ts"
        with open(index_file, 'w') as f:
            f.write(index_content)
        print(f"✅ Generated index file: {index_file}")

    def generate_validation_schemas(self) -> str:
        """Generate Zod validation schemas for runtime type checking"""
        output = []

        output.append("/**")
        output.append(" * Runtime validation schemas using Zod")
        output.append(" */")
        output.append("")
        output.append("import { z } from 'zod';")
        output.append("")

        # Generate Zod schemas for common types
        output.append("// User validation")
        output.append("export const UserSchema = z.object({")
        output.append("  id: z.string(),")
        output.append("  username: z.string(),")
        output.append("  email: z.string().email(),")
        output.append("  full_name: z.string(),")
        output.append("  role: z.string(),")
        output.append("  permissions: z.array(z.string()).optional(),")
        output.append("  is_active: z.boolean().optional(),")
        output.append("});")
        output.append("")

        output.append("// Asset validation")
        output.append("export const AssetSchema = z.object({")
        output.append("  id: z.string(),")
        output.append("  name: z.string(),")
        output.append("  asset_type: z.enum(['domain', 'ip', 'url']),")
        output.append("  status: z.string().optional(),")
        output.append("  domain: z.string().optional(),")
        output.append("  ip_address: z.string().optional(),")
        output.append("  tags: z.array(z.string()).optional(),")
        output.append("  criticality: z.enum(['low', 'medium', 'high', 'critical']).optional(),")
        output.append("});")
        output.append("")

        output.append("// Login validation")
        output.append("export const LoginRequestSchema = z.object({")
        output.append("  username: z.string().min(1),")
        output.append("  password: z.string().min(1),")
        output.append("});")
        output.append("")

        output.append("export const LoginResponseSchema = z.object({")
        output.append("  access_token: z.string(),")
        output.append("  token_type: z.string(),")
        output.append("  expires_in: z.number(),")
        output.append("  user: UserSchema,")
        output.append("});")
        output.append("")

        return "\n".join(output)

    def run(self):
        """Run the complete generation process"""
        print("=" * 60)
        print("🔧 TypeScript Interface Generator")
        print("=" * 60)

        # Parse Python models
        print("\n📚 Parsing Python models...")
        models = self.parse_python_models()
        print(f"   Found {len(models)} models")

        if not models:
            print("⚠️  No models found. Creating basic interfaces...")
            # Create basic interfaces even if models aren't parsed
            models = self.create_basic_models()

        # Generate TypeScript interfaces
        print("\n🔨 Generating TypeScript interfaces...")
        interfaces = self.generate_typescript_interfaces(models)

        # Generate API client
        print("🔨 Generating API client...")
        client = self.generate_api_client()

        # Generate validation schemas
        print("🔨 Generating validation schemas...")
        schemas = self.generate_validation_schemas()

        # Save files
        print("\n💾 Saving TypeScript files...")
        self.save_typescript_files(interfaces, client)

        # Save validation schemas
        schemas_file = self.frontend_dir / "src" / "types" / "generated" / "schemas.ts"
        with open(schemas_file, 'w') as f:
            f.write(schemas)
        print(f"✅ Generated validation schemas: {schemas_file}")

        # Create usage example
        self.create_usage_example()

        print("\n" + "=" * 60)
        print("✅ TypeScript generation complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review generated files in frontend/src/types/generated/")
        print("2. Import types in your components:")
        print("   import { User, Asset, apiClient } from '@/types/generated';")
        print("3. Use the typed API client:")
        print("   const user = await apiClient.getCurrentUser();")

    def create_basic_models(self) -> Dict[str, Dict[str, str]]:
        """Create basic models if parsing fails"""
        return {
            "User": {
                "id": "str",
                "username": "str",
                "email": "str",
                "full_name": "str",
                "role": "str",
                "permissions": "List[str]",
                "is_active": "bool",
                "created_at": "datetime",
                "updated_at": "datetime",
            },
            "Asset": {
                "id": "str",
                "name": "str",
                "asset_type": "str",
                "status": "str",
                "domain": "Optional[str]",
                "ip_address": "Optional[str]",
                "tags": "List[str]",
                "criticality": "str",
                "created_at": "datetime",
                "updated_at": "datetime",
            },
            "Task": {
                "id": "str",
                "name": "str",
                "type": "str",
                "status": "str",
                "priority": "str",
                "created_at": "datetime",
                "updated_at": "datetime",
            },
            "Vulnerability": {
                "id": "str",
                "title": "str",
                "severity": "str",
                "status": "str",
                "asset_id": "str",
                "description": "str",
                "created_at": "datetime",
                "updated_at": "datetime",
            }
        }

    def create_usage_example(self):
        """Create a usage example file"""
        example = '''/**
 * Example: Using Generated TypeScript Types and API Client
 */

import { ref, onMounted } from 'vue';
import { User, Asset, PaginatedResponse, apiClient } from '@/types/generated';
import { UserSchema, AssetSchema } from '@/types/generated/schemas';

// Type-safe component example
export default {
  setup() {
    // Typed reactive refs
    const user = ref<User | null>(null);
    const assets = ref<Asset[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);

    // Fetch current user with type safety
    const fetchUser = async () => {
      loading.value = true;
      try {
        const userData = await apiClient.getCurrentUser();

        // Optional: Validate response at runtime
        const validated = UserSchema.parse(userData);
        user.value = validated;
      } catch (err) {
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    };

    // Fetch assets with proper typing
    const fetchAssets = async () => {
      loading.value = true;
      try {
        const response = await apiClient.getAssets({
          page: 1,
          size: 20,
          asset_type: 'domain'
        });

        // Handle both array and paginated responses
        if (Array.isArray(response)) {
          assets.value = response;
        } else {
          assets.value = response.items;
        }
      } catch (err) {
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    };

    // Create asset with validation
    const createAsset = async (assetData: Partial<Asset>) => {
      try {
        // Validate input
        const validated = AssetSchema.partial().parse(assetData);

        // Create with type-safe API
        const newAsset = await apiClient.createAsset(validated);
        assets.value.push(newAsset);

        return newAsset;
      } catch (err) {
        if (err.name === 'ZodError') {
          // Handle validation errors
          console.error('Validation failed:', err.errors);
        }
        throw err;
      }
    };

    onMounted(() => {
      fetchUser();
      fetchAssets();
    });

    return {
      user,
      assets,
      loading,
      error,
      createAsset,
    };
  },
};
'''
        example_file = self.frontend_dir / "src" / "types" / "generated" / "example.ts"
        with open(example_file, 'w') as f:
            f.write(example)
        print(f"✅ Generated usage example: {example_file}")

def main():
    """Main function"""
    generator = TypeScriptInterfaceGenerator()
    generator.run()

if __name__ == "__main__":
    print("🚀 Starting TypeScript Interface Generation")
    print("This will generate TypeScript types from your Python models")
    print("")
    main()