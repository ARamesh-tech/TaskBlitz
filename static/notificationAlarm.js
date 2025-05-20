document.addEventListener('DOMContentLoaded', () => {
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    setInterval(checkReminders, 5000); // Check every 1 seconds
});

function checkReminders() {
    fetch('/get_due_reminders')
        .then(res => res.json())
        .then(data => {
            data.forEach(task => {
                // Check if already dismissed
                if (!isTaskDismissed(task.id)) {
                    showNotification(task.id, task.task, task.description);
                }
            });
        });
}

function showNotification(id, title, message) {
    if (Notification.permission === "granted") {
        const notification = new Notification("🕒 Reminder: " + title, {
            body: message,
            icon: "/static/bell.png"
        });

        const audio = new Audio("/static/notify.mp3");
        audio.loop = true;
        audio.play();

        const stop = confirm("Reminder: " + title + "\nDescription: " + message + "\n\nDo you want to turn off the alarm?");
        if (stop) {
            notification.close();
            audio.pause();
            markTaskDismissed(id); // ✅ prevent future alerts for this task
        }
    }
}

// Use localStorage to remember dismissed tasks
function isTaskDismissed(id) {
    const dismissed = JSON.parse(localStorage.getItem("dismissedTasks") || "[]");
    return dismissed.includes(id);
}

function markTaskDismissed(id) {
    let dismissed = JSON.parse(localStorage.getItem("dismissedTasks") || "[]");
    dismissed.push(id);
    localStorage.setItem("dismissedTasks", JSON.stringify(dismissed));
}
