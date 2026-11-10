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
const modelSelect = document.getElementById("model");
const agentButtons = [...document.querySelectorAll(".agent-pick")];
const searchInput = document.getElementById("agent-search");
const directoryStatus = document.getElementById("directory-status");
const emptyRow = document.getElementById("empty-agents");
const frame = document.getElementById("preview-frame");
const downloadLink = document.getElementById("download-link");
const openLink = document.getElementById("open-link");
const previewFragment = "#toolbar=0&navpanes=0&view=FitH";
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
    const pdf = `./assets/specimens/${documentKey}-${selectedAgent}.pdf`;

    document.getElementById("agent-name").textContent = agent.name;
    document.getElementById("agent-registration").textContent = agent.registration;
    document.getElementById("agent-service").textContent = agent.service;
    document.getElementById("document-title").textContent = model.title;
    document.getElementById("document-description").textContent = model.description;
    frame.title = `Aperçu PDF · ${model.title} · ${agent.name}`;
    if (frame.getAttribute("src") !== pdf + previewFragment) {
        frame.src = pdf + previewFragment;
    }
    downloadLink.href = pdf;
    openLink.href = pdf;
    document.getElementById("preview-status").textContent = `Aperçu mis à jour. ${model.title} pour ${agent.name}.`;
}

for (const button of agentButtons) {
    button.disabled = false;
    button.addEventListener("click", () => {
        selectedAgent = button.dataset.agent;
        for (const agentButton of agentButtons) {
            const selected = agentButton === button;
            agentButton.setAttribute("aria-pressed", String(selected));
            agentButton.closest("tr").classList.toggle("is-selected", selected);
        }
        updatePreview();
    });
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    updatePreview();
});
modelSelect.disabled = false;
document.getElementById("preview-button").disabled = false;
document.getElementById("directory-tools").hidden = false;
searchInput.addEventListener("input", filterAgents);

const navLinks = document.querySelectorAll(".side-nav .nav-link");
function updateNavigation() {
    const location = window.location.hash || "#overview";
    for (const link of navLinks) {
        if (link.hash === location) {
            link.setAttribute("aria-current", "location");
        } else {
            link.removeAttribute("aria-current");
        }
    }
}
window.addEventListener("hashchange", updateNavigation);
updateNavigation();
