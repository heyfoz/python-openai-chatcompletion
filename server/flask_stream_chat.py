from flask import Flask, g, request, jsonify, session, Response, stream_with_context
import openai
from openai import OpenAI
import os
import json
from datetime import datetime
import tiktoken

# Initialize OpenAI client and tokenizer
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Constants and Initializations
MAX_ALLOWED_TOKENS = 4096
MODEL_NAME = "gpt-4o"
BOT_RESPONSE_BUFFER = 500
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
enc = tiktoken.encoding_for_model(MODEL_NAME)
client = OpenAI()

@app.before_request
def before_request():
    if 'user_id' not in session:
        session['user_id'] = str(datetime.now().timestamp())  # Use timestamp or generate unique ID
    
    if 'conversation' not in session:
        session['conversation'] = load_system_context()  # Initialize conversation with system context

@app.after_request
def after_request(response):
    session.modified = True
    return response

# System context loading function
def load_system_context():
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'system_context.txt')
        with open(file_path, 'r') as file:
            system_context = json.load(file)
    except Exception as e:
        print(f"Error reading system context: {e}")
        system_context = [
            {"role": "system", "content": "Default system context due to an error."}
        ]
    return system_context

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    user_input = request.json.get('input')
    global global_user_name  # Declare the use of the global variable
    global_user_name = request.json.get('user_name', 'unknown_user')  # Extract user_name from the request
    user_id = session.get('user_id')  # Retrieve user_id from session

    # Log received user_name and user_id for debugging
    print(f"Received user_name: {global_user_name}")
    print(f"Session user_id: {user_id}")
    
    # Initialize or load the conversation from session
    conversation = session.get('conversation', load_system_context())
    conversation.append({"role": "user", "content": user_input})
    session['conversation'] = conversation

    print(f"User input added to conversation: {user_input}")
    print(f"Current conversation messages: {conversation}")

    max_response_tokens = MAX_ALLOWED_TOKENS - calculate_messages_tokens(conversation) - BOT_RESPONSE_BUFFER
    temp_response = ""

    def generate():
        nonlocal temp_response

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation,
                temperature=1,
                max_completions_tokens=max_response_tokens,
                top_p=1,
                frequency_penalty=1,
                presence_penalty=1,
                stream=True
            )

            print("API request sent successfully. Streaming response chunks...")

            for chunk in response:
                print(f"Received chunk: {chunk}")

                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    chunk_content = getattr(delta, 'content', '')
                    finish_reason = chunk.choices[0].finish_reason

                    if chunk_content:
                        temp_response += chunk_content
                        chunk_json = json.dumps({"choices": [{"delta": {"content": chunk_content}}]})
                        print(f"Streaming chunk to client: {chunk_json}")
                        yield f"{chunk_json}\n"
                    
                    if finish_reason == 'stop':
                        print(f"Streaming finished. Final response: {temp_response}")
                        conversation.append({"role": "assistant", "content": temp_response})
                        session['conversation'] = conversation
                        print(f"Assistant response added to conversation: {temp_response}")
                        print(f"Updated conversation messages: {conversation}")
                        temp_response = ""

                else:
                    print("Invalid chunk received or chunk has no content.")

        except openai.OpenAIError as e:
            error_message = f"An OpenAI error occurred: {e}"
            print(error_message)
            yield json.dumps({"error": error_message}) + "\n"
        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(error_message)
            yield json.dumps({"error": error_message}) + "\n"

    return Response(stream_with_context(generate()), content_type='application/json')


@app.route('/api/chat/end', methods=['POST'])
def end_chat():
    # Get conversation data from the request
    new_conversation = request.json
    
    if not isinstance(new_conversation, list):
        return jsonify({"error": "Conversation data must be an array."}), 400

    # Load existing system context
    system_context = load_system_context()
    
    # Append new conversation to system context
    system_context.extend(new_conversation)

    # Define the directory for saving chat history
    chat_history_dir = './server/chat_history'

    # Create the directory if it does not exist
    os.makedirs(chat_history_dir, exist_ok=True)

    # Save the conversation history to a file
    filename = os.path.join(chat_history_dir, f"chat_{global_user_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
    try:
        with open(filename, 'w') as f:
            json.dump(system_context, f, indent=4)
        print(f"Chat history saved to {filename}")
        return jsonify({"message": "Conversation saved."})
    except IOError as e:
        print(f"IOError while saving system context: {e}")
        return jsonify({"error": "Error saving conversation."}), 500
    except json.JSONEncodeError as e:
        print(f"JSON encoding error while saving system context: {e}")
        return jsonify({"error": "Error encoding conversation data."}), 500

def calculate_messages_tokens(messages):
    total_tokens = 0
    for message in messages:
        total_tokens += len(enc.encode(message['content']))
    return total_tokens

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        pass
