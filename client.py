import asyncio
import json
import os
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

# Load credentials from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Your Gemini API key from .env

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

async def chat(user_input):
    """
    Processes user input through a two-step LLM interaction with tool integration.

    Args:
        user_input (str): The input message from the user to be processed

    Returns:
        str: The final response message from the LLM
    """
    
    # Define the server parameters for your MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["main.py"],
        env=None
    )
    
    # Connect to your local MCP server 
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialize the connection
            await session.initialize()

            # Get tools from server
            tools_result = await session.list_tools()
            
            print(f"Available tools: {[tool.name for tool in tools_result.tools]}")
            
            # Convert tools to Gemini function calling format
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
            
            # 1st LLM call to determine which tool to use 
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(user_input, tools=gemini_tools)
            
            # Check if LLM decides to use a tool (like checking tool_calls)
            if (response.candidates[0].content.parts and 
                any(hasattr(part, 'function_call') for part in response.candidates[0].content.parts)):
                
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
                    
                    # Execute the tool called by the LLM
                    tool_response = await session.call_tool(tool_name, tool_args)
                    tool_response_text = ""
                    
                    # Extract text from tool response
                    for content in tool_response.content:
                        if hasattr(content, 'text'):
                            tool_response_text += content.text
                    
                    print(f"Tool response length: {len(tool_response_text)} characters")
                    
                    # 2nd LLM call to determine final response (like your Gmail example)
#                     final_prompt = f"""
# User request: {user_input}

# I used the {tool_name} tool and got this information:
# {tool_response_text[:3000]}{"..." if len(tool_response_text) > 3000 else ""}

# Please provide a helpful response based on this tool output.
# """

                    final_prompt = f"""
                    User request: {user_input}

                    I used the {tool_name} tool and got this information:
                    {tool_response_text}

                    Please provide a helpful response based on this tool output.
                    """
                    
                    final_response = await model.generate_content_async(final_prompt)
                    response_content = final_response.text
                else:
                    response_content = response.text
                
            else:
                # If LLM decides not to use a tool (like your Gmail example)
                response_content = response.text
            
            # Connection automatically closes when exiting context managers
            return response_content

# Example usage
async def main():
    # Test queries
    test_queries = [
        "How do I use Chroma DB with LangChain?",
        "Show me OpenAI embeddings documentation", 
        "What are vector stores in LangChain?",
        "Hello, how are you?"  # This should not trigger the tool
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
