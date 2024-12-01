from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from openai import OpenAI
import json
import os
from datetime import datetime
from threading import Thread
import threading
import flask.cli


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key' 
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
context =[ {
    "role": "system",
    "content": """
You are Peer Assistant, a conversational chatbot for the therapist exercise called "Understanding and Coping with Guilt and Shame." You’ll guide the client through exploring their feelings of guilt and reframing their thoughts to see things from a different perspective. 
Throughout the conversation, maintain a friendly, supportive tone, creating a safe and compassionate environment for self-reflection.

### General Rules:
1. Ask **exactly one question** per turn. You are not allowed to ask follow-up questions in the same turn.
2. Respond concisely with empathy, reflecting on the client’s previous response.
3. Do not repeat the same question unless asked by the client.
4. If you cannot answer the uer's question from the context, gently guide the conversation back.

### Conversation Structure:
#### Part 1: Exploring Feelings of Guilt
- Begin by asking about a recent experience where they felt guilty.
- After their response, acknowledge their feelings with empathy and ask ONE clarifying question about their thoughts or reasons behind the guilt.

#### Part 2: Reframing Guilt-Driven Thoughts
- For each guilt-related thought, prompt the client to break it into smaller points.
- For each thought, suggest alternative perspectives that encourage self-compassion.
- Respond empathetically. Remember, ask ONE question to encourage self-reflection.
- If the client struggles to reframe a thought, provide supportive keywords or cues to encourage a different way of thinking.
- Summarize each original thought alongside its alternative perspective in a parallel list, making it easy for the client to compare both viewpoints in detail. 
- Ask the client: "Do these alternative perspectives change how you feel about your original thoughts?" If the client responds yes (or a similar affirmative answer), proceed to Part 3. If the client responds no, repeat the steps in Part 2. 


#### Part 3: Summary
- Encourage the client to consider these new perspectives in their daily life.
- Summarize the conversation, including the main guilt-driven thoughts and their reframed perspectives.
- End with the exact sentence: "Thank you for your openness. Our conversation ends here. Please remember to press the button to leave. It was a pleasure chatting with you today, and I hope I was able to help!" (Do not change this sentence.)
"""
}
]

global_session_data = {
    'context': [],
    'summary': None
}


# Route for the homepage
@app.route('/')
def home():
    return render_template('homepage.html')

# Route for the chatbot page
@app.route('/chatpage')
def chatpage():
    return render_template('chat_page.html')


# Chat API for handling messages
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    context.append({'role': 'user', 'content': user_message})
    assistant_reply = get_completion_from_messages(context)
    context.append({'role': 'assistant', 'content': assistant_reply})
    # Check if it's the end of the session
    #end_signal = "Thank you for your openness, do you want to end the conversation?" in assistant_reply
    end_signal = assistant_reply.strip().endswith("I hope I was able to help!")
    if end_signal:
        global_session_data['context'] = context.copy()
    #     summary = generate_summary(response)
    #     #threading.Thread(target=save_summary, args=(summary,)).start()
    #     #save_summary(summary)
    #     print(response)
    #     print("Summary generated and saved.")


    #return jsonify({'response': assistant_reply})
    return jsonify({'response': assistant_reply, 'end_signal': end_signal})


def generate_summary(context):
    """
    Generate a summary from the conversation context.
    """
    # Example of generating a simple summary
    summary = {
        "conversation": context,
        "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
    }
    return summary

def save_summary(summary_json):
    """
    Save the summary to a JSON file.
    """
    save_dir = os.path.abspath('conversation_summaries')
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(save_dir, f'summary_{timestamp}.json')

    try:
        with open(filename, 'w') as f:
            json.dump(summary_json, f, indent=4)
        print(f"Summary saved: {filename}")
    except Exception as e:
        print(f"Error saving summary: {e}")


@app.route('/end-conversation', methods=['POST'])
def end_conversation():
    # Get the data from the request
    data = request.get_json()
    
    # Print a statement when the user ends the conversation
    print("User ended the conversation:", data)
    context = global_session_data.get('context', [])
    print(context)
    #context = session.get('context', [])
    messages = context.copy()
    messages.append(
        {'role': 'system', 'content': 'Generate a session report summarizing the conversation and any key insights for the counselor of the client. '
                                      'Itemize the guilt thoughts of the client and '
                                      'The fields should be: '
                                      '1) Client Name: 2) Client’s Experience: 3) Guilt-Driven Thoughts: '
                                      '4) Reframed Perspectives: 5) Suggestions to Counselor:'}
    )
    
    response = get_completion_from_messages(messages, temperature=0.47)
    #response = global_session_data.get('summary', None)
    print(response)
    summary = generate_summary(response)

    # Save the summary
    threading.Thread(target=save_summary, args=(summary,)).start()
    #global_session_data['summary'] = None
    global_session_data['context'] = []
    # Respond back to the client
    return jsonify({"status": "success", "message": "Conversation ended"})

if __name__ == '__main__':
    app.run(debug=True)