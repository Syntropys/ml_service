# CLAUDE.md — Agrolytics Project Rules

> Project: Agrolytics — Smart Agricultural BI Platform  
> Team: Pijak (PJK-GM030) × IBM Skillsbuild  
> Duration: 5 weeks (capstone)  
> Last updated: 2026-05-30

## Project Context

Agrolytics adalah platform business intelligence berbasis AI untuk wilayah Kalimantan.
Output utama: prediksi produktivitas padi, peta interaktif, clustering wilayah prioritas,
laporan PDF, dashboard analitik. Phase 1 (5 minggu capstone) fokus pengalaman antarmuka
end-to-end dengan data Supabase. Phase 2 (post-capstone) menambahkan inference ML real-time.

**Design doc**: `docs/superpowers/specs/2026-05-29-agrolytics-design.md`

## Key Decisions (Locked)

1. **Scope**: Phase 1 4 modul + Phase 2 mockup roadmap (opsi D)
2. **Deployment**: Phase 1 Vercel-only mock → Phase 2 Vercel + Railway proxy
3. **Framework**: Vite + React + TypeScript + React Router DOM
4. **Auth**: Supabase Auth + Cloudflare Turnstile + Google OAuth, 2-tier (Admin/User)
5. **Map**: Kabupaten/Kota Kalimantan (~56 wilayah)
6. **Dashboard**: 5 user + 2 admin + 2 Phase 2 placeholder modules
7. **Landing**: 10 sections cinematic, floating glass header, parallax hero
8. **Theme**: Dark Emerald + Gold accent, light theme switcher
9. **Reports**: A1 per-region + B2 multi-year overlay
10. **Data**: A3 Supabase from start + B3 hybrid prediction (Phase 2)
11. **Language**: Bahasa Indonesia only (Phase 1)
12. **Testing**: Smoke test + manual QA, Chrome desktop only

## Folder Structure

```
agrolytics/
├── docs/superpowers/specs/2026-05-29-agrolytics-design.md  (design doc)
├── docs/superpowers/plans/2026-05-29-week-1-foundation.md  (impl plan)
├── supabase/migrations/   (0001-0005, versioned schema + RLS fix)
├── supabase/seed.sql      (56 regions + dummy timeseries, reproducible)
├── src/
│   ├── features/          (feature-first: auth, landing, dashboard,
│   │                       forecast, geospatial, historical, reports,
│   │                       admin, coming-soon)
│   ├── components/         (shell, chart, map, motion — hand-built, NO shadcn)
│   ├── services/          (business logic: regions, production, predictions,
│   │                       clusters, profiles, audit, auth)
│   ├── hooks/             (TanStack Query wrappers)
│   ├── stores/            (Zustand: auth, theme)
│   ├── styles/            (globals.css + theme.ts tokens)
│   └── types/             (database.ts — generated from live schema)
├── public/
│   └── frames/hero/frame-001.jpg ... frame-031.jpg  (parallax frames)
└── tests/                 (Vitest smoke)
```

## Tech Stack

**Frontend**:
- Vite (build tool) + pnpm
- React 18 + TypeScript
- React Router v6 (routing, lazy-loaded dashboard routes)
- Tailwind CSS (styling) — components hand-built, NO shadcn/ui
- TanStack Query (async state)
- Zustand (global state: auth + theme)
- Chart.js + react-chartjs-2 (data viz)
- Leaflet + react-leaflet@4 (geospatial; v5 incompatible with React 18)
- GSAP + Lenis + Framer Motion (animations)
- jsPDF + html2canvas (PDF export)
- Zod + React Hook Form (validation)

**Backend** (Phase 2 only):
- FastAPI (Python)
- Railway (deployment)

**Database**:
- Supabase PostgreSQL
- Supabase Auth
- Supabase Storage

**External**:
- Cloudflare Turnstile (CAPTCHA)
- Google OAuth (Supabase provider)
- NASA POWER (weather data)
- BPS (production data)

**Deployment**:
- Vercel (frontend)
- GitHub Actions (CI/CD)

## Development Workflow

### Git Branching

- `main` — production branch (protected, requires PR review)
- `develop` — integration branch (default for PRs)
- Feature branches: `feature/module-name` (e.g., `feature/forecast-page`)
- Bugfix branches: `fix/issue-description` (e.g., `fix/theme-switcher-hydration`)

**Commit message format**:
```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### Code Review

- All PRs require 1 approval before merge
- Linter + typecheck must pass (GitHub Actions)
- No console errors in Chrome DevTools
- Accessibility check (reduced motion, keyboard nav)

### Testing

- Unit tests: Vitest (smoke only, not comprehensive)
- E2E tests: Playwright (smoke only, manual trigger)
- Manual QA: Chrome desktop, all P0 flows

## Design System

**Colors**:
- Dark theme: `#0A1F1A` (bg) + `#10B981` (emerald) + `#D4AF37` (gold)
- Light theme: `#FAFAF7` (bg) + `#059669` (emerald) + `#B8860B` (gold)
- Theme switch via `[data-theme]` attribute (CSS variables)

**Typography**:
- Display: Instrument Serif (hero, headlines)
- Body: Inter (UI)
- Mono: IBM Plex Mono (numbers, data)

**Motion**:
- Lenis smooth scrolling (landing)
- GSAP ScrollTrigger (pin, scrub)
- Framer Motion (component reveal)
- Reduced motion respected (accessibility)

**Spacing**: Tailwind default (4px base unit)

**Tokens**: `src/styles/theme.ts` (single source of truth)

## API Contracts

**Phase 1**: All data via Supabase JS client + RLS.

**Service layer** (abstraction for Phase 1→2 swap):
```typescript
// src/services/*.ts
export const regionsService = { list(), getById() }
export const productionService = { byRegion(), multiRegionByYears() }
export const predictionsService = { byRegion(), baselineForAllRegions() }
// ... etc
```

**TanStack Query keys**: `['regions']`, `['predictions', regionId, modelName]`, etc.

**Phase 2**: Vercel rewrites `/api/*` → Railway FastAPI endpoints.

## Database

**Schema**: `supabase/migrations/` (versioned, apply in order)

**Tables**:
- `profiles` (extends auth.users)
- `regions` (56 kabupaten Kalimantan)
- `production_history` (BPS 2018–2025)
- `weather_history` (NASA POWER monthly)
- `predictions` (model output)
- `cluster_assignments` (K-means result)
- `audit_log` (admin actions)

**RLS**: Public read on `regions`, `production_history`, `weather_history`,
`cluster_assignments` (for landing Live Map). Auth/admin gated on others.
Admin policies call `is_admin()` SECURITY DEFINER helper (migration 0005) to
avoid infinite recursion — never inline an EXISTS-on-profiles subquery.

**Seed**: `supabase/seed.sql` (56 regions + dummy timeseries, idempotent —
`supabase db reset` re-applies migrations + seed).

**Map rendering**: Leaflet circle markers from `regions.centroid_lat/lng`,
colored by cluster (NOT GeoJSON choropleth polygon). GeoJSON/QGIS path
deferred — would only be needed for polygon choropleth upgrade later.

## Environment Variables

**Required** (`.env.local`, gitignored):
```
VITE_SUPABASE_URL=https://mawewomqcdnsqnxmkjlq.supabase.co
VITE_SUPABASE_ANON_KEY=<publishable-key>
VITE_CLOUDFLARE_TURNSTILE_SITE_KEY=<site-key>
```

**Optional** (Phase 2):
```
VITE_RAILWAY_API_URL=https://api-railway-host
```

## Deployment

**Vercel**:
- Auto-deploy on push to `main`
- Preview deploys for PRs
- Environment variables configured in Vercel dashboard
- Domain: `agrolytics.my.id` (or `*.vercel.app` fallback)

**Phase 2** (Railway):
- Vercel rewrites `/api/*` → Railway FastAPI
- GitHub Actions auto-deploy on push to `main`

## Timeline

**Minggu 1**: Foundation & Setup (M1: repo + auth page working)  
**Minggu 2**: Auth Flow & Landing Foundation (M2: signup/login + hero cinematic)  
**Minggu 3**: Landing Continued + Dashboard Core (M3: 7/10 landing sections + 2/5 dashboard)  
**Minggu 4**: Dashboard Complete + Admin + Reports (M4: full app functional)  
**Minggu 5**: Polish, Deploy, Demo (M5: live + pitch deck ready)

**Priority** (kalau time crunch):
- P0: Auth, Overview, Map, Forecast, Landing hero+map+solution+team+footer, theme, deploy
- P1: Historical, Reports, Admin, Landing problem+insight+tech+vision
- P2: Settings advanced, audit expand, PWA prompt, Lottie

## Accessibility

- **Reduced motion**: `prefers-reduced-motion` query respected (GSAP skip, static fallback)
- **Keyboard navigation**: All interactive elements focusable, logical tab order
- **Color contrast**: WCAG AA minimum (dark emerald + gold + white text)
- **Semantic HTML**: Proper heading hierarchy, alt text on images
- **Screen reader**: ARIA labels where needed (landing sections, form inputs)

**Testing**: Manual Chrome DevTools accessibility audit (Lighthouse)

## Performance

- **Bundle size**: Target <200KB gzipped (Vite build)
- **LCP**: <2.5s (Lighthouse target)
- **CLS**: <0.1 (no layout shift)
- **Code splitting**: Lazy load Leaflet, Chart.js, GSAP
- **Image optimization**: WebP with JPG fallback, responsive sizes
- **Caching**: TanStack Query staleTime per data type (10min master, 1min predictions)

## Security

- **Auth**: Supabase JWT + RLS policies (server-side enforcement)
- **CAPTCHA**: Cloudflare Turnstile on signup/login
- **Secrets**: Never commit `.env.local`, use Vercel dashboard for prod
- **HTTPS**: Enforced on production
- **CORS**: Supabase handles (no custom CORS needed)
- **Input validation**: Zod schemas on all forms

## Monitoring & Debugging

- **Console errors**: Zero tolerance (Chrome DevTools)
- **Network tab**: Check for failed requests, slow endpoints
- **Lighthouse**: Run before each PR (target >80 all categories)
- **Accessibility audit**: Lighthouse accessibility tab
- **Performance trace**: Chrome DevTools Performance tab (landing hero)

## Communication

- **Daily standup**: 9:00 AM (time TBD, platform: Discord/WhatsApp)
- **Weekly sync**: Friday 3:00 PM (design review, blockers, next week plan)
- **Async updates**: Jira board + GitHub PR comments
- **Escalation**: PM (Muhammad Rakha Djauhari) for blockers

## Handoff Checklist (Minggu 5)

- [ ] All P0 features tested + working
- [ ] Design doc reviewed + approved
- [ ] Code reviewed + merged to `main`
- [ ] Vercel deployment successful
- [ ] Pitch deck finalized
- [ ] Video demo recorded
- [ ] Team ready for presentation
- [ ] Post-capstone Phase 2 roadmap documented

## References

- Design doc: `docs/superpowers/specs/2026-05-29-agrolytics-design.md`
- Figma: [link TBD]
- Jira board: [link TBD]
- GitHub repo: [link TBD]
- Supabase project: `mawewomqcdnsqnxmkjlq.supabase.co`
- Vercel project: `agrolytics.my.id`

---

**Last updated**: 2026-05-30  
**Maintained by**: M. Rohid Rivaldi (Front-End Lead)
