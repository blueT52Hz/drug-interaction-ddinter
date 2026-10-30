import { useEffect, useRef } from 'react';
import { SearchIcon, SwapIcon } from './pos-icons';

interface PosTopBarProps {
  query: string;
  onQueryChange: (value: string) => void;
}

/** Blue KiotViet-style top bar: white search box (F3 focuses it) + the single "Hóa đơn 1" tab. */
export function PosTopBar({ query, onQueryChange }: PosTopBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F3') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <header className="top-bar">
      <label className="top-search">
        <SearchIcon />
        <input
          ref={inputRef}
          autoFocus
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Tìm thuốc theo tên hoặc số đăng ký (F3)"
        />
      </label>
      <div className="invoice-tab">
        <SwapIcon />
        <span>Hóa đơn 1</span>
      </div>
      <div className="top-bar-right">POS Nhà thuốc · Demo cảnh báo tương tác thuốc</div>
    </header>
  );
}
