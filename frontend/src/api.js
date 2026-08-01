const API_BASE = import.meta.env.VITE_API_URL || '';

export async function createPlan(payload, onProgress) {
  const res = await fetch(`${API_BASE}/api/v1/plan/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw { status: res.status, ...err };
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  return new Promise(async (resolve, reject) => {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.error) {
                reject(new Error(data.error));
                return;
              }
              if (data.done) {
                resolve({ plan_id: data.plan_id });
                return;
              }
              if (data.node && onProgress) {
                onProgress(data.node);
              }
            } catch (e) {
              console.error("Error parsing SSE data:", e);
            }
          }
        }
      }
      resolve({});
    } catch (err) {
      reject(err);
    }
  });
}

export async function getPlan(planId) {
  const res = await fetch(`${API_BASE}/api/v1/plan/${planId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw { status: res.status, ...err };
  }
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  return res.json();
}
