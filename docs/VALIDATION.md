# Validation

This page distinguishes implementation tests, visual review and unverified hardware behaviour. A numeric review is not a universal quality or compatibility guarantee.

## Tested environment

- Omarchy 4.0.6-1; Lua Hyprland 0.56.2-4; Quickshell 0.3.2.r7.g2b4501a-1.
- 2560 × 1440 landscape output and 1080 × 1920 portrait output.
- Screen recordings at 60 FPS; public GIFs are reduced to 30 FPS for size.

## Launcher morph

Real launcher tests covered full, half and quarter tiled destinations on both outputs; an existing single-instance application; both directions across outputs; reopen/cancellation; unrelated focus and tiling changes; delayed/no-window launches; configuration reload; and failure of an isolated presentation process. Its compositor watchdog restored the held window in the recorded failure case in 1.773 seconds. That test did not crash the main shell.

Inert tests cover request-token ownership, delayed/repeated callbacks, waiting for both outputs, association, watchdogs and restoration. The final border refinement was checked locally in new native captures and both cross-output directions. The window's content coordinates remain unchanged.

Three independent GPT-6.1 Sol council rounds assessed the morph at 8.4/10 (medium confidence), 9.4/10 (high), and 9.8/10 (high). The last round found one small border discontinuity. The subsequent local refinement matches the native border's extent, colour and corner profile. **The independent 9.8 score has not been retroactively raised to 10.** These rounds concern the morph, not a universal score for the whole desktop or the public installer.

## Keyboard shortcuts

The installed native list contained 203 bindings. All 203 were traversed on both outputs, with no clipped action label or overflowing keycap row. The capture checks the actual output and mapped/presented state. Multi-term search, the empty state, and compound mouse-button labels were checked. An earlier capture failed to show the landscape output and was discarded and repeated. A disposable selection receiver verified the original row is returned byte-for-byte; no shortcut action was executed by that test. Generic selectors retain their original representation.

## Installation

Temporary-home tests cover dry-run behaviour, preservation of shell preferences and third-party entries, successful round-trip restoration, conflict refusal before writes, rollback after injected write and script-permission failures, private backup permissions before atomic publication, symlink/path-escape refusal, and detection of an overlapping custom clone. Theme switching and a fresh login on another machine are not simulated by these tests.

The public package contains user-local clones. It excludes personal shell preferences, monitor configuration, background images, font binaries and private recordings. Upstream Omarchy and third-party OmaControl source files were left untouched during development.

## Public package review

Two independent GPT-6.1 Sol council rounds reviewed the shortcut interface and distribution package. Round 2 approved publication; the four initial findings were resolved. Scores apply only to the stated scope, not the whole desktop.

| Scope | Round 1 | Round 2 |
| --- | --- | --- |
| Keyboard shortcut UI | 8.9, medium confidence | 9.7, high confidence |
| Consistency and legibility | 9.2, high confidence | 9.6, high confidence |
| Installation and recovery | 8.5, high confidence | 9.8, high confidence |
| Documentation and distribution | 9.0, high confidence | 9.6, high confidence |

The reviewer independently repeated all 13 package tests, injected permission and recovery failures in temporary homes, checked 205 byte-identical selections and seven generic searches, inspected ten current shortcut crops and the public examples, and verified all 97 payload hashes. Installation on a second real machine was not part of that review.

After round 2, a stale menu description was corrected, punctuation and wheel key names were made readable, and the shortcut footer was enlarged and brightened. An unused copy of the original menu button was also excluded, leaving 96 payload files. These small refinements were verified locally; they do not retroactively change the independent scores. Conflict refusal during uninstall is intentional: reconciling subsequent user edits remains a manual step.

## Remaining limits

- No physical 360 Hz or measured input-latency certification.
- No universal guarantee for splash screens, ambiguous classes, multiple simultaneous windows, monitor hotplug or arbitrary per-window decorations.
- The overlay follows the global active border's first/last colour stops; more complex custom gradients and application-specific decoration overrides need additional validation.
- No claim of full WCAG conformance, every external tray submenu, battery hardware coverage or login/unlock validation.
- Plugin clones need maintenance when upstream changes its interfaces.

## Public media

Comparisons use the actual stock and Nocturne QML components with identical synthetic menu/app data, a neutral generated QML background and Noto Sans. Stock uses Tokyo Night and square corners; Nocturne uses its packaged theme. The Music app is `tools/demo-window.qml`; it is a real Qt window, not a composited mock-up. The demonstration host supplies a small synthetic application library; normal installed launches use Omarchy's native AppLibrary. No private desktop recording is redistributed.
