import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export default function ImageStudio() {
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState('idle'); // idle, generating, done
  const [imageUrl, setImageUrl] = useState(null);

  const handleGenerate = async () => {
    setStatus('generating');
    try {
      const res = await fetch('/api/image/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, width: 1024, height: 1024 })
      });
      const data = await res.json();
      
      if (data.job_id) {
        pollStatus(data.job_id);
      }
    } catch (e) {
      console.error(e);
      setStatus('idle');
    }
  };

  const pollStatus = async (jobId) => {
    const interval = setInterval(async () => {
      const res = await fetch(`/api/image/jobs/${jobId}`);
      const data = await res.json();
      if (data.status === 'completed') {
        clearInterval(interval);
        setImageUrl(data.image_url);
        setStatus('done');
      }
    }, 1000);
  };

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      <header style={{ borderBottom: '1px solid #ccc', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h2><Link to="/" style={{textDecoration: 'none', color: '#333'}}>← Sandbox</Link> / AI Image Studio</h2>
      </header>

      <div>
        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Describe your image:</label>
        <textarea 
          style={{ width: '100%', height: '80px', marginBottom: '1rem' }}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="A futuristic library in Cairo..."
        />
        
        <button 
          onClick={handleGenerate} 
          disabled={status === 'generating'}
          style={{ padding: '0.5rem 1rem', fontSize: '1rem' }}>
          {status === 'generating' ? 'Generating...' : 'Generate'}
        </button>
      </div>

      {status === 'done' && imageUrl && (
        <div style={{ marginTop: '2rem', border: '1px solid #ccc', padding: '1rem', textAlign: 'center' }}>
          <h3>Generated Image</h3>
          <div style={{ width: '100%', height: '300px', backgroundColor: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '1rem 0' }}>
            <span style={{ color: '#999' }}>[Image Placeholder: {imageUrl}]</span>
          </div>
          <button onClick={() => setStatus('idle')} style={{ marginRight: '1rem' }}>Regenerate</button>
          <button>Download</button>
        </div>
      )}
    </div>
  );
}
