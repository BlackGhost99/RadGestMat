(() => {
    const field = document.getElementById('id_password');
    const toggle = document.getElementById('password-toggle');
    if (!field || !toggle) return;
    const hide = () => {
        field.type = 'password';
        toggle.setAttribute('aria-pressed', 'false');
        toggle.setAttribute('aria-label', 'Afficher le mot de passe');
        toggle.title = 'Afficher le mot de passe';
        toggle.firstElementChild.className = 'bi bi-eye';
    };
    toggle.addEventListener('click', () => {
        if (field.type === 'text') { hide(); return; }
        field.type = 'text';
        toggle.setAttribute('aria-pressed', 'true');
        toggle.setAttribute('aria-label', 'Masquer le mot de passe');
        toggle.title = 'Masquer le mot de passe';
        toggle.firstElementChild.className = 'bi bi-eye-slash';
    });
    field.form.addEventListener('submit', hide);
    window.addEventListener('pagehide', hide);
})();
