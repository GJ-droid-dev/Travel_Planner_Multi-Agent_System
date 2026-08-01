import { Link, useLocation } from 'react-router-dom';
import { EMPTY_STATE_IMG_URL } from '../images';

export default function ErrorPage() {
  const location = useLocation();
  const plan = location.state?.plan;
  const errorType = location.state?.errorType;
  const errorPlanId = location.state?.planId;

  return (
    <div className="pt-12 pb-20 px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)] max-w-[var(--spacing-container-max)] mx-auto">
      <header className="mb-12">
        <h1 className="font-display text-5xl font-bold text-primary mb-2">System Diagnostics</h1>
        <p className="text-on-surface-variant max-w-2xl">
          This interface monitors the status of your travel planning engine. Encountered issues and recovery
          steps are listed below.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-[var(--spacing-gutter)]">
        {/* ── Backend Unavailable ── */}
        {(plan?.status === 'failed' || errorType === 'generation_failed') && (
          <section className="md:col-span-12 bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl desert-shadow flex flex-col md:flex-row items-center gap-8 border-l-4 border-l-error">
            <div className="w-24 h-24 flex-shrink-0 bg-error-container/20 rounded-full flex items-center justify-center">
              <span className="material-symbols-outlined text-error text-5xl">cloud_off</span>
            </div>
            <div className="flex-grow text-center md:text-left">
              <h2 className="font-display text-3xl font-semibold text-primary mb-2">Planning Failed</h2>
              <p className="text-on-surface-variant mb-4 text-lg">
                {plan?.errors?.join('. ') || 'Our AI agents encountered an issue while building your itinerary.'}
              </p>
              {plan?.warnings?.length > 0 && (
                <ul className="mb-6 space-y-1">
                  {plan.warnings.map((w, i) => (
                    <li key={i} className="text-sm text-on-surface-variant flex items-center gap-2">
                      <span className="material-symbols-outlined text-tertiary text-[16px]">warning</span>
                      {w}
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex flex-wrap justify-center md:justify-start gap-4">
                <Link
                  to="/"
                  className="bg-primary text-on-primary px-8 py-3 rounded-lg text-sm font-semibold hover:opacity-80 transition-all flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-sm">refresh</span> Try again
                </Link>
              </div>
            </div>
          </section>
        )}

        {/* ── No Plan Found ── */}
        {errorType === 'not_found' && (
          <section className="md:col-span-6 bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl desert-shadow">
            <div className="aspect-video mb-6 relative overflow-hidden rounded-lg bg-surface-variant">
              {EMPTY_STATE_IMG_URL && !EMPTY_STATE_IMG_URL.startsWith('PLACEHOLDER') ? (
                <img src={EMPTY_STATE_IMG_URL} alt="Empty state" className="object-cover w-full h-full" />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-surface-container-low to-surface-container-high">
                  <div className="text-center text-on-surface-variant/60 space-y-2">
                    <span className="material-symbols-outlined text-4xl">image</span>
                    <p className="text-xs font-semibold">Empty State Image</p>
                    <p className="text-xs">600×600 PNG/WebP</p>
                  </div>
                </div>
              )}
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="material-symbols-outlined text-on-surface-variant/40 text-7xl">search_off</span>
              </div>
            </div>
            <h3 className="font-display text-2xl font-semibold text-primary mb-2">No Plan Found</h3>
            <p className="text-on-surface-variant mb-6 text-base">
              We searched our archives, but Itinerary ID{' '}
              <span className="font-bold text-primary">#{errorPlanId || 'unknown'}</span> does not exist or has
              expired from our secure cache.
            </p>
            <div className="flex gap-4">
              <Link to="/" className="flex-1 bg-primary text-on-primary py-3 rounded-lg text-sm font-semibold text-center">
                Start New Plan
              </Link>
              <Link to="/retrieve" className="flex-1 bg-surface border border-outline py-3 rounded-lg text-sm font-semibold text-center">
                Try Another ID
              </Link>
            </div>
          </section>
        )}

        {/* ── Partial Plan ── */}
        {plan?.status === 'partial' && (
          <section className="md:col-span-6 bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl desert-shadow border-l-4 border-l-tertiary">
            <div className="flex items-center gap-3 mb-6">
              <span className="material-symbols-outlined text-tertiary">warning</span>
              <h3 className="font-display text-2xl font-semibold text-primary">Partial Itinerary Ready</h3>
            </div>
            <p className="text-on-surface-variant mb-6">
              We were able to generate a partial plan. Some sections may be incomplete.
            </p>
            <div className="flex flex-col gap-3">
              <Link
                to={`/itinerary/${plan.plan_id}`}
                state={{ plan }}
                className="w-full bg-secondary text-on-secondary py-3 rounded-lg text-sm font-semibold text-center"
              >
                View Partial Plan
              </Link>
              <Link to="/" className="w-full text-secondary py-2 text-sm font-semibold text-center hover:underline">
                Start Fresh
              </Link>
            </div>
          </section>
        )}

        {/* ── Generic fallback if no specific state ── */}
        {!plan && !errorType && (
          <section className="md:col-span-12 bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl desert-shadow flex flex-col items-center text-center gap-6">
            <div className="w-24 h-24 bg-surface-container-high rounded-full flex items-center justify-center">
              <span className="material-symbols-outlined text-on-surface-variant text-5xl">help_outline</span>
            </div>
            <h2 className="font-display text-3xl font-semibold text-primary">Page Not Found</h2>
            <p className="text-on-surface-variant max-w-md">
              The page you're looking for doesn't exist. Let's get you back on track.
            </p>
            <Link to="/" className="bg-primary text-on-primary px-8 py-3 rounded-lg text-sm font-semibold hover:opacity-80 transition-all">
              Back to Home
            </Link>
          </section>
        )}
      </div>
    </div>
  );
}
