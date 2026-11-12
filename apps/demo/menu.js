"use strict";
(() => {
    const button=document.getElementById('menu-toggle'),shell=document.querySelector('.app-shell');
    if(!button||!shell)return;
    const sidebar=shell.querySelector('.sidebar'),main=shell.querySelector('.main-shell'),narrow=matchMedia('(max-width: 900px)');
    const backdrop=document.createElement('button');backdrop.className='menu-backdrop';backdrop.type='button';backdrop.hidden=true;backdrop.tabIndex=-1;backdrop.setAttribute('aria-label','Fermer le menu');document.body.append(backdrop);
    const close=document.createElement('button');close.className='menu-close';close.type='button';close.textContent='×';close.setAttribute('aria-label','Fermer le menu');sidebar.prepend(close);
    function setCollapsed(collapsed,focus=false){
        shell.dataset.menuCollapsed=String(collapsed);button.setAttribute('aria-expanded',String(!collapsed));button.setAttribute('aria-label',collapsed?'Développer le menu':'Replier le menu');
        const open=narrow.matches&&!collapsed;backdrop.hidden=!narrow.matches;backdrop.dataset.open=String(open);sidebar.inert=narrow.matches&&collapsed;main.inert=open;const quick=document.querySelector('.mobile-quick-nav');if(quick)quick.inert=open;document.body.classList.toggle('menu-open',open);
        if(open){sidebar.setAttribute('role','dialog');sidebar.setAttribute('aria-modal','true');sidebar.setAttribute('aria-label','Menu principal');if(focus)close.focus();}
        else{sidebar.removeAttribute('role');sidebar.removeAttribute('aria-modal');sidebar.removeAttribute('aria-label');if(focus&&narrow.matches)button.focus();}
    }
    function restore(){let saved=null;try{saved=sessionStorage.getItem('sigda-menu-desktop');}catch{}setCollapsed(narrow.matches?true:saved==='true');}
    button.addEventListener('click',()=>{const collapsed=shell.dataset.menuCollapsed!=='true';setCollapsed(collapsed,true);if(!narrow.matches)try{sessionStorage.setItem('sigda-menu-desktop',String(collapsed));}catch{}});
    for(const target of [backdrop,close])target.addEventListener('click',()=>setCollapsed(true,true));
    sidebar.addEventListener('click',event=>{if(narrow.matches&&event.target.closest('a[href]'))setCollapsed(true);});
    sidebar.addEventListener('keydown',event=>{
        if(!narrow.matches||shell.dataset.menuCollapsed==='true')return;
        if(event.key==='Escape'){event.preventDefault();setCollapsed(true,true);}
        if(event.key==='Tab'){const nodes=[...sidebar.querySelectorAll('a[href],button:not(:disabled),input,select,textarea')].filter(node=>node.getClientRects().length);const first=nodes[0],last=nodes.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
    });
    narrow.addEventListener('change',restore);window.addEventListener('hashchange',()=>{if(narrow.matches)setCollapsed(true);});window.addEventListener('pageshow',event=>{if(event.persisted&&narrow.matches)setCollapsed(true);});restore();button.hidden=false;
})();
