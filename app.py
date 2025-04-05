from flask import Flask, jsonify, render_template, request, Response
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
import datetime
from flask_cors import CORS


client = MongoClient('mongodb://localhost:27017/')
db = client['time_block']
col_task = db['tasks']
col_user = db['users']
col_backlog = db['backlog']


app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return render_template('calendar8.html')


@app.route('/api/get_task', methods=['GET'])
def get_task():

    tasks = col_task.find()
    task_list = []
    for task in tasks:
        task['_id'] = str(task['_id'])
        task_list.append(task)
    return Response(dumps(task_list), mimetype='application/json')


@app.route('/api/add_task', methods=['POST'])
def add_task_using_API():
    data = request.json
    title = data.get('title')
    date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    category = data.get('category')
    description = data.get('description')

    find_backlog = col_backlog.find_one({'name': title})

    if find_backlog:
        col_backlog.delete_one({'name': title})
    print(data)

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    # Combine date with a default time of 00:00:00

    date = datetime.datetime.combine(date, datetime.time.min)
    col_task.insert_one({
        'name': title,
        'date': date,
        'start_time': start_time,
        'end_time': end_time,
        'category': category,
        'description': description,
        'completed': False,
        'created_at': datetime.datetime.now()
    })

    return jsonify({'status': 'success', 'message': 'Task added successfully'})


@app.route('/api/mark_completed', methods=['POST'])
def mark_completed():
    data = request.json
    task_id = data.get('task_id')

    if task_id:
        col_task.update_one({'_id': ObjectId(task_id)}, {
                            '$set': {'completed': True}})
        return jsonify({'status': 'success', 'message': 'Task marked as completed'})
    else:
        return jsonify({'status': 'error', 'message': 'Task ID is required'})


@app.route('/api/mark_incompleted', methods=['POST'])
def mark_incompleted():
    data = request.json
    task_id = data.get('task_id')

    if task_id:
        col_task.update_one({'_id': ObjectId(task_id)}, {
                            '$set': {'completed': False}})
        return jsonify({'status': 'success', 'message': 'Task marked as incompleted'})
    else:
        return jsonify({'status': 'error', 'message': 'Task ID is required'})


@app.route('/api/delete_task', methods=['POST'])
def delete_task():
    data = request.json
    task_id = data.get('task_id')

    if task_id:
        col_task.delete_one({'_id': ObjectId(task_id)})
        return jsonify({'status': 'success', 'message': 'Task deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Task ID is required'})


@app.route('/api/get_task/<date>', methods=['GET'])
def get_task_by_date(date):
    try:
        print('something')
        print(date)
        # Convert the date string to a datetime object
        query_date = datetime.datetime.strptime(date, "%Y-%m-%d")

        # MongoDB stores datetime with time, so we query for the whole day
        start_of_day = datetime.datetime.combine(
            query_date.date(), datetime.time.min)
        end_of_day = datetime.datetime.combine(
            query_date.date(), datetime.time.max)

        # Query for tasks within the date range
        tasks = col_task.find(
            {'date': {'$gte': start_of_day, '$lt': end_of_day}})

        # Convert BSON to JSON-friendly format
        task_list = []
        for task in tasks:
            task['_id'] = str(task['_id'])
            task_list.append(task)

        print(task_list)

        return Response(dumps(task_list), mimetype='application/json')

    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD.'})


@app.route('/api/get_category/<email>', methods=['GET'])
def get_category(email):
    categories = col_user.find_one({'email': email})
    return jsonify({'status': 'success', 'categories': categories['categories']})


@app.route('/api/add_backlog', methods=['POST'])
def add_backlog():
    data = request.json
    title = data.get('title')
    category = data.get('category')

    col_backlog.insert_one({
        'name': title,
        'category': category,
        'created_at': datetime.datetime.now()
    })

    return jsonify({'status': 'success', 'message': 'Backlog added successfully'})


@app.route('/api/get_backlog', methods=['GET'])
def get_backlog():
    backlogs = col_backlog.find()
    backlog_list = []
    for backlog in backlogs:
        backlog['_id'] = str(backlog['_id'])
        backlog_list.append(backlog)
    return Response(dumps(backlog_list), mimetype='application/json')


@app.route('/api/edit_task', methods=['POST'])
def edit_task():
    data = request.get_json()
    task_id = data.get('task_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    category = data.get('category')
    description = data.get('description')

    if task_id:
        col_task.update_one({'_id': ObjectId(task_id)}, {
                            '$set': {'start_time': start_time, 'end_time': end_time, 'category': category, 'description': description}})
        return jsonify({'status': 'success', 'message': 'Task updated successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Task ID is required'})


if __name__ == '__main__':
    app.run(debug=True)
