"use strict";
// Shared by the public simulation and the authenticated DIRCAB workspace.
window.SIGDAStatistics = (() => {
    const day = at => new Intl.DateTimeFormat('en-CA', {timeZone:'Africa/Kinshasa',year:'numeric',month:'2-digit',day:'2-digit'}).format(at);
    const quantile = (values,p) => {if(!values.length)return null;const v=[...values].sort((a,b)=>a-b),r=p*(v.length-1),i=Math.floor(r);return v[i]+(r-i)*(v[Math.min(i+1,v.length-1)]-v[i]);};
    function wilson(k,n){if(!n)return null;const z=1.96,p=k/n,d=1+z*z/n,c=(p+z*z/(2*n))/d,h=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return [Math.max(0,c-h),Math.min(1,c+h)];}
    function compute(data,period=30){
        const now=data.now||Date.now(),today=day(now),midnight=Date.parse(today+'T00:00:00+01:00'),begin=midnight-(period-1)*86400000,end=midnight+86400000;
        const within=at=>at>=begin&&at<end&&at<=now;
        const days=Array.from({length:period},(_,i)=>({date:day(begin+i*86400000),submitted:0,decided:0,actions:0,actors:new Set()})),byDay=new Map(days.map(d=>[d.date,d]));
        let submitted=0,approved=0,rejected=0,returned=0;const durations=[],stages=['OPS','SECAD','AP','DIRCAB'].map(role=>({role,pending:0,overdue:0,durations:[]}));
        for(const record of data.records||[]){
            const events=[...record.events].sort((a,b)=>a.at-b.at),first=events.find(e=>e.type==='submit');
            for(const e of events.filter(e=>within(e.at))){const d=byDay.get(day(e.at));if(e.type==='submit'){submitted++;d.submitted++;}if(e.type==='return')returned++;
                if((e.type==='approve'&&e.status==='approved')||e.type==='reject'){e.status==='approved'?approved++:rejected++;d.decided++;if(first&&e.at>=first.at)durations.push((e.at-first.at)/3600000);}}
            for(const t of record.tasks||[]){const s=stages.find(s=>s.role===t.stage);if(!s)continue;if(t.state==='pending'){s.pending++;if(t.dueAt&&t.dueAt<now)s.overdue++;}if(t.completedAt&&within(t.completedAt)&&t.completedAt>=t.createdAt)s.durations.push((t.completedAt-t.createdAt)/3600000);}
        }
        const usage=(data.usage||[]).filter(e=>within(e.at));for(const e of usage){const d=byDay.get(day(e.at));d.actions++;d.actors.add(e.actor);}
        return {begin,end,days,submitted,approved,rejected,returned,durations,stages,usage,active:new Set(usage.map(e=>e.actor)).size,interval:wilson(approved,approved+rejected)};
    }
    return {compute,quantile,wilson};
})();

(() => {
    const root=document.querySelector('[data-statistics]');if(!root)return;
    const source=document.getElementById('statistics-data');
    if(!source&&window.SIGDASession?.role!=='DIRCAB')return;
    let data=source?JSON.parse(source.textContent):{records:[],usage:[]};
    const nf=new Intl.NumberFormat('fr',{maximumFractionDigits:1});
    const fmt=new Intl.DateTimeFormat('fr',{dateStyle:'short',timeStyle:'short',timeZone:'Africa/Kinshasa'});
    const el=(tag,text,cls='')=>{const e=document.createElement(tag);e.textContent=text;e.className=cls;return e;};
    const svgEl=(tag,attrs,text)=>{const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;};
    const hours=n=>n===null?'—':n<1?nf.format(n*60)+' min':nf.format(n)+' h';
    function table(headers,rows,expand=true){const wrap=el('div','','stats-table-wrap'),t=el('table','','stats-table'),head=el('thead'),tr=el('tr');headers.forEach(h=>{const th=el('th',h);th.scope='col';tr.append(th);});head.append(tr);const body=el('tbody');for(const row of rows){const r=el('tr');row.forEach(v=>r.append(el('td',String(v))));body.append(r);}if(!rows.length){const r=el('tr'),c=el('td','Aucune observation dans cette période.');c.colSpan=headers.length;r.append(c);body.append(r);}t.append(head,body);wrap.append(t);if(!expand)return wrap;const details=el('details');details.append(el('summary','Consulter les valeurs du graphique'),wrap);return details;}
    function chart(rows,a,b,labelA,labelB){
        const fragment=document.createDocumentFragment(),legend=el('div','','stats-legend');legend.append(el('span',labelA),el('span',labelB));fragment.append(legend);
        const svg=svgEl('svg',{viewBox:'0 0 600 235',role:'img','aria-label':labelA+' et '+labelB+' par jour ; valeurs disponibles dans le tableau suivant.'}),max=Math.max(1,...rows.flatMap(r=>[r[a],r[b]]));
        const x=i=>65+i*490/Math.max(1,rows.length-1),y=n=>190-n*160/max;
        for(let i=0;i<=4;i++){const v=max*i/4;svg.append(svgEl('line',{x1:65,y1:y(v),x2:555,y2:y(v),class:'grid-line'}),svgEl('text',{x:50,y:y(v)+4,'text-anchor':'end'},nf.format(v)));}
        for(const [key,cls] of [[a,'stats-series-a'],[b,'stats-series-b']])svg.append(svgEl('polyline',{points:rows.map((r,i)=>x(i)+','+y(r[key])).join(' '),class:cls}));
        [...new Set([0,Math.floor((rows.length-1)/2),rows.length-1])].forEach(i=>svg.append(svgEl('text',{x:x(i),y:218,'text-anchor':'middle'},rows[i].date.slice(8)+'/'+rows[i].date.slice(5,7))));
        fragment.append(svg,table(['Jour',labelA,labelB],rows.map(r=>[r.date,r[a],r[b]])));return fragment;
    }
    const actionLabels={login:'Connexion',logout:'Déconnexion',preview:'Aperçu',draft_create:'Création du brouillon',draft_update:'Modification du brouillon',submit:'Soumission',approve:'Validation',return:'Retour pour correction',reject:'Refus final',agent_create:'Création d’un dossier agent',agent_update:'Modification d’un dossier agent',pdf_open:'Ouverture du PDF validé',final_pdf_open:'Ouverture du PDF validé',print_dialog:'Dialogue d’impression'};
    function render(){
        const s=SIGDAStatistics.compute({...data,now:source?data.now:Date.now()},Number(root.querySelector('[data-stat-period]').value)),decided=s.approved+s.rejected,n=s.durations.length,q=p=>SIGDAStatistics.quantile(s.durations,p);
        const cards=[['Actions enregistrées',nf.format(s.usage.length),`${s.active} utilisateur(s) distinct(s) · ${s.usage.filter(e=>e.action==='login').length} connexion(s)`],['Soumissions',nf.format(s.submitted),`${s.returned} retour(s) pour correction · ratio ${s.submitted?nf.format(100*s.returned/s.submitted)+' %':'—'}`],['Approbation finale',decided?nf.format(100*s.approved/decided)+' %':'—',`${s.approved} accord(s) / ${decided} décision(s) · IC 95 % ${s.interval?s.interval.map(v=>nf.format(v*100)+' %').join(' à '):'non calculable'}`],['Délai médian',hours(q(.5)),`P90 ${hours(q(.9))} · n = ${n} dossier(s) clos${n<10?' · échantillon réduit':''}`]];
        root.querySelector('[data-stat-summary]').replaceChildren(...cards.map(([title,value,note])=>{const card=el('article','','stats-metric');card.append(el('h2',title),el('strong',value),el('p',note));return card;}));
        root.querySelector('[data-stat-flow]').replaceChildren(chart(s.days,'submitted','decided','Soumissions','Décisions finales'));
        const stageRoot=root.querySelector('[data-stat-stages]');stageRoot.replaceChildren();const peak=Math.max(1,...s.stages.map(t=>t.pending));
        for(const stage of s.stages){const row=el('div','','stats-stage'),track=el('div','','stats-stage-track'),fill=el('div','','stats-stage-fill');fill.style.width=(100*stage.pending/peak)+'%';track.append(fill);row.append(el('strong',stage.role),track,el('span',stage.pending));stageRoot.append(row);}
        stageRoot.append(el('p',s.stages.reduce((n,t)=>n+t.overdue,0)+' tâche(s) en retard sur les échéances renseignées.','stats-note'),table(['Profil','En attente','En retard','Médiane de traitement','n'],s.stages.map(t=>[t.role,t.pending,t.overdue,hours(SIGDAStatistics.quantile(t.durations,.5)),t.durations.length])));
        const delay=root.querySelector('[data-stat-delay]');delay.replaceChildren();
        if(n){const svg=svgEl('svg',{viewBox:'0 0 600 140',role:'img','aria-label':'Distribution des délais en heures. Minimum, quartiles et maximum dans le tableau.'}),max=Math.max(q(1),.001),x=v=>45+v*510/max;
            svg.append(svgEl('line',{x1:x(q(0)),x2:x(q(1)),y1:55,y2:55,stroke:'currentColor'}),svgEl('rect',{x:x(q(.25)),y:30,width:Math.max(1,x(q(.75))-x(q(.25))),height:50,fill:'var(--accent-soft)',stroke:'var(--accent)'}));
            for(const p of [0,.5,1])svg.append(svgEl('line',{x1:x(q(p)),x2:x(q(p)),y1:25,y2:85,stroke:'var(--accent)','stroke-width':p===.5?3:1}));
            svg.append(svgEl('text',{x:45,y:119},hours(q(0))),svgEl('text',{x:555,y:119,'text-anchor':'end'},hours(q(1))));delay.append(svg);
        }else delay.append(el('p','La distribution apparaîtra après la première décision finale.','stats-note'));
        delay.append(table(['Minimum','Q1','Médiane','Q3','P90','Maximum','n'],n?[[0,.25,.5,.75,.9,1].map(p=>hours(q(p))).concat(n)]:[],false));
        root.querySelector('[data-stat-usage]').replaceChildren(chart(s.days.map(d=>({...d,users:d.actors.size})),'actions','users','Actions','Utilisateurs distincts'));
        root.querySelector('[data-stat-log]').replaceChildren(table(['Horodatage · Kinshasa','Compte','Profil','Action'],[...s.usage].sort((a,b)=>b.at-a.at).slice(0,50).map(e=>[fmt.format(e.at),e.actor,e.role||'—',actionLabels[e.action]||e.action]),false));
    }
    async function refresh(){if(!source){data={records:await SIGDAWorkflow.all(),usage:await SIGDAUsage.list()};}render();}
    root.querySelector('[data-stat-period]').addEventListener('change',render);
    for(const event of ['sigda-workflow-changed','sigda-usage-changed'])window.addEventListener(event,()=>refresh().catch(()=>{}));
    refresh().catch(()=>{root.querySelector('[data-stat-summary]').textContent='Le stockage des événements est indisponible.';});
})();
