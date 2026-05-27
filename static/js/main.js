function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function fetchPost(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(data),
    }).then(r => r.json());
}

/* --- Sidebar toggle --- */
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    const overlay = document.getElementById('sidebar-overlay');

    if (!sidebar || !toggle) return;

    const STORAGE_KEY = 'mastitrack_sidebar_collapsed';
    const isMobile = () => window.innerWidth <= 768;

    if (!isMobile() && localStorage.getItem(STORAGE_KEY) === 'true') {
        sidebar.classList.add('collapsed');
        document.body.classList.add('sidebar-is-collapsed');
    }

    toggle.addEventListener('click', function () {
        if (isMobile()) {
            sidebar.classList.toggle('mobile-open');
            overlay.classList.toggle('show');
        } else {
            sidebar.classList.toggle('collapsed');
            document.body.classList.toggle('sidebar-is-collapsed');
            localStorage.setItem(STORAGE_KEY, sidebar.classList.contains('collapsed'));
        }
    });

    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('show');
        });
    }
});
