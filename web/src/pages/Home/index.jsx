import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      <header style={{ borderBottom: '2px solid #333', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h1>MULTIMODAL SANDBOX</h1>
      </header>
      
      <main>
        <p>Explore two local AI experiences:</p>
        <div style={{ display: 'flex', gap: '2rem', marginTop: '2rem' }}>
          
          <div style={{ border: '1px solid #ccc', padding: '1.5rem', borderRadius: '8px', flex: 1 }}>
            <h2>👁 Vision AI</h2>
            <p>Ask AI about your images</p>
            <a href="/chat" style={buttonStyle}>Start</a>
          </div>

          <div style={{ border: '1px solid #ccc', padding: '1.5rem', borderRadius: '8px', flex: 1 }}>
            <h2>🎨 Image Studio</h2>
            <p>Create images from prompts</p>
            <Link to="/images" style={buttonStyle}>Start</Link>
          </div>
          
        </div>
        <div style={{ marginTop: '3rem', fontSize: '0.9rem', color: '#666' }}>
          <p>● Local AI &nbsp;&nbsp;&nbsp; ● No external API</p>
          <Link to="/status" style={{color: '#666'}}>System Status</Link>
        </div>
      </main>
    </div>
  );
}

const buttonStyle = {
  display: 'inline-block',
  marginTop: '1rem',
  padding: '0.5rem 1rem',
  backgroundColor: '#0066cc',
  color: 'white',
  textDecoration: 'none',
  borderRadius: '4px'
};
