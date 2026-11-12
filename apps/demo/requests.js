"use strict";
window.SIGDAWorkflow = (() => {
    const stateRole = { draft: 'OPS', submitted: 'SECAD', ap: 'AP', dircab: 'DIRCAB' };
    const next = { draft: ['SECAD','submitted'], submitted: ['AP','ap'], ap: ['DIRCAB','dircab'] };
    const session = () => window.SIGDASession || {};
    async function all() {
        const db = await SIGDADatabase;
        return new Promise((resolve,reject) => {const r=db.transaction('requests').objectStore('requests').getAll();r.onsuccess=()=>resolve(r.result);r.onerror=reject;});
    }
    function canSee(record) { const who=session();return who.role==='DIRCAB'||record.owner===who.username||record.tasks.some(task=>task.assignee===who.username||task.assignedBy===who.username); }
    async function get(id) { const record=(await all()).find(item=>item.id===id);if(!record||!canSee(record))throw new Error('Ce document ne fait pas partie de votre périmètre.');return record; }
    async function mutate(id, change) {
        const db=await SIGDADatabase;
        return new Promise((resolve,reject)=>{
            const tx=db.transaction('requests','readwrite'),store=tx.objectStore('requests');let result,problem;
            const r=store.get(id);r.onsuccess=()=>{try{result=change(r.result);store.put(result);}catch(error){problem=error;tx.abort();}};
            tx.oncomplete=()=>{window.dispatchEvent(new Event('sigda-workflow-changed'));resolve(result);};
            tx.onabort=()=>reject(problem||new Error('La tâche a changé. Actualisez le suivi.'));tx.onerror=()=>reject(problem||new Error('La base ne peut pas enregistrer cette action.'));
        });
    }
    function task(record,stage,assignee,actor,due='') {return {id:crypto.randomUUID(),stage,assignee,assignedBy:actor,createdAt:Date.now(),dueAt:due?new Date(due).getTime():null,completedAt:null,state:'pending',revision:record.revision,cycle:record.cycle,snapshotHash:record.snapshotHash,note:''};}
    async function digest(value) {const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(value)));return [...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join('');}
    async function saveDraft(snapshot,id='',expectedRevision=0) {
        const who=session();if(who.role!=='OPS')throw new Error('La préparation appartient au profil OPS.');
        SIGDAService.assertCreation();
        const snapshotHash=await digest(snapshot);
        let record;
        if(id){record=await mutate(id,record=>{if(!record||record.owner!==who.username||record.status!=='draft'||record.revision!==expectedRevision)throw new Error('Ce brouillon a changé ou est déjà en validation.');if(record.snapshotHash===snapshotHash)return record;record.snapshot=snapshot;record.snapshotHash=snapshotHash;record.revision+=1;record.tasks.filter(t=>t.state==='pending').forEach(t=>{t.revision=record.revision;t.snapshotHash=snapshotHash;});record.events.push({type:'updated',status:'draft',actor:who.username,role:who.role,at:Date.now(),note:'Nouvelle révision enregistrée.',revision:record.revision,cycle:record.cycle});return record;});}
        else {
            record={id:snapshot.documentId||crypto.randomUUID(),owner:who.username,status:'draft',revision:1,cycle:0,snapshot,snapshotHash,createdAt:Date.now(),tasks:[],events:[]};
            record.tasks.push(task(record,'OPS',who.username,who.username));record.events.push({type:'created',status:'draft',actor:who.username,role:who.role,at:Date.now(),note:'Document préparé depuis la base agents.',revision:1,cycle:0});
            const db=await SIGDADatabase;await new Promise((resolve,reject)=>{const tx=db.transaction('requests','readwrite');tx.objectStore('requests').add(record);tx.oncomplete=resolve;tx.onerror=reject;});window.dispatchEvent(new Event('sigda-workflow-changed'));
        }
        await SIGDAUsage.log(id?'draft_update':'draft_create',snapshot.reference);return record;
    }
    async function act(id,action,assignee,note,due,revision,cycle) {
        const who=session();
        if(action==='submit')SIGDAService.assertCreation();
        const record=await mutate(id,record=>{
            if(!record||!canSee(record)||record.revision!==revision||record.cycle!==cycle)throw new Error('Le dossier ou sa révision a changé. Actualisez.');
            const active=record.tasks.find(t=>t.state==='pending');
            if(!active||active.assignee!==who.username||active.stage!==who.role||stateRole[record.status]!==who.role)throw new Error('Cette tâche ne vous est pas attribuée.');
            if(who.role!=='OPS'&&record.owner===who.username)throw new Error('Vous ne pouvez pas valider votre propre document.');
            if(active.revision!==record.revision||active.snapshotHash!==record.snapshotHash)throw new Error('La version ne correspond pas à la tâche.');
            const allowed=who.role==='OPS'?['submit']:who.role==='DIRCAB'?['approve','return','reject']:['approve','return'];
            if(!allowed.includes(action))throw new Error('Action non autorisée pour ce profil.');
            note=(note||'').trim();if(['return','reject'].includes(action)&&!note)throw new Error('Le motif est obligatoire pour un retour ou un refus.');
            const before=record.status;let after=action==='return'?'draft':action==='reject'?'rejected':next[before]?.[1]||'approved';
            if(!['return','reject'].includes(action)&&next[before]&&assignee!==next[before][0].toLowerCase())throw new Error('Choisissez le responsable de la prochaine étape.');
            if(after==='approved'){
                const stages=record.tasks.filter(t=>t.cycle===record.cycle&&t.revision===record.revision&&t.snapshotHash===record.snapshotHash&&t.state==='approved').map(t=>t.stage);
                if(!['SECAD','AP'].every(stage=>stages.includes(stage)))throw new Error('Les contrôles SECAD et AP sont requis.');
                record.issuedAt=Date.now();record.approvedContentHash=record.snapshotHash;
            }
            active.state=action==='return'?'returned':action==='reject'?'rejected':action==='submit'?'completed':'approved';active.completedAt=Date.now();active.note=note;
            if(action==='submit')record.cycle+=1;
            record.status=after;
            if(action==='return')record.tasks.push(task(record,'OPS',record.owner,who.username));
            else if(!['approved','rejected'].includes(after))record.tasks.push(task(record,stateRole[after],assignee,who.username,due));
            const labels={submit:'Soumission à SECAD',approve:who.role==='DIRCAB'?'Validation finale DIRCAB':`Contrôle / visa ${who.role}`,return:`Retour à OPS par ${who.role}`,reject:'Refus final DIRCAB'};
            record.events.push({type:action,status:after,actor:who.username,role:who.role,at:Date.now(),note:labels[action]+(note?' · '+note:''),revision:record.revision,cycle:record.cycle});return record;
        });
        await SIGDAUsage.log(action,record.snapshot.reference);return record;
    }
    async function printAccess(id, revision) {
        const who = session();
        const record = await mutate(id, record => {
            if (!record || !canSee(record) || record.status !== 'approved' || record.revision !== revision) throw new Error('La validation finale est requise pour imprimer cette version.');
            record.accesses = record.accesses || [];
            record.accesses.push({ actor: who.username, role: who.role, at: Date.now() });
            return record;
        });
        await SIGDAUsage.log('print_dialog', record.snapshot.reference);
    }
    return {all,get,canSee,saveDraft,act,printAccess,stateRole,next};
})();

(() => {
    const list=document.getElementById('demo-request-list'),status=document.getElementById('demo-request-status');
    const who=window.SIGDASession||{};
    const labels={draft:'Préparation OPS',submitted:'Contrôle SECAD',ap:'Visa AP',dircab:'Validation DIRCAB',approved:'Validé — impression autorisée',rejected:'Refus final'};
    const fmt=new Intl.DateTimeFormat('fr',{dateStyle:'short',timeStyle:'short',timeZone:'Africa/Kinshasa'});
    function element(tag,text,className=''){const node=document.createElement(tag);node.textContent=text;node.className=className;return node;}
    function button(parent,text,action,primary=false){const b=element('button',text,primary?'button button-primary':'button');b.type='button';b.addEventListener('click',action);parent.append(b);return b;}
    function renderRecord(record){
        const card=element('li','','workflow-card');card.dataset.requestId=record.id;
        const data=record.snapshot.data,active=record.tasks.find(t=>t.state==='pending');
        card.append(element('h2',documents[data.kind].title),element('p',data.name||data.item||data.subject||data.issuer_service),element('p',record.snapshot.reference+' · Révision '+record.revision),element('span',labels[record.status],'status-pill'));
        if(active)card.append(element('p',`Responsable : ${active.assignee} (${active.stage}) · Attribuée par ${active.assignedBy}${active.dueAt?' · Échéance '+fmt.format(active.dueAt):''}`));
        const actions=element('div','','view-actions');
        button(actions,record.status==='approved'?'Ouvrir la version validée':'Consulter l’aperçu non validé',()=>window.dispatchEvent(new CustomEvent('sigda-review-document',{detail:{record}})));
        if(who.role==='OPS'&&record.owner===who.username&&record.status==='draft')button(actions,'Corriger ou compléter',()=>window.dispatchEvent(new CustomEvent('sigda-edit-document',{detail:{record}})));
        card.append(actions);
        if(active?.assignee===who.username&&active.stage===who.role){
            const form=element('form','','task-form');let assignee,due;
            const target=SIGDAWorkflow.next[record.status]?.[0];
            if(target){const label=element('label','Confier la prochaine tâche au compte '+target);assignee=document.createElement('select');assignee.add(new Option(target+' · '+target.toLowerCase(),target.toLowerCase()));label.append(assignee);form.append(label);const dl=element('label','Échéance facultative (heure locale de votre appareil)');due=document.createElement('input');due.type='datetime-local';dl.append(due);form.append(dl);}
            const nl=element('label','Commentaire ou motif du retour');const note=document.createElement('textarea');note.rows=3;note.maxLength=350;nl.append(note);form.append(nl);
            async function decide(action){
                for(const b of form.querySelectorAll('button'))b.disabled=true;
                try{await SIGDAWorkflow.act(record.id,action,assignee?.value||'',note.value,due?.value||'',record.revision,record.cycle);status.textContent='Action enregistrée et tâche attribuée.';}
                catch(error){status.textContent=error.message;for(const b of form.querySelectorAll('button'))b.disabled=false;}
            }
            const controls=element('div','','view-actions');
            button(controls,who.role==='OPS'?'Soumettre à SECAD':who.role==='SECAD'?'Contrôler et transmettre à AP':who.role==='AP'?'Donner le visa et transmettre à DIRCAB':'Valider définitivement et autoriser l’impression',()=>decide(who.role==='OPS'?'submit':'approve'),true);
            if(who.role!=='OPS')button(controls,'Retourner à OPS pour correction',()=>decide('return'));
            if(who.role==='DIRCAB')button(controls,'Refuser le document',()=>decide('reject'));
            form.append(controls);form.addEventListener('submit',event=>event.preventDefault());card.append(form);
        }
        const details=element('details','','workflow-history');details.append(element('summary','Historique et responsabilités'));
        for(const event of record.events)details.append(element('p',`${fmt.format(event.at)} · ${event.actor} (${event.role}) · ${event.note} · Révision ${event.revision}`));
        for(const task of record.tasks)details.append(element('p',`Tâche ${task.stage} → ${task.assignee} · ${task.state} · Cycle ${task.cycle} / révision ${task.revision}`));
        for(const access of record.accesses || [])details.append(element('p',`${fmt.format(access.at)} · ${access.actor} (${access.role}) · Ouverture du dialogue d’impression`));
        card.append(details);
        if(record.identity){const identity=element('details','','document-identity');identity.append(element('summary','ADN numérique et révision'),element('p',record.identity.id+' · Révision '+record.identity.revision),element('code',record.identity.hash));card.append(identity);}return card;
    }
    async function render(){try{
        const all=await SIGDAWorkflow.all(),records=all.filter(SIGDAWorkflow.canSee).sort((a,b)=>b.createdAt-a.createdAt);
        const dateLabel=new Intl.DateTimeFormat('fr-FR',{dateStyle:'long',timeZone:'UTC'});
        const cards=await Promise.all(records.map(async record=>{record.identity=await SIGDADNA.make(record.snapshot,record.id,record.revision,dateLabel.format(new Date(record.snapshot.data.issue_date+'T12:00:00Z')));return renderRecord(record);}));
        list.replaceChildren(...cards);if(!records.length)list.append(element('li','Aucun document dans votre périmètre. OPS peut en préparer un depuis la base agents.'));
        const assigned=records.filter(r=>r.tasks.some(t=>t.state==='pending'&&t.assignee===who.username)).length;
        for(const node of document.querySelectorAll('[data-my-task-count]'))node.textContent=assigned;
        window.dispatchEvent(new CustomEvent('sigda-workflow-data',{detail:{records:all}}));
    }catch(error){status.textContent=error.message;}}
    window.addEventListener('sigda-workflow-changed',render);render();
})();
