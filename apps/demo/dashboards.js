"use strict";
(() => {
    const who=window.SIGDASession||{},root=document.querySelector('[data-role-dashboard]');if(!root)return;
    const profiles={OPS:['Préparation des documents','Brouillons à préparer','Préparez les documents, corrigez les retours et transmettez à SECAD.'],SECAD:['Contrôle administratif','Documents à contrôler','Contrôlez les données et les pièces des tâches qui vous sont attribuées.'],AP:['Visa hiérarchique','Visas à donner','Examinez le contrôle SECAD, puis donnez votre visa ou retournez le dossier.'],DIRCAB:['Décision et supervision','Décisions finales attendues','Décidez des validations finales et consultez le pilotage institutionnel.']};
    const profile=profiles[who.role];if(!profile)return;
    const node=(tag,text,cls='')=>{const e=document.createElement(tag);e.textContent=text;e.className=cls;return e;};
    async function render(){
        const records=(await SIGDAWorkflow.all()).filter(SIGDAWorkflow.canSee),tasks=records.flatMap(r=>r.tasks.map(t=>({...t,record:r}))).filter(t=>t.assignee===who.username),pending=tasks.filter(t=>t.state==='pending');
        const cards=[[profile[1],pending.length],['Échéances dépassées',pending.filter(t=>t.dueAt&&t.dueAt<Date.now()).length],['Tâches terminées',tasks.filter(t=>t.state!=='pending').length],['Retours effectués',tasks.filter(t=>t.state==='returned').length]];
        if(who.role==='OPS'){cards[2]=['Mes documents en validation',records.filter(r=>r.owner===who.username&&['submitted','ap','dircab'].includes(r.status)).length];cards[3]=['Mes documents validés',records.filter(r=>r.owner===who.username&&r.status==='approved').length];}
        root.replaceChildren();root.append(node('h2',profile[0]),node('p',profile[2],'page-description'));
        const metrics=node('div','','stats-metrics');for(const [label,value]of cards){const card=node('article','','stats-metric');card.append(node('h3',label),node('strong',value));metrics.append(card);}root.append(metrics);
        const panel=node('section','','panel'),header=node('div','','panel-header');header.append(node('h2','Mes prochaines tâches'));panel.append(header);const list=node('ul','','demo-list');
        for(const task of pending.slice(0,8)){const row=node('li','','support-ticket');row.append(node('strong',documents[task.record.snapshot.data.kind].title),node('p',task.record.snapshot.reference+' · Révision '+task.revision));const link=node('a','Traiter cette tâche','button');link.href='#requests';row.append(link);list.append(row);}if(!pending.length)list.append(node('li','Aucune tâche en attente dans votre espace.'));panel.append(list);root.append(panel);
        const heading=document.querySelector('[data-view="overview"] h1');heading.textContent='Tableau de bord '+who.role;
        if(!location.hash||location.hash==='#overview'){document.getElementById('view-breadcrumb').textContent=heading.textContent;document.title=heading.textContent+' · SIGDA';}
    }
    window.addEventListener('sigda-workflow-changed',()=>render().catch(()=>{}));render().catch(()=>{root.textContent='Le tableau de bord ne peut pas lire les tâches. Actualisez la page.';});
})();
