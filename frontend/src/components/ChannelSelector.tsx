import type { Channel } from '../api';

interface Props {
  channels: Channel[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}

export default function ChannelSelector({ channels, selectedIds, onChange }: Props) {
  const toggle = (id: number) => {
    if (selectedIds.includes(id)) onChange(selectedIds.filter(x => x !== id));
    else onChange([...selectedIds, id]);
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Select Channels</h3>
      <div className="space-y-2">
        {channels.map(ch => (
          <label key={ch.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
            <input type="checkbox" checked={selectedIds.includes(ch.id)} onChange={() => toggle(ch.id)} className="w-4 h-4 text-blue-600 border-gray-300 rounded" />
            <span className="text-sm text-gray-800">{ch.name}</span>
            <span className="text-xs text-gray-400">({ch.platform})</span>
          </label>
        ))}
      </div>
    </div>
  );
}