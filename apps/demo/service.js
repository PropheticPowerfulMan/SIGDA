"use strict";
window.SIGDAService = (() => {
    const config = deploymentConfig;
    const today = () => new Intl.DateTimeFormat('en-CA', {timeZone:'Africa/Kinshasa',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    function state(on = today()) {
        const days = Math.round((Date.parse(config.valid_until+'T00:00:00Z')-Date.parse(on+'T00:00:00Z'))/86400000);
        return {name:on>=config.valid_until?'expired':on<config.valid_from?'preparation':days<=config.reminder_days?'reminder':'active',days:Math.max(0,days)};
    }
    function assertCreation() { if (state().name === 'expired') throw new Error('La validité annuelle est échue. Contactez la maintenance pour le renouvellement. Les documents validés restent consultables et imprimables.'); }
    const fmt = iso => new Intl.DateTimeFormat('fr',{dateStyle:'long',timeZone:'UTC'}).format(new Date(iso+'T00:00:00Z'));
    function render() {
        const current = state();
        const last = new Date(Date.parse(config.valid_until+'T00:00:00Z')-86400000).toISOString().slice(0,10);
        for (const node of document.querySelectorAll('[data-service-status]')) {
            node.dataset.state = current.name;
            node.querySelector('strong').textContent = {expired:'Renouvellement annuel requis',preparation:'Préparation · période annuelle à venir',active:'Période annuelle active',reminder:`Échéance dans ${current.days} jour(s)`}[current.name];
            node.querySelector('[data-service-dates]').textContent = `Du ${fmt(config.valid_from)} au ${fmt(last)} inclus.${current.name==='expired'?' Les nouvelles créations sont suspendues. Les documents validés restent consultables et imprimables.':''}`;
        }
    }
    render();setInterval(render,60000);
    return {state,assertCreation};
})();
