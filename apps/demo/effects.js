"use strict";
(() => {
    const reduced=matchMedia('(prefers-reduced-motion: reduce)'),counts=new WeakMap();let pending=0,delay,viewAnimation;
    const progress=document.createElement('div');progress.className='fx-progress';progress.hidden=true;progress.setAttribute('role','status');
    const loading=document.createElement('span');loading.className='sr-only';loading.textContent='Traitement en cours';progress.append(loading);
    const dialog=document.createElement('dialog');dialog.className='fx-result';dialog.setAttribute('aria-modal','true');dialog.setAttribute('aria-labelledby','fx-result-title');dialog.setAttribute('aria-describedby','fx-result-message');
    const mark=document.createElement('span');mark.className='fx-result-mark';mark.setAttribute('aria-hidden','true');
    const title=document.createElement('h2');title.id='fx-result-title';const text=document.createElement('p');text.id='fx-result-message';
    const close=document.createElement('button');close.type='button';close.className='button button-primary';
    dialog.append(mark,title,text,close);document.body.append(progress,dialog);
    let active=null,lastKey='',lastClosed=0;const queue=[];
    function nextResult(){
        if(active||!queue.length)return;active=queue.shift();dialog.dataset.kind=active.kind;dialog.setAttribute('role',active.kind==='error'?'alertdialog':'dialog');
        title.textContent=active.kind==='error'?'L’action n’a pas abouti':'Action confirmée';text.textContent=active.message;mark.textContent=active.kind==='error'?'!':'✓';close.textContent=active.kind==='error'?'Revenir à l’action':'Continuer';
        if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');close.focus();
    }
    function finishResult(){if(!active)return;lastKey=active.key;lastClosed=Date.now();const done=active.resolve;active=null;done();queueMicrotask(nextResult);}
    close.addEventListener('click',()=>{if(typeof dialog.close==='function')dialog.close();else{dialog.removeAttribute('open');finishResult();}});
    dialog.addEventListener('close',finishResult);
    document.addEventListener('keydown',event=>{if(dialog.open&&event.key==='Tab'){event.preventDefault();close.focus();}});
    function notify(message,kind='success'){
        if(!message)return Promise.resolve();const key=kind+':'+message;
        if(key===lastKey&&Date.now()-lastClosed<1200)return Promise.resolve();
        if(active?.key===key)return active.promise;
        let resolve;const promise=new Promise(done=>{resolve=done;});queue.push({message,kind,key,resolve,promise});nextResult();return promise;
    }
    function begin(button){
        pending++;if(pending===1)delay=setTimeout(()=>{if(pending)progress.hidden=false;},140);
        if(button?.matches('button,.button')){counts.set(button,(counts.get(button)||0)+1);button.dataset.fxLoading='true';}
        let finished=false;return()=>{if(finished)return;finished=true;pending=Math.max(0,pending-1);if(!pending){clearTimeout(delay);progress.hidden=true;}if(button&&counts.has(button)){const n=counts.get(button)-1;if(n>0)counts.set(button,n);else{counts.delete(button);delete button.dataset.fxLoading;}}};
    }
    window.SIGDAEffects={notify,begin};
    const originalFetch=window.fetch;
    window.fetch=async function(...args){const end=begin(document.activeElement);try{return await originalFetch.apply(this,args);}finally{end();}};
    document.addEventListener('pointerdown',event=>{
        const button=event.target.closest('button,.button,.nav-link,.catalogue-card');if(!button||button.disabled||reduced.matches)return;
        const rect=button.getBoundingClientRect(),size=Math.max(rect.width,rect.height)*2,ink=document.createElement('span');ink.className='fx-ink';ink.setAttribute('aria-hidden','true');ink.style.cssText=`width:${size}px;height:${size}px;left:${event.clientX-rect.left-size/2}px;top:${event.clientY-rect.top-size/2}px`;
        button.classList.add('fx-clickable');button.append(ink);ink.addEventListener('animationend',()=>ink.remove(),{once:true});setTimeout(()=>ink.remove(),700);
    },{passive:true});
    let nativePending=new WeakSet();
    document.addEventListener('submit',event=>{
        const form=event.target,button=event.submitter;
        if(event.defaultPrevented){
            if(button?.disabled){const end=begin(button),observer=new MutationObserver(()=>{if(!button.disabled||!button.isConnected){observer.disconnect();end();}});observer.observe(document.body,{attributes:true,attributeFilter:['disabled'],childList:true,subtree:true});}
            return;
        }
        if(form.method.toLowerCase()==='post'){
            if(nativePending.has(form)){event.preventDefault();return;}
            nativePending.add(form);form.setAttribute('aria-busy','true');begin(button);
        }
    });
    function wrap(object,key,message){
        if(!object?.[key])return;const original=object[key];object[key]=async function(...args){const end=begin(document.activeElement);try{const result=await original.apply(this,args);end();if(message)await notify(message);return result;}catch(error){end();await notify(error.message||'L’opération n’a pas abouti.','error');throw error;}finally{end();}};
    }
    wrap(window.SIGDAWorkflow,'saveDraft','Brouillon enregistré. Le circuit de validation est disponible.');
    wrap(window.SIGDAWorkflow,'act','Étape enregistrée et responsabilités actualisées.');
    wrap(window.SIGDAWorkflow,'printAccess','Version validée prête pour l’impression.');
    window.addEventListener('sigda-view-changed',event=>{
        const node=document.querySelector(`[data-view="${event.detail.view}"]`);if(!node||reduced.matches)return;
        viewAnimation?.cancel();viewAnimation=node.animate([{opacity:.35,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:170,easing:'ease-out'});
    });
    window.addEventListener('beforeprint',()=>viewAnimation?.finish());
    window.addEventListener('pageshow',event=>{if(event.persisted){nativePending=new WeakSet();for(const form of document.querySelectorAll('form[aria-busy="true"]'))form.removeAttribute("aria-busy");pending=0;progress.hidden=true;for(const node of document.querySelectorAll('[data-fx-loading]'))delete node.dataset.fxLoading;}});
    let invalidBatch=false;
    document.addEventListener('invalid',event=>{
        event.preventDefault();if(invalidBatch)return;invalidBatch=true;setTimeout(()=>{invalidBatch=false;},100);
        const input=event.target,label=input.labels?.[0]?.textContent.trim()||'le champ demandé';
        notify('Vérifiez « '+label+' ». '+input.validationMessage,'error').then(()=>input.focus());
    },true);
    const feedback=document.querySelector('[data-feedback-message]');if(feedback)notify(feedback.textContent);
    try { const message=sessionStorage.getItem('sigda-result-message');sessionStorage.removeItem('sigda-result-message');if(message)notify(message); } catch {}
    const initialError=document.querySelector('.errorlist, [role="alert"]:not([hidden])');if(initialError?.textContent.trim())notify(initialError.textContent.trim(),'error');
})();
