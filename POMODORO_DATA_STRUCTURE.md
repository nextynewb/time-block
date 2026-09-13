# Pomodoro Data Tracking Structure

## **📊 Database Schema**

Each Pomodoro session is stored in MongoDB's `col_pomodoro` collection with the following comprehensive data structure:

### **Core Session Data**
```javascript
{
  _id: ObjectId,                        // Unique session identifier
  session_type: String,                 // "work", "short_break", "long_break"
  planned_duration_minutes: Number,     // Intended session length (usually 25)
  actual_duration_minutes: Number,      // Real duration (excluding pauses)
  started_at: DateTime,                 // Session start timestamp
  completed_at: DateTime,               // Session end timestamp
  status: String,                       // "active", "paused", "completed", "abandoned"
}
```

### **Performance Tracking**
```javascript
{
  completion_percentage: Number,        // How much of planned duration was completed
  focus_score: Number,                  // User-rated focus quality (1-5 scale)
  interruptions_count: Number,         // Number of logged interruptions
  notes: String,                        // User session notes
}
```

### **Pause/Resume Analytics**
```javascript
{
  paused_at: DateTime,                  // When session was last paused
  resumed_at: DateTime,                 // When session was last resumed
  pause_count: Number,                  // Total number of pauses
  total_pause_duration: Number,         // Total pause time in minutes
}
```

### **Analytics Dimensions**
```javascript
{
  // Time-based analytics
  hour_of_day: Number,                  // 0-23 for productivity patterns
  day_of_week: String,                  // "Monday", "Tuesday", etc.
  date: Date,                           // For daily tracking
  week_number: Number,                  // ISO week number
  month: Number,                        // 1-12
  year: Number,                         // Full year

  // Metadata
  task_id: String,                      // Optional link to scheduled task
  abandon_reason: String,               // Why session was abandoned
  created_at: DateTime,                 // Record creation timestamp
  updated_at: DateTime,                 // Last update timestamp
}
```

## **📈 Data Visualization Opportunities**

### **1. Productivity Trends**
- **Daily Progress**: Sessions completed, focus time, completion rates
- **Weekly Patterns**: Best productive days, consistency
- **Monthly Growth**: Long-term productivity trends
- **Hourly Heat Maps**: Best focus hours throughout the day

### **2. Performance Analytics**
- **Focus Score Trends**: Quality of focus over time
- **Completion Rates**: Percentage of sessions completed vs abandoned
- **Session Length Analysis**: Actual vs planned durations
- **Interruption Patterns**: Frequency and impact on focus

### **3. Behavioral Insights**
- **Pause Behavior**: How often users pause and for how long
- **Best Performing Hours**: When user is most productive
- **Session Notes Analysis**: Common themes in successful sessions
- **Streak Tracking**: Consecutive days with completed pomodoros

### **4. Advanced Analytics**
- **Focus Efficiency**: Correlation between interruptions and focus scores
- **Optimal Session Length**: Finding user's sweet spot
- **Break Patterns**: Effectiveness of different break durations
- **Task Correlation**: Which types of tasks have better completion rates

## **🔌 API Endpoints for Analytics**

### **Real-time Stats**
- `GET /api/get_pomodoro_stats?range=today|week|month|all`
- Returns: Sessions, completion rates, focus time, streaks

### **Detailed Analytics**
- `GET /api/get_pomodoro_analytics?days=30`
- Returns: Daily/hourly/weekly breakdown for visualization

### **Session Management**
- `POST /api/start_pomodoro` - Start new session
- `POST /api/pause_pomodoro` - Pause active session
- `POST /api/resume_pomodoro` - Resume paused session
- `POST /api/complete_pomodoro` - Complete with focus score
- `POST /api/abandon_pomodoro` - Mark as abandoned

## **📊 Sample Analytics Queries**

### **Daily Productivity**
```javascript
// Get productivity data for last 30 days
db.col_pomodoro.aggregate([
  {
    $match: {
      created_at: { $gte: new Date(Date.now() - 30*24*60*60*1000) },
      status: "completed"
    }
  },
  {
    $group: {
      _id: "$date",
      sessions: { $sum: 1 },
      total_focus_time: { $sum: "$actual_duration_minutes" },
      avg_focus_score: { $avg: "$focus_score" }
    }
  }
])
```

### **Best Productive Hours**
```javascript
// Find most productive hours
db.col_pomodoro.aggregate([
  {
    $match: { status: "completed" }
  },
  {
    $group: {
      _id: "$hour_of_day",
      sessions: { $sum: 1 },
      avg_focus_score: { $avg: "$focus_score" }
    }
  },
  { $sort: { sessions: -1 } }
])
```

### **Focus Score Trends**
```javascript
// Track focus improvement over time
db.col_pomodoro.aggregate([
  {
    $match: { 
      status: "completed",
      focus_score: { $exists: true }
    }
  },
  {
    $group: {
      _id: { 
        year: "$year", 
        month: "$month" 
      },
      avg_focus_score: { $avg: "$focus_score" },
      sessions: { $sum: 1 }
    }
  }
])
```

## **🎯 Future Dashboard Features**

1. **Progress Cards**: Today's stats with trend indicators
2. **Heat Map Calendar**: Daily productivity visualization
3. **Focus Score Graph**: Trend line showing improvement
4. **Hourly Productivity Chart**: Bar chart of best hours
5. **Weekly Performance**: Radar chart of daily patterns
6. **Streak Counter**: Current and longest streaks
7. **Interruption Analysis**: Impact on productivity
8. **Session Distribution**: Pie chart of completed vs abandoned
9. **Personal Records**: Best focus scores, longest streaks
10. **Goal Tracking**: Daily/weekly targets vs actual

## **🔮 Advanced Analytics Ideas**

- **Machine Learning**: Predict optimal session times
- **Correlation Analysis**: Environment factors vs performance
- **Habit Formation**: Track consistency and streak building
- **Personal Insights**: Automated weekly summary reports
- **Goal Recommendations**: AI-suggested improvements
- **Social Features**: Compare with team/friends (anonymized)

This comprehensive data structure enables rich analytics and personalized insights to help users optimize their productivity and focus patterns. 