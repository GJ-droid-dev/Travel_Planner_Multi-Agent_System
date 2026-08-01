import { Link, useLocation } from 'react-router-dom';

export default function Layout({ children }) {
  const { pathname } = useLocation();

  const navLinks = [
    { to: '/', label: 'Plan a Trip' },
    { to: '/retrieve', label: 'Retrieve Plan' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Top Navigation Bar ── */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)] py-4 bg-surface/80 backdrop-blur-md shadow-sm">
        <div className="flex items-center gap-8">
          <Link to="/" className="font-display text-2xl font-bold text-primary">
            Dubai AI Travel Planner
          </Link>
          <div className="hidden md:flex gap-6">
            {navLinks.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`text-sm font-semibold tracking-wide transition-opacity ${
                  pathname === to
                    ? 'text-secondary border-b-2 border-secondary pb-1'
                    : 'text-on-surface-variant hover:text-primary'
                }`}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className="flex-grow pt-20">{children}</main>

      {/* ── Footer ── */}
      <footer className="w-full py-8 px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)] flex flex-col md:flex-row justify-between items-center gap-4 bg-surface-container-lowest border-t border-outline-variant">
        <span className="font-display text-sm font-bold text-primary">
          Dubai AI Travel Planner
        </span>
        <p className="text-xs text-on-surface-variant">
          © {new Date().getFullYear()} Dubai AI Travel Planner. All rights
          reserved.
        </p>
        <div className="flex gap-6">
          <span className="text-xs text-secondary flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
            Service Status: Online
          </span>
          <a href="#" className="text-xs text-on-surface-variant hover:text-primary transition-all">
            Privacy Policy
          </a>
          <a href="#" className="text-xs text-on-surface-variant hover:text-primary transition-all">
            Terms of Service
          </a>
        </div>
      </footer>
    </div>
  );
}
