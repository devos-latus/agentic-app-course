# Week 3 Assignment Requirements Checklist

## 🐳 Docker Containerization
- [ ] **Dockerfile created** with security best practices
- [ ] **Alpine Linux or distroless base** image used
- [ ] **Non-root user** configured in container
- [ ] **Minimal privileges** - only essential permissions
- [ ] **Multi-stage build** (optional but recommended)
- [ ] **No secrets in image** - uses environment variables

## 🔗 MCP Server Integration (stdio)
- [ ] **MCP server created** using FastMCP 2.0
- [ ] **At least 2 tools** implemented (time + pandas docs helper)
- [ ] **stdio transport** configured for local communication
- [ ] **Same container** - both app and MCP server packaged together
- [ ] **CSV analysis tools** converted from @function_tool to @mcp.tool
- [ ] **Communication working** between FastAPI and MCP server

## 🛡️ Container Security
- [ ] **Minimal attack surface** - only essential packages installed
- [ ] **Non-root execution** - container runs as unprivileged user
- [ ] **No privilege escalation** - proper security configurations
- [ ] **Vulnerability scanning** (optional) - container scanned for issues

## 🌐 HTTP API Endpoints
- [ ] **FastAPI application** created and configured
- [ ] **POST/GET /chat endpoint** - accepts messages, returns agent responses
- [ ] **GET /health endpoint** - returns service health status
- [ ] **Proper error handling** - meaningful HTTP status codes
- [ ] **Response formatting** - consistent JSON response structure
- [ ] **Request validation** - proper input validation with Pydantic

## 📦 All-in-One Container Setup
- [ ] **Agent application** - Week 1 + Week 2 functionality working
- [ ] **REST API endpoints** - /chat and /health accessible
- [ ] **Sample CSV files** - employee_data.csv, sample_sales.csv, weather_data.csv baked in
- [ ] **MCP server** - running with stdio transport in same container
- [ ] **All dependencies** - complete dependency management
- [ ] **Self-contained** - no external dependencies required
- [ ] **Deployable** - single docker run command works

## 🧪 Testing & Validation
- [ ] **Container builds** successfully
- [ ] **Container runs** without errors
- [ ] **Health endpoint** responds with 200 OK
- [ ] **Chat endpoint** accepts POST requests and returns responses
- [ ] **MCP tools** accessible via stdio within container
- [ ] **CSV data** loaded and queryable
- [ ] **Agent functionality** - all Week 1 + 2 features work
- [ ] **Phoenix tracing** (optional) - monitoring still works in container

## 📋 Documentation & Code Quality
- [ ] **README** - clear instructions for building and running
- [ ] **API documentation** - endpoints documented
- [ ] **Code organization** - clean src/ structure
- [ ] **Dependencies** - all requirements properly specified
- [ ] **Error messages** - helpful error responses
- [ ] **Logging** - appropriate logging for debugging

## 🚀 Deployment Ready
- [ ] **Docker image** builds in reasonable time (< 5 minutes)
- [ ] **Image size** reasonable (< 2GB)
- [ ] **Port exposure** - correct ports exposed (8000 for FastAPI)
- [ ] **Environment variables** - proper configuration via env vars
- [ ] **Health checks** - Docker health check configured
- [ ] **Graceful shutdown** - handles SIGTERM properly

---

## ✅ Success Criteria

The assignment is complete when:

1. **Single Docker container** contains everything needed
2. **HTTP API** responds to /chat and /health endpoints
3. **MCP server** provides tools via stdio transport
4. **Agent system** works with CSV analysis capabilities
5. **Security practices** implemented (non-root, minimal surface)
6. **Sample data** baked in and accessible
7. **No external dependencies** - completely self-contained

## 🎯 Final Test Command

```bash
# Build the container
docker build -t week3-agentic-app .

# Run the container
docker run -p 8000:8000 week3-agentic-app

# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What datasets are available?"}'
```

If all tests pass, the assignment requirements are met! 🎉
