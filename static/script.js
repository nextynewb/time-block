$(document).ready(function () {
  // Initialize the schedule
  initializeSchedule();

  // Fetch categories first, then fetch tasks
  fetchCategories().then(() => {
    fetchTasks("2025-03-30");
  });

  // Set up current time indicator
  updateCurrentTimeIndicator();
  setInterval(updateCurrentTimeIndicator, 60000); // Update every minute

  // Set up date navigation
  $("#prev-day").on("click", navigateToPreviousDay);
  $("#next-day").on("click", navigateToNextDay);

  // Set up modal close
  $(".task-modal-close, #cancel-edit-btn").on("click", function () {
    closeTaskModal();
  });

  // Add task button
  $("#add-task-btn, #empty-add-btn").on("click", function () {
    openNewTaskModal();
  });

  // Form submission
  $("#task-form").on("submit", function (e) {
    e.preventDefault();
    saveTaskChanges();
  });

  // Delete task button
  $("#delete-task-btn").on("click", function () {
    deleteTask();
  });
});

// Current date for navigation
let currentDisplayDate = new Date("2025-03-30");

// Store all tasks
let allTasks = [];

// Store categories
let categories = [];

// Store category colors map
let categoryColorMap = {};

// Initialize the schedule grid with time slots
function initializeSchedule() {
  const $timeLabels = $(".time-labels");
  const $scheduleGrid = $(".schedule-grid");

  // Clear existing content
  $timeLabels.empty();
  $scheduleGrid.html(
    '<div class="current-time-indicator" id="current-time-indicator"></div><div class="loading-spinner" id="loading-spinner"></div><div class="empty-state" id="empty-state"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg><h3>No tasks scheduled</h3><p>Your schedule is clear for today. Click "Add Task" to create a new task.</p><button class="add-task-btn pulse" id="empty-add-btn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>Add Task</button></div>'
  );

  // Create time slots from 6:00 to 22:00 (6am to 10pm)
  for (let hour = 6; hour <= 24; hour++) {
    // Create time label
    const $timeLabel = $("<div>", {
      class: "time-label",
      text: formatHour(hour),
    });
    $timeLabels.append($timeLabel);

    // Create time row with quarter-hour divisions
    const $timeRow = $("<div>", {
      class: "time-row",
      "data-hour": hour,
    });

    // Create 4 quarter-hour divisions
    for (let quarter = 0; quarter < 4; quarter++) {
      const $quarterHour = $("<div>", {
        class: "quarter-hour",
        "data-quarter": quarter,
      });
      $timeRow.append($quarterHour);
    }

    $scheduleGrid.append($timeRow);
  }

  // Set up empty state button
  $("#empty-state .add-task-btn").on("click", function () {
    openNewTaskModal();
  });
}

// Format hour for display (12-hour format with am/pm)
function formatHour(hour) {
  if (hour === 0) return "12am";
  if (hour === 12) return "12pm";
  return hour < 12 ? `${hour}am` : `${hour - 12}pm`;
}

// Update the current time indicator position
function updateCurrentTimeIndicator() {
  const now = new Date();
  const today = now.toISOString().split("T")[0]; // Format: YYYY-MM-DD
  const displayedDate = formatDateForAPI(currentDisplayDate);

  // Only show indicator if viewing today's schedule
  if (today === displayedDate) {
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    // Calculate position from top (in pixels)
    const hourHeight = 60; // 60px per hour
    const minuteHeight = hourHeight / 60; // height per minute

    // Position is based on hours since 6am (our start time)
    const hoursSince6am = currentHour - 6 + currentMinute / 60;
    const topPosition = hoursSince6am * hourHeight;

    const $indicator = $("#current-time-indicator");

    // Only show indicator if current time is within our displayed time range
    if (currentHour >= 6 && currentHour <= 22) {
      $indicator.css({
        display: "block",
        top: `${topPosition}px`,
      });
    } else {
      $indicator.css("display", "none");
    }
  } else {
    // Hide indicator if not viewing today
    $("#current-time-indicator").css("display", "none");
  }
}

// Fetch categories from the API
async function fetchCategories() {
  $("#loading-spinner").show();

  try {
    const response = await $.ajax({
      url: "http://127.0.0.1:5000/api/get_category/admin@gmail.com",
      type: "GET",
      dataType: "json",
      headers: {
        Accept: "application/json",
      },
    });

    if (response.status === "success") {
      categories = response.categories;

      // Create a map of category names to colors
      categories.forEach((category) => {
        categoryColorMap[category.name] = category.color;
      });

      // Update category dropdowns
      updateCategoryDropdown();

      // Update category list in insights panel
      updateCategoryList();

      return true;
    } else {
      throw new Error("Failed to fetch categories");
    }
  } catch (error) {
    console.error("Error fetching categories:", error);
    // Use default categories if API fails
    useDefaultCategories();
    return false;
  } finally {
    $("#loading-spinner").hide();
  }
}

// Use default categories if API fails
function useDefaultCategories() {
  categories = [
    { name: "Work", color: "#2E7D32" },
    { name: "Personal", color: "#546E7A" },
    { name: "Learning", color: "#1E88E5" },
    { name: "Health", color: "#E53935" },
    { name: "Social", color: "#FDD835" },
  ];

  // Create a map of category names to colors
  categories.forEach((category) => {
    categoryColorMap[category.name] = category.color;
  });

  // Update category dropdowns
  updateCategoryDropdown();

  // Update category list in insights panel
  updateCategoryList();
}

// Update category dropdown in the task form
function updateCategoryDropdown() {
  const $categorySelect = $("#task-category");
  $categorySelect.empty();

  categories.forEach((category) => {
    const $option = $("<option>", {
      value: category.name,
      text: category.name,
    });
    $categorySelect.append($option);
  });
}

// Update category list in insights panel
function updateCategoryList() {
  const $categoryList = $("#category-list");
  $categoryList.empty();

  categories.forEach((category) => {
    const $categoryItem = $(`
            <div class="category-item">
                <div class="category-color" style="background-color: ${category.color};"></div>
                <span class="category-name">${category.name}</span>
                <span class="category-time">0h 0m</span>
            </div>
        `);
    $categoryList.append($categoryItem);
  });
}

// Fetch tasks from the API
function fetchTasks(dateString) {
  // Show loading spinner
  $("#loading-spinner").show();

  // Format the date as YYYY-MM-DD for the API
  const formattedDate = dateString;
  console.log("Fetching tasks for date:", formattedDate);

  // Update the displayed date
  updateDisplayedDate(new Date(dateString));

  // Fetch tasks from the API
  $.ajax({
    url: `http://127.0.0.1:5000/api/get_task/${formattedDate}`,
    type: "GET",
    dataType: "json",
    headers: {
      Accept: "application/json",
    },
    success: function (tasks) {
      allTasks = tasks; // Store all tasks
      displayTasks(tasks);
      updateInsights(tasks);

      // Show/hide empty state
      if (tasks.length === 0) {
        $("#empty-state").fadeIn(300);
      } else {
        $("#empty-state").hide();
      }

      // Hide loading spinner
      $("#loading-spinner").hide();
    },
    error: function (error) {
      console.error("Error fetching tasks:", error);
      // Use sample tasks for demo if API fails

      // Hide loading spinner
      $("#loading-spinner").hide();
    },
  });
}

// Display tasks on the schedule
function displayTasks(tasks) {
  // Clear existing tasks
  $(".task").remove();

  // Group tasks by time slots
  const timeSlots = groupTasksByTimeSlots(tasks);

  // Display each task
  Object.keys(timeSlots).forEach(function (timeSlot) {
    const tasksInSlot = timeSlots[timeSlot];
    const taskCount = tasksInSlot.length;

    // Display each task in the time slot
    tasksInSlot.forEach(function (task, index) {
      const $taskElement = createTaskElement(task, index, taskCount);
      $(".schedule-grid").append($taskElement);
    });
  });

  // Add animation to tasks
  $(".task").each(function (index) {
    const $this = $(this);
    setTimeout(function () {
      $this.addClass("fade-in");
    }, index * 100);
  });
}

// Group tasks by time slots for overlapping detection
function groupTasksByTimeSlots(tasks) {
  // First, sort tasks by start time
  const sortedTasks = [...tasks].sort((a, b) => {
    return (
      a.start_time.localeCompare(b.start_time) ||
      a.end_time.localeCompare(b.end_time)
    );
  });

  // Find overlapping groups
  const overlappingGroups = [];

  for (let i = 0; i < sortedTasks.length; i++) {
    const currentTask = sortedTasks[i];

    // Check if this task overlaps with any existing group
    let foundGroup = false;

    for (let group of overlappingGroups) {
      // Check if current task overlaps with any task in this group
      const overlapsWithGroup = group.some((groupTask) => {
        return tasksOverlap(currentTask, groupTask);
      });

      if (overlapsWithGroup) {
        group.push(currentTask);
        foundGroup = true;
        break;
      }
    }

    // If no overlapping group found, create a new group
    if (!foundGroup) {
      overlappingGroups.push([currentTask]);
    }
  }

  // Merge groups that have common tasks
  let merged = true;
  while (merged) {
    merged = false;

    for (let i = 0; i < overlappingGroups.length; i++) {
      for (let j = i + 1; j < overlappingGroups.length; j++) {
        // Check if groups share any tasks
        const groupsOverlap = overlappingGroups[i].some((task1) => {
          return overlappingGroups[j].some((task2) => {
            return tasksOverlap(task1, task2);
          });
        });

        if (groupsOverlap) {
          // Merge groups
          overlappingGroups[i] = [
            ...overlappingGroups[i],
            ...overlappingGroups[j],
          ];
          // Remove duplicate tasks
          overlappingGroups[i] = Array.from(new Set(overlappingGroups[i]));
          // Remove the merged group
          overlappingGroups.splice(j, 1);
          merged = true;
          break;
        }
      }
      if (merged) break;
    }
  }

  // Convert to the expected format
  const timeSlots = {};

  overlappingGroups.forEach((group, index) => {
    const key = `group-${index}`;
    timeSlots[key] = group;
  });

  return timeSlots;
}

// Helper function to check if two tasks overlap
function tasksOverlap(task1, task2) {
  // Convert times to comparable format (minutes since midnight)
  const [startHour1, startMinute1] = task1.start_time.split(":").map(Number);
  const [endHour1, endMinute1] = task1.end_time.split(":").map(Number);
  const [startHour2, startMinute2] = task2.start_time.split(":").map(Number);
  const [endHour2, endMinute2] = task2.end_time.split(":").map(Number);

  const start1 = startHour1 * 60 + startMinute1;
  const end1 = endHour1 * 60 + endMinute1;
  const start2 = startHour2 * 60 + startMinute2;
  const end2 = endHour2 * 60 + endMinute2;

  // Check for overlap
  return start1 < end2 && start2 < end1;
}

function createTaskElement(task, index, totalInSlot) {
  // Validate task data
  if (!task.end_time) {
    console.warn(
      `Task "${task.name}" is missing end_time, using default duration of 1 hour`
    );
    // Set default end time to 1 hour after start time
    const [startHour, startMinute] = task.start_time.split(":").map(Number);
    const endHour = startHour + 1;
    task.end_time = `${endHour.toString().padStart(2, "0")}:${startMinute
      .toString()
      .padStart(2, "0")}`;
  }

  const $taskElement = $("<div>", {
    class: "task" + (task.completed ? " completed" : ""),
    "data-id": task._id,
  });

  // Get category color from map or use a default
  const categoryColor = categoryColorMap[task.category] || "#9e9e9e";

  // Apply dynamic styling based on category color
  $taskElement.css({
    background: `linear-gradient(135deg, ${categoryColor}, ${adjustColor(
      categoryColor,
      -20
    )})`,
    "border-left": `3px solid ${categoryColor}`,
  });

  // Parse start and end times
  const [startHour, startMinute] = task.start_time.split(":").map(Number);
  const [endHour, endMinute] = task.end_time.split(":").map(Number);

  // Calculate position and height
  const hourHeight = 60; // 60px per hour
  const minuteHeight = hourHeight / 60; // height per minute

  // Position from top (relative to 6am start)
  const startFromTop =
    (startHour - 6) * hourHeight + startMinute * minuteHeight;

  // Calculate duration in minutes
  const durationMinutes =
    endHour * 60 + endMinute - (startHour * 60 + startMinute);
  const height = durationMinutes * minuteHeight;

  // Calculate width based on number of tasks in the same time slot
  // If it's the only task in the slot, make it full width with a small margin
  const width = totalInSlot === 1 ? 98 : 100 / totalInSlot;
  const left = totalInSlot === 1 ? 1 : width * index;

  // Set position and size
  $taskElement.css({
    top: `${startFromTop}px`,
    height: `${height}px`,
    width: `calc(${width}% - ${totalInSlot === 1 ? 10 : 20}px)`,
    left: `${left}%`,
  });

  // Add task content
  const taskContent = `
    <div class="task-name">${task.name}</div>
    <div class="task-time">${formatTime(task.start_time)} - ${formatTime(
    task.end_time
  )}</div>
    <div class="task-description">${task.description || ""}</div>
    <div class="task-complete-btn" data-id="${task._id}">
        ${
          task.completed
            ? '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
            : '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></svg>'
        }
    </div>
  `;

  $taskElement.html(taskContent);

  // Add click event for task editing
  $taskElement.on("click", function (e) {
    // Don't open edit modal if clicking the complete button
    if (!$(e.target).closest(".task-complete-btn").length) {
      openEditTaskModal(task);
    }
  });

  // Add click event for task completion button
  $taskElement.find(".task-complete-btn").on("click", function (e) {
    e.stopPropagation(); // Prevent task click event
    toggleTaskCompletion(task._id);
  });

  return $taskElement;
}

// Toggle task completion status
function toggleTaskCompletion(taskId) {
  // Find the task in the array
  const taskIndex = allTasks.findIndex((task) => task._id === taskId);

  if (taskIndex !== -1) {
    // Toggle the completed status
    allTasks[taskIndex].completed = !allTasks[taskIndex].completed;

    // Update the UI
    const $task = $(`.task[data-id="${taskId}"]`);

    if (allTasks[taskIndex].completed) {
      $task.addClass("completed");
      $task
        .find(".task-complete-btn")
        .html(
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
        );

      // Show toast notification
      showToast(`Task "${allTasks[taskIndex].name}" marked as completed`);
    } else {
      $task.removeClass("completed");
      $task
        .find(".task-complete-btn")
        .html(
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></svg>'
        );

      // Show toast notification
      showToast(`Task "${allTasks[taskIndex].name}" marked as not completed`);
    }

    // Update insights
    updateInsights(allTasks);
  }
}

// Adjust color brightness (positive value brightens, negative darkens)
function adjustColor(color, percent) {
  // Convert hex to RGB
  let r = parseInt(color.substring(1, 3), 16);
  let g = parseInt(color.substring(3, 5), 16);
  let b = parseInt(color.substring(5, 7), 16);

  // Adjust brightness
  r = Math.max(0, Math.min(255, r + percent));
  g = Math.max(0, Math.min(255, g + percent));
  b = Math.max(0, Math.min(255, b + percent));

  // Convert back to hex
  return `#${r.toString(16).padStart(2, "0")}${g
    .toString(16)
    .padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

// Format time for display (12-hour format)
function formatTime(timeString) {
  const [hours, minutes] = timeString.split(":").map(Number);
  const period = hours >= 12 ? "PM" : "AM";
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${minutes.toString().padStart(2, "0")} ${period}`;
}

// Open modal for editing a task
function openEditTaskModal(task) {
  // Set modal title
  $(".task-modal-title").text("Edit Task");

  // Fill form with task data
  $("#task-id").val(task._id);
  $("#task-name").val(task.name);
  $("#task-category").val(task.category);
  $("#task-start-time").val(task.start_time);
  $("#task-end-time").val(task.end_time);
  $("#task-description").val(task.description || "");
  $("#task-completed").val(task.completed.toString());

  // Show delete button
  $("#delete-task-btn").show();

  // Show modal with animation
  $("#task-modal").fadeIn(300).addClass("active");
}

// Open modal for creating a new task
function openNewTaskModal() {
  // Set modal title
  $(".task-modal-title").text("Add New Task");

  // Clear form
  $("#task-form")[0].reset();
  $("#task-id").val("");

  // Set default times
  const now = new Date();
  const currentHour = now.getHours();
  const nextHour = currentHour + 1;

  $("#task-start-time").val(`${currentHour.toString().padStart(2, "0")}:00`);
  $("#task-end-time").val(`${nextHour.toString().padStart(2, "0")}:00`);

  // Hide delete button
  $("#delete-task-btn").hide();

  // Show modal with animation
  $("#task-modal").fadeIn(300).addClass("active");
}

// Close task modal
function closeTaskModal() {
  $("#task-modal").fadeOut(300);
  setTimeout(function () {
    $("#task-modal").removeClass("active");
  }, 300);
}

// Save task changes
function saveTaskChanges() {
  const taskId = $("#task-id").val();
  const isNewTask = !taskId;
  const taskName = $("#task-name").val();

  // Gather form data
  const taskData = {
    _id: isNewTask ? `temp_${Date.now()}` : taskId,
    name: taskName,
    category: $("#task-category").val(),
    start_time: $("#task-start-time").val(),
    end_time: $("#task-end-time").val(),
    description: $("#task-description").val(),
    completed: $("#task-completed").val() === "true",
    date: formatDateForAPI(currentDisplayDate),
  };

  // In a real implementation, this would call an API
  if (isNewTask) {
    // Add new task
    allTasks.push(taskData);
    // Show toast notification
    showToast(`Task "${taskName}" has been created`);
  } else {
    // Update existing task
    const index = allTasks.findIndex((task) => task._id === taskId);
    if (index !== -1) {
      allTasks[index] = taskData;
      // Show toast notification
      showToast(`Task "${taskName}" has been updated`);
    }
  }

  // Close modal
  closeTaskModal();

  // Refresh tasks display
  displayTasks(allTasks);
  updateInsights(allTasks);

  // Hide empty state if needed
  if (allTasks.length > 0) {
    $("#empty-state").hide();
  }
}

// Delete task
function deleteTask() {
  const taskId = $("#task-id").val();
  const taskName = $("#task-name").val();

  // Confirm deletion
  if (confirm("Are you sure you want to delete this task?")) {
    // In a real implementation, this would call an API
    const index = allTasks.findIndex((task) => task._id === taskId);
    if (index !== -1) {
      allTasks.splice(index, 1);
      // Show toast notification
      showToast(`Task "${taskName}" has been deleted`);
    }

    // Close modal
    closeTaskModal();

    // Refresh tasks display
    displayTasks(allTasks);
    updateInsights(allTasks);

    // Show empty state if needed
    if (allTasks.length === 0) {
      $("#empty-state").fadeIn(300);
    }
  }
}

// Update insights panel based on tasks
function updateInsights(tasks) {
  // Calculate completion percentage
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((task) => task.completed).length;
  const completionPercentage =
    totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Update the UI with animation
  $(".insights-percentage").first().text(`${completionPercentage}%`);
  $(".progress-fill")
    .first()
    .css("width", "0%")
    .animate(
      {
        width: `${completionPercentage}%`,
      },
      800
    );
  $(".insights-description")
    .first()
    .text(`${completedTasks} of ${totalTasks} tasks completed today`);

  // Calculate category durations
  const categoryDurations = calculateCategoryDurations(tasks);
  updateCategorySummary(categoryDurations);
}

// Calculate duration for each category
function calculateCategoryDurations(tasks) {
  const categoryDurations = {};

  // Initialize all categories with zero duration
  categories.forEach((category) => {
    categoryDurations[category.name] = 0;
  });

  // Calculate durations from tasks
  tasks.forEach(function (task) {
    const category = task.category;

    // Skip if category doesn't exist in our list
    if (categoryDurations[category] === undefined) return;

    // Parse start and end times
    const [startHour, startMinute] = task.start_time.split(":").map(Number);
    const [endHour, endMinute] = task.end_time.split(":").map(Number);

    // Calculate duration in minutes
    const durationMinutes =
      endHour * 60 + endMinute - (startHour * 60 + startMinute);

    // Add to category total
    categoryDurations[category] += durationMinutes;
  });

  return categoryDurations;
}

// Update category summary in the insights panel
function updateCategorySummary(categoryDurations) {
  $("#category-list .category-item").each(function () {
    const $item = $(this);
    const categoryName = $item.find(".category-name").text();
    const durationMinutes = categoryDurations[categoryName] || 0;
    const hours = Math.floor(durationMinutes / 60);
    const minutes = durationMinutes % 60;

    $item.find(".category-time").text(`${hours}h ${minutes}m`);
  });
}

// Navigate to previous day
function navigateToPreviousDay() {
  currentDisplayDate.setDate(currentDisplayDate.getDate() - 1);
  const dateString = formatDateForAPI(currentDisplayDate);
  fetchTasks(dateString);

  // Add animation to button
  $("#prev-day").addClass("pulse");
  setTimeout(function () {
    $("#prev-day").removeClass("pulse");
  }, 1000);
}

// Navigate to next day
function navigateToNextDay() {
  currentDisplayDate.setDate(currentDisplayDate.getDate() + 1);
  const dateString = formatDateForAPI(currentDisplayDate);
  fetchTasks(dateString);

  // Add animation to button
  $("#next-day").addClass("pulse");
  setTimeout(function () {
    $("#next-day").removeClass("pulse");
  }, 1000);
}

// Format date for API (YYYY-MM-DD)
function formatDateForAPI(date) {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const day = date.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// Update the displayed date in the header
function updateDisplayedDate(date) {
  const options = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  };
  $("#current-date").text(date.toLocaleDateString("en-US", options));
}

// Show toast notification
function showToast(message, duration = 3000) {
  // Create toast if it doesn't exist
  if ($("#toast").length === 0) {
    $("body").append('<div id="toast"></div>');
    $("#toast").css({
      visibility: "hidden",
      minWidth: "250px",
      backgroundColor: "#4361ee",
      color: "white",
      textAlign: "center",
      borderRadius: "8px",
      padding: "16px",
      position: "fixed",
      zIndex: "1500",
      bottom: "30px",
      right: "30px",
      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
      fontWeight: "500",
      fontSize: "14px",
      opacity: "0",
      transition: "opacity 0.5s",
    });
  }

  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.style.visibility = "visible";
  toast.style.opacity = "1";

  // Hide after duration
  setTimeout(function () {
    toast.style.opacity = "0";
    setTimeout(function () {
      toast.style.visibility = "hidden";
    }, 500);
  }, duration);
}
