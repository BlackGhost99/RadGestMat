(function () {
    const bell = document.getElementById('notification-bell');
    const badge = document.getElementById('notification-count');
    if (!bell || !badge) return;
    let busy = false;
    async function refresh() {
        if (busy || document.hidden) return;
        busy = true;
        try {
            const r = await fetch(bell.dataset.url, {credentials:'same-origin', cache:'no-store', headers:{Accept:'application/json'}});
            if (r.status === 401 || r.status === 403) {
                badge.hidden = true; bell.setAttribute('aria-label','Notifications'); return;
            }
            if (!r.ok) throw new Error('refresh failed');
            const data = await r.json();
            const count = data.reminders.length;
            const overdue = data.reminders.some(item => item.overdue);
            badge.textContent = count > 99 ? '99+' : String(count);
            badge.classList.toggle('bg-danger', overdue);
            badge.classList.toggle('text-white', overdue);
            badge.classList.toggle('bg-warning', !overdue);
            badge.classList.toggle('text-dark', !overdue);
            badge.hidden = !count;
            bell.setAttribute('aria-label', 'Notifications : ' + count + ' retours à surveiller');
            bell.title = count ? count + ' retours à surveiller' : 'Notifications';
        } catch (e) { bell.title = 'Notifications — actualisation indisponible'; }
        finally { busy = false; }
    }
    refresh();
    setInterval(refresh, 60000);
    document.addEventListener('visibilitychange', refresh);
    window.addEventListener('online', refresh);
    window.addEventListener('pageshow', refresh);
}());
