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
        const valid = [...data.keys()].length === 5
            && ["m", "r", "d", "s", "h"].every(key => data.getAll(key).length === 1)
            && Object.hasOwn(documents, model) && Object.hasOwn(styles, style)
            && /^SPEC-[A-Z0-9-]{1,60}$/.test(reference) && dateValid && /^[a-f0-9]{64}$/.test(hash);
        error.hidden = Boolean(valid);
        title.textContent = valid ? documents[model].title : "Lecture du QR";
        if (!valid) return;
        for (const [id, value] of Object.entries({
            "sheet-reference": reference, "sheet-model": documents[model].title,
            "sheet-date": date, "sheet-style": styles[style], "sheet-hash": hash,
        })) document.getElementById(id).textContent = value;
        fields.hidden = false;
    }
    readSheet();
    window.addEventListener("hashchange", readSheet);
})();
