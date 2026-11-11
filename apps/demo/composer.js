"use strict";
(() => {
    const root = document.querySelector("[data-composer]");
    if (!root) return;
    const server = Boolean(root.dataset.endpoint);
    const read = id => JSON.parse(document.getElementById(id).textContent);
    const schema = server ? read("composition-schema") : compositionSchema;
    const models = server ? read("composition-models") : documents;
    const styles = server ? read("composition-styles") : wordingStyles;
    let records = server ? read("composition-agents") : [];
    const form = root.querySelector("form");
    const kind = form.elements.kind, wording = form.elements.wording, selection = form.elements.agent_id;
    const steps = [...root.querySelectorAll("[data-compose-step]")];
    const next = root.querySelector("[data-compose-next]"), back = root.querySelector("[data-compose-back]");
    const errors = root.querySelector("[data-compose-errors]");
    const print = root.querySelector("[data-compose-print]"), download = root.querySelector("[data-compose-download]");
    const save = root.querySelector("[data-compose-save]"), preview = root.querySelector("[data-compose-preview]");
    const state = root.querySelector("[data-composition-status]");
    let step = 0, editingId = "", ticket = "", pdfUrl = "", imageUrl = "", epoch = 0, busy = false, agentEditing = false;
    let readySnapshot = null, editingDocument = null, displayedDocument = null;
    root.querySelector('[data-agent-support]').href = server ? '/assistance/' : '#support';
    root.querySelector('[data-tasks-back]').href = root.dataset.tasksUrl || '#requests';
    if (!server && window.SIGDASession?.role !== 'OPS') root.querySelector('[data-compose-another]').hidden = true;
    const initial = server ? read("composition-initial") : {};
    const today = root.dataset.today || new Intl.DateTimeFormat("sv-SE", { timeZone: "Africa/Kinshasa" }).format(new Date());
    function message(text) { errors.textContent = text; errors.hidden = !text; if (text) window.SIGDAEffects?.notify(text, 'error'); }
    function invalidated() {
        document.body.dataset.printAuthorized = "false"; readySnapshot = null; displayedDocument = null;
        epoch += 1; ticket = ""; print.disabled = true; download.hidden = true; save.hidden = true;
        root.querySelector("[data-compose-surface]").hidden = true;
        root.querySelector("[data-compose-empty]").hidden = false;
        state.textContent = "Les données ont changé. Générez l’aperçu à l’étape 4.";
    }
    function makeFields(specs, target) {
        target.replaceChildren();
        for (const spec of specs) {
            const wrapper = document.createElement("div");
            if (spec.type === "textarea") wrapper.className = "full-field";
            const label = document.createElement("label"); label.htmlFor = `compose-${spec.key}`; label.textContent = spec.label;
            const input = document.createElement(spec.type === "textarea" ? "textarea" : "input");
            input.id = label.htmlFor; input.name = spec.key;
            if (spec.type !== "textarea") input.type = spec.type;
            else input.rows = 4;
            input.required = spec.key !== "signatory";
            input.maxLength = spec.max; input.placeholder = spec.example;
            if (spec.type === "number") { input.min = "1"; input.max = "999"; input.value = "1"; }
            wrapper.append(label, input); target.append(wrapper);
        }
    }
    makeFields(schema.identity, root.querySelector("[data-identity-fields]"));
    makeFields(schema.common, root.querySelector("[data-common-fields]"));
    form.elements.issue_date.value = today; form.elements.place.value = "Kinshasa";
    form.elements.issuer_service.value = "Service des ressources humaines";
    form.elements.signatory_role.value = "Responsable habilité";
    for (const [key, value] of Object.entries(models)) kind.add(new Option(value.title, key));
    for (const [key, label] of Object.entries(styles)) wording.add(new Option(label, key));
    kind.value = Object.hasOwn(models, root.dataset.initialModel) ? root.dataset.initialModel : "attestation-service";
    if (Object.hasOwn(models, initial.kind)) kind.value = initial.kind;
    if (Object.hasOwn(styles, initial.wording)) wording.value = initial.wording;
    function chosen() { return records.find(record => record.id === selection.value); }
    function profileChoices(preferred = selection.value) {
        selection.replaceChildren(new Option("Choisir un dossier enregistré…", ""));
        for (const record of records) selection.add(new Option(`${record.name} · ${record.registration}`, record.id));
        selection.value = records.some(record => record.id === preferred) ? preferred : "";
    }
    function profileDisplay() {
        const record = chosen(); editingId = record?.id || "";
        agentEditing = false;
        const supportLink = root.querySelector('[data-agent-support]');
        supportLink.textContent = record ? 'Demander une correction' : 'Demander un ajout';
        if (server) supportLink.href = '/assistance/?category=' + (record ? 'agent_update' : 'agent_add');
        for (const spec of schema.identity) {
            const input = form.elements[spec.key]; input.value = record?.[spec.key] || ''; input.readOnly = true;
        }
        root.querySelector('[data-agent-status]').textContent = record ? 'Données lues dans la base agents. Leur correction relève de la maintenance.' : 'Sélectionnez un dossier. S’il manque dans la liste, demandez son ajout à la maintenance.';
        invalidated();
    }
    function modelChanged() {
        const agent = schema.models[kind.value].subject === "agent";
        root.querySelector("[data-agent-section]").hidden = !agent;
        root.querySelector("[data-service-help]").hidden = agent;
        root.querySelector("[data-subject-title]").textContent = agent ? "Quel agent est concerné ?" : "Quel service établit le document ?";
        for (const spec of schema.identity) form.elements[spec.key].required = agent;
        makeFields(schema.models[kind.value].fields, root.querySelector("[data-detail-fields]"));
        root.querySelector(".composer-model-help").textContent = agent ? "Ce document sera rempli avec un dossier de la base agents." : "Ce document porte sur une pièce, un dossier ou une consigne de service.";
        invalidated();
    }
    function showStep(value) {
        step = value; message("");
        steps.forEach((node, index) => { node.hidden = index !== step; });
        root.querySelectorAll(".composer-steps li").forEach((node, index) => {
            if (index === step) node.setAttribute("aria-current", "step"); else node.removeAttribute("aria-current");
            node.classList.toggle("is-complete", index < step);
        });
        back.hidden = step === 0; next.hidden = step === 3;
        next.textContent = ["Continuer vers les données →", "Continuer vers les détails →", "Générer et vérifier le document →"][step] || "";
    }
    function validStep() {
        if (step === 1 && schema.models[kind.value].subject === "agent" && (!chosen() || agentEditing)) {
            message("Sélectionnez un dossier enregistré. La maintenance prend en charge les ajouts et les corrections."); return false;
        }
        for (const input of steps[step].querySelectorAll("input, select, textarea")) {
            if (!input.closest("[hidden]") && !input.checkValidity()) { input.reportValidity(); return false; }
        }
        return true;
    }
    function collect() {
        const data = Object.fromEntries(new FormData(form));
        if (schema.models[kind.value].subject === "agent") Object.assign(data, Object.fromEntries(schema.identity.map(spec => [spec.key, chosen()[spec.key]])));
        return data;
    }
    const csrf = () => root.querySelector('[name="csrfmiddlewaretoken"]')?.value || "";
    async function post(url, payload) {
        const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 30000);
        try {
            const response = await fetch(url, { method: "POST", body: payload, cache: "no-store", signal: controller.signal, headers: { "X-CSRFToken": csrf() } });
            if (response.redirected) throw new Error("Votre session a expiré. Reconnectez-vous.");
            if (!response.headers.get("Content-Type")?.includes("application/json")) throw new Error("Le service est indisponible. Réessayez dans un instant.");
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || Object.entries(result.errors || {}).map(([key, values]) => `${form.elements[key]?.labels?.[0]?.textContent || key} — ${values.join(" ")}`).join("\n") || "Vérifiez les informations saisies.");
            return result;
        } catch (error) { if (error.name === "AbortError") throw new Error("Le délai de réponse est dépassé. Réessayez."); throw error; }
        finally { clearTimeout(timeout); }
    }
    selection.addEventListener("change", profileDisplay);
    kind.addEventListener("change", modelChanged);
    form.addEventListener("input", invalidated);
    form.addEventListener("change", invalidated);
    back.addEventListener("click", () => showStep(step - 1));
    function formatDate(value) {
        const [year, month, day] = value.split("-").map(Number);
        return `${day} ${["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"][month - 1]} ${year}`;
    }
    function localText(data) {
        const values = { ...data };
        for (const spec of [...schema.common, ...schema.models[data.kind].fields]) {
            if (spec.type === "date") values[spec.key] = formatDate(data[spec.key]);
            if (spec.type === "time") values[spec.key] = data[spec.key].replace(":", " h ");
        }
        if (data.kind === "ordre-mission") values.duration = Math.round((Date.parse(data.mission_end) - Date.parse(data.mission_start)) / 86400000) + 1;
        const facts = schema.models[data.kind].facts.replace(/\{([a-z_]+)\}/g, (_, key) => values[key]);
        return `${schema.openings[data.wording]}\n\n${facts}\n\n${schema.closings[data.wording]}`;
    }
    function review(data, text) {
        const list = root.querySelector("[data-review]"); list.replaceChildren();
        const specs = [...(schema.models[data.kind].subject === "agent" ? schema.identity : []), ...schema.common, ...schema.models[data.kind].fields];
        for (const spec of specs) {
            if (!data[spec.key]) continue;
            const row = document.createElement("div"); const term = document.createElement("dt"), value = document.createElement("dd");
            term.textContent = spec.label; value.textContent = spec.type === "date" ? formatDate(data[spec.key]) : data[spec.key]; row.append(term, value); list.append(row);
        }
        root.querySelector("[data-composed-text]").textContent = text;
    }
    function objectUrl(uri) {
        const [header, encoded] = uri.split(",");
        return URL.createObjectURL(new Blob([Uint8Array.from(atob(encoded), c => c.charCodeAt(0))], { type: header.slice(5, header.indexOf(";")) }));
    }
    form.addEventListener("submit", async event => {
        event.preventDefault(); if (busy || step === 3) return;
        if (!server) { try { SIGDAService.assertCreation(); } catch(error) { message(error.message); return; } }
        if (!validStep()) return;
        if (step < 2) { showStep(step + 1); return; }
        const data = collect();
        for (const [start, end] of [["mission_start", "mission_end"], ["from_time", "to_time"]]) {
            if (data[start] && data[end] && data[end] < data[start]) { message("La date ou l’heure de fin doit être postérieure ou égale au début."); return; }
        }
        const version = epoch; busy = true; next.disabled = true; message(""); state.textContent = "Création du document avec vos données…";
        try {
            let text, reference;
            if (!server && schema.models[data.kind].subject === "agent") {
                records = await SIGDAAgents.list();
                const current = records.find(record => record.id === data.agent_id);
                if (!current) throw new Error("Le dossier n’est plus disponible. Revenez aux données et choisissez un dossier.");
                Object.assign(data, Object.fromEntries(schema.identity.map(spec => [spec.key, current[spec.key]])));
            }
            if (server) {
                const payload = new FormData(form);
                if (root.dataset.draftId) payload.set("draft_id", root.dataset.draftId);
                const result = await post(root.dataset.endpoint, payload);
                if (version !== epoch) return;
                Object.assign(data, result.data);
                text = result.text; reference = result.reference; ticket = result.ticket;
                const nextImage = objectUrl(result.preview);
                if (imageUrl) URL.revokeObjectURL(imageUrl);
                imageUrl = nextImage;
                const image = document.createElement("img"); image.src = imageUrl; image.alt = `Document rempli — ${models[data.kind].title}`;
                preview.replaceChildren(image); await image.decode();
                download.hidden = true; save.hidden = false;
            } else {
                text = localText(data);
                reference = editingDocument?.snapshot.reference || `SPEC-${data.kind.split("-").map(word => word[0]).join("").toUpperCase()}-${crypto.randomUUID().replaceAll("-", "").slice(0, 12).toUpperCase()}-${data.issue_date.slice(0, 4)}`;
                const paper = await buildPaper(data, text, reference);
                if (version !== epoch) return;
                preview.replaceChildren(paper);
                await SIGDAUsage.log("preview", reference);
            }
            if (version !== epoch) return;
            review(data, text); showStep(3); root.querySelector("[data-compose-surface]").hidden = false;
            root.querySelector("[data-compose-empty]").hidden = true; fitPaper();
            readySnapshot = { data, text, reference };
            print.disabled = true; save.hidden = false;
            state.textContent = `${models[data.kind].title} · ${reference} · Aperçu non validé`;
            document.title = `${models[data.kind].title} · ${reference} · SIGDA`;
            window.SIGDAEffects?.notify("L’aperçu du document est prêt. Relisez-le avant de l’enregistrer dans le circuit de validation.");
        } catch (error) { message(error.message || "Impossible de préparer le document."); state.textContent = "L’aperçu n’a pas été généré."; }
        finally { busy = false; next.disabled = false; }
    });
    save.addEventListener("click", async () => {
        save.disabled = true;
        try {
            if (server) { const payload = new FormData(); payload.set("ticket", ticket); location.assign((await post(root.dataset.saveEndpoint, payload)).url); }
            else { editingDocument = await SIGDAWorkflow.saveDraft(readySnapshot, editingDocument?.id || "", editingDocument?.revision || 0); location.hash = "requests"; save.disabled = false; }
        }
        catch (error) { message(error.message); save.disabled = false; }
    });
    print.addEventListener("click", async () => {
        if (print.disabled || !displayedDocument) return;
        try {
            const latest = await SIGDAWorkflow.get(displayedDocument.id);
            if (latest.status !== "approved" || latest.revision !== displayedDocument.revision) throw new Error("La validation finale est requise pour imprimer cette version.");
            await SIGDAWorkflow.printAccess(latest.id, latest.revision);
            document.body.dataset.printAuthorized = "true";
            window.print();
        } catch (error) { message(error.message); }
    });
    root.querySelector("[data-compose-view]").addEventListener("click", () => root.querySelector(".composer-preview").scrollIntoView({ block: "start" }));
    root.querySelector("[data-compose-another]").addEventListener("click", () => { editingDocument = null; root.classList.remove("review-mode"); window.SIGDAReviewMode = false; modelChanged(); root.querySelector('[data-compose-step="3"] h2').textContent = "Vérifiez avant de soumettre"; showStep(0); root.scrollIntoView({ block: "start" }); });
    root.querySelector("[data-storage-help]").textContent = "Enregistrez le brouillon, puis confiez la tâche à SECAD. Le document passera ensuite par AP et DIRCAB. La version finale deviendra imprimable après toutes les validations.";
    root.querySelector("[data-database-help]").textContent = server ? "Base agents privée de votre compte · documents et brouillons conservés sur le serveur." : "Base de démonstration locale à cet appareil · utilisez des données fictives. Aucun dossier saisi n’est envoyé à un serveur.";
    async function initialize() {
        try {
            if (!server) records = await SIGDAAgents.list();
            profileChoices(initial.agent_id || root.dataset.initialAgent); profileDisplay();
            for (const [key, value] of Object.entries(initial)) if (form.elements[key] && !schema.identity.some(spec => spec.key === key) && key !== "agent_id") form.elements[key].value = value;
        }
        catch (error) { message(error.message); }
    }
    for (const link of document.querySelectorAll('a[data-roles="OPS"][href="#compose"]')) link.addEventListener('click', () => { editingDocument = null; root.classList.remove('review-mode'); window.SIGDAReviewMode = false; modelChanged(); showStep(0); });
    modelChanged(); showStep(0); initialize();
    window.addEventListener("sigda-view-changed", event => {
        document.body.dataset.printAuthorized = event.detail.view === "compose" && displayedDocument?.status === "approved" ? "true" : "false";
    });
    window.addEventListener("sigda-review-document", async event => {
        try {
            const record = await SIGDAWorkflow.get(event.detail.record.id);
            window.SIGDAReviewMode = true; root.classList.add("review-mode"); location.hash = "compose";
            root.querySelector('[data-compose-step="3"] h2').textContent = record.status === "approved" ? "Version validée" : "Document à examiner";
            const data = record.snapshot.data;
            kind.value = data.kind; wording.value = data.wording;
            review(data, record.snapshot.text); showStep(3); back.hidden = true;
            root.querySelector("[data-compose-another]").hidden = window.SIGDASession.role !== "OPS";
            const paper = await buildPaper(data, record.snapshot.text, record.snapshot.reference, record.status === "approved");
            preview.replaceChildren(paper); root.querySelector("[data-compose-surface]").hidden = false; root.querySelector("[data-compose-empty]").hidden = true;
            save.hidden = true; print.disabled = record.status !== "approved";
            displayedDocument = record; fitPaper();
            state.textContent = `${record.snapshot.reference} · Révision ${record.revision} · ${record.status === "approved" ? "Validation finale obtenue" : "Aperçu non validé"}`;
            await new Promise(resolve => requestAnimationFrame(resolve));
            document.body.dataset.printAuthorized = record.status === "approved" && location.hash === "#compose" ? "true" : "false";
        } catch (error) { message(error.message); }
    });
    window.addEventListener("sigda-edit-document", async event => {
        try {
            const record = await SIGDAWorkflow.get(event.detail.record.id);
            if (window.SIGDASession.role !== "OPS" || record.status !== "draft") throw new Error("Seul OPS peut corriger ce brouillon.");
            records = await SIGDAAgents.list(); editingDocument = record;
            root.classList.remove("review-mode"); window.SIGDAReviewMode = false;
            kind.value = record.snapshot.data.kind; wording.value = record.snapshot.data.wording;
            modelChanged(); profileChoices(record.snapshot.data.agent_id); profileDisplay();
            for (const [key, value] of Object.entries(record.snapshot.data)) if (form.elements[key] && !schema.identity.some(spec => spec.key === key) && key !== "agent_id") form.elements[key].value = value;
            showStep(0); location.hash = "compose";
        } catch (error) { message(error.message); }
    });
    window.addEventListener("sigda-compose", async event => {
        if (!server) records = await SIGDAAgents.list();
        profileChoices(event.detail.newAgent ? "" : event.detail.agent || selection.value); profileDisplay();
        if (event.detail.kind && Object.hasOwn(models, event.detail.kind)) { kind.value = event.detail.kind; modelChanged(); }
        showStep(event.detail.newAgent ? 1 : 0); location.hash = "compose";
    });
    function fitPaper() {
        const holder = preview.querySelector(".paper-holder"); if (!holder) return;
        const scale = Math.min(1, (preview.clientWidth - 22) / (595.276 * 96 / 72));
        holder.style.width = `${595.276 * 96 / 72 * scale}px`; holder.style.height = `${841.89 * 96 / 72 * scale}px`;
        holder.firstElementChild.style.transform = `scale(${scale})`;
    }
    new ResizeObserver(fitPaper).observe(preview);
    async function buildPaper(data, text, reference, approved = false) {
        const holder = document.createElement("div"); holder.className = "paper-holder";
        const paper = document.createElement("article"); paper.className = "composed-page"; holder.append(paper);
        const certificate = models[data.kind].category === "Attestations";
        function part(className, content) { const node = document.createElement("div"); node.className = className; node.textContent = content; paper.append(node); return node; }
        paper.classList.toggle("certificate-paper", certificate);
        part("paper-nation", "République Démocratique du Congo");
        if (!certificate) part("paper-presidency", "PRÉSIDENCE DE LA RÉPUBLIQUE");
        const logo = document.createElement("img"); logo.src = root.dataset.emblem; logo.alt = ""; logo.className = "paper-emblem"; paper.append(logo);
        part("paper-institution", "CABINET DU PRÉSIDENT DE LA RÉPUBLIQUE");
        part("paper-issuer", data.issuer_service);
        part("paper-date", `${data.place}, le ${formatDate(data.issue_date)}`);
        part("paper-reference", `N/Réf. : ${reference}`);
        part("paper-specimen", "SPÉCIMEN — NON VALABLE");
        if (!approved) part("paper-watermark", "APERÇU — NON VALIDÉ");
        if (!certificate) part("paper-recipient", `${data.recipient || data.name}\nà ${data.place.toUpperCase()}`);
        part("paper-title", models[data.kind].title.toUpperCase());
        const watermark = document.createElement("img"); watermark.src = root.dataset.emblem; watermark.alt = ""; watermark.setAttribute("aria-hidden", "true"); watermark.className = "paper-body-emblem";
        const bodyTop = certificate ? 310 : 364, bodyLimit = data.kind === "bordereau-transmission" ? 532 : 622;
        const watermarkSize = Math.min(250, bodyLimit - bodyTop);
        watermark.style.width = `${watermarkSize}pt`; watermark.style.height = `${watermarkSize}pt`; watermark.style.top = `${(bodyTop + bodyLimit - watermarkSize) / 2}pt`;
        paper.append(watermark);
        const body = part("paper-body", "");
        for (const paragraph of text.split("\n\n")) { const p = document.createElement("p"); p.textContent = paragraph; body.append(p); }
        let table;
        if (data.kind === "bordereau-transmission") {
            table = document.createElement("table"); table.className = "paper-table";
            for (const values of [["Désignation de la pièce", "Nombre"], [data.item, data.quantity]]) {
                const row = document.createElement("tr"); for (const value of values) { const cell = document.createElement("td"); cell.textContent = value; row.append(cell); } table.append(row);
            }
            paper.append(table);
        }
        const signature = part("paper-signature", `Fait à ${data.place}, le ${formatDate(data.issue_date)}\n\n${data.signatory || data.signatory_role}\n\nSignature et cachet`);
        const footer = part("paper-footer", "");
        for (const line of ["+243 81 940 21 22       sgpr@presidence.cd       www.presidence.cd", "Palais de la Nation · Avenue Roi Baudouin, Gombe · Kinshasa", reference, "SPÉCIMEN — NON VALABLE · Données de démonstration"]) {
            const p = document.createElement("p"); p.textContent = line; footer.append(p);
        }
        const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
        const hash = [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
        const link = "https://propheticpowerfulman.github.io/SIGDA/fiche.html#" + new URLSearchParams({ m: data.kind, r: reference, d: formatDate(data.issue_date), s: "personnalise", h: hash });
        const code = qrcode(0, "M"); code.addData(link); code.make(); const count = code.getModuleCount();
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("viewBox", `-4 -4 ${count + 8} ${count + 8}`); svg.classList.add("paper-qr");
        const white = document.createElementNS(svg.namespaceURI, "rect"); for (const [key, value] of Object.entries({ x: -4, y: -4, width: count + 8, height: count + 8, fill: "white" })) white.setAttribute(key, value); svg.append(white);
        const path = document.createElementNS(svg.namespaceURI, "path"); let drawing = "";
        for (let row = 0; row < count; row++) for (let col = 0; col < count; col++) if (code.isDark(row, col)) drawing += `M${col},${row}h1v1h-1z`;
        path.setAttribute("d", drawing); path.setAttribute("fill", "black"); svg.append(path); paper.append(svg);
        // Measure at physical A4 size before scaling it for the screen.
        holder.style.position = "fixed"; holder.style.left = "-10000px"; document.body.append(holder);
        await document.fonts.ready;
        const limit = data.kind === "bordereau-transmission" ? 532 : 622;
        let bottom = 0;
        for (const size of [12, 11.5, 11]) {
            body.style.fontSize = `${size}pt`; body.style.lineHeight = `${size + 6}pt`;
            bottom = (body.offsetTop + body.offsetHeight) * 72 / 96;
            if (bottom <= limit) break;
        }
        if (bottom > limit) { holder.remove(); throw new Error("Le texte est trop long pour une page A4. Raccourcissez les champs de détail."); }
        if (table) { table.style.top = `${bottom + 5}pt`; bottom += table.offsetHeight * 72 / 96 + 14; }
        const signatureTop = Math.max(571, bottom + 35);
        signature.style.top = `${signatureTop}pt`;
        if (signatureTop + signature.offsetHeight * 72 / 96 > 733) { holder.remove(); throw new Error("Le texte dépasse la zone disponible. Raccourcissez les détails ou le nom du signataire."); }
        holder.remove(); holder.style.position = ""; holder.style.left = "";
        return holder;
    }
})();
