import React, { useEffect, useState } from "react";
import axios from "axios";
import "./index.css";

const shipsConfig = [
  { id: "black_pearl", port: 8000 },
  { id: "flying_dutchman", port: 8001 },
  { id: "queen_annes_revenge", port: 8002 },
  { id: "interceptor", port: 8003 },
  { id: "endeavour", port: 8004 },
];

export default function FleetStatus() {
  const [fleet, setFleet] = useState([]);
  const [voteMode, setVoteMode] = useState(null);
  const [attackMode, setAttackMode] = useState(null);
  const [selectedVoter, setSelectedVoter] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState("");

  const fetchFleetStatus = async () => {
    try {
      const newFleet = await Promise.all(
        shipsConfig.map(async (ship) => {
          try {
            const response = await axios.get(`http://localhost:${ship.port}/status`);
            return {
              ...ship,
              alive: response.data.alive,
              leader: response.data.leader === ship.id,
              voted: response.data.voted,
              vote_mode: response.data.vote_mode,
              votes_cast: response.data.votes_cast,
            };
          } catch {
            return {
              ...ship,
              alive: false,
              leader: false,
              voted: false,
              vote_mode: null,
              votes_cast: {},
            };
          }
        })
      );
      setFleet(newFleet);
    } catch (error) {
      console.error("Error fetching fleet:", error);
    }
  };

  useEffect(() => {
    fetchFleetStatus();
    const interval = setInterval(fetchFleetStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const setModeOnAllNodes = async (modeType, modeValue) => {
    for (const ship of fleet) {
      try {
        await axios.post(`http://localhost:${ship.port}/set_${modeType}_mode`, {
          mode: modeValue,
        });
      } catch (err) {
        console.error(`Error setting ${modeType} mode on ${ship.id}`, err);
      }
    }
    if (modeType === "vote") setVoteMode(modeValue);
    else setAttackMode(modeValue);
  };

  const handleManualVote = async () => {
    if (!selectedVoter || !selectedCandidate) return;
    try {
      await axios.post(`http://localhost:${shipsConfig.find(s => s.id === selectedVoter).port}/vote_for`, {
        target_id: selectedCandidate,
      });
    } catch (err) {
      console.error("Manual vote failed:", err);
    }
  };

  const handleManualAttack = async (targetId) => {
    try {
      await axios.post(`http://localhost:${shipsConfig.find(s => s.id === targetId).port}/hit`);
    } catch (err) {
      console.error("Hit failed:", err);
    }
  };

  return (
    <div className="fleet-container">
      <div className="controls">
        {!voteMode && (
          <div className="mode-buttons">
            <h3>Wybierz tryb głosowania</h3>
            <button onClick={() => setModeOnAllNodes("vote", "auto")}>Auto głosowanie</button>
            <button onClick={() => setModeOnAllNodes("vote", "manual")}>Manualne głosowanie</button>
          </div>
        )}

        {voteMode === "manual" && (
          <div className="manual-vote">
            <h3>Manualne głosowanie</h3>
            <select onChange={(e) => setSelectedVoter(e.target.value)} value={selectedVoter}>
              <option value="">Wybierz głosującego</option>
              {fleet.filter(s => s.alive).map((ship) => (
                <option key={ship.id} value={ship.id}>{ship.id}</option>
              ))}
            </select>
            <select onChange={(e) => setSelectedCandidate(e.target.value)} value={selectedCandidate}>
              <option value="">Wybierz kandydata</option>
              {fleet.filter(s => s.alive).map((ship) => (
                <option key={ship.id} value={ship.id}>{ship.id}</option>
              ))}
            </select>
            <button onClick={handleManualVote}>Głosuj</button>
          </div>
        )}

        {voteMode && !attackMode && (
          <div className="mode-buttons">
            <h3>Wybierz tryb zestrzeliwania</h3>
            <button onClick={() => setModeOnAllNodes("attack", "auto")}>Auto zestrzeliwanie</button>
            <button onClick={() => setModeOnAllNodes("attack", "manual")}>Manualne zestrzeliwanie</button>
          </div>
        )}
      </div>

      <div className="fleet-grid">
        {fleet.map((ship) => (
          <div
            key={ship.id}
            className={`ship-box ${!ship.alive ? "ship-dead" : ship.leader ? "ship-leader" : "ship-alive"}`}
            onClick={() => {
              if (attackMode === "manual" && ship.alive) handleManualAttack(ship.id);
            }}
          >
            <div className="ship-id">{ship.id.replace(/_/g, " ")}</div>
            <div className="ship-vote">
              {Object.entries(ship.votes_cast).length > 0 &&
                Object.entries(ship.votes_cast).map(([voter, votedFor]) => (
                  <div key={voter}>{voter} ➜ {votedFor}</div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
