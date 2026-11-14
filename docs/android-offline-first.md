# RadGestMat Android — Offline First

## Architecture
Keep Django authentication and business rules, Render API hosting and Supabase PostgreSQL as central authority. Build a standalone Android client with bundled UI, Room/SQLite, Android Keystore-backed credential protection and WorkManager for durable background sync. Never embed database credentials. First login and bootstrap require server connectivity; subsequent local access requires device/user authorization with a bounded offline authorization period. Partition local data by account and permission scope.

## Synchronisation
Store each local business mutation and its outbox entry in one transaction. Persist UUID operation IDs, entity IDs, dependencies, base revision and payload. Django must validate permissions and business invariants on every replay, atomically record unique operation receipts scoped to account/device, and return canonical entity state. Retry transient failures with backoff; retain rejected operations and show actionable conflicts. Pull changes using a server-issued cursor, including deletions and permission changes. Never silently overwrite divergent updates. Offline attributions are provisional until accepted; concurrent conflicting assignments must be rejected. Do not purge unsynced operations on restart, update or token expiry.

## Delivery
Publish signed APKs as GitHub release assets with stable versioning and checksums. Add web download link and dismissible Android prompt only when a tested release exists. Never publish signing keys. Keep production untouched until validation.

## Milestones
1. Audit existing API, authentication, models and Android artifacts.
2. Implement versioned bootstrap, push and pull endpoints with authorization and idempotency tests.
3. Build Android local database, native inventory and QR scanner; implement local outbox.
4. Add clients, attributions, returns and offline reporting as permissions allow.
5. Implement conflict UI and background synchronization; handle expired sessions and device loss.
6. Sign, test and publish APK; expose download on web.

## Acceptance
- After initial online bootstrap, airplane mode launch, inventory search, QR scan and local create/update work with no server wait.
- Pending changes survive process death, reboot and APK upgrade.
- Reconnection retries safely without duplicate assets even if a response is lost.
- Two devices editing the same revision produce a visible conflict; no double attribution.
- Server outage with working Wi-Fi does not block local UI.
- Revoked permissions and expired credentials are handled without silently losing pending data.
- No production migration or deployment until tests pass and database connectivity is restored or verified.
