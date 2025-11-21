# PostgreSQL MCP Server

![Build Status](https://github.com/YOUR_USERNAME/mcp-postgres-wrapper/workflows/Build%20%26%20Deploy%20PostgreSQL%20MCP%20Server/badge.svg)
![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A production-ready, standalone Model Context Protocol (MCP) server that provides PostgreSQL database access for AI agents and chat applications.

## 🎯 Production Ready

This server has been thoroughly tested and includes:
- ✅ Automated CI/CD pipeline with security scanning
- ✅ Comprehensive health checks and monitoring
- ✅ Kubernetes deployment manifests
- ✅ Complete documentation and deployment guide

**📚 For production deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)**

## Overview

This MCP server implements the full MCP protocol (2024-11-05), allowing AI agents to interact with PostgreSQL databases through standardized tools. It supports both SSE (Server-Sent Events) and HTTP/JSON-RPC transports.

## Features

- ✅ **Full MCP Protocol Support** - Implements initialize, tools/list, tools/call, resources/list, and prompts/list
- ✅ **PostgreSQL Integration** - Execute queries, list tables, and describe schemas
- ✅ **Dual Transport** - Supports both SSE and HTTP transports
- ✅ **Docker Ready** - Includes Dockerfile and docker-compose.yml
- ✅ **Kubernetes Ready** - Production-grade K8s manifests included
- ✅ **Health Checks** - Built-in health monitoring
- ✅ **CI/CD Pipeline** - Automated testing, building, and deployment
- ✅ **Security Scanning** - Automated vulnerability detection with Trivy

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
- An existing PostgreSQL database (the server will connect to your database)

### 1. Configure Database Connection

Copy the example environment file and configure your PostgreSQL connection:

```bash
cp env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```bash
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

### 2. Start the Server

```bash
docker compose up -d
```

This starts the MCP server on port 8100.

### 3. Verify It's Running

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

The server requires a `.env` file with the following PostgreSQL connection settings:

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL server hostname or IP | `localhost` or `192.168.1.100` |
| `POSTGRES_PORT` | PostgreSQL server port | `5432` |
| `POSTGRES_DB` | Database name | `your_database` |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `your_secure_password` |

**Important:** Create your `.env` file from the provided `env.example`:

```bash
cp env.example .env
# Then edit .env with your actual credentials
```

### Database Connection

The server connects to your existing PostgreSQL database using the credentials specified in the `.env` file. Make sure:

1. Your PostgreSQL server is accessible from the Docker container
2. The user has appropriate permissions on the database
3. Firewall rules allow the connection
4. If PostgreSQL is on the same host, use `host.docker.internal` instead of `localhost`

## Usage with AI Agents

### Connecting from mcp-use Python Library

```python
from mcp_use import MCPClient, MCPAgent
from langchain_openai import ChatOpenAI

# Create MCP client
client = MCPClient.from_dict({
    "mcpServers": {
        "PostgreSQL": {
            "url": "http://localhost:8100/mcp",
            "headers": {}
        }
    }
})

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = MCPAgent(llm=llm, client=client)

# Use it
result = agent.run("Show me all tables in the database")
```

### Important Note on LLM Selection

For best tool-calling results, use:
- ✅ **OpenAI:** gpt-4, gpt-4o, gpt-4o-mini (Excellent)
- ✅ **Ollama:** llama3.1, llama3.2, mistral (Good)
- ⚠️ **Avoid:** qwen2.5:7b (Limited tool calling support)

## Example Usage

Once connected, you can use the MCP tools to interact with your PostgreSQL database:

```python
# List all tables
agent.run("What tables are available in the database?")

# Describe a table
agent.run("Show me the structure of the users table")

# Query data
agent.run("SELECT * FROM users WHERE status='active' LIMIT 10")
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
pip install -r requirements.txt
# Or manually:
# pip install fastapi uvicorn psycopg2-binary pydantic

# Set environment variables (or create .env file)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=your_username
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=your_database

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
1. Your PostgreSQL server is running and accessible
2. The `.env` file contains correct database credentials
3. Port 8100 is not in use: `lsof -i :8100`
4. The MCP server is healthy: `curl http://localhost:8100/health`
5. If PostgreSQL is on localhost, try using `host.docker.internal` as the host

### Tool Calls Not Working

If the AI agent discovers tools but doesn't call them:
1. Check your LLM model supports tool calling
2. Use explicit prompts: "Call the postgres_list_tables tool"
3. Consider switching to OpenAI (gpt-4o-mini)

### Database Connection Issues

Check MCP server logs:
```bash
docker compose logs postgres-mcp-server
```

Test database connection manually from your host:
```bash
psql -h your_postgres_host -U your_username -d your_database
```

Check if PostgreSQL allows connections from Docker:
- Verify `pg_hba.conf` allows connections from Docker network
- Ensure PostgreSQL is listening on the correct interface (check `postgresql.conf`)

## Security Considerations

⚠️ **Important security guidelines:**

1. **Never commit `.env` file** - Add it to `.gitignore`
2. **Use strong passwords** for PostgreSQL users
3. **Use environment variables** or secrets management in production
4. **Implement authentication** for the MCP endpoint
5. **Limit SQL query capabilities** (prevent DROP, DELETE, etc.)
6. **Use read-only database users** when possible
7. **Enable SSL/TLS** for database connections
8. **Restrict network access** to PostgreSQL server

## 📦 Deployment

### Quick Deploy Options

1. **Docker Compose** (Development & Testing)
   ```bash
   docker-compose up -d
   ```

2. **Kubernetes** (Production)
   ```bash
   kubectl apply -f kubernetes/
   ```

3. **GitHub Container Registry** (Latest Image)
   ```bash
   docker pull ghcr.io/YOUR_USERNAME/mcp-postgres-wrapper:latest
   ```

For detailed deployment instructions including Kubernetes, CI/CD setup, and production best practices, see **[DEPLOYMENT.md](./DEPLOYMENT.md)**.

## 🔄 CI/CD Pipeline

This project includes a production-ready CI/CD pipeline that:
- Runs automated tests and linting
- Builds and pushes Docker images to GitHub Container Registry
- Performs security scanning with Trivy
- Creates semantic version tags automatically
- Generates GitHub releases with deployment instructions

**Recent Fixes:**
- ✅ Fixed deprecated `actions/create-release` causing build failures
- ✅ Fixed repository name case sensitivity for GHCR
- ✅ Added comprehensive security scanning
- ✅ Improved error handling and notifications

See [CHANGELOG.md](./CHANGELOG.md) for detailed release notes.

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

## 📋 Project Structure

```
mcp-postgres-wrapper/
├── .github/
│   ├── workflows/
│   │   ├── build.yml        # Main CI/CD pipeline
│   │   └── pr-check.yml     # PR quality checks
│   └── dependabot.yml       # Automated dependency updates
├── kubernetes/               # K8s deployment manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secret.yaml
├── server.py                # Main MCP server implementation
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
├── env.example              # Environment variable template
├── README.md                # This file
├── DEPLOYMENT.md            # Detailed deployment guide
└── CHANGELOG.md             # Version history and changes
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
