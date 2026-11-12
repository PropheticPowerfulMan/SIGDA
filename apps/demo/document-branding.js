"use strict";
window.SIGDADNA=(()=>{
    const ordered=value=>Array.isArray(value)?value.map(ordered):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(key=>[key,ordered(value[key])])):value;
    async function make(snapshot,id,revision,dateLabel){
        const fields=snapshot.data,envelope={schema:'sigda-dna-v1',id,revision,model:fields.kind,reference:snapshot.reference,date:dateLabel,style:'personnalise',body:snapshot.text,fields};
        const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(ordered(envelope))));
        const hash=[...new Uint8Array(bytes)].map(n=>n.toString(16).padStart(2,'0')).join('');
        return {schema:envelope.schema,id,revision,hash,label:'SGD-'+id.replaceAll('-','').slice(0,12).toUpperCase()+'-R'+revision+'-'+hash.slice(0,16).toUpperCase()};
    }
    function fill(root,dna){const panel=root.querySelector('[data-document-identity]');if(!panel||!dna)return;panel.hidden=false;for(const key of ['id','revision','hash','label']){const target=panel.querySelector('[data-dna-'+key+']');if(target)target.textContent=dna[key];}}
    function footer(root,reference,dna){
        const config=institutionalFooter,node=(tag,text,cls='')=>{const e=document.createElement(tag);e.textContent=text;e.className=cls;return e;};
        const link=(label,url)=>{const a=node('a',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;};
        const contacts=node('div','','paper-footer-contacts');contacts.append(link(config.phone,'tel:+243819402122'),link(config.email,'mailto:'+config.email),link(config.website_label,config.website));
        const socials=node('div','','paper-footer-socials');
        for(const item of config.social){const a=link('',item.url);a.setAttribute('aria-label',item.label+' - Présidence RDC');a.title=item.label+' · Présidence RDC';const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');
            for(const shape of institutionalIcons[item.key]){const part=document.createElementNS(svg.namespaceURI,shape.tag);for(const [key,value]of Object.entries(shape))if(!['tag','outline','white'].includes(key))part.setAttribute(key,String(value));part.setAttribute('fill',shape.outline?'none':shape.white?'white':'#2e3845');if(shape.outline){part.setAttribute('stroke','#2e3845');part.setAttribute('stroke-width','1.9');}svg.append(part);}a.append(svg);socials.append(a);}
        const address=node('div','','paper-footer-address');address.append(node('span','Palais de la Nation,'),node('span',config.address),node('span',config.postal));
        root.replaceChildren(contacts,socials,address,node('p',reference+' · Révision '+dna.revision,'paper-footer-reference'),node('p','ADN numérique · '+dna.label,'paper-footer-dna'),node('p','SPÉCIMEN - NON VALABLE · Données fictives','paper-footer-specimen'));
    }
    return {make,fill,footer};
})();
