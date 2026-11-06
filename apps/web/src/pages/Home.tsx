import { Link } from 'react-router-dom';

const steps = [
  { to: '/stock', title: '1. See the stock', text: 'Lots that cannot sell through primary retail, by reason, brand and plant.' },
  { to: '/results', title: '2. Read the plan', text: 'The optimizer places each lot in a second life channel under business rules.' },
  { to: '/compare', title: '3. Compare', text: 'Optimizer against the greedy baseline, with the rules the baseline breaks.' },
  { to: '/parameters', title: '4. Change a rule', text: 'Tighten a rule, run the solver, see what it costs in euros and why.' },
];

export function Home() {
  return (
    <>
      <section className="rs-page-head" data-testid="home-head">
        <h2>Tighten a rule. See what it costs. See why.</h2>
        <p>
          Reshelf gives sleeping stock a second shelf. It allocates near expiry, discontinued and overproduced stock to
          second life channels, and explains each decision. All data is simulated and every KPI is shown against a greedy
          baseline.
        </p>
        <div className="rs-actions">
          <Link className="rs-btn rs-btn--primary" to="/results">
            Open the results
          </Link>
        </div>
      </section>
      <section className="rs-cards">
        {steps.map((s) => (
          <Link key={s.to} to={s.to} className="rs-card" data-testid="home-step">
            <h3>{s.title}</h3>
            <p>{s.text}</p>
          </Link>
        ))}
      </section>
    </>
  );
}
