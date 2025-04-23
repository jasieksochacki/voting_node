type Props = {
  port: string;
  votes: Record<string, string> | 'offline';
};

const NodeCard = ({ port, votes }: Props) => {
  return (
    <div className="border p-4 rounded shadow">
      <h3 className="font-bold mb-2">Node {port}</h3>
      {votes === 'offline' ? (
        <p className="text-red-500">Offline</p>
      ) : (
        <ul className="text-sm list-disc ml-4">
          {Object.entries(votes).map(([voter, candidate]) => (
            <li key={voter}>
              {voter} ➞ {candidate}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default NodeCard;
