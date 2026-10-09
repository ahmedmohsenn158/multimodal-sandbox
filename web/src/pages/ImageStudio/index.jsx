import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

const POLL_INTERVAL_MS = 1000;
const CLIENT_TIMEOUT_MS = 10 * 60 * 1000;

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function getErrorMessage(data, fallback) {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') return detail.message || JSON.stringify(detail);
  return data?.error || data?.message || fallback;
}

export default function ImageStudio() {
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState('idle'); // idle, generating, done, failed
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState('');
  const [queuePosition, setQueuePosition] = useState(-1);
  const [seed, setSeed] = useState(null);
  const pollTimerRef = useRef(null);
  const mountedRef = useRef(true);

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearPollTimer();
    };
  }, [clearPollTimer]);

  const fail = useCallback((message) => {
    clearPollTimer();
    if (!mountedRef.current) return;
    setError(message || 'Image generation failed. Please try again.');
    setStatus('failed');
    setQueuePosition(-1);
  }, [clearPollTimer]);

  const pollStatus = useCallback(async (jobId, startedAt) => {
    if (Date.now() - startedAt > CLIENT_TIMEOUT_MS) {
      fail('Image generation took too long. The job may still be running on the server; check system status before retrying.');
      return;
    }

    const response = await fetch(`/api/image/jobs/${encodeURIComponent(jobId)}`, {
      cache: 'no-store',
    });
    const data = await readJson(response);

    if (!response.ok) {
      throw new Error(getErrorMessage(data, `Could not retrieve job status (HTTP ${response.status}).`));
    }

    if (data.status === 'completed') {
      if (!data.image_url) throw new Error('The job completed but the server did not return an image URL.');
      if (!mountedRef.current) return;
      clearPollTimer();
      setImageUrl(data.image_url);
      setSeed(data.seed ?? null);
      setQueuePosition(-1);
      setError('');
      setStatus('done');
      return;
    }

    if (data.status === 'failed' || data.status === 'error') {
      throw new Error(data.error || 'ComfyUI failed to generate the image.');
    }

    if (!['queued', 'waiting_for_gpu', 'running'].includes(data.status)) {
      throw new Error(`The server returned an unexpected job status: ${String(data.status)}.`);
    }

    if (mountedRef.current) setQueuePosition(data.queue_position ?? -1);
    pollTimerRef.current = setTimeout(() => {
      pollStatus(jobId, startedAt).catch((err) => fail(err?.message || 'Could not poll image job status.'));
    }, POLL_INTERVAL_MS);
  }, [clearPollTimer, fail]);

  const handleGenerate = async () => {
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt) {
      setError('Please describe the image you want to generate.');
      setStatus('failed');
      return;
    }
    if (cleanPrompt.length > 1000) {
      setError('Keep the prompt to 1,000 characters or fewer.');
      setStatus('failed');
      return;
    }

    clearPollTimer();
    setStatus('generating');
    setError('');
    setImageUrl(null);
    setQueuePosition(-1);
    setSeed(null);

    try {
      const response = await fetch('/api/image/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: cleanPrompt, width: 1024, height: 1024, seed: -1 }),
      });
      const data = await readJson(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, `Could not start generation (HTTP ${response.status}).`));
      }
      if (!data.job_id) {
        throw new Error('The server accepted the request but did not return a job ID.');
      }

      await pollStatus(data.job_id, Date.now());
    } catch (err) {
      fail(err?.message || 'An unexpected error occurred while generating the image.');
    }
  };

  const resetForAnotherImage = () => {
    clearPollTimer();
    setStatus('idle');
    setImageUrl(null);
    setError('');
    setQueuePosition(-1);
    setSeed(null);
  };

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      <header style={{ borderBottom: '1px solid #ccc', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h2><Link to="/" style={{ textDecoration: 'none', color: '#333' }}>← Sandbox</Link> / AI Image Studio</h2>
      </header>

      <div>
        <label htmlFor="image-prompt" style={{ display: 'block', marginBottom: '0.5rem' }}>
          Describe your image:
        </label>
        <textarea
          id="image-prompt"
          maxLength={1000}
          style={{ boxSizing: 'border-box', width: '100%', minHeight: '100px', marginBottom: '0.5rem' }}
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="A futuristic library in Cairo at sunset..."
          disabled={status === 'generating'}
        />
        <div style={{ color: '#666', fontSize: '0.85rem', marginBottom: '1rem' }}>
          {prompt.length}/1000 characters · 1024 × 1024 output
        </div>

        <button
          onClick={handleGenerate}
          disabled={status === 'generating'}
          style={{ padding: '0.65rem 1.2rem', fontSize: '1rem', cursor: status === 'generating' ? 'wait' : 'pointer' }}
        >
          {status === 'generating' ? 'Generating…' : 'Generate image'}
        </button>

        {status === 'generating' && (
          <p role="status" aria-live="polite">
            {queuePosition > 0 ? `Waiting for GPU (queue position ${queuePosition})…` : 'Generating your image…'}
          </p>
        )}

        {status === 'failed' && error && (
          <div role="alert" style={{ marginTop: '1rem', padding: '0.75rem', border: '1px solid #d88', color: '#8a1c1c', whiteSpace: 'pre-wrap' }}>
            {error}
            <div><button onClick={() => { setError(''); setStatus('idle'); }} style={{ marginTop: '0.75rem' }}>Dismiss</button></div>
          </div>
        )}
      </div>

      {status === 'done' && imageUrl && (
        <section style={{ marginTop: '2rem', border: '1px solid #ccc', padding: '1rem', textAlign: 'center' }}>
          <h3>Generated Image</h3>
          <div style={{ width: '100%', minHeight: '300px', backgroundColor: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '1rem 0', overflow: 'hidden' }}>
            <img
              src={imageUrl}
              alt="Generated from your prompt"
              style={{ maxWidth: '100%', maxHeight: '640px', objectFit: 'contain' }}
              onError={() => fail('The image was generated, but the browser could not load it. Check the Nginx /images/ route and shared output volume.')}
            />
          </div>
          {seed !== null && <p style={{ color: '#666', fontSize: '0.85rem' }}>Seed: {seed}</p>}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button onClick={resetForAnotherImage}>Generate another</button>
            <a href={imageUrl} download="generated-image.png" style={{ display: 'inline-block', padding: '0.35rem 0.75rem', border: '1px solid #888', borderRadius: '3px', color: 'inherit', textDecoration: 'none' }}>
              Download image
            </a>
          </div>
        </section>
      )}
    </main>
  );
}
