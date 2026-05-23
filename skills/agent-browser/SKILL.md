---
name: agent-browser
description: Use Vercel's agent-browser CLI to verify web UI behavior with browser DOM snapshots, accessibility-tree snapshots, screenshots, and element interactions. Use when asked to inspect, test, or verify a running web app, confirm rendered DOM state, click through UI, fill forms, take screenshots, or debug browser-visible behavior.
allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*)
---

# agent-browser

Use this skill when browser-rendered behavior needs verification instead of relying only on code inspection. Prefer DOM/accessibility snapshots for fast checks, then screenshots when visual layout matters.

This skill is based on Vercel's `agent-browser` CLI.

## Setup

If `agent-browser` is not installed globally, run it through `npx`:

```bash
npx agent-browser --help
npx agent-browser install
```

If it is installed globally, `agent-browser ...` is fine. Use one style consistently during a task.

## Verification Loop

```bash
npx agent-browser open http://localhost:3000
npx agent-browser snapshot -i
npx agent-browser click @e3
npx agent-browser wait --load networkidle
npx agent-browser snapshot -i
```

After any click, submit, navigation, route change, or dynamic render, take a fresh snapshot before using another `@eN` reference. Element refs are only valid for the most recent snapshot.

## Snapshot Commands

```bash
npx agent-browser snapshot
npx agent-browser snapshot -i
npx agent-browser snapshot -i -u
npx agent-browser snapshot -i -c
npx agent-browser snapshot -i --json
npx agent-browser snapshot -s "#main"
```

Use `snapshot -i` first for compact interactive checks. Use full snapshots or scoped snapshots when validating rendered content, ARIA structure, headings, forms, dialogs, and page state.

## Common Checks

```bash
npx agent-browser get title
npx agent-browser get url
npx agent-browser get text @e1
npx agent-browser get html @e1
npx agent-browser get attr @e1 aria-label
npx agent-browser get value @e1
npx agent-browser get count ".selector"
```

Use these to verify exact rendered values after opening a page or performing an interaction.

## Interactions

```bash
npx agent-browser click @e1
npx agent-browser fill @e2 "example text"
npx agent-browser type @e2 " more text"
npx agent-browser press Enter
npx agent-browser check @e3
npx agent-browser uncheck @e3
npx agent-browser select @e4 "option-value"
npx agent-browser hover @e5
```

If refs are unavailable or stale, use semantic locators:

```bash
npx agent-browser find role button click --name "Submit"
npx agent-browser find text "Sign In" click
npx agent-browser find label "Email" fill "user@example.com"
npx agent-browser find placeholder "Search" type "query"
```

## Waiting

Pick a specific wait after page-changing actions:

```bash
npx agent-browser wait --text "Success"
npx agent-browser wait --url "**/dashboard"
npx agent-browser wait --load networkidle
npx agent-browser wait --load domcontentloaded
npx agent-browser wait --fn "window.appReady === true"
```

Avoid fixed sleeps except while debugging.

## Screenshots

```bash
npx agent-browser screenshot artifacts/page.png
```

Use screenshots when verifying layout, spacing, visual regressions, canvas output, or responsive behavior. DOM snapshots are still the default for content and interaction checks.

## Cleanup

```bash
npx agent-browser close
npx agent-browser close --all
```

Close sessions when verification is finished.
