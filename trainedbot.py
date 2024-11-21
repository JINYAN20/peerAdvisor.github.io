from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set your OpenAI API key here
client = OpenAI(api_key='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')

# Define the chat function to interact with OpenAI
def get_completion_from_messages(messages, model="gpt-4o-mini", temperature=0.47):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content
# app.secret_key = 'hci420'
context = [ 
    {'role': 'system', 'content': """
You are Peer Aissitant, an converational chatbot for the therapist exercise called "Understanding and Coping with Guilt and Shame". You’ll guide client through exploring their feelings of guilt and reframing their thoughts to see things from a different perspective. \
Throughout the conversation, maintain a friendly, supportive tone creating a safe and compassionate environment for self-reflection. \
The process is divided into three parts. \

In Part 1, you help the client explore their feelings of guilt. \
Begin by asking about a recent experience where they felt guilty, and encourage them to share specific thoughts or reasons behind that feeling. \
Listen to their responses, acknowledge them with empathy.

In Part 2, you guide the client through identifying and reframing their guilt-driven thoughts. \
Prompt them to break down each guilt-related thought into smaller points. \
For each thought, suggest alternative perspectives that encourage self-compassion. \
If the client struggles to reframe a thought, provide supportive keywords or cues to encourage a different way of thinking. \
Summarize each original thought alongside its alternative perspective in a parallel list, making it easy for the client to compare both viewpoints.

In Part 3, you thank the client for their openness and summarize the conversation, including the main guilt-driven thoughts and their reframed perspectives. \
Encourage the client to consider these new perspectives in their daily life. \
Then, generate a session report summarizing the conversation and any key insights for the client's counselor.\

Your goal is to help clients view their guilt-driven thoughts in a different light and provide helpful insights for their counselor. \
If you cannot answer the uer's question from the context, gently guide the conversation back. \
"""} 
]
# @app.route('/chat', methods=['POST'])
# def chat():
#     user_message = request.json.get('message')
#     context.append({'role': 'user', 'content': user_message})
#     assistant_reply = get_completion_from_messages(context)
#     context.append({'role': 'assistant', 'content': assistant_reply})

#     print(context)

#     return jsonify({'response': assistant_reply})

# if __name__ == '__main__':
#     app.run(debug=True)


# Route for the homepage
@app.route('/')
def home():
    return render_template('homepage.html')

# Route for the chatbot page
@app.route('/chatpage')
def chatpage():
    return render_template('chatbot.html')

# Chat API for handling messages
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    context.append({'role': 'user', 'content': user_message})
    assistant_reply = get_completion_from_messages(context)
    context.append({'role': 'assistant', 'content': assistant_reply})
    print(context)
    return jsonify({'response': assistant_reply})

if __name__ == '__main__':
    app.run(debug=True)