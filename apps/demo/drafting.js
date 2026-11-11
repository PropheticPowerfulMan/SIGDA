"use strict";

(() => {
    const editor = document.querySelector("[data-draft-editor]");
    if (!editor) return;
    const form = editor.querySelector("form");
    const status = editor.querySelector("[data-draft-status]");
    const text = form.elements.text;
    let pdfUrl;
    let imageUrl;
    const controls = [...form.querySelectorAll("button")];
    const availability = controls.map((button) => button.disabled);
    text.addEventListener("input", () => {
        status.textContent = "Texte modifié. Appliquez-le pour mettre à jour l’aperçu avant impression.";
    });
    const blobUrl = (uri) => {
        const [header, data] = uri.split(",");
        const bytes = Uint8Array.from(atob(data), (character) => character.charCodeAt(0));
        return URL.createObjectURL(new Blob([bytes], { type: header.slice(5, header.indexOf(";")) }));
    };
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const action = event.submitter?.value || "preview";
        const payload = new FormData(form);
        payload.set("action", action === "preview" ? "preview" : "rewrite");
        payload.set("mode", action === "gpt" ? "gpt" : "local");
        controls.forEach((button) => { button.disabled = true; });
        text.readOnly = true;
        form.setAttribute("aria-busy", "true");
        status.textContent = action === "preview" ? "Préparation de l’aperçu…" : "Préparation de la reformulation…";
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        try {
            const response = await fetch(form.getAttribute("action"), { method: "POST", body: payload, cache: "no-store", signal: controller.signal });
            if (response.redirected) throw new Error("Votre session a expiré. Reconnectez-vous.");
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "La demande n’a pas abouti.");
            if (action === "preview") {
                const nextPdf = blobUrl(result.pdf);
                const nextImage = blobUrl(result.preview);
                if (pdfUrl) URL.revokeObjectURL(pdfUrl);
                if (imageUrl) URL.revokeObjectURL(imageUrl);
                pdfUrl = nextPdf;
                imageUrl = nextImage;
                document.getElementById("preview-image").src = imageUrl;
                const download = document.getElementById("download-link");
                download.href = pdfUrl;
                download.download = result.filename;
                document.getElementById("open-link").href = pdfUrl;
                status.textContent = "Texte appliqué. L’aperçu, le PDF et l’impression utilisent cette version. Cette rédaction reste dans la page et n’est pas enregistrée avec une demande.";
            } else {
                text.value = result.text;
                form.elements.wording.value = result.wording;
                status.textContent = "Reformulation proposée. Relisez les faits et le sens, puis appliquez le texte à l’aperçu.";
            }
        } catch (error) {
            status.textContent = error.name === "AbortError" ? "Le délai est dépassé. Réessayez." : (error.message || "Service indisponible.");
        } finally {
            clearTimeout(timeout);
            controls.forEach((button, index) => { button.disabled = availability[index]; });
            text.readOnly = false;
            form.removeAttribute("aria-busy");
        }
    });
    window.addEventListener("pagehide", (event) => {
        if (event.persisted) return;
        if (pdfUrl) URL.revokeObjectURL(pdfUrl);
        if (imageUrl) URL.revokeObjectURL(imageUrl);
    });
})();
