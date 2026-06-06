// --- API key handling -------------------------------------------------
// The backend requires an API key when YTGRID_API_KEY is set on the server.
// Browser EventSource cannot send headers, so the key is passed as a query
// parameter for the SSE stream and as a header for normal fetch() calls.
function getApiKey() {
    let key = localStorage.getItem('ytgrid_api_key');
    if (key === null) {
        key = window.prompt('Enter YTGrid API key (leave blank if auth is disabled):') || '';
        localStorage.setItem('ytgrid_api_key', key);
    }
    return key;
}

const API_KEY = getApiKey();

function authHeaders(extra) {
    const headers = extra || {};
    if (API_KEY) headers['X-API-Key'] = API_KEY;
    return headers;
}

document.addEventListener('DOMContentLoaded', () => {

    // Connect to Server-Sent Events stream
    const streamUrl = API_KEY
        ? `/dashboard/stream?api_key=${encodeURIComponent(API_KEY)}`
        : '/dashboard/stream';
    const evtSource = new EventSource(streamUrl);

    const valActiveSessions = document.getElementById('val-active-sessions');
    const valCpuUsage = document.getElementById('val-cpu-usage');
    const valRamUsage = document.getElementById('val-ram-usage');
    const tbody = document.getElementById('sessions-tbody');

    evtSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        } catch (err) {
            console.error("Failed to parse SSE data: ", err);
        }
    };

    evtSource.onerror = (err) => {
        console.error("SSE connection error", err);
    }

    // Process update logic
    function updateDashboard(data) {
        valActiveSessions.innerText = data.session_count !== undefined ? data.session_count : 0;
        if(data.system_health) {
            valCpuUsage.innerText = data.system_health.cpu !== "N/A" ? `${data.system_health.cpu}%` : "N/A";
            valRamUsage.innerText = data.system_health.ram !== "N/A" ? `${data.system_health.ram}%` : "N/A";
        }

        // Rebuild Table
        tbody.innerHTML = '';
        if (data.active_sessions && Array.isArray(data.active_sessions)) {
            if (data.active_sessions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No active sessions</td></tr>`;
                return;
            }

            data.active_sessions.forEach(session => {
                const sessionLoop = session.loop !== undefined ? `Loop ${session.loop}` : "Running";
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-family: monospace; color: var(--accent);">${session.id.substring(0, 8)}...</td>
                    <td><span class="status-badge running">${sessionLoop}</span></td>
                    <td><span style="color: var(--text-secondary);">Active</span></td>
                    <td><button class="btn-danger" onclick="stopSession('${session.id}')">Stop</button></td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
});

// Helper bound to Window to trigger standard REST backend endpoints natively.
window.stopSession = async function(session_id) {
    if(!confirm(`Are you sure you want to kill session ${session_id}?`)) return;

    try {
        const response = await fetch('/tasks/stop', {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                "session_id": session_id
            })
        });

        if(response.ok) {
            alert(`Signal sent to stop ${session_id}`);
        } else {
            const err = await response.json();
            alert(`Failed: ${err.detail || 'Unknown error'}`);
        }
    } catch (e) {
        alert("Network error: " + e.message);
    }
}

// UI Tab Switching
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        if(e.target.classList.contains('disabled')) return;

        // Remove active class from all
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        e.target.classList.add('active');

        // Hide all views
        document.querySelectorAll('.dashboard-content').forEach(view => view.style.display = 'none');

        // Show target view
        const targetId = e.target.getAttribute('data-target');
        if(targetId) {
            document.getElementById(targetId).style.display = 'block';
        }
    });
});

// Launch Task Form Submission
window.submitTask = async function(e) {
    e.preventDefault();
    const url = document.getElementById('input-url').value;
    const speed = parseFloat(document.getElementById('input-speed').value);
    const loops = parseInt(document.getElementById('input-loops').value);

    // Simple task_type inference from URL
    let task_type = "video";
    if(url.includes('playlist')) task_type = "playlist";
    if(url.includes('/@') || url.includes('/channel/')) task_type = "channel";

    try {
        const response = await fetch('/tasks/', {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                url: url,
                speed: speed,
                loop_count: loops,
                task_type: task_type
            })
        });

        if (response.ok) {
            // Auto redirect back to dashboard tab
            document.querySelector('[data-target="dashboard-view"]').click();
            document.getElementById('launch-form').reset();
        } else {
            const err = await response.json();
            alert(`Failed to launch task: ${err.detail || 'Unknown error'}`);
        }
    } catch (err) {
        alert("Network error submitting task.");
    }
}
