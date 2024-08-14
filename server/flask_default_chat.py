from flask import Flask, request, jsonify, session
from flask_session import Session  # Flask-Session extension
import openai 
from openai import OpenAI
import os
import json
import tiktoken
from datetime import datetime

app = Flask(__name__)
# Replace with a real secret key
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Flask-Session
Session(app)

# Constants and Initializations
MAX_ALLOWED_TOKENS = 8192
MODEL_NAME = "gpt-4"  # Updated model name
BOT_RESPONSE_BUFFER = 500
openai.api_key = os.getenv("OPENAI_API_KEY")
enc = tiktoken.encoding_for_model(MODEL_NAME)

client = OpenAI()

def initialize_system_context():
    # Read the system context from the text file, using an example of the Streamy AI sidekick by mAInstream studIOs LLC (mainstreamstudios.ai).
    try:
        with open(os.path.join(os.path.dirname(__file__), 'system_context.txt'), 'r') as file:
            system_context = json.load(file)
    except Exception as e:
        print(f"Error reading system context: {e}")
        system_context = [
            {"role": "system", "content": "Default system context due to an error."}
        ]
    return system_context

@app.before_request
def before_request():
    # Check if 'messages' is not in session or 'init_done' flag is False, then initialize it
    if 'messages' not in session or not session.get('init_done', False):
        session['messages'] = initialize_system_context()
        session['init_done'] = True  # Set the flag to True after initialization

@app.after_request
def after_request(response):
    session.modified = True
    return response

def get_token_count(text):
    return len(enc.encode(text))

def calculate_messages_tokens(messages):
    total_tokens = 0
    for message in messages:
        total_tokens += get_token_count(message['content'])
    return total_tokens

def save_conversation(user_name):
        # Define the directory for saving chat history
    chat_history_dir = './server/chat_history'

    # Create the directory if it does not exist
    os.makedirs(chat_history_dir, exist_ok=True)

    # Save the conversation history to a file
    filename = os.path.join(chat_history_dir, f"chat_{user_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
    # Use the user_name from the request to save the file
    # filename = f"conversation_{user_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(filename, 'w') as f:
        json.dump(session['messages'], f, indent=4)
    session.pop('messages', None)  # Clear the messages in session after saving

# Helper function to add messages with the specified role
def add_message(role, content):
    session['messages'].append({"role": role, "content": content})

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    user_input = request.json.get('input')
    user_name = request.json.get('user_name', 'unknown_user')  # Get user_name from the request
    session['user_name'] = user_name  # Save it in the session
    session['messages'].append({"role": "user", "content": user_input})

    # Calculate the available token space for the response
    max_response_tokens = MAX_ALLOWED_TOKENS - calculate_messages_tokens(session['messages']) - BOT_RESPONSE_BUFFER

    try:
        # Call the Chat completions API with appropriate parameters
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=session['messages'],  # Use the messages from the session
            temperature=1,
            max_tokens=max_response_tokens,
            top_p=1,
            frequency_penalty=1,
            presence_penalty=1
        )

        # Access usage and choices using dot notation
        tokens_used = response.usage.total_tokens  # Correct access to 'total_tokens'
        
        if tokens_used + calculate_messages_tokens(session['messages']) > MAX_ALLOWED_TOKENS:
            print("Token limit exceeded by the bot's response.")
            return jsonify({"response": "Sorry, the token limit has been exceeded."})

        # Add the assistant's response to the session messages
        bot_response = response.choices[0].message.content  # Accessing 'content' via dot notation
        session['messages'].append({"role": "assistant", "content": bot_response})

    except openai.OpenAIError as e:  # Corrected error handling to match the updated client
        print(f"OpenAI Error: {e}.")
        return jsonify({"response": f"An OpenAI error occurred: {e}"})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"response": f"An error occurred: {e}"})

    # Return the assistant's response
    return jsonify({"response": bot_response})

@app.route('/api/chat/end', methods=['POST'])
def end_chat():
    # Extract the user_name when the chat ends
    conversation_data = request.json
    user_name = conversation_data.get('user_name', 'unknown_user')
    save_conversation(user_name)
    return jsonify({"message": "Conversation saved."})

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        # Here we should not save the conversation because we don't have a user_name
        pass

"""
Reponse example
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4o-mini",
  "system_fingerprint": "fp_44709d6fcb",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "\n\nHello there, how may I assist you today?",
    },
    "logprobs": null,
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
"""
