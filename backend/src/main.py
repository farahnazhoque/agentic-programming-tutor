from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langgraph_config import compiled_graph

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:5175", "http://localhost:5176"]}})

@app.route("/start_agent/", methods=["POST"])
def start_agent():
    try:
        # Get request data from frontend
        user_input = request.get_json()
        
        # Debugging log
        print("Received request data:", user_input)

        # Validate required fields
        if not user_input:
            return jsonify({"error": "No input data provided"}), 400

        explanation = user_input.get("explanation")
        max_attempts = user_input.get("max_attempts", 3)
        language = user_input.get("language", "Python")

        # Validate explanation field
        if not explanation:
            return jsonify({"error": "Explanation field is required"}), 400

        # Initialize state dictionary (not object)
        state = {
            "explanation": explanation,
            "max_attempts": max_attempts,
            "language": language,
            "user_attempts": 0,
            "user_code": "",
            "correct_output": "",
            "hints_given": [],
            "summary": "",
            "boilerplate_code": "",
            "is_correct": False
        }

        # Run compiled state graph
        result = compiled_graph.invoke(state)  # ✅ Use compiled graph

        # Log output
        print("Processing result:", result)

        # Return JSON response
        return jsonify(result)

    except Exception as e:
        # Log detailed error traceback
        import traceback
        print("Error occurred:", str(e))
        print("Traceback:", traceback.format_exc())
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5015, debug=True)
