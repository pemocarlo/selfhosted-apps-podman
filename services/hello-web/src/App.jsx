import { useEffect, useState } from "react";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api";

export default function App() {
  const [message, setMessage] = useState("Loading...");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadMessage() {
      try {
        const response = await fetch(`${apiBaseUrl}/hello`);
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();
        if (!cancelled) {
          setMessage(data.message);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load API message");
        }
      }
    }

    loadMessage();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">React + FastAPI</p>
        <h1>Hello Web</h1>
        <p className="message">{error || message}</p>
        <p className="hint">This React app calls <code>/api/hello</code>. Vite proxies it in development; Caddy proxies it in production.</p>
      </section>
    </main>
  );
}
