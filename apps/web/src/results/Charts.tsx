import { HBars, type BarItem } from '../components/HBars';
import { useMoney } from '../data/currency';
import { channelInfo } from '../glossary';
import { int } from '../stock/model';
import { pct, type Result } from './model';

type Kpis = Result['optimizer'];

function pairs(label: (c: string) => string, channels: string[], base: Kpis, opt: Kpis, pick: (k: Kpis, c: string) => number, text: (v: number) => string): BarItem[] {
  return channels.flatMap<BarItem>((c) => [
    { key: `${c}-b`, label: `${label(c)}, greedy baseline`, value: pick(base, c), text: text(pick(base, c)), series: 'baseline' },
    { key: `${c}-o`, label: `${label(c)}, optimizer`, value: pick(opt, c), text: text(pick(opt, c)), series: 'optimizer' },
  ]);
}

/** Every figure is read from the KPI blocks of the result. Nothing is recomputed here. */
export function Charts({ result }: { result: Result }) {
  const { money: eur } = useMoney();
  const label = (c: string) => channelInfo(c, result.geo.channels).name;
  const opt = result.optimizer;
  const base = result.baseline.compliant;
  const raw = result.baseline.raw;
  const channels = Object.keys(opt.fill_rate).sort();

  const value: BarItem[] = [
    { key: 'raw', label: 'Greedy baseline, raw', value: raw.value_recovered, text: eur(raw.value_recovered), series: 'baseline' },
    { key: 'compliant', label: 'Greedy baseline, compliant', value: base.value_recovered, text: eur(base.value_recovered), series: 'baseline' },
    { key: 'optimizer', label: 'Optimizer', value: opt.value_recovered, text: eur(opt.value_recovered), series: 'optimizer' },
  ];
  const fill = pairs(label, channels, base, opt, (k, c) => k.fill_rate[c] ?? 0, pct);
  const skus = pairs(label, channels, base, opt, (k, c) => k.skus_per_channel[c] ?? 0, int);

  return (
    <section data-testid="charts">
      <h3>How the plan compares with a plan made by hand</h3>
      <div className="rs-cards">
        <div className="rs-card">
          <h4>Value recovered</h4>
          <HBars items={value} testId="chart-value" />
        </div>
        <div className="rs-card">
          <h4>Channel fill rate, against the greedy baseline (compliant plan)</h4>
          <HBars items={fill} testId="chart-fill" />
        </div>
        <div className="rs-card">
          <h4>SKUs per channel, against the greedy baseline (compliant plan)</h4>
          <HBars items={skus} testId="chart-skus" />
        </div>
      </div>
    </section>
  );
}
