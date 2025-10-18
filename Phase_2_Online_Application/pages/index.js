import { useEffect, useState } from 'react';

export default function Home() {
  const [timestamps, setTimestamps] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/demo.json')
      .then(res => {
        if (!res.ok) throw new Error('Could not load demo.json');
        return res.json();
      })
      .then(data => {
        // Assume demo.json contains { timestamps: [10, 30, 45, ...] } or similar
        let ts = data.timestamps || data.segments || [];
        if (Array.isArray(data)) ts = data;
        setTimestamps(ts);
      })
      .catch(e => setError(e.message));
  }, []);

  function handleSeek(ts) {
    // In future: call Panopto player
    console.log('Seek to:', ts);
    // window.seekToTime(ts) -- will add later
  }

  return (
    <div style={{ padding: 32, maxWidth: 600, margin: '0 auto' }}>
      <h1>Panopto Demo Player - Timestamp List</h1>
      {error && <div style={{color: 'red'}}>Failed to load: {error}</div>}
      <div style={{marginTop: 24}}>
        {timestamps.length > 0 ? (
          <ul style={{listStyle: 'none', padding: 0}}>
            {timestamps.map((ts, i) => (
              <li key={i} style={{marginBottom: 16}}>
                <button onClick={() => handleSeek(ts)} style={{padding: '6px 18px', fontSize: 18}}>
                  Seek to {ts} seconds
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div>No timestamps loaded...</div>
        )}
      </div>
    </div>
  );
}
