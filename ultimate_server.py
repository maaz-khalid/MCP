from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
import sqlite3
import math
import datetime
from pathlib import Path
import hashlib
from typing import List, Dict
import asyncio

load_dotenv()

mcp = FastMCP("ultimate-tools")

# Initialize SQLite database
DB_FILE = "ultimate_tools.db"
CACHE = {}  # Simple in-memory cache

def init_database():
    """Initialize SQLite database with sample data"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER,
        city TEXT
    )
    ''')
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT,
        stock INTEGER
    )
    ''')
    
    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            (1, "Rajesh Kumar", "rajesh@gmail.com", 28, "Mumbai"),
            (2, "Priya Sharma", "priya@yahoo.com", 25, "Delhi"),
            (3, "Amit Patel", "amit@hotmail.com", 32, "Bangalore"),
            (4, "Sunita Singh", "sunita@gmail.com", 29, "Chennai"),
            (5, "Rohit Gupta", "rohit@outlook.com", 35, "Pune")
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", sample_users)
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            (1, "iPhone 15", 79999.00, "Electronics", 50),
            (2, "Samsung TV", 45000.00, "Electronics", 25),
            (3, "Nike Shoes", 5999.00, "Fashion", 100),
            (4, "Laptop Bag", 1299.00, "Accessories", 75),
            (5, "Coffee Mug", 299.00, "Home", 200)
        ]
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", sample_products)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Simple vector store (in-memory for demo)
VECTOR_STORE = {
    "documents": [
        {"id": 1, "text": "Python is a high-level programming language", "category": "programming"},
        {"id": 2, "text": "Machine learning is a subset of artificial intelligence", "category": "ai"},
        {"id": 3, "text": "Docker containers provide lightweight virtualization", "category": "devops"},
        {"id": 4, "text": "React is a JavaScript library for building user interfaces", "category": "programming"},
        {"id": 5, "text": "Kubernetes orchestrates containerized applications", "category": "devops"},
        {"id": 6, "text": "Natural language processing helps computers understand human language", "category": "ai"}
    ]
}

@mcp.tool()
async def get_weather(city: str):
    """
    API TOOL: Get current weather information for a city.
    
    Args:
        city: Name of the city
    
    Returns:
        Weather information
    """
    # Using a free weather API (OpenWeatherMap requires API key, so using a mock for demo)
    # You can replace this with real API calls
    mock_weather = {
        "mumbai": {"temp": 32, "condition": "Sunny", "humidity": 78},
        "delhi": {"temp": 28, "condition": "Cloudy", "humidity": 65},
        "bangalore": {"temp": 24, "condition": "Pleasant", "humidity": 70},
        "chennai": {"temp": 35, "condition": "Hot", "humidity": 80},
        "pune": {"temp": 26, "condition": "Partly Cloudy", "humidity": 68}
    }
    
    city_lower = city.lower()
    if city_lower in mock_weather:
        weather = mock_weather[city_lower]
        return f"Weather in {city}:\n🌡️ Temperature: {weather['temp']}°C\n☁️ Condition: {weather['condition']}\n💧 Humidity: {weather['humidity']}%"
    else:
        return f"Weather data not available for {city}. Try: Mumbai, Delhi, Bangalore, Chennai, or Pune"

@mcp.tool()
async def query_users(filter_by: str = "all"):
    """
    DATABASE TOOL: Query users from SQLite database.
    
    Args:
        filter_by: Filter criteria - "all", "young" (age < 30), "mumbai", "delhi", etc.
    
    Returns:
        List of users matching the criteria
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        if filter_by == "all":
            cursor.execute("SELECT * FROM users")
        elif filter_by == "young":
            cursor.execute("SELECT * FROM users WHERE age < 30")
        elif filter_by.lower() in ["mumbai", "delhi", "bangalore", "chennai", "pune"]:
            cursor.execute("SELECT * FROM users WHERE LOWER(city) = LOWER(?)", (filter_by,))
        else:
            cursor.execute("SELECT * FROM users WHERE LOWER(name) LIKE LOWER(?)", (f"%{filter_by}%",))
        
        users = cursor.fetchall()
        
        if not users:
            return f"No users found for filter: {filter_by}"
        
        result = f"Users ({filter_by}):\n\n"
        for user in users:
            result += f"👤 {user[1]} (ID: {user[0]})\n"
            result += f"   📧 {user[2]}\n"
            result += f"   📅 Age: {user[3]}\n"
            result += f"   🏙️ City: {user[4]}\n\n"
        
        return result
        
    finally:
        conn.close()

@mcp.tool()
async def search_products(category: str = "all", max_price: float = 100000.0):
    """
    DATABASE TOOL: Search products in SQLite database.
    
    Args:
        category: Product category or "all"
        max_price: Maximum price filter
    
    Returns:
        List of products matching criteria
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        if category == "all":
            cursor.execute("SELECT * FROM products WHERE price <= ?", (max_price,))
        else:
            cursor.execute("SELECT * FROM products WHERE LOWER(category) = LOWER(?) AND price <= ?", (category, max_price))
        
        products = cursor.fetchall()
        
        if not products:
            return f"No products found for category: {category} under ₹{max_price}"
        
        result = f"Products (Category: {category}, Max Price: ₹{max_price}):\n\n"
        for product in products:
            result += f"🛍️ {product[1]} (ID: {product[0]})\n"
            result += f"   💰 Price: ₹{product[2]}\n"
            result += f"   📦 Category: {product[3]}\n"
            result += f"   📊 Stock: {product[4]} units\n\n"
        
        return result
        
    finally:
        conn.close()

@mcp.tool()
async def vector_search(query: str, category: str = "all"):
    """
    VECTOR SEARCH TOOL: Search documents using simple text matching (mock vector search).
    
    Args:
        query: Search query
        category: Filter by category ("programming", "ai", "devops", or "all")
    
    Returns:
        Relevant documents based on the query
    """
    query_words = set(query.lower().split())
    results = []
    
    for doc in VECTOR_STORE["documents"]:
        if category != "all" and doc["category"] != category:
            continue
            
        doc_words = set(doc["text"].lower().split())
        # Simple similarity score based on word overlap
        overlap = len(query_words.intersection(doc_words))
        
        if overlap > 0:
            results.append({
                "doc": doc,
                "score": overlap / len(query_words)  # Simple similarity score
            })
    
    # Sort by relevance score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    if not results:
        return f"No documents found for query: '{query}'"
    
    response = f"Vector Search Results for '{query}':\n\n"
    for i, result in enumerate(results[:3], 1):  # Top 3 results
        doc = result["doc"]
        response += f"{i}. 📄 {doc['text']}\n"
        response += f"   🏷️ Category: {doc['category']}\n"
        response += f"   📊 Relevance: {result['score']:.2f}\n\n"
    
    return response

@mcp.tool()
async def calculate_math(expression: str):
    """
    COMPUTATIONAL TOOL: Perform mathematical calculations.
    
    Args:
        expression: Mathematical expression (e.g., "2+2", "sqrt(16)", "sin(30)")
    
    Returns:
        Result of the calculation
    """
    try:
        # Safe evaluation with limited functions
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
        
        # Replace common functions
        expression = expression.replace("^", "**")  # Power operator
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"🔢 {expression} = {result}"
        
    except Exception as e:
        return f"❌ Error calculating '{expression}': {str(e)}"

@mcp.tool()
async def file_operations(operation: str, filename: str = "", content: str = ""):
    """
    FILE SYSTEM TOOL: Perform file operations.
    
    Args:
        operation: "list", "read", "write", "delete", or "info"
        filename: Name of the file (for read/write/delete/info operations)
        content: Content to write (for write operation)
    
    Returns:
        Result of the file operation
    """
    try:
        data_dir = Path("mcp_data")
        data_dir.mkdir(exist_ok=True)
        
        if operation == "list":
            files = list(data_dir.glob("*"))
            if not files:
                return "📁 No files found in mcp_data directory"
            
            result = "📁 Files in mcp_data directory:\n\n"
            for file_path in files:
                stat = file_path.stat()
                size = stat.st_size
                modified = datetime.datetime.fromtimestamp(stat.st_mtime)
                result += f"📄 {file_path.name}\n"
                result += f"   📊 Size: {size} bytes\n"
                result += f"   🕒 Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            return result
            
        elif operation == "read":
            if not filename:
                return "❌ Filename required for read operation"
            
            file_path = data_dir / filename
            if not file_path.exists():
                return f"❌ File '{filename}' not found"
            
            content = file_path.read_text()
            return f"📄 Content of '{filename}':\n\n{content}"
            
        elif operation == "write":
            if not filename or not content:
                return "❌ Both filename and content required for write operation"
            
            file_path = data_dir / filename
            file_path.write_text(content)
            return f"✅ Successfully wrote to '{filename}'"
            
        elif operation == "delete":
            if not filename:
                return "❌ Filename required for delete operation"
            
            file_path = data_dir / filename
            if not file_path.exists():
                return f"❌ File '{filename}' not found"
            
            file_path.unlink()
            return f"🗑️ Successfully deleted '{filename}'"
            
        elif operation == "info":
            if not filename:
                return "❌ Filename required for info operation"
            
            file_path = data_dir / filename
            if not file_path.exists():
                return f"❌ File '{filename}' not found"
            
            stat = file_path.stat()
            modified = datetime.datetime.fromtimestamp(stat.st_mtime)
            created = datetime.datetime.fromtimestamp(stat.st_ctime)
            
            return f"📄 File Info for '{filename}':\n" \
                   f"📊 Size: {stat.st_size} bytes\n" \
                   f"🕒 Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}\n" \
                   f"📅 Created: {created.strftime('%Y-%m-%d %H:%M:%S')}"
        
        else:
            return f"❌ Unknown operation: {operation}. Use: list, read, write, delete, or info"
            
    except Exception as e:
        return f"❌ File operation error: {str(e)}"

@mcp.tool()
async def cache_operations(operation: str, key: str = "", value: str = ""):
    """
    MEMORY/CACHE TOOL: Perform in-memory cache operations.
    
    Args:
        operation: "get", "set", "delete", "list", or "clear"
        key: Cache key (for get/set/delete operations)
        value: Cache value (for set operation)
    
    Returns:
        Result of the cache operation
    """
    global CACHE
    
    if operation == "get":
        if not key:
            return "❌ Key required for get operation"
        
        if key in CACHE:
            return f"📦 Cache['{key}'] = {CACHE[key]}"
        else:
            return f"❌ Key '{key}' not found in cache"
            
    elif operation == "set":
        if not key or not value:
            return "❌ Both key and value required for set operation"
        
        CACHE[key] = value
        return f"✅ Cache['{key}'] = '{value}' saved"
        
    elif operation == "delete":
        if not key:
            return "❌ Key required for delete operation"
        
        if key in CACHE:
            deleted_value = CACHE.pop(key)
            return f"🗑️ Deleted Cache['{key}'] = '{deleted_value}'"
        else:
            return f"❌ Key '{key}' not found in cache"
            
    elif operation == "list":
        if not CACHE:
            return "📦 Cache is empty"
        
        result = "📦 Cache Contents:\n\n"
        for k, v in CACHE.items():
            result += f"🔑 {k} = {v}\n"
        return result
        
    elif operation == "clear":
        count = len(CACHE)
        CACHE.clear()
        return f"🧹 Cleared cache ({count} items removed)"
        
    else:
        return f"❌ Unknown operation: {operation}. Use: get, set, delete, list, or clear"

@mcp.tool()
async def generate_hash(text: str, algorithm: str = "md5"):
    """
    COMPUTATIONAL TOOL: Generate hash for text.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm ("md5", "sha1", "sha256")
    
    Returns:
        Hash value of the text
    """
    try:
        if algorithm == "md5":
            hash_obj = hashlib.md5(text.encode())
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1(text.encode())
        elif algorithm == "sha256":
            hash_obj = hashlib.sha256(text.encode())
        else:
            return f"❌ Unsupported algorithm: {algorithm}. Use: md5, sha1, or sha256"
        
        return f"🔐 {algorithm.upper()} hash of '{text}': {hash_obj.hexdigest()}"
        
    except Exception as e:
        return f"❌ Hash generation error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
