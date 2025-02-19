from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/gsi', methods=['POST'])
def gsi():
    data = request.json
    # Process GSI data here
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(port=3000)