function joinStream() {
    fetch('/stream/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(data.error);
            return;
        }
        console.log(data.message);
    })
    .catch(error => console.error('Error:', error));
}

function updateStatus(isOnline, title) {
    const statusIndicator = document.getElementById('status-indicator');
    statusIndicator.classList.toggle('online', isOnline);
    statusIndicator.innerHTML = `<i class="fas fa-circle"></i> ${isOnline ? 'Live: ' + title : 'Waiting for stream...'}`;
    const streamEmbed = document.getElementById('stream-embed');
    const streamPlaceholder = document.getElementById('stream-placeholder');
    if (isOnline) {
        streamEmbed.style.display = 'block';
        streamPlaceholder.style.display = 'none';
    } else {
        streamEmbed.style.display = 'none';
        streamPlaceholder.style.display = 'block';
        streamEmbed.src = ''; // Clear the iframe source when offline
    }
}

function updateResources() {
    fetch('/resources')
        .then(response => response.json())
        .then(data => {
            const resourcesList = document.querySelector('.resources-list');
            resourcesList.innerHTML = '';
            data.resources.forEach(resource => {
                const item = document.createElement('div');
                item.className = 'resource-item';
                const iconClass = resource.file_type === 'PDF' ? 'fa-file-pdf' :
                                 resource.file_type === 'MP4' ? 'fa-file-video' :
                                 'fa-file-code';
                item.innerHTML = `
                    <div class="resource-icon"><i class="fas ${iconClass}"></i></div>
                    <div class="resource-info">
                        <div class="resource-name">${resource.name}</div>
                        <div class="resource-meta">${resource.file_type} • ${resource.file_size}</div>
                    </div>
                    <a class="download-btn" href="${resource.file_path}" download><i class="fas fa-download"></i></a>
                `;
                resourcesList.appendChild(item);
            });
        })
        .catch(error => console.error('Error fetching resources:', error));
}

function submitInteraction(type, content = '') {
    fetch('/interaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        alert(data.message);
    })
    .catch(error => console.error('Error submitting interaction:', error));
}

function checkStreamStatus() {
    fetch('/stream/status')
        .then(response => response.json())
        .then(data => {
            const isOnline = data.status === 'Active';
            updateStatus(isOnline, data.title);

            if (isOnline) {
                joinStream(); // Automatically join the stream
                const streamEmbed = document.getElementById('stream-embed');
                streamEmbed.src = data.stream_url; // Set the stream URL in the iframe
                streamEmbed.style.display = 'block';
                document.getElementById('stream-placeholder').style.display = 'none';
            } else {
                console.log("No active stream");
            }
        })
        .catch(error => console.error('Error fetching stream status:', error));
}

function fetchStreamStatus() {
    fetch('/stream/status')
        .then(response => response.json())
        .then(data => {
            if (data.status === "Active") {
                const streamEmbed = document.getElementById('stream-embed');
                streamEmbed.src = data.stream_url; // Set the stream URL in the iframe
                streamEmbed.style.display = 'block'; // Show the iframe
                document.getElementById('stream-placeholder').style.display = 'none'; // Hide the placeholder
                document.getElementById('status-indicator').innerHTML = `
                    <i class="fas fa-circle" style="color: green;"></i> Live
                `;
            } else {
                console.log("No active stream");
            }
        })
        .catch(error => console.error('Error fetching stream status:', error));
}

function toggleFullScreen() {
    const streamEmbed = document.getElementById('stream-embed');
    if (streamEmbed.requestFullscreen) {
        streamEmbed.requestFullscreen();
    } else if (streamEmbed.mozRequestFullScreen) { // For Firefox
        streamEmbed.mozRequestFullScreen();
    } else if (streamEmbed.webkitRequestFullscreen) { // For Chrome, Safari, and Opera
        streamEmbed.webkitRequestFullscreen();
    } else if (streamEmbed.msRequestFullscreen) { // For IE/Edge
        streamEmbed.msRequestFullscreen();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStreamStatus();
    updateResources();
    setInterval(checkStreamStatus, 10000); // Check stream status every 10 seconds
    setInterval(updateResources, 5000); // Update resources every 5 seconds

    document.querySelectorAll('.interaction-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.querySelector('.interaction-label').textContent.toLowerCase().replace(' ', '_');
            let content = '';
            if (type === 'ask_question' || type === 'send_message') {
                content = prompt(`Enter your ${type.replace('_', ' ')}:`);
                if (!content) return;
            }
            submitInteraction(type, content);
        });
    });
});