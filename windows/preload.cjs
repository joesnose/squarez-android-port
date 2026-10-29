const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('squarezLAN', { host: () => ipcRenderer.invoke('lan-host'), stop: () => ipcRenderer.invoke('lan-stop'), discover: () => ipcRenderer.invoke('lan-discover') });
