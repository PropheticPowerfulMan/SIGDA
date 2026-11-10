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
const agentSelect = document.getElementById("agent");
const modelSelect = document.getElementById("model");
const frame = document.getElementById("preview-frame");
const downloadLink = document.getElementById("download-link");
const openLink = document.getElementById("open-link");
const previewFragment = "#toolbar=0&navpanes=0&view=FitH";

function updatePreview() {
    const agentKey = agentSelect.value;
    const documentKey = modelSelect.value;
    if (!Object.hasOwn(agents, agentKey) || !Object.hasOwn(documents, documentKey)) {
        return;
    }

    const agent = agents[agentKey];
    const model = documents[documentKey];
    const pdf = `./assets/specimens/${documentKey}-${agentKey}.pdf`;

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

form.addEventListener("submit", (event) => {
    event.preventDefault();
    updatePreview();
});
document.getElementById("preview-button").disabled = false;
