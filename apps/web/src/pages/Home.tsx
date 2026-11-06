import { Link } from 'react-router-dom';

const steps = [
  { to: '/stock', title: 'See the stock', text: 'Which lots cannot sell the normal way, and how much value is at risk.' },
  { to: '/parameters', title: 'Set the rules', text: 'Check the business rules: shelf life, brand level, channel limits.' },
  { to: '/parameters', title: 'Run the plan', text: 'The solver places each lot in a second life channel.' },
  { to: '/results', title: 'Review the plan', text: 'See where stock goes, and open any line to see why.' },
  { to: '/results', title: 'Export', text: 'Download the plan as an Excel file for the brand.' },
];

export function Home() {
  return (
    <div className="rs-stack">
      <section className="rs-goal" data-testid="home-head">
        <h2>Tighten a rule. See what it costs. See why.</h2>
        <p>
          Reshelf builds a plan that finds a second life for stock that cannot sell the normal way, so it is not destroyed.
          The plan follows your business rules, and every line says why it is there. When the plan is ready, you send it to
          the brand.
        </p>
        <div className="rs-actions">
          <Link className="rs-btn rs-btn--primary rs-btn--lg" to="/stock">
            Start with the stock
          </Link>
          <Link className="rs-btn rs-btn--lg" to="/results">
            Go to the ready plan
          </Link>
        </div>
        <p className="rs-note">All data is simulated. Every comparison is shown against a greedy baseline, a plan made by hand.</p>
      </section>
      <section aria-label="Five steps to a plan">
        <ol className="rs-flow">
          {steps.map((s) => (
            <li key={s.title}>
              <Link to={s.to} className="rs-flow__step" data-testid="home-step">
                <b>{s.title}</b>
                <span>{s.text}</span>
              </Link>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
