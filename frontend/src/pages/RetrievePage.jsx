import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPlan } from '../api';

export default function RetrievePage() {
  const [planId, setPlanId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!planId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getPlan(planId.trim());
      if (data.status === 'completed' || data.status === 'partial') {
        navigate(`/itinerary/${planId.trim()}`, { state: { plan: data } });
      } else if (data.status === 'failed') {
        navigate('/error', { state: { plan: data } });
      } else {
        navigate(`/status/${planId.trim()}`, { state: { plan: data } });
      }
    } catch (err) {
      if (err?.status === 404) {
        setError(`Plan "${planId.trim()}" was not found. It may have expired or the ID is incorrect.`);
      } else {
        setError('Something went wrong. Please try again.');
      }
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-[var(--spacing-margin-mobile)] relative">
      {/* Background atmospheric element */}
      <div className="absolute inset-0 pointer-events-none opacity-20 z-0">
        <div className="absolute bottom-0 left-0 right-0 h-96 bg-gradient-to-t from-surface-container to-transparent blur-3xl" />
      </div>

      <div className="w-full max-w-md z-10">
        {/* Header */}
        <div className="text-center mb-[var(--spacing-stack-md)]">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary-container mb-6">
            <span className="material-symbols-outlined text-on-secondary-container text-4xl">travel_explore</span>
          </div>
          <h1 className="font-display text-3xl font-semibold text-primary mb-2">Retrieve a saved itinerary</h1>
          <p className="text-base text-on-surface-variant">Enter your unique Plan ID to pick up where you left off.</p>
        </div>

        {/* Form Card */}
        <div className="bg-surface-container-lowest p-8 rounded-xl desert-shadow border border-outline-variant/10">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="plan-id" className="block text-sm font-semibold tracking-wide text-on-surface-variant mb-2">
                Plan ID
              </label>
              <div className="relative border border-outline/20 bg-surface rounded-lg transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_0_2px_rgba(0,105,114,0.1)]">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-outline">key</span>
                <input
                  id="plan-id"
                  type="text"
                  value={planId}
                  onChange={(e) => setPlanId(e.target.value)}
                  className="w-full bg-transparent border-none py-4 pl-12 pr-4 text-base focus:ring-0 focus:outline-none placeholder:text-outline-variant"
                  placeholder="e.g. DXB-8291-KLA"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-error-container/20 border border-error/30 rounded-lg text-error text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !planId.trim()}
              className="w-full bg-primary text-on-primary py-4 rounded-lg text-sm font-semibold tracking-wide hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <span>{loading ? 'Searching...' : 'Find my plan'}</span>
              <span className="material-symbols-outlined text-lg">arrow_forward</span>
            </button>
          </form>

          {/* Help note */}
          <div className="mt-8 pt-6 border-t border-outline-variant/30 text-center">
            <p className="text-xs text-on-surface-variant flex items-center justify-center gap-1.5">
              <span className="material-symbols-outlined text-[14px]">info</span>
              Plans are stored temporarily for 30 days.
            </p>
            <p className="mt-4 text-base">
              <span className="text-on-surface-variant">Lost your code? </span>
              <a href="/" className="text-secondary font-semibold hover:underline transition-all">Plan a Trip</a>
            </p>
          </div>
        </div>

        {/* Help card */}
        <div className="mt-[var(--spacing-stack-md)] bg-white/50 border border-outline-variant/20 p-4 rounded-lg flex items-center gap-4 transition-transform hover:scale-[1.02] cursor-pointer">
          <div className="w-10 h-10 rounded-full bg-tertiary-container/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-tertiary fill-icon">stars</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-primary">Need help finding your ID?</p>
            <p className="text-xs text-on-surface-variant">Check your email or text messages.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
