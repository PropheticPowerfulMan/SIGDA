"use strict";
(() => {
    const root=document.querySelector('[data-maintenance-dashboard]');if(!root)return;
    const endpoint=root.dataset.endpoint,who=window.SIGDASession||{};
    if(!endpoint&&who.role!=='MAINTENANCE')return;
    const news=root.querySelector('[data-maint-news]')||document.querySelector('[data-maint-news]'),status=root.querySelector('[data-maint-poll-status]');
    const fmt=new Intl.DateTimeFormat('fr',{dateStyle:'short',timeStyle:'short',timeZone:'Africa/Kinshasa'}),states={open:'À traiter',processing:'En cours',resolved:'Traitée'};
    const categories={agent_add:'Ajout d’un agent',agent_update:'Correction d’un agent',app_update:'Mise à jour',renewal:'Renouvellement',assistance:'Assistance'};
    let stamp=root.dataset.stamp||'',pending=false,page=1,tickets=[],initialized=false;
    const el=(tag,text='',cls='')=>{const e=document.createElement(tag);e.textContent=text;e.className=cls;return e;};
    function counts(values){for(const [key,value]of Object.entries(values)){const target=root.querySelector('[data-maint-count="'+key+'"]');if(target)target.textContent=value;}}
    async function allTickets(){const db=await SIGDADatabase;return new Promise((resolve,reject)=>{const r=db.transaction('support').objectStore('support').getAll();r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(Error('La file ne peut pas être lue.'));});}
    function row(ticket){
        const item=el('li','','support-ticket'),state=ticket.state||'open';item.dataset.ticketId=ticket.id;
        item.append(el('strong',(categories[ticket.category]||'Demande')+' · '+ticket.owner),el('p',ticket.details),el('small',ticket.id+' · '+fmt.format(ticket.at)+' · '+states[state]+(ticket.handledBy?' · Suivi par '+ticket.handledBy:'')));
        const form=el('form','','support-form');form.dataset.maintTicketForm='true';
        const label=el('label','État'),select=document.createElement('select');select.name='state';for(const [value,text]of Object.entries(states))select.add(new Option(text,value));select.value=state;label.append(select);
        const responseLabel=el('label','Réponse à l’utilisateur'),response=document.createElement('textarea');response.name='response';response.rows=3;response.maxLength=1000;response.required=true;response.value=ticket.response||'';responseLabel.append(response);
        const save=el('button','Enregistrer le suivi','button button-primary');save.type='submit';form.append(label,responseLabel,save);item.append(form);
        const history=el('details','','workflow-history');history.append(el('summary','Historique de prise en charge'));for(const e of ticket.history||[])history.append(el('p',fmt.format(e.at)+' · '+e.actor+' · '+states[e.state]+' · '+e.response));item.append(history);
        form.addEventListener('submit',async event=>{
            event.preventDefault();const answer=response.value.trim();if(!answer||!states[select.value])return;save.disabled=true;const finish=window.SIGDAEffects?.begin(save,'Enregistrement du suivi…');
            try{const db=await SIGDADatabase;const updated=await new Promise((resolve,reject)=>{const tx=db.transaction('support','readwrite'),store=tx.objectStore('support');let result,problem;const get=store.get(ticket.id);get.onsuccess=()=>{const current=get.result;if(!current||(current.revision||0)!==(ticket.revision||0)){problem=Error('Cette demande a changé. Actualisez la file avant de répondre.');tx.abort();return;}result={...current,state:select.value,response:answer,handledBy:who.username,updatedAt:Date.now(),revision:(current.revision||0)+1,history:[...(current.history||[]),{at:Date.now(),actor:who.username,state:select.value,response:answer}]};store.put(result);};tx.oncomplete=()=>resolve(result);tx.onabort=()=>reject(problem||Error('Le suivi ne peut pas être enregistré.'));tx.onerror=()=>reject(problem||Error('La base locale est indisponible.'));});
                item.replaceWith(row(updated));stamp=stamp.replace(ticket.id+':'+(ticket.revision||0),ticket.id+':'+updated.revision);await SIGDAUsage.log('support_update',ticket.id);await refresh(false);channel?.postMessage({type:'support_updated'});window.dispatchEvent(new Event('sigda-support-changed'));finish?.();window.SIGDAEffects?.notify('Suivi enregistré. La réponse est disponible dans l’espace du demandeur sur cet appareil.');
            }catch(error){finish?.();window.SIGDAEffects?.notify(error.message,'error');save.disabled=false;}finally{finish?.();}
        });return item;
    }
    function showTickets(){
        const filter=root.querySelector('[data-maint-filter]').value,selected=tickets.filter(t=>filter==='all'||(t.state||'open')===filter),total=Math.max(1,Math.ceil(selected.length/10));page=Math.min(page,total);
        const list=root.querySelector('[data-maint-tickets]');list.replaceChildren(...selected.slice((page-1)*10,page*10).map(row));if(!list.children.length)list.append(el('li','Aucune demande dans cet état.'));
        root.querySelector('[data-maint-page]').textContent='Page '+page+' / '+total;root.querySelector('[data-maint-previous]').disabled=page===1;root.querySelector('[data-maint-next]').disabled=page===total;
    }
    async function refresh(force=false){
        if(pending)return;pending=true;
        try{
            if(endpoint){const response=await fetch(endpoint,{cache:'no-store',sigdaQuiet:true,headers:{Accept:'application/json'}});if(response.redirected||!response.ok||!response.headers.get('content-type')?.includes('application/json'))throw Error('Le suivi doit être reconnecté. Actualisez la page pour poursuivre.');const data=await response.json();counts(data.counts);if(data.latest!==stamp&&news){news.hidden=false;const link=news.querySelector('a');if(link){const target=new URL(location.href);target.hash='tickets';target.searchParams.set('state','all');target.searchParams.set('_updated',data.latest);target.searchParams.delete('page');link.href=target.href;}}status.textContent='Suivi vérifié à '+fmt.format(new Date(data.checked_at))+' · actualisation des compteurs toutes les 20 secondes.';return;}
            const items=await allTickets(),records=await SIGDAWorkflow.all(),usage=await SIGDAUsage.list(),agents=await SIGDAAgents.list();
            const values={open:0,processing:0,resolved:0,total:items.length};for(const t of items)values[t.state||'open']++;counts(values);
            const updated=items.map(t=>t.id+':'+(t.revision||0)).sort().join('|');if(initialized&&updated!==stamp&&news)news.hidden=false;
            tickets=items.sort((a,b)=>['open','processing','resolved'].indexOf(a.state||'open')-['open','processing','resolved'].indexOf(b.state||'open')||b.at-a.at);
            if(force||!initialized){showTickets();stamp=updated;initialized=true;if(news)news.hidden=true;}
            const metric=root.querySelector('[data-maint-technical]');metric.replaceChildren();for(const [label,value]of [['Agents fictifs',agents.length],['Espaces de démonstration',5],['Documents validés',records.filter(r=>r.status==='approved').length],['Tâches en attente',records.flatMap(r=>r.tasks).filter(t=>t.state==='pending').length]]){const card=el('article','','stats-metric');card.append(el('h2',label),el('strong',value));metric.append(card);}
            const load=root.querySelector('[data-maint-load]');load.replaceChildren();for(const stage of ['OPS','SECAD','AP','DIRCAB']){const line=el('div');line.append(el('strong',stage),el('span',records.flatMap(r=>r.tasks).filter(t=>t.stage===stage&&t.state==='pending').length+' tâche(s) en attente'));load.append(line);}
            const tbody=root.querySelector('[data-maint-usage]');tbody.replaceChildren();const labels={login:'Connexion',logout:'Déconnexion',preview:'Préparation d’un aperçu',draft_create:'Création d’un brouillon',draft_update:'Correction d’un brouillon',submit:'Soumission',approve:'Validation / visa',return:'Retour pour correction',reject:'Refus',support_request:'Demande de maintenance',support_update:'Suivi d’une demande',print_dialog:'Ouverture de l’impression',view:'Consultation'};
            for(const e of usage.sort((a,b)=>b.at-a.at).slice(0,15)){const tr=el('tr');for(const value of [fmt.format(e.at),e.actor,e.role,labels[e.action]||e.action])tr.append(el('td',value));tbody.append(tr);}
            const date=iso=>new Intl.DateTimeFormat('fr',{dateStyle:'long',timeZone:'UTC'}).format(new Date(iso+'T00:00:00Z'));const end=new Date(Date.parse(deploymentConfig.valid_until+'T00:00:00Z')-86400000).toISOString().slice(0,10);root.querySelector('[data-maint-validity]').textContent='Du '+date(deploymentConfig.valid_from)+' au '+date(end)+' inclus. Renouvellement réel réservé à l’équipe habilitée.';
            status.textContent='Source : démonstration locale · vérifiée à '+fmt.format(new Date());
        }catch(error){status.textContent=error.message;if(force)window.SIGDAEffects?.notify(error.message,'error');}finally{pending=false;}
    }
    const channel=!endpoint&&typeof BroadcastChannel==='function'?new BroadcastChannel('sigda-maintenance-demo-v1'):null;if(channel)channel.onmessage=()=>refresh(false);
    if(!endpoint){root.querySelector('[data-maint-filter]').addEventListener('change',()=>{page=1;showTickets();});for(const button of root.querySelectorAll('[data-maint-refresh]'))button.addEventListener('click',()=>refresh(true));root.querySelector('[data-maint-previous]').addEventListener('click',()=>{page--;showTickets();});root.querySelector('[data-maint-next]').addEventListener('click',()=>{page++;showTickets();});}
    document.addEventListener('click',event=>{const button=event.target.closest('[data-maint-focus]');if(button){const target=document.getElementById(button.dataset.maintFocus);target?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth',block:'start'});}});
    window.addEventListener('sigda-view-changed',event=>{if(event.detail.view==='maintenance')refresh(false);});window.addEventListener('sigda-support-changed',()=>refresh(false));
    setInterval(()=>{if(document.visibilityState==='visible'&&(endpoint||!root.closest('[data-view]')?.hidden))refresh(false);},20000);refresh(true);
})();
