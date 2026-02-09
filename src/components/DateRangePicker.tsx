import type { DateRange } from '../types';

interface DateRangePickerProps {
  value: DateRange | null;
  onChange: (range: DateRange | null) => void;
  minDate: string; // YYYY-MM-DD
  maxDate: string; // YYYY-MM-DD
}

type Preset = { label: string; months?: number; years?: number };

const PRESETS: Preset[] = [
  { label: '1M', months: 1 },
  { label: '3M', months: 3 },
  { label: '6M', months: 6 },
  { label: '1Y', years: 1 },
  { label: '5Y', years: 5 },
  { label: 'All' },
];

function subtractFromDate(dateStr: string, preset: Preset): string {
  const d = new Date(dateStr + 'T00:00:00');
  if (preset.years) d.setFullYear(d.getFullYear() - preset.years);
  if (preset.months) d.setMonth(d.getMonth() - preset.months);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function isActivePreset(value: DateRange | null, preset: Preset, minDate: string, maxDate: string): boolean {
  if (!preset.months && !preset.years) {
    return value === null;
  }
  if (!value) return false;
  const expectedFrom = subtractFromDate(maxDate, preset);
  const clampedFrom = expectedFrom < minDate ? minDate : expectedFrom;
  return value.from === clampedFrom && value.to === maxDate;
}

export function DateRangePicker({ value, onChange, minDate, maxDate }: DateRangePickerProps) {
  const handlePreset = (preset: Preset) => {
    if (!preset.months && !preset.years) {
      onChange(null);
      return;
    }
    const from = subtractFromDate(maxDate, preset);
    const clampedFrom = from < minDate ? minDate : from;
    onChange({ from: clampedFrom, to: maxDate });
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="flex gap-1">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            onClick={() => handlePreset(p)}
            className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
              isActivePreset(value, p, minDate, maxDate)
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-300'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-1 text-xs">
        <input
          type="date"
          value={value?.from ?? minDate}
          min={minDate}
          max={value?.to ?? maxDate}
          onChange={(e) => onChange({ from: e.target.value, to: value?.to ?? maxDate })}
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-300 text-xs"
        />
        <span className="text-gray-500">—</span>
        <input
          type="date"
          value={value?.to ?? maxDate}
          min={value?.from ?? minDate}
          max={maxDate}
          onChange={(e) => onChange({ from: value?.from ?? minDate, to: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-300 text-xs"
        />
      </div>
    </div>
  );
}
