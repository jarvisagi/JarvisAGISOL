import requests
import json
import os
from groq import Groq
from googlesearch import search
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_web_info(query, max_results=20, prints=False) -> str:
    """
    Retrieves real-time web search results for a given query.

    Parameters:
    - query (str): The search query.
    - max_results (int): Maximum number of search results to return.
    - prints (bool): Flag to enable printing of the response.

    Returns:
    - str: A JSON string containing the search results.
    """
    results = list(search(query, num_results=max_results, advanced=True))
    response = []
    for link in results:
        response.append({"link": link.url, "title": link.title, "description": link.description})
    return json.dumps(response)

def generate(user_prompt, system_prompt="Be Short and Concise", prints=False) -> str:
    """
    Generates a response to the user's prompt using the Groq API.

    Parameters:
    - user_prompt (str): The user's input prompt.
    - system_prompt (str): System's instruction to the model.
    - prints (bool): Flag to enable printing of the process.

    Returns:
    - str: The final response generated by the model.
    """
    function_descriptions = {
        "type": "function",
        "function": {
            "name": "get_web_info",
            "description": "Gets real-time information about the query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search on the web",
                    },
                },
                "required": ["query"],
            },
        },
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    api_key = os.environ.get("GROQ_AI")
    response = Groq(api_key=api_key).chat.completions.create(
        model='llama3-70b-8192',
        messages=messages,
        tools=[function_descriptions],
        tool_choice="auto",
        max_tokens=4096
    )

    response_message = response.choices[0].message
    if prints: print(f"Initial Response: {response_message} \n")
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_web_info": get_web_info,
        }

        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })

        second_response = Groq(api_key=api_key).chat.completions.create(
            model='llama3-70b-8192',
            messages=messages
        )
        return second_response.choices[0].message.content
    else:
        return response.choices[0].message.content


if __name__ == "__main__":

    # response = generate(user_prompt = "when is IPL 2024 starting  ", prints = True)
    # response = generate(user_prompt = "when is the election 2024 starting and ending. how much money is spend on the elctions 2024 in India", prints = True)
    response = generate(user_prompt = "Search the web for GPT-5 release date and features", prints = True, system_prompt='Be Short and Concise')
    
    print("Final Response:\n", response)