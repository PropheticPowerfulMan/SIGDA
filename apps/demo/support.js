"use strict";
(() => {
    const form = document.querySelector('[data-support-form]'); if (!form) return;
    const status = document.querySelector('[data-support-status]'), list = document.querySelector('[data-support-list]');
    const categories = {agent_add:'Ajout d’un agent',agent_update:'Correction d’un dossier agent',app_update:'Mise à jour de l’application',renewal:'Renouvellement annuel',assistance:'Assistance'};
    const el = (tag,text) => { const node=document.createElement(tag);node.textContent=text;return node; };
    function download(ticket) {
        const text = ['SIGDA · Cabinet du Président de la République','DEMANDE DE MAINTENANCE · DÉMONSTRATION',ticket.id,
            'Compte : '+ticket.owner,'Date : '+new Date(ticket.at).toISOString(),categories[ticket.category],ticket.details,
            'À transmettre à l’équipe de maintenance. Ce fichier ne constitue pas un envoi automatique.'].join('\n\n');
        const url = URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'})), link=document.createElement('a');
        link.href=url;link.download='SIGDA-maintenance-'+ticket.id+'.txt';link.click();window.SIGDAEffects?.notify('Demande prête : le fichier est à transmettre à la maintenance.');setTimeout(()=>URL.revokeObjectURL(url),3000);
    }
    async function refresh() {
        const db=await SIGDADatabase;
        const tickets=await new Promise((resolve,reject)=>{const r=db.transaction('support').objectStore('support').getAll();r.onsuccess=()=>resolve(r.result);r.onerror=reject;});
        list.replaceChildren();
        for(const ticket of tickets.filter(t=>t.owner===SIGDASession.username).sort((a,b)=>b.at-a.at)) {
            const row=el('li','');row.className='support-ticket';const button=el('button','Télécharger la demande');button.type='button';button.className='button';button.addEventListener('click',()=>download(ticket));
            row.append(el('strong',categories[ticket.category]+' · À transmettre'),el('p',ticket.details),el('small',ticket.id),button);list.append(row);
        }
        if(!list.children.length)list.append(el('li','Aucune demande préparée sur cet appareil.'));
    }
    form.addEventListener('submit',async event=>{
        event.preventDefault();if(!form.reportValidity())return;
        const button=form.querySelector('button[type="submit"]');button.disabled=true;
        try {
            const ticket={id:crypto.randomUUID(),owner:SIGDASession.username,at:Date.now(),category:form.elements.category.value,details:form.elements.details.value.trim()};
            if(!ticket.details||!categories[ticket.category])throw new Error('Précisez la demande.');
            const db=await SIGDADatabase;await new Promise((resolve,reject)=>{const tx=db.transaction('support','readwrite');tx.objectStore('support').add(ticket);tx.oncomplete=resolve;tx.onerror=reject;});
            await SIGDAUsage.log('support_request');await refresh();download(ticket);
            status.textContent='Demande préparée et enregistrée sur cet appareil. Transmettez le fichier téléchargé à votre équipe de maintenance. Aucun envoi automatique n’a été effectué.';form.reset();
        } catch(error) {status.textContent=error.message||'Impossible de préparer la demande.';}
        finally {button.disabled=false;}
    });
    refresh().catch(error=>{status.textContent=error.message;});
})();
