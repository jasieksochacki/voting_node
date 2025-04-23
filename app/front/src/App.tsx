import { useEffect, useState } from "react";
import axios from "axios";

const BACKEND_URL = "http://localhost:8000";

function App() {
  const [nodes] = useState<string[]>(["node1", "node2", "node3", "node4", "node5"]);
  const [voter, setVoter] = useState("");
  const [candidate, setCandidate] = useState("");
  const [points, setPoints] = useState<number>(0);
  const [leader, setLeader] = useState("Brak");
  const [message, setMessage] = useState("");

  useEffect(() => {
  (async () => await fetchLeader())();
}, []);


  const fetchLeader = async () => {
    try {
      const res = await axios.get<{ leader: string }>(`${BACKEND_URL}/leader`);
setLeader(res.data.leader || "Brak");

    } catch (err) {
      setMessage("Błąd pobierania lidera");
    }
  };

  const handleSetPoints = async () => {
    if (!voter) return;
    try {
      await axios.post(`${BACKEND_URL}/set-points`, { node_id: voter, points });
      setMessage(`Punkty dla ${voter} ustawione`);
    } catch {
      setMessage("Błąd przy ustawianiu punktów");
    }
  };

  const handleVote = async () => {
    if (!voter || !candidate) return;
    try {
      const res = await axios.post<{ error?: string }>(`${BACKEND_URL}/vote`, { voter, candidate });

if (res.data.error) {
  setMessage(`Nie możesz głosować dwa razy`);
} else {
  setMessage(`Node ${voter} zagłosował na ${candidate}`);
  fetchLeader();
}

    } catch {
      setMessage("Błąd przy głosowaniu");
    }
  };

  const handleReset = async () => {
    try {
      await axios.post(`${BACKEND_URL}/reset`);
      setMessage("Głosowanie zresetowane");
      setLeader("Brak");
    } catch {
      setMessage("Błąd przy resetowaniu");
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>⚓ Wybór kapitana Papieskiej Morskiej Floty</h1>

      <div>
        <label>Wybierz node głosujący:</label>
        <select value={voter} onChange={(e) => setVoter(e.target.value)}>
          <option value="">-- wybierz --</option>
          {nodes.map((node) => (
            <option key={node} value={node}>{node}</option>
          ))}
        </select>
      </div>

      <div style={{ marginTop: "1rem" }}>
        <label>Ustaw punkty bojowe:</label>
        <input
          type="number"
          value={points}
          onChange={(e) => setPoints(Number(e.target.value))}
        />
        <button onClick={handleSetPoints}>Zapisz punkty</button>
      </div>

      <div style={{ marginTop: "1rem" }}>
        <label>Na kogo głosujesz:</label>
        <select value={candidate} onChange={(e) => setCandidate(e.target.value)}>
          <option value="">-- wybierz --</option>
          {nodes.map((node) => (
            <option key={node} value={node}>{node}</option>
          ))}
        </select>
        <button onClick={handleVote} style={{ marginLeft: "1rem" }}>Głosuj</button>
      </div>

      <div style={{ marginTop: "1rem" }}>
        <button onClick={handleReset}>Resetuj głosowanie</button>
      </div>

      <div style={{ marginTop: "2rem" }}>
        <h2>🏆 Aktualny lider: {leader}</h2>
        {message && <p><strong>📣 {message}</strong></p>}
      </div>
    </div>
  );
}

export default App;
