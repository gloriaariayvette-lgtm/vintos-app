addEventListener('checkOutreach', async (resolve, reject) => {
  try {
    const env = (typeof process !== 'undefined' && process.env) || {};
    const saved = (typeof CapacitorKV !== 'undefined' && CapacitorKV.get('VINTOS_SECRET')) || {};
    const SECRET = String(env.VINTOS_SECRET || saved.value || '');
    const baseSaved = (typeof CapacitorKV !== 'undefined' && CapacitorKV.get('VINTOS_API_BASE')) || {};
    const API = env.VINTOS_API_BASE || baseSaved.value || 'https://aegis.tailaa3de5.ts.net:8443';
    if (SECRET.length < 32) throw new Error('House environment is not enrolled');
    const response = await fetch(`${API}/api/outreach`, {headers: {'X-Vintos-Secret': SECRET}});

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

addEventListener('configureHouse', (resolve, reject, args) => {
  try {
    const value=String((args || {}).VINTOS_SECRET || '');
    if(value.length<32)throw new Error('House credential required');
    CapacitorKV.set('VINTOS_SECRET',value);
    CapacitorKV.set('VINTOS_API_BASE',String(args.VINTOS_API_BASE || 'https://aegis.tailaa3de5.ts.net:8443'));
    resolve({configured:true});
  } catch (_) { reject(new Error('House enrollment failed')); }
});
