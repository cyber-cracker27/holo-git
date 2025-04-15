function startStream() {
    const title = document.getElementById('stream-title').value;
    const streamUrl = document.getElementById('stream-url').value; // Get the stream URL from the input field

    if (!title || !streamUrl) {
        alert('Please provide both a title and a stream URL.');
        return;
    }

    fetch('/stream/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, stream_url: streamUrl }) // Send title and stream_url
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        updateStatus(true);
        alert(data.message);
    })
    .catch(error => console.error('Error:', error));
}

function stopStream() {
    fetch('/stream/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        updateStatus(false);
        alert(data.message);
    })
    .catch(error => console.error('Error:', error));
}

function uploadResource() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.onchange = () => {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        fetch('/resource/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            alert(data.message);
        })
        .catch(error => console.error('Error:', error));
    };
    fileInput.click();
}

function updateStatus(isOnline) {
    const statusIndicator = document.getElementById('status-indicator');
    statusIndicator.classList.toggle('online', isOnline);
    statusIndicator.innerHTML = `<i class="fas fa-circle"></i> ${isOnline ? 'Online' : 'Offline'}`;
    const streamEmbed = document.getElementById('stream-embed');
    const streamPlaceholder = document.getElementById('stream-placeholder');
    if (isOnline) {
        streamEmbed.style.display = 'block';
        streamPlaceholder.style.display = 'none';
        // Simulate stream URL (replace with actual streaming service URL)
        streamEmbed.src = 'https://www.youtube.com/embed/dQw4w9WgXcQ'; // Placeholder
    } else {
        streamEmbed.style.display = 'none';
        streamPlaceholder.style.display = 'block';
        streamEmbed.src = '';
    }
}

function updateAttendance() {
    fetch('/stream/attendance')
        .then(response => response.json())
        .then(data => {
            const attendanceList = document.getElementById('attendance-list');
            const viewerCount = document.getElementById('viewer-count');
            attendanceList.innerHTML = '';
            viewerCount.textContent = data.attendees.length;
            data.attendees.forEach(attendee => {
                const item = document.createElement('div');
                item.className = 'student-item';
                item.innerHTML = `
                    <div class="student-avatar">${attendee.name[0]}</div>
                    <div class="student-name">${attendee.name}</div>
                    <div class="student-status">Connected at ${attendee.join_time}</div>
                `;
                attendanceList.appendChild(item);
            });
        })
        .catch(error => console.error('Error:', error));
}

function checkStreamStatus() {
    fetch('/stream/status')
        .then(response => response.json())
        .then(data => {
            updateStatus(data.status === 'Active');
        })
        .catch(error => console.error('Error:', error));
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStreamStatus();
    updateAttendance();
    setInterval(checkStreamStatus, 10000);
    setInterval(updateAttendance, 5000);
});