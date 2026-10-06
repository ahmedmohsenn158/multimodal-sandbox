import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function Status() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(data => setStatus(data))
      .catch(console.error);
  }, []);

  return (
    <div style={{ fontFamily: 'monospace', maxWidth: '600px', margin: '2rem auto', padding: '1rem', backgroundColor: '#1e1e1e', color: '#00ff00' }}>
      <Link to="/" style={{ color: '#fff', textDecoration: 'none' }}>[Back to Home]</Link>
      <h2 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>System Status</h2>
      
      {status ? (
        <pre style={{ fontSize: '1.1rem' }}>
          GPU: {status.gpu}{'\n'}
          VRAM: {status.vram}{'\n\n'}
          VLM: {status.vlm}{'\n'}
          FLUX: {status.flux}{'\n\n'}
          Current GPU owner: {status.current_owner}{'\n'}
          Queue: {status.queue_size} jobs{'\n'}
        </pre>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}
