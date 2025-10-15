#!/usr/bin/env python3
"""
PostgreSQL MCP Server - Full MCP Protocol Implementation
Compatible with mcp-use Python client library
Implements both SSE and HTTP transports
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import psycopg2
from typing import Dict, Any, List, Optional
import uvicorn
import os
import json
import asyncio
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PostgreSQL MCP Server",
    description="MCP server for PostgreSQL - implements full MCP protocol",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST', 'mcp-postgres-db'),
    'port': int(os.environ.get('POSTGRES_PORT', '5432')),
    'user': os.environ.get('POSTGRES_USER', 'demouser'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'demo123'),
    'database': os.environ.get('POSTGRES_DB', 'demodb')
}

# MCP Tools Definition
MCP_TOOLS = [
    {
        "name": "postgres_query",
        "description": "Execute a SQL query on the PostgreSQL database. Use this to SELECT, INSERT, UPDATE, or DELETE data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to execute (e.g., SELECT * FROM employees WHERE department='Engineering')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "postgres_list_tables",
        "description": "List all tables in the current PostgreSQL database",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "postgres_describe_table",
        "description": "Get the schema/structure of a specific table including column names and types",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to describe"
                }
            },
            "required": ["table_name"]
        }
    }
]

def get_db_connection():
    """Get PostgreSQL database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def execute_query(query: str):
    """Execute SQL query and return results."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Check if it's a SELECT-like query
        if query.strip().upper().startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE')):
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            # Convert to list of dicts
            result = [dict(zip(columns, row)) for row in rows]
            return {"success": True, "data": result, "row_count": len(result)}
        else:
            # INSERT, UPDATE, DELETE, CREATE, etc.
            conn.commit()
            return {
                "success": True,
                "message": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                "affected_rows": cursor.rowcount
            }
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Root endpoint
@app.get("/")
async def root():
    """Server info endpoint."""
    return JSONResponse({
        "name": "PostgreSQL MCP Server",
        "version": "1.0.0",
        "protocol": "mcp",
        "protocol_version": "2024-11-05",
        "transports": ["sse", "http"],
        "database": {
            "host": DB_CONFIG['host'],
            "database": DB_CONFIG['database']
        },
        "status": "running"
    })

# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        conn.close()
        return JSONResponse({"status": "healthy", "database": "connected"})
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)

# MCP Protocol Endpoint - Supporting both GET and POST
@app.get("/mcp")
@app.post("/mcp")
@app.options("/mcp")
async def mcp_endpoint(request: Request):
    """
    MCP protocol endpoint.
    Supports both SSE (Server-Sent Events) and HTTP transports.
    """
    
    # Handle OPTIONS for CORS
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    # Check if client prefers SSE
    accept_header = request.headers.get("accept", "")
    prefer_sse = "text/event-stream" in accept_header or request.method == "GET"
    
    if prefer_sse:
        # SSE Transport
        async def sse_generator():
            """Generate SSE events for MCP protocol."""
            try:
                # If POST, read the request body
                if request.method == "POST":
                    try:
                        body = await request.json()
                        method = body.get("method", "")
                        params = body.get("params", {})
                        msg_id = body.get("id", 1)
                        
                        logger.info(f"MCP Request: {method}")
                        
                        if method == "initialize":
                            # Initialization handshake
                            response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {
                                        "tools": {}
                                    },
                                    "serverInfo": {
                                        "name": "PostgreSQL MCP Server",
                                        "version": "1.0.0"
                                    }
                                }
                            }
                            yield f"data: {json.dumps(response)}\n\n"
                        
                        elif method == "tools/list":
                            # List available tools
                            response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "tools": MCP_TOOLS
                                }
                            }
                            yield f"data: {json.dumps(response)}\n\n"
                        
                        elif method == "resources/list":
                            # List available resources (empty for database server)
                            response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "resources": []
                                }
                            }
                            yield f"data: {json.dumps(response)}\n\n"
                        
                        elif method == "prompts/list":
                            # List available prompts (empty for database server)
                            response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "prompts": []
                                }
                            }
                            yield f"data: {json.dumps(response)}\n\n"
                        
                        elif method == "tools/call":
                            # Execute tool
                            tool_name = params.get("name", "")
                            arguments = params.get("arguments", {})
                            
                            logger.info(f"Tool call: {tool_name} with {arguments}")
                            
                            # Execute the tool
                            if tool_name == "postgres_list_tables":
                                query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
                                result = execute_query(query)
                                
                            elif tool_name == "postgres_describe_table":
                                table_name = arguments.get("table_name", "")
                                query = f"""
                                    SELECT column_name, data_type, is_nullable, column_default
                                    FROM information_schema.columns
                                    WHERE table_name = '{table_name}'
                                    ORDER BY ordinal_position
                                """
                                result = execute_query(query)
                            
                            elif tool_name == "postgres_query":
                                query = arguments.get("query", "")
                                result = execute_query(query)
                            
                            else:
                                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                            
                            # Format response for MCP
                            response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": json.dumps(result, default=str, indent=2)
                                        }
                                    ]
                                }
                            }
                            yield f"data: {json.dumps(response)}\n\n"
                        
                        else:
                            # Unknown method
                            error_response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "error": {
                                    "code": -32601,
                                    "message": f"Method not found: {method}"
                                }
                            }
                            yield f"data: {json.dumps(error_response)}\n\n"
                    
                    except json.JSONDecodeError:
                        # Invalid JSON
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error: Invalid JSON"
                            }
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"
                
                else:
                    # GET request - send server capabilities
                    capabilities = {
                        "jsonrpc": "2.0",
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "PostgreSQL MCP Server",
                                "version": "1.0.0"
                            }
                        }
                    }
                    yield f"data: {json.dumps(capabilities)}\n\n"
                    
                    # Keep connection alive with periodic pings
                    for _ in range(3):
                        await asyncio.sleep(1)
                        yield f": ping\n\n"
            
            except Exception as e:
                logger.error(f"SSE generator error: {e}")
                error_msg = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                yield f"data: {json.dumps(error_msg)}\n\n"
        
        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    else:
        # HTTP Transport (JSON-RPC over HTTP)
        try:
            body = await request.json()
            method = body.get("method", "")
            params = body.get("params", {})
            msg_id = body.get("id", 1)
            
            if method == "initialize":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {}
                        },
                        "serverInfo": {
                            "name": "PostgreSQL MCP Server",
                            "version": "1.0.0"
                        }
                    }
                })
            
            elif method == "tools/list":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": MCP_TOOLS}
                })
            
            elif method == "resources/list":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"resources": []}
                })
            
            elif method == "prompts/list":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"prompts": []}
                })
            
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                # Execute tool (same logic as SSE)
                if tool_name == "postgres_list_tables":
                    query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
                    result = execute_query(query)
                elif tool_name == "postgres_describe_table":
                    table_name = arguments.get("table_name", "")
                    query = f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                    result = execute_query(query)
                elif tool_name == "postgres_query":
                    query = arguments.get("query", "")
                    result = execute_query(query)
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, default=str, indent=2)
                            }
                        ]
                    }
                })
        
        except Exception as e:
            logger.error(f"HTTP handler error: {e}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }, status_code=500)

if __name__ == "__main__":
    logger.info("🚀 Starting PostgreSQL MCP Server with full protocol support...")
    logger.info(f"   Database: {DB_CONFIG['database']} at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    logger.info(f"   MCP Endpoint: http://0.0.0.0:8100/mcp")
    logger.info(f"   Transports: SSE (preferred) and HTTP/JSON-RPC")
    uvicorn.run(app, host="0.0.0.0", port=8100, log_level="info")

