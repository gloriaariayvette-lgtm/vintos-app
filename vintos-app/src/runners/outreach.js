addEventListener('checkOutreach', async (resolve, reject) => {
  try {
    const HOST = '100.72.225.119';
    const PORT = 8500;
    const SECRET = 'vintos-aegis-2026';

    const response = await fetch(`http://${HOST}:${PORT}/api/outreach`, {
      headers: { 'X-Vintos-Secret': SECRET },
    });

    if (!response.ok) {
      reject(new Error("Outreach request failed: " + response.status));
      return;
    }

    const data = await response.json();

    if ((data.has_message || data.pending) && data.message) {
      const emoji = data.emoji || '✦';

      await CapacitorNotifications.schedule([{
        id: Math.floor(Date.now() / 1000),
        title: 'Vintos',
        body: `${emoji} ${data.message}`,
        sound: 'default',
        threadIdentifier: 'vintos-outreach',
      }]);
    }

    resolve();
  } catch (error) {
    reject(error);
  }
});
