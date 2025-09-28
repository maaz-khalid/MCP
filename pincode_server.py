from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os

load_dotenv()

mcp = FastMCP("pincode-info")

USER_AGENT = "pincode-app/1.0"

async def fetch_pincode_data(pincode: str) -> dict:
    """Fetch area details for a given PIN code"""
    url = f"https://api.postalpincode.in/pincode/{pincode}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"Status": "Error", "Message": "Timeout error"}
        except Exception as e:
            return {"Status": "Error", "Message": str(e)}

async def fetch_postoffice_data(area_name: str) -> dict:
    """Fetch post offices for a given area name"""
    url = f"https://api.postalpincode.in/postoffice/{area_name}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"Status": "Error", "Message": "Timeout error"}
        except Exception as e:
            return {"Status": "Error", "Message": str(e)}

@mcp.tool()
async def get_pincode_info(pincode: str):
    """
    Get detailed information about an Indian PIN code including area name, 
    district, state, and post office details.
    
    Args:
        pincode: 6-digit Indian PIN code (e.g., "400001" for Mumbai)
    
    Returns:
        Detailed area information for the PIN code
    """
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return "Please provide a valid 6-digit PIN code (e.g., 400001)"
    
    data = await fetch_pincode_data(pincode)
    
    if not data or data[0].get("Status") != "Success":
        return f"No information found for PIN code {pincode}"
    
    post_offices = data[0].get("PostOffice", [])
    if not post_offices:
        return f"No post office data found for PIN code {pincode}"
    
    # Format the response
    result = f"PIN Code: {pincode}\n\n"
    
    for po in post_offices:
        result += f"📍 **{po.get('Name', 'N/A')}**\n"
        result += f"   District: {po.get('District', 'N/A')}\n"
        result += f"   State: {po.get('State', 'N/A')}\n"
        result += f"   Division: {po.get('Division', 'N/A')}\n"
        result += f"   Region: {po.get('Region', 'N/A')}\n"
        result += f"   Country: {po.get('Country', 'N/A')}\n\n"
    
    return result

@mcp.tool()
async def find_postoffices(area_name: str):
    """
    Find post offices and PIN codes for a given area/city name.
    
    Args:
        area_name: Name of the area/city (e.g., "Mumbai", "Delhi", "Andheri")
    
    Returns:
        List of post offices with their PIN codes for the given area
    """
    if not area_name or len(area_name.strip()) < 2:
        return "Please provide a valid area name (minimum 2 characters)"
    
    data = await fetch_postoffice_data(area_name.strip())
    
    if not data or data[0].get("Status") != "Success":
        return f"No post offices found for area: {area_name}"
    
    post_offices = data[0].get("PostOffice", [])
    if not post_offices:
        return f"No post office data found for area: {area_name}"
    
    # Format the response
    result = f"Post Offices in '{area_name}':\n\n"
    
    for po in post_offices[:10]:  # Limit to first 10 results
        result += f"📮 **{po.get('Name', 'N/A')}**\n"
        result += f"   PIN Code: {po.get('Pincode', 'N/A')}\n"
        result += f"   District: {po.get('District', 'N/A')}\n"
        result += f"   State: {po.get('State', 'N/A')}\n"
        result += f"   Division: {po.get('Division', 'N/A')}\n\n"
    
    if len(post_offices) > 10:
        result += f"... and {len(post_offices) - 10} more post offices\n"
    
    return result

@mcp.tool()
async def get_random_joke():
    """
    Get a random programming joke to lighten the mood!
    
    Returns:
        A random programming joke
    """
    url = "https://v2.jokeapi.dev/joke/Programming?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("type") == "single":
                return f"😄 {data.get('joke', 'No joke found!')}"
            elif data.get("type") == "twopart":
                setup = data.get("setup", "")
                delivery = data.get("delivery", "")
                return f"😄 {setup}\n\n🎯 {delivery}"
            else:
                return "Sorry, couldn't fetch a joke right now!"
                
        except Exception as e:
            return f"Couldn't fetch joke: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
