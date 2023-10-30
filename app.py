from flask import Flask, request, jsonify, render_template


app = Flask(__name__)


@app.route('/', methods=['POST'])
def handle_post_request():
    try:
        # Get and process the JSON data from the POST request
        json_data = request.get_json()
        print(json_data)
        # Handle the JSON data as needed
        return jsonify({"message": "JSON data received"})
    except Exception as e:
        return jsonify({"message": "Error processing JSON data"}), 500


if __name__ == '__main__':
    app.run(debug=True)
