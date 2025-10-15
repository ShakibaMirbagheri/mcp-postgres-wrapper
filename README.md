# PostgreSQL MCP Server

A standalone Model Context Protocol (MCP) server that provides PostgreSQL database access for AI agents and chat applications.

## Overview

This MCP server implements the full MCP protocol (2024-11-05), allowing AI agents to interact with PostgreSQL databases through standardized tools. It supports both SSE (Server-Sent Events) and HTTP/JSON-RPC transports.

## Features

- ✅ **Full MCP Protocol Support** - Implements initialize, tools/list, tools/call, resources/list, and prompts/list
- ✅ **PostgreSQL Integration** - Execute queries, list tables, and describe schemas
- ✅ **Dual Transport** - Supports both SSE and HTTP transports
- ✅ **Docker Ready** - Includes Dockerfile and docker-compose.yml
- ✅ **Health Checks** - Built-in health monitoring

## Available Tools

The server exposes three MCP tools:

### 1. `postgres_query`
Execute SQL queries on the PostgreSQL database.

**Input:**
```json
{
  "query": "SELECT * FROM employees WHERE department='Engineering'"
}
```

**Output:** Query results as JSON array of objects

### 2. `postgres_list_tables`
List all tables in the current database.

**Input:** None required

**Output:** Array of table names

### 3. `postgres_describe_table`
Get schema information for a specific table.

**Input:**
```json
{
  "table_name": "employees"
}
```

**Output:** Table schema with column names, types, and constraints

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL database (or use the included one)

### 1. Start the Server

```bash
docker compose up -d
```

This starts two services:
- `mcp-postgres-db` - PostgreSQL database (port 5433)
- `postgres-mcp-server` - MCP server (port 8100)

### 2. Verify It's Running

```bash
# Check health
curl http://localhost:8100/health

# Expected: {"status":"healthy","database":"connected"}
```

### 3. Test MCP Endpoint

```bash
# Test SSE endpoint
curl -H "Accept: text/event-stream" http://localhost:8100/mcp

# Test HTTP endpoint  
curl -X POST http://localhost:8100/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Configuration

### Environment Variables

Edit the `docker-compose.yml` to configure:

```yaml
postgres-mcp-server:
  environment:
    # Database connection
    POSTGRES_HOST: mcp-postgres-db
    POSTGRES_PORT: 5432
    POSTGRES_USER: demouser
    POSTGRES_PASSWORD: demo123
    POSTGRES_DB: demodb
```

### Database Connection

The server connects to PostgreSQL using these settings (configured via environment variables):

- **Host:** `mcp-postgres-db` (Docker service name) or your PostgreSQL host
- **Port:** `5432` (internal) / `5433` (external)
- **Database:** `demodb`
- **User:** `demouser`
- **Password:** `demo123`

## Usage with AI Agents

### Connecting from mcp-use Python Library

```python
from mcp_use import MCPClient, MCPAgent
from langchain_openai import ChatOpenAI

# Create MCP client
client = MCPClient.from_dict({
    "mcpServers": {
        "PostgreSQL": {
            "url": "http://postgres-mcp-server:8100/mcp",
            "headers": {}
        }
    }
})

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = MCPAgent(llm=llm, client=client)

# Use it
result = agent.run("Show me all employees in the Engineering department")
```

### Important Note on LLM Selection

For best tool-calling results, use:
- ✅ **OpenAI:** gpt-4, gpt-4o, gpt-4o-mini (Excellent)
- ✅ **Ollama:** llama3.1, llama3.2, mistral (Good)
- ⚠️ **Avoid:** qwen2.5:7b (Limited tool calling support)

## Sample Data

The included PostgreSQL database comes with sample tables:

```sql
-- Employees table
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  department VARCHAR(50),
  salary DECIMAL(10,2)
);

-- Products table
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  price DECIMAL(10,2),
  stock INT
);
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server information |
| `/health` | GET | Health check |
| `/mcp` | GET/POST | MCP protocol endpoint (SSE/HTTP) |

## Development

### Running Without Docker

```bash
# Install dependencies
pip install fastapi uvicorn psycopg2-binary pydantic

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=demouser
export POSTGRES_PASSWORD=demo123
export POSTGRES_DB=demodb

# Run server
python server.py
```

### Rebuild After Changes

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

### Connection Refused

If you get connection errors, ensure:
1. PostgreSQL is running: `docker compose ps`
2. Port 8100 is not in use: `lsof -i :8100`
3. Database is healthy: `curl http://localhost:8100/health`

### Tool Calls Not Working

If the AI agent discovers tools but doesn't call them:
1. Check your LLM model supports tool calling
2. Use explicit prompts: "Call the postgres_list_tables tool"
3. Consider switching to OpenAI (gpt-4o-mini)

### Database Connection Issues

Check database logs:
```bash
docker compose logs mcp-postgres-db
```

Verify connection manually:
```bash
docker exec -it mcp-postgres-db psql -U demouser -d demodb
```

## Security Considerations

⚠️ **This is a development/demo setup. For production:**

1. **Change default credentials** in docker-compose.yml
2. **Use environment variables** or secrets management
3. **Implement authentication** for the MCP endpoint
4. **Limit SQL query capabilities** (prevent DROP, DELETE, etc.)
5. **Use read-only database users** when possible
6. **Enable SSL/TLS** for database connections

## Integration with Main Application

This MCP server can be used standalone or integrated with the main MCP management system.

### Standalone Usage

Run independently and connect from any MCP-compatible client.

### Integration with MCP Management System

Add to your main application's settings:

```
Name: PostgreSQL MCP Server
Type: HTTP/HTTPS
Category: database
URL: http://postgres-mcp-server:8100/mcp
```

## License

MIT License

## Support

For issues or questions, please check:
1. Server logs: `docker compose logs postgres-mcp-server`
2. Database logs: `docker compose logs mcp-postgres-db`
3. Health endpoint: `curl http://localhost:8100/health`

## Technical Details

- **Protocol:** MCP 2024-11-05
- **Transport:** SSE (preferred) and HTTP/JSON-RPC
- **Server:** FastAPI + Uvicorn
- **Database Driver:** psycopg2
- **Container:** Python 3.11-slim

---

Built with ❤️ for the Model Context Protocol ecosystem
