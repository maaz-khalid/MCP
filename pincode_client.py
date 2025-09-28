import asyncio
import json
import os
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

# Load credentials from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

async def chat(user_input):
    """
    Chat function using the PIN code MCP server tools.
    """
    
    # Define server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["pincode_server.py"],
        env=None
    )
    
    # Connect to MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialize connection
            await session.initialize()
            
            # Get available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools_result.tools]}")
            
            # Convert tools to Gemini format
            gemini_tools = []
            for tool in tools_result.tools:
                function_declaration = genai.protos.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            prop_name: genai.protos.Schema(
                                type=genai.protos.Type.STRING,
                                description=prop_info.get("description", "")
                            )
                            for prop_name, prop_info in tool.inputSchema.get("properties", {}).items()
                        },
                        required=tool.inputSchema.get("required", [])
                    )
                )
                gemini_tools.append(genai.protos.Tool(function_declarations=[function_declaration]))
            
            # 1st LLM call with tools
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(user_input, tools=gemini_tools)
            
            # Check if LLM decided to use a tool
            if response.candidates[0].content.parts and any(hasattr(part, 'function_call') for part in response.candidates[0].content.parts):
                # Find the function call
                function_call = None
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        break
                
                if function_call:
                    tool_name = function_call.name
                    tool_args = {key: value for key, value in function_call.args.items()}
                    print(f"Tool Used: {tool_name}, Arguments: {tool_args}")
                    
                    # Execute the tool
                    tool_response = await session.call_tool(tool_name, tool_args)
                    tool_response_text = ""
                    
                    # Extract text from tool response
                    for content in tool_response.content:
                        if hasattr(content, 'text'):
                            tool_response_text += content.text
                    
                    print(f"Tool response length: {len(tool_response_text)} characters")
                    
                    # 2nd LLM call with tool results
                    if tool_name == "get_random_joke":
                        # For jokes, just share the joke directly
                        return tool_response_text
                    else:
                        # For other tools, show the data and provide helpful context
                        final_prompt = f"""
User request: {user_input}

I retrieved this information using the {tool_name} tool:

{tool_response_text}

Please present this information clearly to the user. Include all the details from the tool response, and add any helpful context or formatting to make it easy to read.
"""
                        final_response = await model.generate_content_async(final_prompt)
                        return final_response.text
                    
            # If no tool was used
            return response.text

# Example usage
async def main():
    test_queries = [
        "What is the PIN code for Andheri West Mumbai?",
        "Tell me about PIN code 400001",
        "Find post offices in Bangalore", 
        "What area does PIN code 110001 cover?",
        "Tell me a programming joke",
        "Hello, how are you?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        try:
            response = await chat(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
