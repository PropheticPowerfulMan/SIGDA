"use strict";

const agents = {
    alpha: {
        name: "Camille Exemple",
        registration: "DEMO-001",
        service: "Service des systèmes d’information",
    },
    beta: {
        name: "Dominique Témoin",
        registration: "DEMO-002",
        service: "Service de la gestion documentaire",
    },
};

const documents = {
    "attestation-nuit": {
        title: "Attestation de travail de nuit",
        description: "Certifier une affectation au service de nuit.",
    },
    notification: {
        title: "Notification administrative",
        description: "Notifier une régularisation de situation administrative.",
    },
};

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
let selectedAgent = "alpha";

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
        previewImage.parentElement.scrollTop = 0;
    }
    downloadLink.href = `${specimen}.pdf`;
    openLink.href = downloadLink.href;
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

const navLinks = document.querySelectorAll(".side-nav .nav-link");
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
