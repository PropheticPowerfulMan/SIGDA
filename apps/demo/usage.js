"use strict";
window.SIGDADatabase = new Promise((resolve, reject) => {
    const open = indexedDB.open('sigda-demo-agents-v1', 3);
    open.onupgradeneeded = () => {
        const db = open.result;
        if (!db.objectStoreNames.contains('agents')) {
            const store = db.createObjectStore('agents', { keyPath: 'id' });
            store.createIndex('registration_key', 'registration_key', { unique: true });
        }
        if (!db.objectStoreNames.contains('requests')) db.createObjectStore('requests', { keyPath: 'id' });
        if (!db.objectStoreNames.contains('support')) db.createObjectStore('support', { keyPath: 'id' });
        if (!db.objectStoreNames.contains('usage')) db.createObjectStore('usage', { keyPath: 'id', autoIncrement: true });
    };
    open.onsuccess = () => resolve(open.result);
    open.onerror = () => reject(new Error('La base locale est indisponible. Autorisez le stockage de ce site.'));
});
window.SIGDAUsage = {
    async log(action, reference = '') {
        try {
            const db = await SIGDADatabase;
            const actor = sessionStorage.getItem('sigda-demo-user') || '';
            const role = sessionStorage.getItem('sigda-demo-role') || '';
            if (!actor) return;
            return await new Promise((resolve, reject) => {
                const transaction = db.transaction('usage', 'readwrite');
                transaction.objectStore('usage').add({ action, actor, role, reference, at: Date.now() });
                transaction.oncomplete = () => { window.dispatchEvent(new Event('sigda-usage-changed')); resolve(); };
                transaction.onerror = reject;
            });
        } catch { /* The composer reports storage failures before permitting a document. */ }
    },
    async list() {
        const db = await SIGDADatabase;
        return new Promise((resolve, reject) => {
            const request = db.transaction('usage').objectStore('usage').getAll();
            request.onsuccess = () => resolve(request.result); request.onerror = reject;
        });
    }
};
