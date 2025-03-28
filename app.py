from flask import Flask, jsonify, render_template, request, Response
import pymongo


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


"""
Make code for APIs to: -

1. Insert Data
2. Fetch Data
3. Update Data
4. Mark Data Completed
"""

if __name__ == '__main__':
    app.run(debug=True)