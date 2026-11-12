"use strict";
(() => {
    const link=document.querySelector('[data-demo-guide]');if(!link)return;let busy=false;
    link.addEventListener('click',async event=>{
        if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;event.preventDefault();if(busy)return;busy=true;
        const finish=window.SIGDAEffects?.begin(link,'Préparation du guide illustré…');link.setAttribute('aria-disabled','true');
        try{const response=await fetch(link.href,{cache:'no-store'});if(!response.ok||!response.headers.get('content-type')?.includes('application/pdf'))throw Error('Le guide ne peut pas être téléchargé. Réessayez dans un instant.');const blob=await response.blob();if(link.dataset.guideSha256){const digest=await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()),hash=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');if(hash!==link.dataset.guideSha256)throw Error('L’empreinte du guide reçu ne correspond pas à cette édition. Actualisez la page puis réessayez.');}const url=URL.createObjectURL(blob),download=document.createElement('a');download.href=url;download.download=link.download;download.click();setTimeout(()=>URL.revokeObjectURL(url),60000);finish?.();window.SIGDAEffects?.notify('Le téléchargement du guide illustré a été lancé. Retrouvez-le dans les téléchargements de votre appareil.');}
        catch(error){finish?.();window.SIGDAEffects?.notify(error.message||'Le téléchargement n’a pas abouti.','error');}
        finally{finish?.();busy=false;link.removeAttribute('aria-disabled');}
    });
})();
