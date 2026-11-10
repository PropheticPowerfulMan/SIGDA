"use strict";

const form = document.getElementById("specimen-form");
const workshopAgent = document.getElementById("workshop-agent");
const modelSelect = document.getElementById("model");
const agentButtons = [...document.querySelectorAll(".agent-pick")];
const searchInput = document.getElementById("agent-search");
const directoryStatus = document.getElementById("directory-status");
const emptyRow = document.getElementById("empty-agents");
const previewImage = document.getElementById("preview-image");
const downloadLink = document.getElementById("download-link");
const openLink = document.getElementById("open-link");
const requestLink = document.getElementById("request-specimen");
const catalogueGrid = document.getElementById("catalogue-models");
const catalogueFilters = document.getElementById("catalogue-filters");
const catalogueCards = [];
let selectedAgent = "alpha";

function setFamily(family) {
    for (const button of catalogueFilters.querySelectorAll("button")) {
        button.setAttribute("aria-pressed", String(button.dataset.family === family));
    }
    for (const card of catalogueCards) {
        card.hidden = Boolean(family) && card.dataset.family !== family;
    }
}

function setupCatalogue() {
    const models = Object.entries(documents);
    document.getElementById("model-count").textContent = models.length;
    document.getElementById("specimen-count").textContent = models.length * Object.keys(agents).length;

    for (const family of ["", ...new Set(models.map(([, model]) => model.category))]) {
        const button = document.createElement("button");
        button.className = "button";
        button.type = "button";
        button.textContent = family || "Tous";
        button.dataset.family = family;
        button.addEventListener("click", () => setFamily(family));
        catalogueFilters.append(button);
    }

    for (const [key, model] of models) {
        modelSelect.add(new Option(model.title, key));
        const card = document.createElement("button");
        card.className = "catalogue-card";
        card.type = "button";
        card.dataset.model = key;
        card.dataset.family = model.category;
        const category = document.createElement("span");
        category.className = "catalogue-category";
        category.textContent = model.category;
        const title = document.createElement("strong");
        title.textContent = model.title;
        const description = document.createElement("span");
        description.className = "catalogue-description";
        description.textContent = model.description;
        card.append(category, title, description);
        card.addEventListener("click", () => {
            modelSelect.value = key;
            selectAgent(workshopAgent.value);
        });
        catalogueCards.push(card);
        catalogueGrid.append(card);
    }
    setFamily("");
}

function normalizeSearch(value) {
    return value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase("fr").trim();
}

function filterAgents() {
    const query = normalizeSearch(searchInput.value);
    let visible = 0;
    for (const button of agentButtons) {
        const agent = agents[button.dataset.agent];
        const haystack = normalizeSearch(`${agent.name} ${agent.registration} ${agent.service}`);
        const matches = haystack.includes(query);
        button.closest("tr").hidden = !matches;
        if (matches) visible += 1;
    }
    emptyRow.hidden = visible > 0;
    directoryStatus.textContent = visible === 1 ? "1 dossier affiché" : `${visible} dossiers affichés`;
}

function updatePreview() {
    const documentKey = modelSelect.value;
    if (!Object.hasOwn(documents, documentKey)) return;

    const agent = agents[selectedAgent];
    const model = documents[documentKey];
    const specimen = `./assets/specimens/${documentKey}-${selectedAgent}`;

    document.getElementById("agent-name").textContent = agent.name;
    document.getElementById("agent-registration").textContent = agent.registration;
    document.getElementById("agent-service").textContent = agent.service;
    document.getElementById("document-title").textContent = model.title;
    document.getElementById("document-description").textContent = model.description;
    const preview = `${specimen}.png`;
    previewImage.alt = `Aperçu · ${model.title} · ${agent.name}`;
    if (previewImage.getAttribute("src") !== preview) {
        previewImage.src = preview;
        previewImage.parentElement.scrollTo(0, 0);
    }
    downloadLink.href = `${specimen}.pdf`;
    openLink.href = downloadLink.href;
    requestLink.dataset.agent = selectedAgent;
    requestLink.dataset.model = documentKey;
    for (const card of catalogueCards) {
        card.setAttribute("aria-pressed", String(card.dataset.model === documentKey));
    }
    document.getElementById("preview-status").textContent = `Aperçu mis à jour. ${model.title} pour ${agent.name}.`;
}

function selectAgent(key) {
    if (!Object.hasOwn(agents, key)) return;
    selectedAgent = key;
    workshopAgent.value = key;
    for (const button of agentButtons) {
        const selected = button.dataset.agent === key;
        button.setAttribute("aria-pressed", String(selected));
        button.closest("tr").classList.toggle("is-selected", selected);
    }
    updatePreview();
}

setupCatalogue();
updatePreview();

for (const button of agentButtons) {
    button.disabled = false;
    button.addEventListener("click", () => {
        selectAgent(button.dataset.agent);
        window.location.hash = "documents";
    });
}
form.addEventListener("submit", (event) => {
    event.preventDefault();
    selectAgent(workshopAgent.value);
});
modelSelect.disabled = false;
document.getElementById("preview-button").disabled = false;
document.getElementById("directory-tools").hidden = false;
searchInput.addEventListener("input", filterAgents);

const navLinks = document.querySelectorAll(".side-nav a.nav-link");
const views = [...document.querySelectorAll("[data-view]")];
const breadcrumb = document.getElementById("view-breadcrumb");

function updateNavigation(focusHeading = false) {
    const route = window.location.hash.slice(1);
    const active = views.find((view) => view.dataset.view === route) || views[0];
    for (const view of views) view.hidden = view !== active;
    const heading = active.querySelector("h1");
    const hash = `#${active.dataset.view}`;
    for (const link of navLinks) {
        if (link.hash === hash) {
            link.setAttribute("aria-current", "page");
        } else {
            link.removeAttribute("aria-current");
        }
    }
    breadcrumb.textContent = heading.textContent;
    document.title = `${heading.textContent} · SIGDA`;
    document.body.classList.toggle("specimen-page", active.dataset.view === "documents");
    if (focusHeading) {
        window.scrollTo(0, 0);
        heading.tabIndex = -1;
        heading.focus({ preventScroll: true });
    }
}

document.querySelector(".skip-link").addEventListener("click", (event) => {
    event.preventDefault();
    document.getElementById("main").focus();
});
window.addEventListener("hashchange", () => updateNavigation(true));
updateNavigation();
