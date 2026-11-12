"use strict";
for (const button of document.querySelectorAll('[data-password-toggle]')) {
    const input = document.getElementById(button.getAttribute('aria-controls'));
    if (!input) continue;
    const icon=document.createElementNS('http://www.w3.org/2000/svg','svg');icon.setAttribute('viewBox','0 0 24 24');icon.setAttribute('aria-hidden','true');icon.classList.add('password-eye');
    const outline=document.createElementNS(icon.namespaceURI,'path');outline.setAttribute('d','M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12Z');
    const pupil=document.createElementNS(icon.namespaceURI,'circle');pupil.setAttribute('cx','12');pupil.setAttribute('cy','12');pupil.setAttribute('r','2.7');
    const slash=document.createElementNS(icon.namespaceURI,'path');slash.setAttribute('d','M4 3 21 21');icon.append(outline,pupil,slash);button.replaceChildren(icon);
    const conceal = () => { input.type = 'password'; slash.style.display=''; button.setAttribute('aria-pressed', 'false'); button.setAttribute('aria-label', 'Afficher le mot de passe'); };
    button.hidden = false;
    button.addEventListener('click', () => {
        if (input.type === 'password') { input.type = 'text'; slash.style.display='none'; button.setAttribute('aria-pressed', 'true'); button.setAttribute('aria-label', 'Masquer le mot de passe'); }
        else conceal();
    });
    input.form?.addEventListener('submit', conceal);
    window.addEventListener('pagehide', conceal);
    document.addEventListener('visibilitychange', () => { if (document.hidden) conceal(); });
}
