from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify(message="Hello from Flask on Vercel!")

# For Vercel Python serverless function
def handler(environ, start_response):
    return app(environ, start_response)
