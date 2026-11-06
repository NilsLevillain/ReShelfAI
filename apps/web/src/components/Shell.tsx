import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { CURRENCIES, useMoney, type CurrencyCode } from '../data/currency';
import { useSource } from '../data/DataSource';
import { useTheme } from '../theme';
import { Icon, IconSprite } from './Icon';
import { Stepper } from './Stepper';

type NavItem = { to: string; label: string; icon: string; step?: number };

export const NAV: NavItem[] = [
  { to: '/', label: 'Home', icon: 'flag' },
  { to: '/stock', label: 'Stock', icon: 'box', step: 0 },
  { to: '/parameters', label: 'Rules and run', icon: 'sliders', step: 1 },
  { to: '/results', label: 'Plan', icon: 'chart', step: 3 },
  { to: '/compare', label: 'Compare scenarios', icon: 'scale' },
];

export function Shell() {
  const [theme, toggle] = useTheme();
  const source = useSource();
  const { currency, setCurrency } = useMoney();
  const { pathname } = useLocation();
  const step = NAV.find((n) => n.to === pathname)?.step;

  return (
    <>
      <IconSprite />
      <header className="rs-nav">
        <div className="rs-nav__in">
          <NavLink className="rs-brand" to="/" aria-label="Reshelf home">
            <span className="rs-wordmark">Reshelf</span>
          </NavLink>
          <nav className="rs-tabs" aria-label="Main">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.to === '/'} className="rs-tab">
                <Icon name={n.icon} />
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="rs-nav__right">
            <label className="rs-groupby">
              <span className="rs-sr">Show amounts in</span>
              <select
                className="rs-select"
                value={currency}
                aria-label="Show amounts in"
                title="Display only. Invented rates. The solver works in euro."
                onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
              >
                {Object.entries(CURRENCIES).map(([code, c]) => (
                  <option key={code} value={code}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <span className="rs-badge" data-testid="simulated-badge">
              Simulated data
            </span>
            <button
              className="rs-iconbtn"
              type="button"
              aria-label="Switch theme"
              title={`Theme: ${theme}`}
              onClick={toggle}
            >
              <Icon name="sun" className="rs-theme-sun" />
              <Icon name="moon" className="rs-theme-moon" />
            </button>
          </div>
        </div>
      </header>
      <div
        className={`rs-callout rs-callout--action ${source === 'live' ? '' : 'rs-callout--info'}`}
        data-testid="data-source-banner"
        role="status"
      >
        {source === null ? (
          'Checking the data source'
        ) : source === 'live' ? (
          'Live solver'
        ) : (
          <>
            <span>
              <strong>Cached results</strong>: you are looking at a plan that was prepared in advance. To change rules and run the
              plan yourself, start the live solver.
            </span>
            <Link className="rs-btn--link" to="/parameters">
              How to start the live solver
            </Link>
          </>
        )}
      </div>
      <main className="rs-page">
        {step !== undefined && <Stepper current={step} />}
        <Outlet />
      </main>
    </>
  );
}
