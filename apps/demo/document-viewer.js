"use strict";
(() => {
    let dialog, viewport, stage, canvas, level, notice, less, more, closing=false, opener, mode='width', scale=1, generation=0, closeTimer;
    const width=210*96/25.4, height=297*96/25.4, reduced=matchMedia('(prefers-reduced-motion: reduce)');
    function control(label,text,action){const b=document.createElement('button');b.type='button';b.className='button';b.setAttribute('aria-label',label);b.textContent=text;b.addEventListener('click',action);return b;}
    function create(){
        dialog=document.createElement('dialog');dialog.className='document-viewer';dialog.setAttribute('aria-labelledby','document-viewer-title');
        const header=document.createElement('header');header.className='document-viewer-header';
        const heading=document.createElement('div'),title=document.createElement('h2');title.id='document-viewer-title';title.textContent='Aperçu grand format';
        notice=document.createElement('p');heading.append(title,notice);const close=control('Fermer l’aperçu','×',dismiss);close.className='button document-viewer-close';header.append(heading,close);
        const tools=document.createElement('div');tools.className='document-viewer-tools';tools.setAttribute('role','group');tools.setAttribute('aria-label','Zoom du document');
        less=control('Réduire le document','−',()=>zoom(scale-.15));more=control('Agrandir le document','+',()=>zoom(scale+.15));
        level=document.createElement('output');level.setAttribute('aria-live','polite');level.setAttribute('aria-label','Niveau de zoom');
        const fitWidth=control('Ajuster à la largeur','Largeur',()=>fit('width')),fitPage=control('Afficher la page entière','Page entière',()=>fit('page')),actual=control('Afficher à 100 %','100 %',()=>zoom(1));
        tools.append(less,level,more,fitWidth,fitPage,actual);
        viewport=document.createElement('div');viewport.className='document-viewer-viewport';viewport.tabIndex=0;viewport.setAttribute('role','region');viewport.setAttribute('aria-label','Document en lecture : défilement horizontal et vertical');
        stage=document.createElement('div');stage.className='document-viewer-stage';canvas=document.createElement('div');canvas.className='document-viewer-canvas';stage.append(canvas);viewport.append(stage);
        const foot=document.createElement('p');foot.className='document-viewer-note';foot.textContent='Lecture seule · L’impression reste accessible depuis le circuit de validation après accord de DIRCAB.';
        dialog.append(header,tools,viewport,foot);document.body.append(dialog);
        dialog.addEventListener('cancel',event=>{event.preventDefault();dismiss();});
        dialog.addEventListener('close',()=>{if(!dialog.open)cleanup();});
        dialog.addEventListener('keydown',event=>{
            if(event.ctrlKey||event.metaKey||event.altKey)return;
            if(['+','=','-','0'].includes(event.key)){event.preventDefault();if(event.key==='0')zoom(1);else zoom(scale+(event.key==='-'?-.15:.15));}
            if(event.key==='Tab'){const nodes=[...dialog.querySelectorAll('button:not(:disabled),[tabindex="0"]')],first=nodes[0],last=nodes.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
        });
        new ResizeObserver(()=>{if(dialog.open&&!closing&&mode!=='custom')fit(mode);}).observe(viewport);
        window.addEventListener('beforeprint',closeNow);
        window.addEventListener('hashchange',closeNow);
        return close;
    }
    function cleanup(){if(!document.body.classList.contains('document-viewer-open'))return;clearTimeout(closeTimer);generation++;closing=false;dialog.removeAttribute('aria-busy');delete dialog.dataset.closing;document.body.classList.remove('document-viewer-open');canvas.replaceChildren();if(opener?.isConnected)opener.focus({preventScroll:true});}
    function closeNow(){if(dialog?.open)dialog.close();if(dialog)cleanup();}
    function dismiss(){if(!dialog?.open||closing)return;closing=true;if(reduced.matches){closeNow();return;}dialog.dataset.closing='true';closeTimer=setTimeout(closeNow,170);}
    function update(value,preserve=false){
        const x=(viewport.scrollLeft+viewport.clientWidth/2)/(viewport.scrollWidth||1),y=(viewport.scrollTop+viewport.clientHeight/2)/(viewport.scrollHeight||1);
        scale=Math.max(.2,Math.min(2.5,value));stage.style.width=width*scale+'px';stage.style.height=height*scale+'px';canvas.style.transform=`scale(${scale})`;
        level.textContent=Math.round(scale*100)+' %';less.disabled=scale<=.2;more.disabled=scale>=2.5;
        for(const b of dialog.querySelectorAll('.document-viewer-tools button')){const label=b.getAttribute('aria-label');if(label==='Ajuster à la largeur')b.setAttribute('aria-pressed',String(mode==='width'));else if(label==='Afficher la page entière')b.setAttribute('aria-pressed',String(mode==='page'));}
        if(preserve)viewport.scrollTo(x*viewport.scrollWidth-viewport.clientWidth/2,y*viewport.scrollHeight-viewport.clientHeight/2);else viewport.scrollTo(0,0);
    }
    function fit(value){mode=value;const css=getComputedStyle(viewport),w=viewport.clientWidth-parseFloat(css.paddingLeft)-parseFloat(css.paddingRight),h=viewport.clientHeight-parseFloat(css.paddingTop)-parseFloat(css.paddingBottom);if(w>0&&h>0)update(value==='page'?Math.min(w/width,h/height,1.5):Math.min(w/width,1.5));}
    function zoom(value){mode='custom';update(value,true);}
    async function open(button){
        if(dialog?.open)return;
        const target=document.getElementById(button.dataset.viewerSource),original=target?.querySelector('.composed-page')||target?.querySelector('img');
        if(!original){window.SIGDAEffects?.notify('Générez d’abord l’aperçu du document.','error');return;}
        const close=dialog?dialog.querySelector('.document-viewer-close'):create();opener=button;closing=false;clearTimeout(closeTimer);delete dialog.dataset.closing;
        const current=++generation,clone=original.cloneNode(true);clone.style.transform='none';clone.style.width='100%';clone.style.height='100%';clone.style.maxWidth='none';clone.style.margin='0';
        canvas.replaceChildren(clone);canvas.style.width=width+'px';canvas.style.height=height+'px';canvas.dataset.ready='false';
        notice.textContent='Préparation de la lecture…';dialog.setAttribute('aria-busy','true');dialog.showModal();document.body.classList.add('document-viewer-open');fit('width');close.focus();
        try{
            const images=clone.matches('img')?[clone]:[...clone.querySelectorAll('img')];await Promise.all(images.map(image=>image.decode()));await document.fonts.ready;
            if(current!==generation||!dialog.open)return;
            notice.textContent=target.closest('[data-composer]')?.querySelector('[data-composition-status]')?.textContent||button.dataset.viewerLabel||'Document administratif · A4';
            canvas.dataset.ready='true';fit('width');
        }catch{if(current===generation&&dialog.open){closeNow();window.SIGDAEffects?.notify('L’aperçu ne peut pas être chargé. Réessayez depuis le document.','error');}}
        finally{if(current===generation)dialog.removeAttribute('aria-busy');}
    }
    document.addEventListener('click',event=>{const button=event.target.closest('[data-document-viewer]');if(button&&!button.disabled){event.preventDefault();open(button);}});
})();
