# MCP Client & Server Learning Repository

This repository demonstrates how to build and use **Model Context Protocol (MCP)** clients and servers for integrating AI agents with various tools and data sources. Perfect for learning MCP fundamentals and exploring different implementation patterns.

## 📚 What is MCP?

The Model Context Protocol (MCP) is an open standard that enables AI applications to securely connect to external data sources and tools. It allows Large Language Models (LLMs) to access real-time information and perform actions through a standardized interface.

**Key Benefits:**
- 🔗 Connect LLMs to external APIs and databases
- 🛠️ Enable AI agents to use tools and perform actions
- 🔒 Secure, standardized communication protocol
- 🚀 Extensible architecture for custom integrations

## 🛠️ Available Servers & Tools

### 1. **Basic Server** (`main.py`)
- **Purpose**: Documentation search across popular AI frameworks
- **Tools**: 
  - `search_docs`: Search LangChain, LlamaIndex, and OpenAI documentation
- **APIs Used**: Serper API for web search

### 2. **PIN Code Server** (`pincode_server.py`)
- **Purpose**: Indian postal code lookup and area information
- **Tools**:
  - `get_pincode_info`: Get area details for a PIN code
  - `get_postoffice_info`: Find post offices by area name
- **APIs Used**: Postal PIN Code API

### 3. **Ultimate Server** (`ultimate_server.py`)
The comprehensive server with multiple tool categories:

#### 🌐 **API Tools**
- `get_weather`: Current weather information for any city

#### 🗄️ **Database Tools**
- `query_users`: Search users by age criteria
- `query_products`: Find products by price range and category

#### 🔍 **Vector Search Tools**
- `vector_search`: Semantic search through document embeddings

#### 🧮 **Computational Tools**
- `calculate_math`: Evaluate mathematical expressions
- `generate_hash`: Generate MD5/SHA256 hashes

#### 📁 **File System Tools**
- `file_operations`: Read, write, list, and delete files

#### 💾 **Cache Tools**
- `cache_operations`: In-memory key-value storage

## 🔧 How It Works

### Server Side (MCP Server)
1. **Tool Definition**: Servers define tools with schemas using `@mcp.tool()` decorator
2. **Tool Execution**: Handle tool calls and return structured responses
3. **Communication**: Use stdio transport for client-server communication

```python
@mcp.tool()
def calculate_math(expression: str) -> str:
    """Calculate mathematical expressions safely"""
    # Tool implementation
    return result
```

### Client Side (MCP Client)
1. **Connection**: Connect to MCP server via stdio
2. **Tool Discovery**: List available tools from the server
3. **LLM Integration**: Convert tools to LLM-compatible format (Gemini, OpenAI, etc.)
4. **Tool Execution**: Call tools based on LLM decisions

```python
# Connect to server
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Get tools and integrate with LLM
        tools = await session.list_tools()
        # Execute tools based on LLM decisions
```