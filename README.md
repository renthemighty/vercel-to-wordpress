# vercel-to-wordpress

Extension of the base44towordpress (b442) pipeline to handle Vercel/Next.js-hosted apps
being converted into WordPress themes. Shares the same architecture (Playwright crawl →
Analyzer → StaticRebuilder+Claude SectionGen → MediaImporter → deterministic visual-diff
gate), with Vercel/Next.js-specific detection and rewrite rules layered on top.

Read `docs/BUILD_SPEC.md` first.

Private repo — do not make public. No production keys committed here (reference only).
