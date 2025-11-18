// Custom JavaScript for RadGestMat

document.addEventListener('DOMContentLoaded', () => {
    const navbar = document.querySelector('.navbar-elevated');
    const alerts = document.querySelectorAll('.alert');

    const handleNavbarOffset = () => {
        if (!navbar) return;
        const scrolled = window.scrollY > 24;
        navbar.classList.toggle('navbar-scrolled', scrolled);
    };

    handleNavbarOffset();
    window.addEventListener('scroll', handleNavbarOffset, { passive: true });

    // Auto-dismiss alerts after a short delay to keep the UI clean
    alerts.forEach((alert) => {
        const timer = setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5500);

        alert.addEventListener('mouseover', () => clearTimeout(timer));
    });

    // Enable Bootstrap tooltips when present
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].forEach((tooltipTriggerEl) => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
