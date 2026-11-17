import { useEffect, useState } from 'react';

type Props = {
  value: number;
  onValue: (n: number) => void;
  min?: number;
  max?: number;
  step?: number;
  'aria-label'?: string;
};

/**
 * Number input that keeps what the user types as text. An empty field stays empty while typing,
 * so replacing 0.7 by 2 does not leave a leading 0. The number is sent up only when the text is a valid number.
 * On blur an empty or invalid text goes back to the last valid value.
 */
export function NumberField({ value, onValue, min, max, step, 'aria-label': label }: Props) {
  const [text, setText] = useState(String(value));

  // Follow outside changes (reset to defaults, load a saved scenario) without fighting the typing.
  useEffect(() => {
    setText((t) => (t.trim() !== '' && Number(t) === value ? t : String(value)));
  }, [value]);

  return (
    <input
      className="rs-input"
      type="number"
      inputMode="decimal"
      min={min}
      max={max}
      step={step}
      aria-label={label}
      value={text}
      onChange={(e) => {
        setText(e.target.value);
        const n = e.target.valueAsNumber;
        if (e.target.value.trim() !== '' && Number.isFinite(n)) onValue(n);
      }}
      onBlur={() => setText(String(value))}
    />
  );
}
