import { useState, useRef, useEffect, useCallback } from 'react';
import type { ManifestTicker } from '../types';

interface SearchBarProps {
  onSelect: (ticker: ManifestTicker) => void;
  search: (query: string) => ManifestTicker[];
  loading: boolean;
  selectedSymbols?: string[];
  maxReached?: boolean;
  onRemove?: (symbol: string) => void;
}

export function SearchBar({ onSelect, search, loading, selectedSymbols = [], maxReached = false, onRemove }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ManifestTicker[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const doSearch = useCallback(
    (q: string) => {
      if (!q.trim()) {
        setResults([]);
        setIsOpen(false);
        return;
      }
      const matches = search(q.trim());
      setResults(matches);
      setIsOpen(matches.length > 0);
      setActiveIndex(-1);
    },
    [search]
  );

  const handleChange = (value: string) => {
    setQuery(value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 150);
  };

  const handleSelect = (ticker: ManifestTicker) => {
    if (selectedSymbols.includes(ticker.s)) return;
    setQuery('');
    setIsOpen(false);
    setResults([]);
    onSelect(ticker);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(results[activeIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      {selectedSymbols.length > 0 && (
        <div className="flex gap-1.5 mb-1.5">
          {selectedSymbols.map((sym) => (
            <span
              key={sym}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs font-mono text-white"
            >
              {sym}
              {onRemove && (
                <button
                  onClick={() => onRemove(sym)}
                  className="text-gray-500 hover:text-gray-200 ml-0.5"
                >
                  x
                </button>
              )}
            </span>
          ))}
          <span className="text-xs text-gray-600 self-center">{selectedSymbols.length}/4</span>
        </div>
      )}
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => handleChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => results.length > 0 && setIsOpen(true)}
        placeholder={loading ? 'Loading tickers...' : maxReached ? 'Max 4 tickers selected' : selectedSymbols.length > 0 ? 'Add ticker to compare...' : 'Search ticker or company...'}
        disabled={loading || maxReached}
        className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
      />
      {isOpen && (
        <ul className="absolute z-50 mt-1 w-full max-h-80 overflow-y-auto bg-gray-900 border border-gray-700 rounded-lg shadow-lg">
          {results.map((ticker, i) => {
            const alreadySelected = selectedSymbols.includes(ticker.s);
            return (
            <li
              key={ticker.s}
              onClick={() => !alreadySelected && handleSelect(ticker)}
              onMouseEnter={() => setActiveIndex(i)}
              className={`px-4 py-2 flex items-center gap-3 text-sm ${
                alreadySelected
                  ? 'opacity-40 cursor-default'
                  : `cursor-pointer ${i === activeIndex ? 'bg-gray-800' : 'hover:bg-gray-800/50'}`
              }`}
            >
              <span className="font-mono font-semibold text-white w-16">{ticker.s}</span>
              <span className="text-gray-400 truncate flex-1">{ticker.n}</span>
              <span className="text-xs text-gray-600">{ticker.e}</span>
              {!ticker.a && (
                <span className="text-xs px-1.5 py-0.5 bg-red-900/50 text-red-400 rounded">
                  Delisted
                </span>
              )}
            </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
