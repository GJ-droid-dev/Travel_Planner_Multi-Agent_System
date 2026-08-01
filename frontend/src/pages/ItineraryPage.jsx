import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { getPlan } from '../api';
import { ITINERARY_HOTEL_IMG_URL, ITINERARY_TRANSPORT_IMG_URL } from '../images';

export default function ItineraryPage() {
  const { planId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [plan, setPlan] = useState(location.state?.plan || null);
  const [loading, setLoading] = useState(!plan);
  const [copied, setCopied] = useState(false);
  const [addedExtras, setAddedExtras] = useState([]);

  useEffect(() => {
    if (plan) return;
    (async () => {
      try {
        const data = await getPlan(planId);
        setPlan(data);
      } catch {
        navigate('/error', { state: { errorType: 'not_found', planId } });
      } finally {
        setLoading(false);
      }
    })();
  }, [planId, plan, navigate]);

  function copyPlanId() {
    navigator.clipboard.writeText(planId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <span className="material-symbols-outlined text-secondary text-5xl animate-spin">progress_activity</span>
      </div>
    );
  }

  if (!plan) return null;

  const itinerary = plan.itinerary;
  const days = itinerary?.days || [];
  const budget = itinerary?.budget_breakdown;
  const accommodation = itinerary?.accommodation;
  const review = itinerary?.review_result;
  const request = itinerary?.request;
  const extra_activities = itinerary?.extra_activities || [];

  function toggleExtraActivity(activity) {
    setAddedExtras(prev => {
      const exists = prev.find(a => a.name === activity.name);
      if (exists) {
        return prev.filter(a => a.name !== activity.name);
      }
      return [...prev, activity];
    });
  }

  // Budget bars helper
  function BudgetBar({ label, spent, allocated }) {
    const pct = allocated > 0 ? Math.min((spent / allocated) * 100, 100) : 0;
    const over = spent > allocated;
    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm font-semibold">
          <span className="text-on-surface">{label}</span>
          <span className="text-on-surface-variant">${spent} / ${allocated}</span>
        </div>
        <div className="h-2 w-full bg-surface-container rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${over ? 'bg-error' : 'bg-secondary'}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
    );
  }

  const preferences = request?.preferences || [];
  const totalBudget = budget?.total_budget_usd || request?.budget_usd || 0;
  
  const addedExtrasCost = addedExtras.reduce((sum, a) => sum + (a.estimated_cost_usd || 0), 0);
  const estTotal = (budget?.estimated_total_usd || 0) + addedExtrasCost;
  const remaining = (budget?.remaining_usd || totalBudget - (budget?.estimated_total_usd || 0)) - addedExtrasCost;
  
  const displayCategories = { ...(budget?.categories || {}) };
  if (displayCategories.activities != null) {
    displayCategories.activities += addedExtrasCost;
  }

  return (
    <div className="pb-[var(--spacing-stack-lg)] px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)] max-w-[var(--spacing-container-max)] mx-auto pt-6">
      {/* ── Summary Header ── */}
      <header className="mb-[var(--spacing-stack-lg)] bg-surface-container-lowest p-[var(--spacing-stack-md)] rounded-xl desert-shadow border border-outline-variant/10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="font-display text-3xl font-semibold text-primary">
                Your {days.length > 0 ? `${days.length}-Day` : ''} Dubai Odyssey
              </h1>
              <span className="bg-secondary-container text-on-secondary-container text-xs font-semibold px-2 py-0.5 rounded">
                AI Generated
              </span>
            </div>
            <div className="flex items-center gap-2 text-on-surface-variant text-sm font-semibold">
              <span>Plan ID: {planId?.slice(0, 8)}</span>
              <button onClick={copyPlanId} className="hover:text-primary transition-colors cursor-pointer">
                <span className="material-symbols-outlined text-[18px]">{copied ? 'check' : 'content_copy'}</span>
              </button>
              {request?.travelers && (
                <>
                  <span className="mx-2">•</span>
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-[18px]">group</span>
                    {request.travelers} Traveler{request.travelers > 1 ? 's' : ''}
                  </span>
                </>
              )}
            </div>
          </div>
          {totalBudget > 0 && (
            <div className="flex flex-col items-end">
              <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Total Budget</span>
              <div className="flex items-baseline gap-2">
                <span className="font-display text-3xl font-semibold text-primary">${totalBudget.toLocaleString()}</span>
                {estTotal > 0 && <span className="text-secondary text-sm font-semibold">Est. ${estTotal.toLocaleString()} spent</span>}
              </div>
              {remaining > 0 && (
                <span className="text-tertiary text-sm font-semibold flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">account_balance_wallet</span>
                  ${remaining.toLocaleString()} Remaining
                </span>
              )}
            </div>
          )}
        </div>
        {preferences.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-4 border-t border-outline-variant/10">
            {preferences.map((pref) => (
              <span key={pref} className="px-4 py-1.5 rounded-full bg-surface-container-high text-on-surface text-sm font-semibold border border-outline-variant/20 flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-secondary">interests</span>
                {pref}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* ── Bento Grid: Accommodation & Transport & Budget ── */}
      <div className="mb-[var(--spacing-stack-lg)]">
        {/* Budget Dashboard */}
        <div className="bg-surface-container-lowest p-[var(--spacing-stack-md)] rounded-xl desert-shadow border border-outline-variant/10">
          <h2 className="font-display text-2xl font-semibold text-primary mb-6 flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary">analytics</span> Budget Dashboard
          </h2>
          <div className="space-y-6 mb-8">
            {displayCategories.stay != null && <BudgetBar label="Accommodation" spent={displayCategories.stay} allocated={Math.round(totalBudget * 0.35)} />}
            {displayCategories.food != null && <BudgetBar label="Dining & Food" spent={displayCategories.food} allocated={Math.round(totalBudget * 0.25)} />}
            {displayCategories.activities != null && <BudgetBar label="Activities & Tours" spent={displayCategories.activities} allocated={Math.round(totalBudget * 0.30)} />}
            {displayCategories.transport != null && <BudgetBar label="Transport" spent={displayCategories.transport} allocated={Math.round(totalBudget * 0.10)} />}
          </div>
          
          {extra_activities.length > 0 && (
            <div className="pt-6 border-t border-outline-variant/30 mt-8">
              <h3 className="font-display text-xl font-semibold text-primary mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">extension</span> Optional Extras (Within Budget)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {extra_activities.map((act, i) => {
                  const isAdded = addedExtras.some(a => a.name === act.name);
                  return (
                    <div key={i} className={`p-4 rounded-xl border ${isAdded ? 'border-primary bg-primary/5' : 'border-outline-variant/30 bg-surface'} flex justify-between items-center transition-colors`}>
                      <div className="pr-4">
                        <h4 className="font-display font-semibold text-on-surface">{act.name}</h4>
                        <p className="text-xs text-on-surface-variant line-clamp-2 mt-1">{act.description}</p>
                        <span className="text-sm font-bold text-secondary mt-2 inline-block">${act.estimated_cost_usd}</span>
                      </div>
                      <button 
                        onClick={() => toggleExtraActivity(act)}
                        className={`px-4 py-2 rounded-full text-xs font-bold transition-colors cursor-pointer shrink-0 ${isAdded ? 'bg-error/10 text-error hover:bg-error/20' : 'bg-primary text-on-primary hover:bg-primary/90'}`}
                      >
                        {isAdded ? 'Remove' : 'Add'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* ── Day-by-Day Itinerary ── */}
      <section className="mb-[var(--spacing-stack-lg)]">
        <h2 className="font-display text-3xl font-semibold text-primary mb-[var(--spacing-stack-md)]">Day-by-Day Itinerary</h2>
        <div className="space-y-[var(--spacing-stack-md)]">
          {days.map((day, idx) => (
            <div key={idx} className="bg-surface-container-lowest rounded-xl overflow-hidden desert-shadow border border-outline-variant/10">
              <div className="bg-primary-container text-on-primary p-4 flex justify-between items-center">
                <div>
                  <h3 className="font-display text-2xl font-semibold uppercase">Day {day.day_number || idx + 1}</h3>
                </div>
                <span className="material-symbols-outlined text-tertiary-fixed">wb_sunny</span>
              </div>
              <div className="p-[var(--spacing-stack-md)] grid grid-cols-1 md:grid-cols-3 gap-6">
                {[...(day.activities || [])].sort((a, b) => {
                  const order = { 'Morning': 1, 'Afternoon': 2, 'Evening': 3 };
                  const slotA = a.time_slot || 'Morning';
                  const slotB = b.time_slot || 'Morning';
                  return (order[slotA] || 4) - (order[slotB] || 4);
                }).map((activity, aIdx) => {
                  const timeSlots = ['Morning', 'Afternoon', 'Evening'];
                  const slot = activity.time_slot || timeSlots[aIdx % 3];
                  const opacities = [1, 0.5, 0.2];
                  return (
                    <div key={aIdx} className="relative pl-8">
                      {aIdx < (day.activities?.length || 0) - 1 && <div className="timeline-thread" />}
                      <div
                        className="absolute left-0 top-0 w-6 h-6 rounded-full border-4 border-surface-container-lowest z-10"
                        style={{ backgroundColor: `rgba(0, 105, 114, ${opacities[aIdx % 3] || 0.2})` }}
                      />
                      <span className="text-secondary uppercase text-xs font-semibold">{slot}</span>
                      <h4 className="font-display text-lg text-primary mt-1 mb-2">{activity.name}</h4>
                      <p className="text-base text-on-surface-variant">{activity.description}</p>
                      {activity.estimated_cost_usd > 0 && (
                        <span className="inline-block mt-2 text-xs font-semibold text-tertiary bg-tertiary-fixed/20 px-2 py-0.5 rounded">
                          ~${activity.estimated_cost_usd}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
              {day.transport_notes && (
                <div className="px-[var(--spacing-stack-md)] pb-4">
                  <p className="text-xs text-on-surface-variant flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-secondary">directions</span>
                    {day.transport_notes}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>



      {/* ── Actions ── */}
      <div className="flex flex-col md:flex-row items-center justify-center gap-4 border-t border-outline-variant/30 pt-[var(--spacing-stack-md)]">
        <Link
          to="/"
          className="w-full md:w-auto px-8 py-3 rounded-full bg-surface-container-high text-on-surface text-sm font-semibold hover:bg-surface-variant transition-colors flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined">add_circle</span> Start New Plan
        </Link>
        <button
          onClick={copyPlanId}
          className="w-full md:w-auto px-8 py-3 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-lg cursor-pointer"
        >
          <span className="material-symbols-outlined">save</span> {copied ? 'Copied!' : 'Copy Plan ID'}
        </button>
      </div>
    </div>
  );
}
