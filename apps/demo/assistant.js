"use strict";

(() => {
    const root = document.querySelector("[data-assistant]");
    const form = root.querySelector("[data-ai-form]");
    const messages = root.querySelector(".assistant-messages");
    const initial = messages.firstElementChild.cloneNode(true);
    const question = root.querySelector('[name="question"]');
    const mode = root.querySelector('[name="mode"]');
    const submit = form.querySelector('[type="submit"]');
    const clear = root.querySelector("[data-ai-clear]");
    const status = root.querySelector("[data-ai-status]");

    function words(text) {
        return new Set(text.normalize("NFD").replace(/\p{Diacritic}/gu, "")
            .toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").split(" ")
            .filter(word => word.length > 1 && !assistantStopwords.includes(word)));
    }

    function localAnswer(text) {
        const query = words(text);
        const options = assistantGuides.map(guide => ({
            title: guide.title, text: guide.text, target: guide.target, model: null,
            keywords: new Set(guide.terms),
        }));
        for (const [key, model] of Object.entries(documents)) {
            options.push({
                title: model.title, text: model.description, target: "documents", model: key,
                keywords: new Set([...words(model.title), ...(assistantAliases[key] || [])]),
            });
        }
        const ranked = options.map(option => ({
            ...option, score: [...query].filter(word => option.keywords.has(word)).length,
        })).filter(option => option.score > 0).sort((a, b) => b.score - a.score).slice(0, 3);
        return {
            text: ranked.length
                ? ranked.map(option => `${option.title}\n${option.text}`).join("\n\n")
                : "Je peux vous guider dans le catalogue, l’impression A4, les demandes et les statistiques. Précisez le document recherché ou l’étape concernée.",
            links: ranked.map(({ title, target, model }) => ({ label: title, target, model })),
            mode: "Guidage local",
        };
    }

    function appendMessage(text, who) {
        const row = document.createElement("div");
        row.className = `assistant-message ${who === "Vous" ? "assistant-user" : "assistant-reply"}`;
        const label = document.createElement("strong");
        label.textContent = who;
        const body = document.createElement("p");
        body.textContent = text;
        row.append(label, body);
        messages.append(row);
        return row;
    }

    function appendLinks(row, links) {
        const routes = {
            compose: root.dataset.composeUrl,
            documents: root.dataset.documentsUrl,
            requests: root.dataset.requestsUrl,
            activity: root.dataset.activityUrl,
        };
        for (const item of links || []) {
            if (!routes[item.target]) continue;
            const link = document.createElement("a");
            link.className = "button";
            link.textContent = item.label;
            link.href = routes[item.target];
            if (item.model && item.target === "documents") {
                if (form.dataset.endpoint) {
                    const target = new URL(link.href);
                    target.searchParams.set("type", item.model);
                    link.href = target.href;
                } else {
                    link.addEventListener("click", () => {
                        const model = document.getElementById("model");
                        if ([...model.options].some(option => option.value === item.model)) {
                            model.value = item.model;
                            document.getElementById("specimen-form").requestSubmit();
                        }
                    });
                }
            }
            row.append(link);
        }
    }

    for (const suggestion of root.querySelectorAll("[data-ai-suggestion]")) {
        suggestion.addEventListener("click", () => {
            question.value = suggestion.textContent.trim();
            question.focus();
        });
    }
    clear.addEventListener("click", () => {
        messages.replaceChildren(initial.cloneNode(true));
        status.textContent = "";
        question.focus();
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (submit.disabled) return;
        const text = question.value.trim();
        if (!text) return;
        const selectedMode = mode.value;
        const payload = new FormData(form);
        appendMessage(text, "Vous");
        question.value = "";
        submit.disabled = true;
        clear.disabled = true;
        mode.disabled = true;
        status.textContent = "Recherche en cours…";
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 30000);
        try {
            let result;
            if (form.dataset.endpoint) {
                const response = await fetch(form.dataset.endpoint, {
                    method: "POST", body: payload, signal: controller.signal,
                    credentials: "same-origin", cache: "no-store",
                    headers: { "Accept": "application/json" },
                });
                if (response.redirected) throw new Error("Votre session a expiré. Reconnectez-vous.");
                result = await response.json();
                if (!response.ok) throw new Error(result.error || "L’assistant est indisponible.");
            } else {
                result = localAnswer(text);
            }
            const row = appendMessage(result.text, result.mode);
            appendLinks(row, result.links);
            status.textContent = selectedMode === "gpt" ? "Réponse GPT reçue." : "Réponse du guidage local.";
        } catch (error) {
            status.textContent = error.name === "AbortError" ? "Le délai de réponse est dépassé. Réessayez." : error.message;
        } finally {
            clearTimeout(timer);
            submit.disabled = false;
            clear.disabled = false;
            mode.disabled = false;
            messages.scrollTop = messages.scrollHeight;
        }
    });
})();
