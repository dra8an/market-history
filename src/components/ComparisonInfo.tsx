import type { ManifestTicker } from '../types';
import { COMPARISON_COLORS } from '../types';
import { formatPrice } from '../utils/format';

interface TickerGain {
  percent: string;
  positive: boolean;
}

interface ComparisonInfoProps {
  tickers: ManifestTicker[];
  lastCloses: Map<string, number>;
  gains: Map<string, TickerGain>;
  onRemove: (symbol: string) => void;
}

export function ComparisonInfo({ tickers, lastCloses, gains, onRemove }: ComparisonInfoProps) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {tickers.map((t, i) => {
        const color = COMPARISON_COLORS[i];
        const lastClose = lastCloses.get(t.s);
        const gain = gains.get(t.s);
        return (
          <div key={t.s} className="flex items-center gap-1.5 text-sm">
            <span
              className="w-2.5 h-2.5 rounded-full inline-block flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            <span className="font-mono font-semibold text-white">{t.s}</span>
            {lastClose != null && (
              <span className="text-gray-400">{formatPrice(lastClose)}</span>
            )}
            {gain && (
              <span className={gain.positive ? 'text-green-400' : 'text-red-400'}>
                {gain.percent}
              </span>
            )}
            <button
              onClick={() => onRemove(t.s)}
              className="text-gray-600 hover:text-gray-300 text-xs ml-0.5"
              title={`Remove ${t.s}`}
            >
              x
            </button>
          </div>
        );
      })}
    </div>
  );
}
