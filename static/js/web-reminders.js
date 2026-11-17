(function () {
    const panel = document.getElementById('web-reminders');
    if (!panel) return;
    const list = document.getElementById('web-reminder-items');
    const stale = document.getElementById('web-reminders-stale');
    let busy = false, last = null;
    async function refresh() {
        if (busy || document.hidden) return;
        busy = true;
        try {
            const r = await fetch(panel.dataset.url, {credentials:'same-origin', cache:'no-store', headers:{Accept:'application/json'}});
            if (r.status === 401 || r.status === 403) {
                list.replaceChildren(); panel.hidden = true; last = null; return;
            }
            if (!r.ok) throw new Error('refresh failed');
            const data = await r.json();
            const key = JSON.stringify(data.reminders);
            if (last !== key) {
                list.replaceChildren();
                for (const item of data.reminders) {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = item.url;
                    a.textContent = item.asset + ' — ' + (item.overdue ? 'En retard depuis ' : 'Retour prévu le ') + item.deadline;
                    if (item.overdue) a.classList.add('text-danger','fw-semibold');
                    li.append(a); list.append(li);
                }
                last = key;
            }
            panel.hidden = !data.reminders.length;
            stale.hidden = true;
        } catch (e) { stale.hidden = false; }
        finally { busy = false; }
    }
    refresh();
    setInterval(refresh, 60000);
    document.addEventListener('visibilitychange', refresh);
    window.addEventListener('online', refresh);
    window.addEventListener('pageshow', refresh);
}());
