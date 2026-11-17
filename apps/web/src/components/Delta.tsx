export type Better = 'up' | 'down';
export type Tone = 'good' | 'bad' | 'neutral';

/** Whether a change is good, bad or neutral, given which direction is better. `epsilon` hides rounding noise. */
export function toneOf(change: number, better: Better, epsilon = 0): Tone {
  if (Math.abs(change) <= epsilon) return 'neutral';
  return (change > 0) === (better === 'up') ? 'good' : 'bad';
}

const WORD: Record<Tone, string> = { good: 'better', bad: 'worse', neutral: 'no change' };

/** A change with an arrow and a word. Color helps, but the arrow and the word carry the meaning. */
export function Delta({ text, change, better, epsilon, large }: { text: string; change: number; better: Better; epsilon?: number; large?: boolean }) {
  const tone = toneOf(change, better, epsilon);
  const arrow = tone === 'neutral' ? '=' : change > 0 ? '▲' : '▼';
  return (
    <span className={`rs-delta${large ? ' rs-stat__value' : ''}`} data-tone={tone} data-testid="delta">
      <span aria-hidden="true">{arrow}</span>
      {text}
      <span className="rs-delta__word">{WORD[tone]}</span>
    </span>
  );
}
