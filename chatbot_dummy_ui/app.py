from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Configuration - Update these with your actual API details
API_URL = "http://localhost:5001/api/chat"  # Replace with your actual API URL
ORG_ID = 67
USER_ID = 121

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({
                'response': 'Please enter a question',
                'status': 'error'
            }), 400
        
        # Prepare payload for your API
        payload = {
            'question': question,
            'org_id': ORG_ID,
            'user_id': USER_ID
        }
        
        # Call your API
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        # Get the response from your API
        api_response = response.json()
        
        return jsonify(api_response)
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'response': f'Error connecting to API: {str(e)}',
            'status': 'error'
        }), 500
    
    except Exception as e:
        return jsonify({
            'response': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)