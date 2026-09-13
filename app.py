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
col_notes = db['notes']
col_pomodoro = db['pomodoro_sessions']
col_quick_links = db['quick_links']


app = Flask(__name__)

# Configure CORS to allow requests from production domain
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://time.rahmanrom.my",
            "http://localhost:*",
            "http://127.0.0.1:*"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


@app.route('/')
def index():
    return render_template('calendar_new.html')

@app.route('/wow')
def calendar_wow():
    return render_template('calendar_motivational.html')


@app.route('/wow')
def wow_calendar():
    return render_template('calendar_wow.html')

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


@app.route('/api/delete_backlog', methods=['POST'])
def delete_backlog():
    """Delete a backlog item"""
    try:
        data = request.json
        backlog_id = data.get('backlog_id')
        
        if not backlog_id:
            return jsonify({'status': 'error', 'message': 'Backlog ID is required'})
        
        result = col_backlog.delete_one({'_id': ObjectId(backlog_id)})
        
        if result.deleted_count > 0:
            return jsonify({'status': 'success', 'message': 'Backlog deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Backlog not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


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


# ===== NOTES API ENDPOINTS =====

@app.route('/api/get_notes', methods=['GET'])
def get_notes():
    """Get all sticky notes"""
    try:
        notes = col_notes.find().sort('created_at', -1)  # Sort by newest first
        note_list = []
        for note in notes:
            note['_id'] = str(note['_id'])
            note_list.append(note)
        return Response(dumps(note_list), mimetype='application/json')
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/add_note', methods=['POST'])
def add_note():
    """Add a new sticky note"""
    try:
        data = request.json
        content = data.get('content')
        color = data.get('color', 'yellow')  # Default to yellow
        note_type = data.get('note_type', 'text')  # Default to text
        todos = data.get('todos', [])  # Default to empty array
        
        if not content or not content.strip():
            return jsonify({'status': 'error', 'message': 'Note content is required'})
        
        note_doc = {
            'content': content.strip(),
            'color': color,
            'note_type': note_type,
            'todos': todos,
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }
        
        result = col_notes.insert_one(note_doc)
        
        return jsonify({
            'status': 'success', 
            'message': 'Note added successfully',
            'note_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/edit_note', methods=['POST'])
def edit_note():
    """Edit an existing sticky note"""
    try:
        data = request.json
        note_id = data.get('note_id')
        content = data.get('content')
        color = data.get('color')
        note_type = data.get('note_type')
        todos = data.get('todos')
        
        if not note_id:
            return jsonify({'status': 'error', 'message': 'Note ID is required'})
        
        if not content or not content.strip():
            return jsonify({'status': 'error', 'message': 'Note content is required'})
        
        # Build update document with only provided fields
        update_fields = {
            'content': content.strip(),
            'updated_at': datetime.datetime.now()
        }
        
        if color is not None:
            update_fields['color'] = color
        if note_type is not None:
            update_fields['note_type'] = note_type
        if todos is not None:
            update_fields['todos'] = todos
        
        result = col_notes.update_one(
            {'_id': ObjectId(note_id)}, 
            {'$set': update_fields}
        )
        
        if result.matched_count > 0:
            return jsonify({'status': 'success', 'message': 'Note updated successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Note not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/delete_note', methods=['POST'])
def delete_note():
    """Delete a sticky note"""
    try:
        data = request.json
        note_id = data.get('note_id')
        
        if not note_id:
            return jsonify({'status': 'error', 'message': 'Note ID is required'})
        
        result = col_notes.delete_one({'_id': ObjectId(note_id)})
        
        if result.deleted_count > 0:
            return jsonify({'status': 'success', 'message': 'Note deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Note not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# ===== POMODORO SESSION API ENDPOINTS =====

@app.route('/api/start_pomodoro', methods=['POST'])
def start_pomodoro():
    """Start a new pomodoro session with comprehensive tracking"""
    try:
        print("🍅 Starting pomodoro session...")
        data = request.json
        print(f"📥 Received data: {data}")
        
        session_type = data.get('session_type', 'work')  # work, short_break, long_break
        duration_minutes = data.get('duration_minutes', 25)
        task_id = data.get('task_id', None)  # Optional: link to specific task
        
        now = datetime.datetime.now()
        print(f"⏰ Current time: {now}")
        
        session_doc = {
            'session_type': session_type,
            'planned_duration_minutes': duration_minutes,
            'actual_duration_minutes': None,
            'time_remaining_seconds': duration_minutes * 60,  # Track remaining time
            'started_at': now.isoformat(),  # Convert to ISO string
            'completed_at': None,
            'paused_at': None,
            'resumed_at': None,
            'last_updated_at': now.isoformat(),  # Convert to ISO string
            'status': 'active',  # active, paused, completed, abandoned
            'completion_percentage': 0,
            'interruptions_count': 0,
            'focus_score': None,  # 1-5 scale, set when session ends
            'task_id': task_id,
            'notes': '',
            # Analytics fields
            'hour_of_day': now.hour,
            'day_of_week': now.strftime('%A'),
            'date': now.date().isoformat(),  # Convert to ISO string
            'week_number': now.isocalendar()[1],
            'month': now.month,
            'year': now.year,
            # Performance tracking
            'pause_count': 0,
            'total_pause_duration': 0,  # in minutes
            'created_at': now.isoformat(),  # Convert to ISO string
            'updated_at': now.isoformat()  # Convert to ISO string
        }
        
        print(f"📄 Session document: {session_doc}")
        print(f"💾 Attempting to insert into collection: {col_pomodoro}")
        
        result = col_pomodoro.insert_one(session_doc)
        print(f"✅ Insert result: {result}")
        print(f"🆔 Inserted ID: {result.inserted_id}")
        
        # Verify the insertion
        verification = col_pomodoro.find_one({'_id': result.inserted_id})
        print(f"🔍 Verification query result: {verification}")
        
        return jsonify({
            'status': 'success',
            'message': 'Pomodoro session started',
            'session_id': str(result.inserted_id)
        })
    except Exception as e:
        print(f"❌ Error in start_pomodoro: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/update_pomodoro', methods=['POST'])
def update_pomodoro():
    """Update pomodoro session with current progress (real-time tracking)"""
    try:
        data = request.json
        session_id = data.get('session_id')
        time_remaining_seconds = data.get('time_remaining_seconds')
        interruptions_count = data.get('interruptions_count', 0)
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID is required'})
        
        now = datetime.datetime.now()
        
        # Calculate completion percentage
        session = col_pomodoro.find_one({'_id': ObjectId(session_id)})
        if not session:
            return jsonify({'status': 'error', 'message': 'Session not found'})
        
        planned_duration_seconds = session.get('planned_duration_minutes', 25) * 60
        completion_percentage = ((planned_duration_seconds - time_remaining_seconds) / planned_duration_seconds) * 100
        
        result = col_pomodoro.update_one(
            {'_id': ObjectId(session_id)},
            {
                '$set': {
                    'time_remaining_seconds': time_remaining_seconds,
                    'completion_percentage': round(completion_percentage, 2),
                    'interruptions_count': interruptions_count,
                    'last_updated_at': now.isoformat(),  # Convert to ISO string
                    'updated_at': now.isoformat()  # Convert to ISO string
                }
            }
        )
        
        if result.matched_count > 0:
            return jsonify({'status': 'success', 'message': 'Session updated'})
        else:
            return jsonify({'status': 'error', 'message': 'Session not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/get_active_session', methods=['GET'])
def get_active_session():
    """Get current active or paused pomodoro session"""
    try:
        # Find the most recent active or paused session
        session = col_pomodoro.find_one(
            {'status': {'$in': ['active', 'paused']}},
            sort=[('created_at', -1)]
        )
        
        if session:
            session['_id'] = str(session['_id'])
            return jsonify({
                'status': 'success',
                'session': session
            })
        else:
            return jsonify({
                'status': 'success',
                'session': None
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/pause_pomodoro', methods=['POST'])
def pause_pomodoro():
    """Pause a pomodoro session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID is required'})
        
        now = datetime.datetime.now()
        
        result = col_pomodoro.update_one(
            {'_id': ObjectId(session_id)},
            {
                '$set': {
                    'status': 'paused',
                    'paused_at': now.isoformat(),  # Convert to ISO string
                    'updated_at': now.isoformat()  # Convert to ISO string
                },
                '$inc': {
                    'pause_count': 1
                }
            }
        )
        
        if result.matched_count > 0:
            return jsonify({'status': 'success', 'message': 'Pomodoro session paused'})
        else:
            return jsonify({'status': 'error', 'message': 'Session not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/resume_pomodoro', methods=['POST'])
def resume_pomodoro():
    """Resume a paused pomodoro session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID is required'})
        
        now = datetime.datetime.now()
        
        # Get current session to calculate pause duration
        session = col_pomodoro.find_one({'_id': ObjectId(session_id)})
        if not session:
            return jsonify({'status': 'error', 'message': 'Session not found'})
        
        pause_duration = 0
        if session.get('paused_at'):
            # Parse the ISO format string back to datetime
            paused_at = datetime.datetime.fromisoformat(session['paused_at'])
            pause_duration = (now - paused_at).total_seconds() / 60  # in minutes
        
        result = col_pomodoro.update_one(
            {'_id': ObjectId(session_id)},
            {
                '$set': {
                    'status': 'active',
                    'resumed_at': now.isoformat(),  # Convert to ISO string
                    'updated_at': now.isoformat(),  # Convert to ISO string
                    'total_pause_duration': session.get('total_pause_duration', 0) + pause_duration
                }
            }
        )
        
        if result.matched_count > 0:
            return jsonify({'status': 'success', 'message': 'Pomodoro session resumed'})
        else:
            return jsonify({'status': 'error', 'message': 'Session not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/complete_pomodoro', methods=['POST'])
def complete_pomodoro():
    """Complete a pomodoro session with detailed tracking"""
    try:
        data = request.json
        session_id = data.get('session_id')
        focus_score = data.get('focus_score', 3)  # 1-5 scale
        notes = data.get('notes', '')
        interruptions = data.get('interruptions_count', 0)
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID is required'})
        
        # Get session to calculate actual duration
        session = col_pomodoro.find_one({'_id': ObjectId(session_id)})
        if not session:
            return jsonify({'status': 'error', 'message': 'Session not found'})
        
        now = datetime.datetime.now()
        started_at = datetime.datetime.fromisoformat(session['started_at'])  # Parse ISO string
        
        # Calculate actual duration (excluding pause time)
        total_duration = (now - started_at).total_seconds() / 60  # in minutes
        pause_duration = session.get('total_pause_duration', 0)
        actual_duration = total_duration - pause_duration
        
        # Calculate completion percentage
        planned_duration = session.get('planned_duration_minutes', 25)
        completion_percentage = min(100, (actual_duration / planned_duration) * 100)
        
        result = col_pomodoro.update_one(
            {'_id': ObjectId(session_id)},
            {
                '$set': {
                    'status': 'completed',
                    'completed_at': now.isoformat(),  # Convert to ISO string
                    'actual_duration_minutes': round(actual_duration, 2),
                    'completion_percentage': round(completion_percentage, 2),
                    'focus_score': focus_score,
                    'notes': notes,
                    'interruptions_count': interruptions,
                    'updated_at': now.isoformat()  # Convert to ISO string
                }
            }
        )
        
        if result.matched_count > 0:
            return jsonify({'status': 'success', 'message': 'Pomodoro session completed'})
        else:
            return jsonify({'status': 'error', 'message': 'Session not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/abandon_pomodoro', methods=['POST'])
def abandon_pomodoro():
    """Mark a pomodoro session as abandoned"""
    try:
        data = request.json
        session_id = data.get('session_id')
        reason = data.get('reason', 'user_cancelled')  # user_cancelled, interrupted, etc.
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID is required'})
        
        # Get session to calculate partial duration
        session = col_pomodoro.find_one({'_id': ObjectId(session_id)})
        if not session:
            return jsonify({'status': 'error', 'message': 'Session not found'})
        
        now = datetime.datetime.now()
        started_at = datetime.datetime.fromisoformat(session['started_at'])  # Parse ISO string
        
        # Calculate partial duration
        total_duration = (now - started_at).total_seconds() / 60
        pause_duration = session.get('total_pause_duration', 0)
        actual_duration = total_duration - pause_duration
        
        planned_duration = session.get('planned_duration_minutes', 25)
        completion_percentage = (actual_duration / planned_duration) * 100
        
        result = col_pomodoro.update_one(
            {'_id': ObjectId(session_id)},
            {
                '$set': {
                    'status': 'abandoned',
                    'completed_at': now.isoformat(),  # Convert to ISO string
                    'actual_duration_minutes': round(actual_duration, 2),
                    'completion_percentage': round(completion_percentage, 2),
                    'abandon_reason': reason,
                    'updated_at': now.isoformat()  # Convert to ISO string
                }
            }
        )
        
        if result.matched_count > 0:
            return jsonify({'status': 'success', 'message': 'Pomodoro session abandoned'})
        else:
            return jsonify({'status': 'error', 'message': 'Session not found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/get_pomodoro_stats', methods=['GET'])
def get_pomodoro_stats():
    """Get comprehensive pomodoro statistics"""
    try:
        # Get date range (default to today, but can accept query params)
        date_range = request.args.get('range', 'today')  # today, week, month, all
        
        now = datetime.datetime.now()
        
        if date_range == 'today':
            start_date = datetime.datetime.combine(now.date(), datetime.time.min)
            end_date = datetime.datetime.combine(now.date(), datetime.time.max)
        elif date_range == 'week':
            days_since_monday = now.weekday()
            start_date = now - datetime.timedelta(days=days_since_monday)
            start_date = datetime.datetime.combine(start_date.date(), datetime.time.min)
            end_date = start_date + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
        elif date_range == 'month':
            start_date = datetime.datetime.combine(now.replace(day=1).date(), datetime.time.min)
            end_date = now
        else:  # all time
            start_date = datetime.datetime.min
            end_date = now
        
        # Build query with ISO format strings
        query = {
            'created_at': {
                '$gte': start_date.isoformat(),  # Convert to ISO string
                '$lt': end_date.isoformat()  # Convert to ISO string
            }
        }
        
        # Get all sessions in range
        sessions = list(col_pomodoro.find(query))
        
        # Calculate statistics
        total_sessions = len(sessions)
        completed_sessions = len([s for s in sessions if s.get('status') == 'completed'])
        abandoned_sessions = len([s for s in sessions if s.get('status') == 'abandoned'])
        
        # Focus time calculation
        total_focus_time = sum(s.get('actual_duration_minutes', 0) for s in sessions if s.get('status') == 'completed')
        
        # Average session length
        avg_session_length = 0
        if completed_sessions > 0:
            avg_session_length = total_focus_time / completed_sessions
        
        # Completion rate
        completion_rate = 0
        if total_sessions > 0:
            completion_rate = (completed_sessions / total_sessions) * 100
        
        # Average focus score
        focus_scores = [s.get('focus_score') for s in sessions if s.get('focus_score') is not None]
        avg_focus_score = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        
        # Best productive hour
        hour_stats = {}
        for session in sessions:
            if session.get('status') == 'completed':
                hour = session.get('hour_of_day', 0)
                if hour not in hour_stats:
                    hour_stats[hour] = {'count': 0, 'total_duration': 0}
                hour_stats[hour]['count'] += 1
                hour_stats[hour]['total_duration'] += session.get('actual_duration_minutes', 0)
        
        best_hour = None
        if hour_stats:
            best_hour = max(hour_stats.keys(), key=lambda h: hour_stats[h]['count'])
        
        # Streak calculation (consecutive days with at least 1 completed pomodoro)
        current_streak = calculate_current_streak()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'abandoned_sessions': abandoned_sessions,
                'completion_rate': round(completion_rate, 1),
                'total_focus_time_minutes': round(total_focus_time, 1),
                'total_focus_time_hours': round(total_focus_time / 60, 1),
                'avg_session_length_minutes': round(avg_session_length, 1),
                'avg_focus_score': round(avg_focus_score, 1),
                'best_productive_hour': best_hour,
                'current_streak_days': current_streak,
                'date_range': date_range
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/get_pomodoro_analytics', methods=['GET'])
def get_pomodoro_analytics():
    """Get detailed analytics data for visualization"""
    try:
        # Get date range
        days = int(request.args.get('days', 30))  # Last 30 days by default
        
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Get sessions in range
        sessions = list(col_pomodoro.find({
            'created_at': {'$gte': start_date, '$lt': end_date}
        }))
        
        # Daily productivity data
        daily_data = {}
        for session in sessions:
            date_str = session['date'].strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'completed': 0,
                    'abandoned': 0,
                    'total_focus_time': 0,
                    'avg_focus_score': 0,
                    'focus_scores': []
                }
            
            if session.get('status') == 'completed':
                daily_data[date_str]['completed'] += 1
                daily_data[date_str]['total_focus_time'] += session.get('actual_duration_minutes', 0)
                if session.get('focus_score'):
                    daily_data[date_str]['focus_scores'].append(session['focus_score'])
            elif session.get('status') == 'abandoned':
                daily_data[date_str]['abandoned'] += 1
        
        # Calculate average focus scores
        for date_data in daily_data.values():
            if date_data['focus_scores']:
                date_data['avg_focus_score'] = sum(date_data['focus_scores']) / len(date_data['focus_scores'])
            del date_data['focus_scores']  # Remove raw scores from response
        
        # Hourly productivity data
        hourly_data = {}
        for hour in range(24):
            hourly_data[hour] = {'hour': hour, 'completed': 0, 'total_focus_time': 0}
        
        for session in sessions:
            if session.get('status') == 'completed':
                hour = session.get('hour_of_day', 0)
                hourly_data[hour]['completed'] += 1
                hourly_data[hour]['total_focus_time'] += session.get('actual_duration_minutes', 0)
        
        # Weekly patterns
        weekly_data = {}
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            weekly_data[day] = {'day': day, 'completed': 0, 'total_focus_time': 0}
        
        for session in sessions:
            if session.get('status') == 'completed':
                day = session.get('day_of_week', 'Monday')
                weekly_data[day]['completed'] += 1
                weekly_data[day]['total_focus_time'] += session.get('actual_duration_minutes', 0)
        
        return jsonify({
            'status': 'success',
            'analytics': {
                'daily_data': list(daily_data.values()),
                'hourly_data': list(hourly_data.values()),
                'weekly_data': list(weekly_data.values()),
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'days': days
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


def calculate_current_streak():
    """Calculate current consecutive days streak"""
    try:
        today = datetime.datetime.now().date()
        
        # Check if user completed at least one pomodoro today
        today_sessions = col_pomodoro.count_documents({
            'date': today,
            'status': 'completed'
        })
        
        streak = 0
        current_date = today
        
        # If no sessions today, start from yesterday
        if today_sessions == 0:
            current_date = today - datetime.timedelta(days=1)
        else:
            streak = 1
            current_date = today - datetime.timedelta(days=1)
        
        # Count backward until we find a day with no completed sessions
        while True:
            day_sessions = col_pomodoro.count_documents({
                'date': current_date,
                'status': 'completed'
            })
            
            if day_sessions == 0:
                break
            
            streak += 1
            current_date -= datetime.timedelta(days=1)
            
            # Prevent infinite loop - max 365 days
            if streak >= 365:
                break
        
        return streak
    except Exception as e:
        print(f"Error calculating streak: {e}")
        return 0


# ===== QUICK LINKS API ENDPOINTS =====

@app.route('/api/get_quick_links', methods=['GET'])
def get_quick_links():
    """Get all quick links sorted by usage count and category"""
    try:
        # Get all quick links
        links = list(col_quick_links.find())
        
        # Convert ObjectId to string for JSON serialization
        for link in links:
            link['_id'] = str(link['_id'])
        
        # Sort by usage count (descending) and then by name
        links.sort(key=lambda x: (-x.get('usage_count', 0), x.get('name', '')))
        
        return jsonify(links)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/add_quick_link', methods=['POST'])
def add_quick_link():
    """Add a new quick link"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'General')
        icon = data.get('icon', '')
        
        if not name or not url:
            return jsonify({'status': 'error', 'message': 'Name and URL are required'})
        
        # Auto-add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check if link already exists
        existing_link = col_quick_links.find_one({'name': name})
        if existing_link:
            return jsonify({'status': 'error', 'message': 'Link with this name already exists'})
        
        # Create new link
        new_link = {
            'name': name,
            'url': url,
            'description': description,
            'category': category,
            'icon': icon,
            'usage_count': 0,
            'created_at': datetime.datetime.now(),
            'last_used': None
        }
        
        result = col_quick_links.insert_one(new_link)
        
        return jsonify({
            'status': 'success',
            'message': 'Quick link added successfully',
            'link_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/update_quick_link', methods=['POST'])
def update_quick_link():
    """Update an existing quick link"""
    try:
        data = request.json
        link_id = data.get('link_id')
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'General')
        icon = data.get('icon', '')
        
        if not link_id or not name or not url:
            return jsonify({'status': 'error', 'message': 'Link ID, name, and URL are required'})
        
        # Auto-add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check if another link with the same name exists
        existing_link = col_quick_links.find_one({
            'name': name,
            '_id': {'$ne': ObjectId(link_id)}
        })
        if existing_link:
            return jsonify({'status': 'error', 'message': 'Another link with this name already exists'})
        
        # Update the link
        update_data = {
            'name': name,
            'url': url,
            'description': description,
            'category': category,
            'icon': icon,
            'updated_at': datetime.datetime.now()
        }
        
        result = col_quick_links.update_one(
            {'_id': ObjectId(link_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'status': 'error', 'message': 'Link not found'})
        
        return jsonify({
            'status': 'success',
            'message': 'Quick link updated successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/delete_quick_link', methods=['POST'])
def delete_quick_link():
    """Delete a quick link"""
    try:
        data = request.json
        link_id = data.get('link_id')
        
        if not link_id:
            return jsonify({'status': 'error', 'message': 'Link ID is required'})
        
        result = col_quick_links.delete_one({'_id': ObjectId(link_id)})
        
        if result.deleted_count == 0:
            return jsonify({'status': 'error', 'message': 'Link not found'})
        
        return jsonify({
            'status': 'success',
            'message': 'Quick link deleted successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/track_link_usage', methods=['POST'])
def track_link_usage():
    """Track usage of a quick link"""
    try:
        data = request.json
        link_id = data.get('link_id')
        
        if not link_id:
            return jsonify({'status': 'error', 'message': 'Link ID is required'})
        
        # Increment usage count and update last used timestamp
        result = col_quick_links.update_one(
            {'_id': ObjectId(link_id)},
            {
                '$inc': {'usage_count': 1},
                '$set': {'last_used': datetime.datetime.now()}
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'status': 'error', 'message': 'Link not found'})
        
        return jsonify({
            'status': 'success',
            'message': 'Usage tracked successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/get_quick_links_by_category', methods=['GET'])
def get_quick_links_by_category():
    """Get quick links grouped by category"""
    try:
        # Aggregate links by category
        pipeline = [
            {
                '$group': {
                    '_id': '$category',
                    'links': {
                        '$push': {
                            'id': {'$toString': '$_id'},
                            'name': '$name',
                            'url': '$url',
                            'description': '$description',
                            'icon': '$icon',
                            'usage_count': '$usage_count',
                            'last_used': '$last_used'
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}  # Sort categories alphabetically
            }
        ]
        
        result = list(col_quick_links.aggregate(pipeline))
        
        # Format response
        categories = {}
        for item in result:
            category = item['_id']
            # Sort links within each category by usage count
            links = sorted(item['links'], key=lambda x: -x.get('usage_count', 0))
            categories[category] = {
                'category': category,
                'links': links,
                'count': item['count']
            }
        
        return jsonify({
            'status': 'success',
            'categories': categories
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
