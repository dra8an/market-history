import type { ManifestTicker } from '../types';
import { formatDate, formatPrice, formatChange } from '../utils/format';

interface StockInfoProps {
  ticker: ManifestTicker;
  lastClose: number | null;
  prevClose: number | null;
  firstClose: number | null;
}

export function StockInfo({ ticker, lastClose, prevClose, firstClose }: StockInfoProps) {
  const dayChange = lastClose != null && prevClose != null ? formatChange(lastClose, prevClose) : null;
  const totalReturn = lastClose != null && firstClose != null && firstClose > 0 ? formatChange(lastClose, firstClose) : null;

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <h2 className="text-lg font-bold text-white">{ticker.s}</h2>
      <span className="text-sm text-gray-400">{ticker.n}</span>
      <span className="text-xs px-1.5 py-0.5 bg-gray-800 text-gray-500 rounded">{ticker.e}</span>
      <span
        className={`text-xs px-1.5 py-0.5 rounded ${
          ticker.a ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
        }`}
      >
        {ticker.a ? 'Active' : 'Delisted'}
      </span>
      <span className="text-xs text-gray-600">
        {formatDate(ticker.from)} — {formatDate(ticker.to)}
      </span>
      {lastClose != null && (
        <span className="text-sm font-medium text-white">
          {formatPrice(lastClose)} <span className="text-xs text-gray-500">(split-adj.)</span>
        </span>
      )}
      {dayChange && (
        <span className={`text-xs ${dayChange.positive ? 'text-green-400' : 'text-red-400'}`}>
          Day: {dayChange.value} ({dayChange.percent})
        </span>
      )}
      {totalReturn && (
        <span className={`text-xs ${totalReturn.positive ? 'text-green-400' : 'text-red-400'}`}>
          All-time: {totalReturn.percent}
        </span>
      )}
    </div>
  );
}
