"use strict";

(() => {
    const title = document.getElementById("sheet-title");
    const fields = document.getElementById("sheet-data");
    const error = document.getElementById("sheet-error");
    const styles = { ...wordingStyles, personnalise: "Texte personnalisé" };
    function readSheet() {
        fields.hidden = true;
        const encoded = location.hash.slice(1);
        if (encoded.length >= 700) {
            error.hidden = false;
            title.textContent = "Lecture du QR";
            return;
        }
        const data = new URLSearchParams(encoded);
        const model = data.get("m");
        const reference = data.get("r") || "";
        const date = data.get("d") || "";
        const style = data.get("s");
        const hash = data.get("h") || "";
        const month = "janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre";
        const match = date.match(new RegExp(`^(\\d{1,2}) (${month}) (\\d{4})$`));
        const monthIndex = match ? month.split("|").indexOf(match[2]) : -1;
        const parsed = match ? new Date(Date.UTC(Number(match[3]), monthIndex, Number(match[1]))) : null;
        const dateValid = parsed && parsed.getUTCFullYear() === Number(match[3])
            && parsed.getUTCMonth() === monthIndex && parsed.getUTCDate() === Number(match[1]);
        const hasDNA=data.has('a'),keys=hasDNA?['m','r','d','s','h','a','u','v','e']:['m','r','d','s','h'];
        const dnaValid=!hasDNA||(data.get('e')==='sigda-dna-v1'&&/^[a-f0-9]{64}$/.test(data.get('a')||'')&&/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(data.get('u')||'')&&/^[1-9][0-9]{0,8}$/.test(data.get('v')||''));
        const valid = [...data.keys()].length === keys.length
            && keys.every(key => data.getAll(key).length === 1) && dnaValid
            && Object.hasOwn(documents, model) && Object.hasOwn(styles, style)
            && /^SPEC-[A-Z0-9-]{1,60}$/.test(reference) && dateValid && /^[a-f0-9]{64}$/.test(hash);
        error.hidden = Boolean(valid);
        title.textContent = valid ? documents[model].title : "Lecture du QR";
        if (!valid) return;
        for (const [id, value] of Object.entries({
            "sheet-reference": reference, "sheet-model": documents[model].title,
            "sheet-date": date, "sheet-style": styles[style], "sheet-hash": hash,
        })) document.getElementById(id).textContent = value;
        for(const node of document.querySelectorAll('[data-sheet-dna]'))node.hidden=!hasDNA;
        if(hasDNA){document.getElementById('sheet-dna').textContent=data.get('a');document.getElementById('sheet-identity').textContent=data.get('u')+' · Révision '+data.get('v');}
        fields.hidden = false;
    }
    readSheet();
    window.addEventListener("hashchange", readSheet);
})();
