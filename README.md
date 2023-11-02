# openai_chatcompletion_py_client

# OpenAI Chat Completion API Example

This repository demonstrates a simple client-server implementation of the OpenAI Chat Completion API, which utilizes the powerful GPT-3.5 language model to create conversational AI applications. The example consists of a Python Flask server that handles the interaction with the OpenAI API, and a Python client that communicates with the server to carry out the conversation.

## About

The OpenAI Chat Completion API provides an easy way to integrate AI-powered conversational capabilities into applications. The API leverages the GPT-3.5 language model to understand and generate human-like text based on the input it receives.

This project consists of two main components:

- **Server (`/server`):** A Flask application that processes incoming messages from the client, sends them to the OpenAI API, and returns the generated responses. It also handles the session state and conversation logging.

- **Client (`/client`):** A simple command-line interface (CLI) that allows users to send messages to the Flask server and receive responses from the AI.

For more information about the OpenAI Chat Completion API, you can visit the following resources:

- [Playground](https://platform.openai.com/playground)
- [Chat Completions API Guide](https://platform.openai.com/docs/guides/gpt/chat-completions-api)
- [API Reference](https://platform.openai.com/docs/api-reference/chat)

## Features

- Interactive CLI for sending and receiving messages.
- Flask server for API requests and response handling.
- Conversation persistence on both the client and server sides.
- Customizable user identification for conversation logging.

## Setup

To get started with this example:

1. Clone the repository to your local machine.
2. Install the required dependencies by running `pip install -r requirements.txt` in both the `/client` and `/server` directories.
3. Create an `.env` file within the `/server` directory containing your OpenAI API key like so:

OPENAI_API_KEY='your_api_key_here'

4. Start the server by running `python server.py` within the `/server` directory.
5. In a separate terminal, start the client by running `python client.py` within the `/client` directory.
6. Follow the prompts in the client to begin a conversation with the AI.

## Contributions

Contributions to this example are welcome! If you have an improvement or encounter an issue, please feel free to open an issue or submit a pull request.

## License

This project is open-sourced under the MIT License. See the [LICENSE](LICENSE) file for more details.
