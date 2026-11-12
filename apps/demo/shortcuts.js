"use strict";
(() => {
 const shell=document.querySelector('.app-shell');if(!shell)return;
 const nav=document.querySelector('.side-nav'),links=[...nav.querySelectorAll('a.nav-link')],bar=document.createElement('nav');bar.className='mobile-quick-nav';bar.setAttribute('aria-label','Accès rapides');
 const find=word=>links.find(a=>a.getAttribute('href').includes(word));
 const home=find('overview')||find('accueil'),create=find('compose'),tasks=find('requests')||find('demandes'),stats=find('activity')||find('activite'),assistant=find('assistant');
 const role=window.SIGDASession?.role||document.body.dataset.profile;
 const entries=[[home,'Accueil','⌂'],[role==='OPS'?create:tasks,role==='OPS'?'Créer':'Tâches','＋'],[role==='OPS'?tasks:role==='DIRCAB'?stats:assistant,role==='OPS'?'Tâches':role==='DIRCAB'?'Pilotage':'Assistant','▤']];
 for(const [source,label,symbol]of entries){if(!source)continue;const a=document.createElement('a');a.href=source.href;const icon=document.createElement('span');icon.textContent=symbol;icon.setAttribute('aria-hidden','true');const text=document.createElement('span');text.textContent=label;a.append(icon,text);bar.append(a);}
 const menu=document.createElement('button');menu.type='button';menu.setAttribute('aria-label','Ouvrir le menu');menu.innerHTML='<span aria-hidden="true">☰</span><span>Menu</span>';menu.addEventListener('click',()=>document.getElementById('menu-toggle').click());bar.append(menu);document.body.append(bar);
 function update(){for(const a of bar.querySelectorAll('a')){if(a.hash?a.hash===(location.hash||'#overview'):a.pathname===location.pathname)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}}
 window.addEventListener('hashchange',update);update();
})();
