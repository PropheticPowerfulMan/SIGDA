"use strict";
for (const button of document.querySelectorAll('[data-password-toggle]')) {
    const input = document.getElementById(button.getAttribute('aria-controls'));
    if (!input) continue;
    const conceal = () => { input.type = 'password'; button.textContent = 'Afficher'; button.setAttribute('aria-pressed', 'false'); button.setAttribute('aria-label', 'Afficher le mot de passe'); };
    button.hidden = false;
    button.addEventListener('click', () => {
        if (input.type === 'password') { input.type = 'text'; button.textContent = 'Masquer'; button.setAttribute('aria-pressed', 'true'); button.setAttribute('aria-label', 'Masquer le mot de passe'); }
        else conceal();
    });
    input.form?.addEventListener('submit', conceal);
    window.addEventListener('pagehide', conceal);
    document.addEventListener('visibilitychange', () => { if (document.hidden) conceal(); });
}
