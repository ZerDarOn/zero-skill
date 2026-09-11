import {
  Profiler,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ProfilerOnRenderCallback,
} from "react";
import "./styles.css";

const ITEM_COUNT = 100;
const VIRTUAL_WINDOW_SIZE = 5;
const VIRTUAL_ITEMS = Array.from({ length: ITEM_COUNT }, (_, index) => ({
  id: `item-${index + 1}`,
  label: `Item ${index + 1}`,
}));
const FILTER_ITEMS = ["Alpha", "Alpine", "Beta", "Gamma"];

function ControlledRaceSearch() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState("No result");
  const [pendingQueries, setPendingQueries] = useState<string[]>([]);
  const latestRequestIdRef = useRef(0);
  const pendingResolversRef = useRef(new Map<string, (value: string) => void>());

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submittedQuery = query.trim();

    if (!submittedQuery) {
      return;
    }

    const requestId = latestRequestIdRef.current + 1;
    latestRequestIdRef.current = requestId;
    setResult(`Loading ${submittedQuery}`);

    const response = new Promise<string>((resolve) => {
      pendingResolversRef.current.set(submittedQuery, resolve);
      setPendingQueries((current) => [...current, submittedQuery]);
    });

    void response.then((value) => {
      if (requestId === latestRequestIdRef.current) {
        setResult(value);
      }
    });
  }

  function handleResolve(pendingQuery: string) {
    const resolve = pendingResolversRef.current.get(pendingQuery);

    if (!resolve) {
      return;
    }

    pendingResolversRef.current.delete(pendingQuery);
    setPendingQueries((current) => current.filter((item) => item !== pendingQuery));
    resolve(`Result for ${pendingQuery}`);
  }

  return (
    <section aria-labelledby="race-heading">
      <h2 id="race-heading">Late response control</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="race-query">Search query</label>
        <div className="control-row">
          <input
            id="race-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit">Start search</button>
        </div>
      </form>
      <div className="control-row" aria-label="Pending requests">
        {pendingQueries.map((pendingQuery) => (
          <button
            key={pendingQuery}
            type="button"
            onClick={() => handleResolve(pendingQuery)}
          >
            Resolve {pendingQuery}
          </button>
        ))}
      </div>
      <output role="status" aria-label="Search result">
        {result}
      </output>
    </section>
  );
}

function VirtualFocusList() {
  const [activeIndex, setActiveIndex] = useState(VIRTUAL_WINDOW_SIZE - 1);
  const listRef = useRef<HTMLDivElement>(null);
  const shouldTransferFocusRef = useRef(false);
  const maximumWindowStart = ITEM_COUNT - VIRTUAL_WINDOW_SIZE;
  const windowStart = Math.min(
    Math.max(activeIndex - VIRTUAL_WINDOW_SIZE + 1, 0),
    maximumWindowStart,
  );
  const visibleItems = VIRTUAL_ITEMS.slice(
    windowStart,
    windowStart + VIRTUAL_WINDOW_SIZE,
  );

  useLayoutEffect(() => {
    if (!shouldTransferFocusRef.current) {
      return;
    }

    const target = listRef.current?.querySelector<HTMLElement>(
      `[data-item-index="${activeIndex}"]`,
    );
    target?.focus();
    shouldTransferFocusRef.current = false;
  }, [activeIndex, windowStart]);

  function handleKeyDown(
    event: KeyboardEvent<HTMLDivElement>,
    itemIndex: number,
  ) {
    const offset = event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0;

    if (offset === 0) {
      return;
    }

    event.preventDefault();
    const nextIndex = Math.min(Math.max(itemIndex + offset, 0), ITEM_COUNT - 1);

    if (nextIndex === itemIndex) {
      return;
    }

    shouldTransferFocusRef.current = true;
    setActiveIndex(nextIndex);
  }

  return (
    <section aria-labelledby="virtual-heading">
      <h2 id="virtual-heading">Virtual focus handoff</h2>
      <p id="virtual-help">Use the up and down arrow keys to move through all 100 items.</p>
      <div
        ref={listRef}
        role="listbox"
        aria-label="Virtual results"
        aria-describedby="virtual-help"
      >
        {visibleItems.map((item, visibleIndex) => {
          const itemIndex = windowStart + visibleIndex;
          const isActive = itemIndex === activeIndex;

          return (
            <div
              key={item.id}
              role="option"
              aria-selected={isActive}
              aria-posinset={itemIndex + 1}
              aria-setsize={ITEM_COUNT}
              data-item-index={itemIndex}
              tabIndex={isActive ? 0 : -1}
              onKeyDown={(event) => handleKeyDown(event, itemIndex)}
            >
              {item.label}
            </div>
          );
        })}
      </div>
    </section>
  );
}

interface FilteredResultsProps {
  query: string;
}

function FilteredResults({ query }: FilteredResultsProps) {
  const normalizedQuery = query.toLocaleLowerCase();
  const visibleItems = FILTER_ITEMS.filter((item) =>
    item.toLocaleLowerCase().includes(normalizedQuery),
  );

  return (
    <ul aria-label="Filtered results">
      {visibleItems.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function MeasuredResults() {
  const [query, setQuery] = useState("");
  const profilerCommitCountRef = useRef(0);
  const analyticsSyncCountRef = useRef(0);
  const profilerEvidenceRef = useRef<HTMLOutputElement>(null);
  const analyticsEvidenceRef = useRef<HTMLOutputElement>(null);

  // React state here would add observer-induced commits to the measurement.
  const handleRender: ProfilerOnRenderCallback = (
    _id,
    _phase,
    actualDuration,
  ) => {
    profilerCommitCountRef.current += 1;
    const evidence = profilerEvidenceRef.current;

    if (evidence) {
      evidence.dataset.commitCount = String(profilerCommitCountRef.current);
      evidence.textContent = `commits=${profilerCommitCountRef.current}; actualDuration=${actualDuration.toFixed(3)}ms`;
    }
  };

  useEffect(() => {
    analyticsSyncCountRef.current += 1;
    const evidence = analyticsEvidenceRef.current;

    if (evidence) {
      evidence.dataset.syncCount = String(analyticsSyncCountRef.current);
      evidence.textContent = `syncs=${analyticsSyncCountRef.current}; query=${query}`;
    }
  }, [query]);

  return (
    <section aria-labelledby="profiler-heading">
      <h2 id="profiler-heading">Measured render derivation</h2>
      <label htmlFor="filter-query">Filter measured results</label>
      <input
        id="filter-query"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <div className="evidence-row">
        <output
          ref={profilerEvidenceRef}
          role="status"
          aria-label="Profiler evidence"
          data-commit-count="0"
        >
          commits=0
        </output>
        <output
          ref={analyticsEvidenceRef}
          role="status"
          aria-label="Analytics evidence"
          data-sync-count="0"
        >
          syncs=0
        </output>
      </div>
      <Profiler id="filtered-results" onRender={handleRender}>
        <FilteredResults query={query} />
      </Profiler>
    </section>
  );
}

export function App() {
  return (
    <main>
      <header>
        <p className="eyebrow">Synthetic browser acceptance</p>
        <h1>React performance review runtime</h1>
      </header>
      <ControlledRaceSearch />
      <VirtualFocusList />
      <MeasuredResults />
    </main>
  );
}
