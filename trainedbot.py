from flask import Flask, request, jsonify, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
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
app.secret_key = 'hci420' 
CORS(app)

# Set your OpenAI API key here
client = OpenAI(api_key='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')

# -----------------------------------------Therapist Side-----------------------------------------------#
# Directory to save data
DATA_DIRECTORY = 'client_data'

if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY)

@app.route('/psyc_side', methods=['POST'])
def upload_data():
    try:
        # Get JSON data from the client
        data = request.get_json()
        client_id = data.get('client_id', 'unknown_client')
        
        # Save the data as a JSON file
        file_path = os.path.join(DATA_DIRECTORY, f"{client_id}.json")
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=2)

        return jsonify({"message": "Data uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# -----------------------------------------Therapist Side-----------------------------------------------#



# -----------------------------------------Login+signup Database Storage-----------------------------------------------#
# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False, unique=True)
    last_name = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_counselor = db.Column(db.Boolean, default=False)
    

# Create the database (run once)
with app.app_context():
    db.create_all()

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(first_name=data['first_name'],
                     last_name=data['last_name'],
                     email=data['email'], 
                     password=hashed_password,
                     is_counselor=data['is_counselor'])
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created successfully."}), 201
    except Exception as e:
        db.session.rollback()  # Roll back the failed transaction
        print(f"Error during signup: {str(e)}")  # This will help you debug
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"message": "Email or name already registered!"}), 400
        return jsonify({"message": f"Error during signup: {str(e)}"}), 400

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password, data['password']):
        session['id']=user.id
        session['Fist_name']=user.first_name
        session['Last_name']=user.last_name
        session['is_counselor']=user.is_counselor
        if session['is_counselor']:
            return jsonify({
                "message": "Login successful!",
                "redirect_url": "http://127.0.0.1:5500/psyc_home.html#"
            }), 200
        else:          
            return jsonify({
                "message": "Login successful!",
                "redirect_url": "http://127.0.0.1:5500/home_page.html#"
            }), 200
    return jsonify({"message": "Invalid credentials!"}), 401

# -----------------------------------------Login+signup Database Storage-----------------------------------------------#



# Define the chat function to interact with OpenAI
def get_completion_from_messages(messages, model="gpt-4o-mini", temperature=0.47):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content

# Load Personalized Data
def load_personalized_data(client_id):
    try:
        with open(os.path.join(DATA_DIRECTORY, f"{client_id}.json"), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

global_question = None
global_question_answer =None
# If there are personalized data from couselor side
def update_instructions_with_personalization(base_context, personalized_data):
    if personalized_data:
        global global_question
        tone = ", ".join(personalized_data.get("tone", ["supportive", "friendly"]))
        risky_keywords = personalized_data.get("risky", [])
        risky_keywords_str = ", ".join(risky_keywords) if risky_keywords else "none provided"
        homework_name = personalized_data.get("homework_name")
        description = personalized_data.get("description")
        global_question = personalized_data.get("questions")

        # Append personalized details to the base instructions
        personalized_instructions = f"""
        Keep the tone {tone}. The client is working on a task named '{homework_name}', described as: "{description}". 
        Be mindful of these keywords: {risky_keywords_str}. Guide the client thoughtfully, ensuring sensitivity to their unique situation.
        - Ask the client exact sentence {global_question} one by one provided by his or her counselor after Ask the client: "Do these alternative perspectives change how you feel about your original thoughts?" If the client responds yes (or a similar affirmative answer) . After this, proceed to Part 3
        """
        # Add the personalized instructions to the default system context
        base_context[0]["content"] += personalized_instructions
    else:
        print("No personalized data provided. Using default instructions.") 
    return base_context
# app.secret_key = 'hci420'
context =[ {
    "role": "system",
    "content": f"""
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
- Ask the client: "Do these alternative perspectives change how you feel about your original thoughts?" If the client responds yes (or a similar affirmative answer), proceed to next instruction to ask client questions prepared by the counselors. If the client responds no, repeat the steps in Part 2. 


#### Part 3: Summary
- Encourage the client to consider these new perspectives in their daily life.
- Summarize the conversation, including the main guilt-driven thoughts and their reframed perspectives.
- End with the exact sentence: "Thank you for your openness. Our conversation ends here. Please remember to press the button to leave. It was a pleasure chatting with you today, and I hope I was able to help!" (Do not change this sentence.)
"""
}
]

#print(context)

global_session_data = {
    'context': [],
    'summary': None,
    'Name' : None
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
    # Add personalized context
    client_id = "Claudia Alves" # default value here
    personalized_data = load_personalized_data(client_id) if client_id else None
    update_instructions_with_personalization(context, personalized_data)
    print(global_question)
    print(context)
   
    context.append({'role': 'user', 'content': user_message})
    assistant_reply = get_completion_from_messages(context)
    context.append({'role': 'assistant', 'content': assistant_reply})
    # Check if it's the end of the session
    #end_signal = "Thank you for your openness, do you want to end the conversation?" in assistant_reply
    end_signal = assistant_reply.strip().endswith("I hope I was able to help!")
    specific_question = assistant_reply.strip().endswith(f"{global_question}")
    if specific_question:
         # store exact question from user as a global varaible to couselor
        global global_question_answer
        global_question_answer = user_message
        print("User's answer to the question:", global_question_answer)
       
    if end_signal:
        global_session_data['context'] = context.copy()
        global_session_data['Name'] = client_id
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
    name = global_session_data.get('Name', 'Default Name')
    formatted_name = name.replace(" ", "_") 
    save_dir = os.path.abspath('conversation_summaries')
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(save_dir, f'summary_{timestamp}_{formatted_name}.json')

    try:
        with open(filename, 'w') as f:
            json.dump(summary_json, f, indent=4)
        print(f"Summary saved: {filename}")
    except Exception as e:
        print(f"Error saving summary: {e}")

def generate_history(context):
    """
    Generate a summary from the conversation context.
    """
    # Example of generating a simple summary
    summary = {
        "conversation": context,
        "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
    }
    return summary

def save_history(summary_json):
    """
    Save the summary to a JSON file.
    """
    name = global_session_data.get('Name', 'Default Name')
    formatted_name = name.replace(" ", "_") 
    save_dir = os.path.abspath('conversation_histories')
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(save_dir, f'history_{timestamp}_{formatted_name}.json')

    try:
        with open(filename, 'w') as f:
            json.dump(summary_json, f, indent=4)
        print(f"History saved: {filename}")
    except Exception as e:
        print(f"Error saving history: {e}")


@app.route('/end-conversation', methods=['POST'])
def end_conversation():
    # Get the data from the request
    data = request.get_json()
    name = global_session_data.get('Name', 'Default Name')
    # Print a statement when the user ends the conversation
    #print("User ended the conversation:", data)
    context = global_session_data.get('context', [])
    #print(context)
    #context = session.get('context', [])
    messages = context.copy()
    messages.append(
        {'role': 'system', 'content': f'Generate a session report summarizing the conversation and any key insights for the counselor of the client. '
                                      f'Itemize the guilt thoughts of the client and Provide the exact answer of the user for the question '
                                      f'The fields should be: '
                                      f'1) Client Name: {name} 2) Clients Experience: 3) Guilt-Driven Thoughts: '
                                      f'4) Reframed Perspectives: 5). {global_question} : \n {global_question_answer} 6) Suggestions to Counselor: '}
    )
    
    response = get_completion_from_messages(messages, temperature=0.47)
    #response = global_session_data.get('summary', None)
    print(response)
    print(messages)
    summary = generate_summary(response)
    history = generate_summary(messages)

    # Save the summary
    threading.Thread(target=save_summary, args=(summary,)).start()
    threading.Thread(target=save_history, args=(history,)).start()
    #global_session_data['summary'] = None
    global_session_data['context'] = []
    # Respond back to the client
    return jsonify({"status": "success", "message": "Conversation ended"})

if __name__ == '__main__':
    app.run(debug=True)