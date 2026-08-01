import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPlan } from '../api';
import { HERO_IMAGE_URL } from '../images';

const INTEREST_OPTIONS = [
  'Food', 'Architecture', 'Desert', 'Culture',
  'Beaches', 'Shopping', 'Wellness', 'Adventure'
];

const AVOIDANCE_OPTIONS = [
  'Crowds', 'Nightlife', 'Long walks', 'Shopping'
];

const EXCHANGE_RATE_USD_AED = 3.67;

export default function LandingPage() {
  const navigate = useNavigate();
  
  // State for structured form
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [duration, setDuration] = useState(5);
  const [travelers, setTravelers] = useState(2);
  const [budgetAmount, setBudgetAmount] = useState(3000);
  const [currency, setCurrency] = useState('USD');
  const [budgetScope, setBudgetScope] = useState('Total trip'); // 'Total trip' | 'Per traveler'
  const [includeAccommodation, setIncludeAccommodation] = useState(true);
  
  const [interests, setInterests] = useState([]);
  const [avoidances, setAvoidances] = useState([]);
  const [extraNotes, setExtraNotes] = useState('');

  // Validation
  const isValid = duration >= 1 && duration <= 14 && 
                  travelers >= 1 && travelers <= 20 && 
                  budgetAmount > 0 && budgetAmount.toString().trim() !== '';

  const handleToggleChip = (list, setList, max, item) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item));
    } else if (list.length < max) {
      setList([...list, item]);
    }
  };

  const estimatedTotalUSD = useMemo(() => {
    let amount = parseFloat(budgetAmount) || 0;
    if (budgetScope === 'Per traveler') {
      amount = amount * travelers;
    }
    if (currency === 'AED') {
      amount = amount / EXCHANGE_RATE_USD_AED;
    }
    return Math.round(amount);
  }, [budgetAmount, travelers, budgetScope, currency]);

  function handleSubmit(e) {
    e.preventDefault();
    if (!isValid) return;
    
    const payload = {
      destination: "Dubai, UAE",
      duration_days: parseInt(duration),
      travelers: parseInt(travelers),
      budget_amount: parseFloat(budgetAmount),
      budget_currency: currency,
      budget_scope: budgetScope,
      include_accommodation: includeAccommodation,
      interests,
      avoidances,
      extra_notes: extraNotes.trim() || undefined
    };

    navigate('/status/generating', { state: { query: 'Custom Trip', payload } });
  }

  const steps = [
    { icon: 'psychology', title: 'Understand', desc: 'AI analyzes your nuances, preferences, and pace.' },
    { icon: 'travel_explore', title: 'Research', desc: 'Simultaneous scans of 500+ local venues.' },
    { icon: 'route', title: 'Route', desc: 'Optimization of logistics and transit paths.' },
    { icon: 'payments', title: 'Budget', desc: 'Financial agent secures the best value slots.' },
    { icon: 'verified', title: 'Review', desc: 'Final human-like polish for your approval.', gold: true },
  ];

  return (
    <>
      <section className="pt-12 pb-[var(--spacing-stack-lg)] overflow-hidden">
        <div className="max-w-[var(--spacing-container-max)] mx-auto px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)]">
          <div className="flex flex-col lg:flex-row items-start gap-12">
            
            {/* Left column */}
            <div className="flex-1 space-y-[var(--spacing-stack-md)] w-full">
              <span className="inline-block px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full text-sm font-semibold tracking-wide">
                Powered by Advanced Neural Agents
              </span>

              <h1 className="font-display text-4xl md:text-5xl font-bold text-primary leading-tight tracking-tight">
                A Dubai itinerary <br /> built around{' '}
                <span className="text-secondary">you</span>
              </h1>

              <p className="text-lg text-on-surface-variant max-w-xl leading-relaxed">
                Our multi-agent AI system doesn't just search; it negotiates, optimizes, and designs.
              </p>

              {/* Structured Input Form */}
              <form onSubmit={handleSubmit} className="bg-surface-container-lowest desert-shadow p-6 md:p-8 rounded-xl border border-outline-variant/10 space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-primary mb-1">Plan your Dubai trip</h2>
                  <p className="text-sm text-on-surface-variant mb-6">Complete the essentials before generating your itinerary.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Destination */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Destination</label>
                    <div className="w-full bg-surface-variant/50 border border-outline-variant/20 rounded-lg p-3 text-sm text-on-surface-variant cursor-not-allowed">
                      Dubai, UAE ▾
                    </div>
                  </div>

                  {/* Duration */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Trip duration</label>
                    <div className="flex items-center justify-between w-full bg-surface border border-outline-variant/20 rounded-lg p-2">
                      <button type="button" onClick={() => setDuration(Math.max(1, duration - 1))} className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-variant cursor-pointer text-primary">-</button>
                      <span className="text-sm font-semibold text-primary">{duration} days</span>
                      <button type="button" onClick={() => setDuration(Math.min(14, duration + 1))} className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-variant cursor-pointer text-primary">+</button>
                    </div>
                  </div>

                  {/* Travelers */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Travelers</label>
                    <div className="flex items-center justify-between w-full bg-surface border border-outline-variant/20 rounded-lg p-2">
                      <button type="button" onClick={() => setTravelers(Math.max(1, travelers - 1))} className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-variant cursor-pointer text-primary">-</button>
                      <span className="text-sm font-semibold text-primary">{travelers} {travelers === 1 ? 'traveler' : 'travelers'}</span>
                      <button type="button" onClick={() => setTravelers(Math.min(20, travelers + 1))} className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-variant cursor-pointer text-primary">+</button>
                    </div>
                  </div>

                  {/* Budget */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Total trip budget</label>
                    <div className="flex items-center w-full bg-surface border border-outline-variant/20 rounded-lg focus-within:border-secondary transition-colors overflow-hidden">
                      <span className="pl-3 text-on-surface-variant text-sm">$</span>
                      <input 
                        type="number" 
                        min="1"
                        value={budgetAmount}
                        onChange={(e) => setBudgetAmount(e.target.value)}
                        className="flex-1 bg-transparent p-3 text-sm font-semibold text-primary focus:outline-none"
                      />
                      <select 
                        value={currency} 
                        onChange={(e) => setCurrency(e.target.value)}
                        className="bg-surface-variant/50 p-3 text-sm font-semibold text-primary border-l border-outline-variant/20 focus:outline-none cursor-pointer"
                      >
                        <option value="USD">USD</option>
                        <option value="AED">AED</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Budget applies to</label>
                  <div className="flex p-1 bg-surface-variant/30 rounded-lg">
                    <button type="button" onClick={() => setBudgetScope('Total trip')} className={`flex-1 py-2 text-sm font-semibold rounded-md transition-all ${budgetScope === 'Total trip' ? 'bg-surface shadow-sm text-primary' : 'text-on-surface-variant hover:text-primary'}`}>Total trip</button>
                    <button type="button" onClick={() => setBudgetScope('Per traveler')} className={`flex-1 py-2 text-sm font-semibold rounded-md transition-all ${budgetScope === 'Per traveler' ? 'bg-surface shadow-sm text-primary' : 'text-on-surface-variant hover:text-primary'}`}>Per traveler</button>
                  </div>
                  {(currency === 'AED' || budgetScope === 'Per traveler') && budgetAmount > 0 && (
                    <p className="text-xs text-secondary font-medium pt-1">
                      Estimated total planning budget: USD {estimatedTotalUSD.toLocaleString()}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Accommodation</label>
                  <div className="flex p-1 bg-surface-variant/30 rounded-lg">
                    <button type="button" onClick={() => setIncludeAccommodation(true)} className={`flex-1 py-2 text-sm font-semibold rounded-md transition-all ${includeAccommodation ? 'bg-surface shadow-sm text-primary' : 'text-on-surface-variant hover:text-primary'}`}>Include stay</button>
                    <button type="button" onClick={() => setIncludeAccommodation(false)} className={`flex-1 py-2 text-sm font-semibold rounded-md transition-all ${!includeAccommodation ? 'bg-surface shadow-sm text-primary' : 'text-on-surface-variant hover:text-primary'}`}>I already have accommodation</button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold tracking-wide text-secondary uppercase">What would you like to do?</label>
                  <div className="flex flex-wrap gap-2">
                    {INTEREST_OPTIONS.map(opt => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => handleToggleChip(interests, setInterests, 5, opt)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer border ${interests.includes(opt) ? 'bg-secondary text-on-secondary border-secondary' : 'bg-surface border-outline-variant/30 text-on-surface-variant hover:border-secondary/50'}`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold tracking-wide text-secondary uppercase">What would you like to avoid?</label>
                  <div className="flex flex-wrap gap-2">
                    {AVOIDANCE_OPTIONS.map(opt => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => handleToggleChip(avoidances, setAvoidances, 10, opt)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer border ${avoidances.includes(opt) ? 'bg-error text-error-container border-error' : 'bg-surface border-outline-variant/30 text-on-surface-variant hover:border-error/50'}`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold tracking-wide text-secondary uppercase">Extra details (optional)</label>
                  <textarea
                    value={extraNotes}
                    onChange={(e) => setExtraNotes(e.target.value)}
                    maxLength={1000}
                    className="w-full bg-surface border border-outline-variant/20 rounded-lg p-3 text-sm focus:border-secondary focus:ring-0 focus:outline-none transition-all resize-none min-h-[80px]"
                    placeholder="Vegetarian meals, slower pace, travelling with parents..."
                  />
                </div>

                {error && (
                  <div className="p-3 bg-error-container/20 border border-error/30 rounded-lg text-error text-sm">
                    {error}
                  </div>
                )}

                <div className="pt-2 border-t border-outline-variant/10">
                  <button
                    type="submit"
                    disabled={loading || !isValid}
                    className="w-full px-8 py-4 bg-primary text-on-primary rounded-lg text-sm font-semibold tracking-wide flex items-center justify-center gap-3 hover:opacity-90 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                  >
                    {loading ? 'Creating...' : 'Generate my Dubai itinerary'}
                    <span className="material-symbols-outlined">auto_awesome</span>
                  </button>
                  {!isValid && (
                    <p className="text-center text-xs text-on-surface-variant mt-3">
                      Add a valid trip duration, travelers, and budget to continue.
                    </p>
                  )}
                </div>
              </form>
            </div>

            {/* Right column — Hero Image + Trip Summary (Sticky) */}
            <div className="flex-1 w-full relative hidden lg:block sticky top-32 space-y-6">
              <div className="relative w-full aspect-square rounded-2xl overflow-hidden shadow-2xl bg-surface-container">
                {HERO_IMAGE_URL && !HERO_IMAGE_URL.startsWith('PLACEHOLDER') ? (
                  <img src={HERO_IMAGE_URL} alt="Dubai skyline at twilight" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-surface-container-low to-surface-container-high">
                    <div className="text-center text-on-surface-variant/60 space-y-3">
                      <span className="material-symbols-outlined text-6xl">image</span>
                      <p className="text-sm font-semibold">Hero Image</p>
                      <p className="text-xs">800×800 JPEG/WebP</p>
                    </div>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-primary/40 to-transparent" />
                {loading && (
                  <div className="absolute bottom-8 left-8 right-8 bg-surface/10 backdrop-blur-xl p-4 rounded-xl border border-white/20">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center text-on-secondary">
                        <span className="material-symbols-outlined fill-icon">smart_toy</span>
                      </div>
                      <div>
                        <p className="text-white text-sm font-semibold">Current Optimization</p>
                        <p className="text-white/70 text-xs">Balancing transit times vs landmark density...</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Live trip summary card */}
              <div className="bg-surface-container-lowest border border-outline-variant/10 rounded-xl p-5 desert-shadow space-y-4">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-lg">summarize</span>
                  <h3 className="text-xs font-semibold tracking-wide text-secondary uppercase">Trip at a glance</h3>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-surface rounded-lg p-3 border border-outline-variant/10">
                    <p className="text-xs text-on-surface-variant mb-0.5">Duration</p>
                    <p className="text-lg font-bold text-primary">{duration} <span className="text-sm font-normal text-on-surface-variant">days</span></p>
                  </div>
                  <div className="bg-surface rounded-lg p-3 border border-outline-variant/10">
                    <p className="text-xs text-on-surface-variant mb-0.5">Travelers</p>
                    <p className="text-lg font-bold text-primary">{travelers} <span className="text-sm font-normal text-on-surface-variant">{travelers === 1 ? 'person' : 'people'}</span></p>
                  </div>
                  <div className="bg-surface rounded-lg p-3 border border-outline-variant/10">
                    <p className="text-xs text-on-surface-variant mb-0.5">Daily budget</p>
                    <p className="text-lg font-bold text-primary">
                      ${duration > 0 ? Math.round(estimatedTotalUSD / duration).toLocaleString() : '—'}
                      <span className="text-sm font-normal text-on-surface-variant">/day</span>
                    </p>
                  </div>
                  <div className="bg-surface rounded-lg p-3 border border-outline-variant/10">
                    <p className="text-xs text-on-surface-variant mb-0.5">Per person/day</p>
                    <p className="text-lg font-bold text-primary">
                      ${duration > 0 && travelers > 0 ? Math.round(estimatedTotalUSD / duration / travelers).toLocaleString() : '—'}
                      <span className="text-sm font-normal text-on-surface-variant">/day</span>
                    </p>
                  </div>
                </div>

                {(interests.length > 0 || avoidances.length > 0) && (
                  <div className="space-y-2 pt-1 border-t border-outline-variant/10">
                    {interests.length > 0 && (
                      <div>
                        <p className="text-xs text-on-surface-variant mb-1.5">Interests</p>
                        <div className="flex flex-wrap gap-1.5">
                          {interests.map(i => (
                            <span key={i} className="px-2 py-0.5 bg-secondary/10 text-secondary rounded-full text-xs font-medium">{i}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {avoidances.length > 0 && (
                      <div>
                        <p className="text-xs text-on-surface-variant mb-1.5">Avoiding</p>
                        <div className="flex flex-wrap gap-1.5">
                          {avoidances.map(a => (
                            <span key={a} className="px-2 py-0.5 bg-error/10 text-error rounded-full text-xs font-medium">{a}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-start gap-2 pt-1 border-t border-outline-variant/10">
                  <span className="material-symbols-outlined text-tertiary-container text-base mt-0.5">lightbulb</span>
                  <p className="text-xs text-on-surface-variant leading-relaxed">
                    {estimatedTotalUSD >= 500 * duration
                      ? 'Luxury tier — premium hotels and fine dining are within reach.'
                      : estimatedTotalUSD >= 150 * duration
                      ? 'Comfortable tier — great mid-range hotels and experiences.'
                      : 'Budget tier — hostels, street food, and free attractions.'}
                  </p>
                </div>
              </div>

              {/* Decorative blurs */}
              <div className="absolute -top-4 -right-4 w-24 h-24 bg-tertiary-fixed rounded-full blur-3xl opacity-30 pointer-events-none" />
              <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-secondary-fixed rounded-full blur-3xl opacity-20 pointer-events-none" />
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="py-[var(--spacing-stack-lg)] bg-surface-container-low">
        <div className="max-w-[var(--spacing-container-max)] mx-auto px-[var(--spacing-margin-mobile)] md:px-[var(--spacing-margin-desktop)] text-center">
          <h2 className="font-display text-3xl font-semibold text-primary mb-12">How it works</h2>
          <div className="relative grid grid-cols-1 md:grid-cols-5 gap-8 items-start">
            <div className="hidden md:block absolute top-12 left-[10%] right-[10%] h-0.5 timeline-gradient" />
            {steps.map(({ icon, title, desc, gold }) => (
              <div key={title} className="relative z-10 flex flex-col items-center group">
                <div
                  className={`w-16 h-16 rounded-full bg-surface flex items-center justify-center mb-4 desert-shadow group-hover:scale-110 transition-transform duration-300 border-2 ${
                    gold ? 'border-tertiary-container' : 'border-secondary'
                  }`}
                >
                  <span className={`material-symbols-outlined text-3xl ${gold ? 'text-tertiary-container' : 'text-secondary'}`}>
                    {icon}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-primary mb-2">{title}</h3>
                <p className="text-xs text-on-surface-variant px-4">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
