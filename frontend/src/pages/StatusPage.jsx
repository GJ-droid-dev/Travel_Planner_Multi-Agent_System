import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { getPlan, createPlan } from '../api';

const STEPS = [
  { id: 'understand', label: 'Understanding', sub: 'Intents mapped', icon: 'check_circle' },
  { id: 'research', label: 'Researching', sub: 'Fetching landmarks', icon: 'check_circle' },
  { id: 'plan', label: 'Planning', sub: 'Optimizing routes', icon: 'progress_activity' },
  { id: 'budget', label: 'Checking costs', sub: 'Budget sync', icon: 'payments' },
  { id: 'review', label: 'Reviewing', sub: 'Final polish', icon: 'rate_review' },
];

export default function StatusPage() {
  const { planId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const userQuery = location.state?.query || '';

  const [activeStep, setActiveStep] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const pollRef = useRef(null);

  useEffect(() => {
    const timer = setInterval(() => setElapsedSeconds(prev => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  // Poll backend for completion or generate immediately
  useEffect(() => {
    if (!planId) return;

    if (planId === 'generating' && location.state?.payload) {
      const payload = location.state.payload;
      
      async function generate() {
        try {
          const onProgress = (nodeName) => {
            if (nodeName === 'parse_request') setActiveStep(0);
            else if (nodeName === 'destination' || nodeName === 'logistics_base' || nodeName === 'budget_base') setActiveStep(prev => Math.max(prev, 1));
            else if (nodeName === 'merge_draft_itinerary') setActiveStep(2);
            else if (nodeName === 'logistics_final' || nodeName === 'budget_final') setActiveStep(3);
            else if (nodeName === 'review') setActiveStep(4);
          };
          const data = await createPlan(payload, onProgress);
          // When creating with SSE, `data` is just { plan_id }, we need to fetch the full plan
          const fullPlan = await getPlan(data.plan_id);
          if (!fullPlan.itinerary) {
            navigate('/error', { state: { errorType: 'generation_failed' }, replace: true });
            return;
          }
          navigate(`/itinerary/${data.plan_id}`, { state: { plan: fullPlan }, replace: true });
        } catch {
          navigate('/error', { state: { errorType: 'generation_failed' }, replace: true });
        }
      }
      
      generate();
      return;
    }

    async function poll() {
      try {
        const data = await getPlan(planId);
        if (data.status === 'completed' || data.status === 'partial') {
          navigate(`/itinerary/${planId}`, { state: { plan: data }, replace: true });
        } else if (data.status === 'failed') {
          navigate('/error', { state: { plan: data }, replace: true });
        }
      } catch {
        // keep polling
      }
    }

    pollRef.current = setInterval(poll, 3000);
    // Also poll immediately
    poll();

    return () => clearInterval(pollRef.current);
  }, [planId, navigate, location.state]);

  function handleCancel() {
    if (window.confirm('Are you sure you want to stop the planning process?')) {
      navigate('/');
    }
  }

  const progressWidth = `${(activeStep / (STEPS.length - 1)) * 100}%`;

  return (
    <div className="flex flex-col items-center min-h-[80vh] px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)] max-w-[var(--spacing-container-max)] mx-auto w-full py-12 gap-[var(--spacing-stack-md)]">

      {/* Central Animation */}
      <section className="flex-grow flex flex-col items-center justify-center py-[var(--spacing-stack-lg)] select-none">
        <div className="relative w-full max-w-lg flex items-center justify-center mb-[var(--spacing-stack-md)]">
          <div className="flex flex-col items-center text-center px-6">
            <div className="w-24 h-24 rounded-full bg-white shadow-xl flex items-center justify-center mb-6 pulse-soft">
              <span className="material-symbols-outlined text-secondary text-5xl" style={{ fontVariationSettings: "'wght' 200" }}>
                hub
              </span>
            </div>
            <h1 className="font-display text-3xl font-semibold text-primary mb-2">Architecting Your Oasis</h1>
            <p className="text-base text-on-surface-variant max-w-sm">
              Building a grounded itinerary using verified local travel data.
            </p>
            <div className="mt-4 inline-flex items-center gap-2 bg-surface-container-high px-3 py-1.5 rounded-full border border-outline-variant/30">
              <span className="material-symbols-outlined text-sm text-tertiary">timer</span>
              <span className="text-sm font-medium text-on-surface-variant">Time elapsed: {elapsedSeconds}s <span className="opacity-50">/ ~30 secs to 1 min</span></span>
            </div>
          </div>
        </div>

        {/* Multi-Agent Workflow Timeline */}
        <div className="w-full max-w-4xl glass-panel p-[var(--spacing-stack-md)] rounded-2xl shadow-sm border border-outline-variant/30">
          <div className="relative flex flex-col md:flex-row justify-between items-start md:items-start gap-8 md:gap-0">
            {/* Timeline connector */}
            <div className="hidden md:block absolute top-[28px] left-[10%] right-[10%] h-[2px] bg-outline-variant/30 -z-10">
              <div className="h-full bg-secondary transition-all duration-1000 ease-in-out" style={{ width: progressWidth }} />
            </div>

            {STEPS.map((step, i) => {
              const isCompleted = i < activeStep;
              const isActive = i === activeStep;
              const isPending = i > activeStep;

              return (
                <div key={step.id} className={`flex md:flex-col items-center gap-4 md:text-center w-full md:flex-1 ${isPending ? 'opacity-50' : ''}`}>
                  <div
                    className={`w-14 h-14 rounded-full flex items-center justify-center shadow-md ${
                      isCompleted
                        ? 'bg-secondary text-on-secondary ring-4 ring-secondary-container/30'
                        : isActive
                        ? 'bg-white border-2 border-secondary text-secondary shadow-lg timeline-glow relative'
                        : 'bg-surface-container-high border-2 border-outline-variant text-on-surface-variant'
                    }`}
                  >
                    {isCompleted && <span className="material-symbols-outlined">check_circle</span>}
                    {isActive && (
                      <>
                        <span className="material-symbols-outlined animate-spin">progress_activity</span>
                        <div className="absolute -inset-2 bg-secondary/10 rounded-full animate-ping" />
                      </>
                    )}
                    {isPending && <span className="material-symbols-outlined">{step.icon}</span>}
                  </div>
                  <div>
                    <p className={`text-sm font-semibold ${isActive ? 'text-on-surface font-bold' : isCompleted ? 'text-secondary' : ''}`}>
                      {step.label}
                    </p>
                    <p className={`text-xs ${isActive ? 'text-secondary' : 'text-on-surface-variant'}`}>{step.sub}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>


        {/* Cancel button */}
        <button
          onClick={handleCancel}
          className="mt-8 flex items-center gap-2 text-on-surface-variant text-sm font-semibold hover:opacity-80 transition-opacity cursor-pointer select-auto"
        >
          <span className="material-symbols-outlined">arrow_back</span>
          Cancel
        </button>
      </section>
    </div>
  );
}
