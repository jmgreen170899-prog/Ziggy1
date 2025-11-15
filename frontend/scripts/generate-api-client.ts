#!/usr/bin/env tsx
/**
 * Generate TypeScript types and API client from OpenAPI spec
 *
 * This script:
 * 1. Fetches the OpenAPI spec from the backend
 * 2. Generates TypeScript types
 * 3. Generates a typed API client
 *
 * Usage: npm run generate:api
 */

import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const OPENAPI_URL = `${BACKEND_URL}/openapi.json`;

interface OpenAPISpec {
  openapi: string;
  info: Record<string, any>;
  paths: Record<string, any>;
  components?: {
    schemas?: Record<string, any>;
  };
}

/**
 * Fetch OpenAPI spec from backend
 */
async function fetchOpenAPISpec(): Promise<OpenAPISpec> {
  console.log(`Fetching OpenAPI spec from ${OPENAPI_URL}...`);

  const response = await fetch(OPENAPI_URL);
  if (!response.ok) {
    throw new Error(`Failed to fetch OpenAPI spec: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * Convert OpenAPI schema type to TypeScript type
 */
function convertType(schema: any): string {
  if (!schema) return "any";

  if (schema.$ref) {
    const refName = schema.$ref.split("/").pop();
    return refName || "any";
  }

  if (schema.type === "array") {
    const itemType = convertType(schema.items);
    return `Array<${itemType}>`;
  }

  if (schema.type === "object") {
    if (schema.properties) {
      const props = Object.entries(schema.properties)
        .map(([key, value]: [string, any]) => {
          const optional = schema.required?.includes(key) ? "" : "?";
          const type = convertType(value);
          return `  ${key}${optional}: ${type};`;
        })
        .join("\n");
      return `{\n${props}\n}`;
    }
    if (schema.additionalProperties) {
      const valueType = convertType(schema.additionalProperties);
      return `Record<string, ${valueType}>`;
    }
    return "Record<string, any>";
  }

  const typeMap: Record<string, string> = {
    string: "string",
    number: "number",
    integer: "number",
    boolean: "boolean",
    null: "null",
  };

  return typeMap[schema.type] || "any";
}

/**
 * Generate TypeScript interfaces from schemas
 */
function generateTypes(spec: OpenAPISpec): string {
  const schemas = spec.components?.schemas || {};

  let output = `/**
 * Auto-generated TypeScript types from OpenAPI spec
 * Generated on ${new Date().toISOString()}
 * DO NOT EDIT MANUALLY
 */

`;

  // Generate interfaces for each schema
  for (const [name, schema] of Object.entries(schemas)) {
    const schemaObj = schema as any;

    if (schemaObj.type === "object") {
      output += `export interface ${name} {\n`;

      const properties = schemaObj.properties || {};
      const required = schemaObj.required || [];

      for (const [propName, propSchema] of Object.entries(properties)) {
        const prop = propSchema as any;
        const isRequired = required.includes(propName);
        const optional = isRequired ? "" : "?";
        const description = prop.description
          ? `  /** ${prop.description} */\n`
          : "";
        const type = convertType(prop);

        output += `${description}  ${propName}${optional}: ${type};\n`;
      }

      output += `}\n\n`;
    }
  }

  return output;
}

/**
 * Generate API client methods from paths
 */
function generateClient(spec: OpenAPISpec): string {
  let output = `/**
 * Auto-generated API client from OpenAPI spec
 * Generated on ${new Date().toISOString()}
 * DO NOT EDIT MANUALLY
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

export class ZiggyAPIClient {
  private client: AxiosInstance;
  
  constructor(baseURL: string = 'http://localhost:8000', config?: AxiosRequestConfig) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      ...config,
    });
    
    // Add request interceptor for auth
    this.client.interceptors.request.use((config) => {
      if (typeof window !== 'undefined') {
        const token = window.localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = \`Bearer \${token}\`;
        }
      }
      return config;
    });
  }
  
`;

  const paths = spec.paths || {};
  const methodCounter: Record<string, number> = {};

  // Generate methods for each endpoint
  for (const [path, pathItem] of Object.entries(paths)) {
    const pathObj = pathItem as any;

    for (const [method, operation] of Object.entries(pathObj)) {
      if (!["get", "post", "put", "patch", "delete"].includes(method)) continue;

      const op = operation as any;
      const operationId =
        op.operationId || `${method}_${path.replace(/[^a-zA-Z0-9]/g, "_")}`;
      const summary = op.summary || "";
      const deprecated = op.deprecated ? "@deprecated " : "";

      // Generate method name
      const baseName = operationId.replace(/[^a-zA-Z0-9]/g, "_");
      const count = methodCounter[baseName] || 0;
      methodCounter[baseName] = count + 1;
      const methodName = count === 0 ? baseName : `${baseName}_${count}`;

      // Get request body type
      const requestBody = op.requestBody?.content?.["application/json"]?.schema;
      const requestType = requestBody ? convertType(requestBody) : null;

      // Get response type
      const responseSchema =
        op.responses?.["200"]?.content?.["application/json"]?.schema ||
        op.responses?.["201"]?.content?.["application/json"]?.schema;
      const responseType = responseSchema ? convertType(responseSchema) : "any";

      // Generate method signature
      const params = [];
      if (requestType) {
        params.push(`data: ${requestType}`);
      }

      // Add path parameters
      if (op.parameters) {
        for (const param of op.parameters) {
          if (param.in === "path") {
            params.push(`${param.name}: ${convertType(param.schema)}`);
          }
        }
      }

      const paramsStr = params.length > 0 ? params.join(", ") : "";

      output += `  /**\n   * ${summary}\n   * ${deprecated}${method.toUpperCase()} ${path}\n   */\n`;
      output += `  async ${methodName}(${paramsStr}): Promise<${responseType}> {\n`;

      if (method === "get" || method === "delete") {
        output += `    const response = await this.client.${method}('${path}');\n`;
      } else {
        output += `    const response = await this.client.${method}('${path}', data);\n`;
      }

      output += `    return response.data;\n`;
      output += `  }\n\n`;
    }
  }

  output += `}\n\n`;
  output += `// Export singleton instance\n`;
  output += `export const apiClient = new ZiggyAPIClient(\n`;
  output += `  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'\n`;
  output += `);\n`;

  return output;
}

/**
 * Main function
 */
async function main() {
  try {
    console.log("Starting API client generation...\n");

    // Fetch OpenAPI spec
    const spec = await fetchOpenAPISpec();
    console.log("✓ OpenAPI spec fetched successfully\n");

    // Create output directories
    const typesDir = join(process.cwd(), "src", "types", "api");
    const servicesDir = join(process.cwd(), "src", "services");

    mkdirSync(typesDir, { recursive: true });
    mkdirSync(servicesDir, { recursive: true });

    // Generate types
    console.log("Generating TypeScript types...");
    const types = generateTypes(spec);
    const typesPath = join(typesDir, "generated.ts");
    writeFileSync(typesPath, types);
    console.log(`✓ Types written to ${typesPath}\n`);

    // Generate client
    console.log("Generating API client...");
    const client = generateClient(spec);
    const clientPath = join(servicesDir, "apiClient.ts");
    writeFileSync(clientPath, client);
    console.log(`✓ Client written to ${clientPath}\n`);

    // Save the OpenAPI spec for reference
    const specPath = join(process.cwd(), "openapi.json");
    writeFileSync(specPath, JSON.stringify(spec, null, 2));
    console.log(`✓ OpenAPI spec saved to ${specPath}\n`);

    console.log("✓ API client generation complete!");
    console.log("\nNext steps:");
    console.log("1. Review the generated types in src/types/api/generated.ts");
    console.log("2. Review the generated client in src/services/apiClient.ts");
    console.log("3. Update your components to use the typed client");
  } catch (error) {
    console.error("Error generating API client:", error);
    process.exit(1);
  }
}

main();
