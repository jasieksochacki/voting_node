import React from "react";

interface Props {
  nodes: { name: string; url: string }[];
  selectedCandidate: string;
  setSelectedCandidate: (value: string) => void;
  onVote: () => void;
}

const VoteForm: React.FC<Props> = ({
  nodes,
  selectedCandidate,
  setSelectedCandidate,
  onVote,
}) => {
  return (
    <div>
      <label>Na kogo głosujesz:</label>
      <select
        value={selectedCandidate}
        onChange={(e) => setSelectedCandidate(e.target.value)}
      >
        <option value="">-- wybierz --</option>
        {nodes.map((node) => (
          <option key={node.name} value={node.name}>
            {node.name}
          </option>
        ))}
      </select>
      <button onClick={onVote}>Głosuj</button>
    </div>
  );
};

export default VoteForm;
