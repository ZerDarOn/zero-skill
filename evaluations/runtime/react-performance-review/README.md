# React performance review runtime

This synthetic React 19.2 fixture exercises three runtime boundaries from `react-performance-review`:

- a late response cannot replace the newest search result;
- keyboard navigation across a virtual window preserves DOM focus and full-set semantics;
- render-time derivation preserves filtering and required analytics synchronization while React Profiler records commits.

The fixture is browser acceptance evidence for these implementations. It does not test implicit Skill routing, model output quality, production data, performance gains, or a real screen reader.

Run locally:

```sh
npm ci
npm run typecheck
npm test
```

On Windows, Playwright uses the installed Microsoft Edge channel by default. On other systems, install the matching Playwright Chromium before running the tests:

```sh
npx playwright install chromium
```
