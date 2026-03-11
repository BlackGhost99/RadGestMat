/**
 * Theme Toggle JavaScript
 * Gère le changement de thème rapide dans le header
 */

(function() {
    'use strict';

    // Initialiser le thème au chargement
    function initTheme() {
        const theme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        updateThemeIcon(theme);
    }

    // Mettre à jour l'icône du toggle selon le thème
    function updateThemeIcon(theme) {
        const toggleBtn = document.getElementById('themeToggleBtn');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.className = 'bi bi-sun';
                    toggleBtn.setAttribute('title', 'Passer en mode clair');
                } else {
                    icon.className = 'bi bi-moon';
                    toggleBtn.setAttribute('title', 'Passer en mode sombre');
                }
            }
        }
        // Mettre à jour aussi le dropdown menu
        const dropdownToggle = document.querySelector('.dropdown-item[onclick="toggleTheme()"]');
        if (dropdownToggle) {
            const dropdownIcon = dropdownToggle.querySelector('i');
            const dropdownText = dropdownToggle.childNodes[dropdownToggle.childNodes.length - 1];
            if (dropdownIcon) {
                dropdownIcon.className = theme === 'dark' ? 'bi bi-sun me-2' : 'bi bi-moon me-2';
            }
            if (dropdownText && dropdownText.textContent) {
                dropdownText.textContent = theme === 'dark' ? 'Mode clair' : 'Mode sombre';
            }
        }
    }
    
    // Exposer la fonction globalement
    window.updateThemeIcon = updateThemeIcon;

    // Toggle rapide du thème
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        const darkMode = newTheme === 'dark';

        // Appliquer immédiatement
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        updateThemeIcon(newTheme);

        // Sauvegarder via AJAX
        const csrftoken = getCookie('csrftoken');
        fetch('/users/api/toggle-theme/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                dark_mode: darkMode
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Erreur lors de la sauvegarde du thème:', data.error);
                // Revenir au thème précédent en cas d'erreur
                document.documentElement.setAttribute('data-bs-theme', currentTheme);
                updateThemeIcon(currentTheme);
            }
        })
        .catch(error => {
            console.error('Erreur lors du changement de thème:', error);
            // Revenir au thème précédent en cas d'erreur
            document.documentElement.setAttribute('data-bs-theme', currentTheme);
            updateThemeIcon(currentTheme);
        });
    }

    // Fonction utilitaire pour récupérer le cookie CSRF
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

    // Initialiser au chargement du DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }

    // Exposer les fonctions globalement
    window.toggleTheme = toggleTheme;
})();
