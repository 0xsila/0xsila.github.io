# Codemy - stealing an admin session through a chained cache-poisoning bug

**Author** : 0xsila

## Summary

Codemy is a small course platform. A support feature lets any signed-in
or anonymous visitor report a broken page to staff; a staff member (in
this build, an automated bot standing in for one) opens whatever link is
reported. Chaining three independent, individually low-impact issues lets
an unauthenticated attacker steal that staff member's session and recover
the flag:

1. A reflected injection point that, on its own, only ever fires against
   the person who constructs the malicious URL themselves ("self-XSS").
2. A path-parsing disagreement between the caching layer in front of the
   app and the app itself, which lets that injection be stored under the
   URL of a completely unrelated, otherwise-safe page.
3. A race condition in a request validator sitting in front of the cache,
   which is meant to block exactly this kind of payload but can be
   bypassed by sending two requests at once.

None of these three is exploitable alone. Together, they let an attacker
plant persistent script on a link a real user would never think twice
about clicking, and have that script fire in an authenticated staff
member's browser.

## Architecture

```
 attacker/victim
        |
        v
  proxy (:47002)  <-- caches responses, has a request validator ("WAF")
        |
        v
  origin (:47001) <-- the actual app: accounts, certificates, report queue
```

The proxy is a reverse cache sitting in front of the app. It exists to
avoid re-rendering certificate pages on every request. The origin is the
actual Express application.

## Stage 1 - the injection point

Codemy has a small personalization feature: `/preferences?nickname=...`
sets a `nickname` cookie. It's echoed back as a "Welcome back, ..."
greeting - including on the site's generic browse/landing fallback (any
path that doesn't match a defined route), which reflects it with no
escaping:

```js
app.use((req, res) => {
  res.status(200);
  const nickname = req.cookies.nickname;
  res.send(`... ${nickname ? `<p>Welcome back, ${nickname}.</p>` : ''} ...`);
});
```

Set your own `nickname` cookie to `<img src=x onerror=alert(1)>` via
`/preferences?nickname=...` and any page that falls through to this
handler pops the alert. On its own this is barely interesting: **a URL
cannot set someone else's cookies**, so there's no way to deliver this to
another person by just sending them a link - whoever clicks it sees
their own (empty) `nickname` state, not yours. This is what makes it
"self," and it's why anchoring the payload in cookie state (rather than
the URL) matters: a version of this bug reflecting something present in
the URL itself would let an attacker just report a link with the payload
baked in directly, skipping the rest of the chain entirely.

## Stage 2 - turning it persistent (CSPT / cache-key confusion)

The proxy caches certificate pages by looking only at the first two raw
path segments (`/certificate/<id>`) and ignoring everything after -
a realistic canonicalization rule (real CDNs commonly key on a URL prefix
this way, to avoid cache fragmentation from tracking params or trailing
junk). It does **not** resolve dot-segments itself:

```js
const segments = rawPathname.split('/').filter(Boolean);
const cacheable = segments[0] === 'certificate' && /^\d+$/.test(segments[1]);
const cacheKey = `/certificate/${segments[1]}`;
```

The origin, on the other hand, *does* resolve dot-segments before
routing (a normalization middleware, matching how many real backends or
reverse proxies in front of an app behave). So the raw request

```
GET /certificate/1/../../badges HTTP/1.1
Cookie: nickname=<img src=x onerror="...">
```

is interpreted completely differently by each layer:

- The **proxy** looks at the first two raw segments - `certificate`,
  `1` - decides it's cacheable, and uses `/certificate/1` as the key.
- The **origin** resolves the dot-segments itself: `1/../../badges`
  cancels back to just `/badges`, and routes to the real badges page,
  which reflects the attacker's `nickname` cookie.

The proxy caches *that* (badges) response under the key `/certificate/1`.
From then on, anyone requesting the plain, ordinary `/certificate/1` -
the actual certificate page - gets served the badges page's poisoned
content instead.

## Stage 3 - getting the payload past the WAF (race condition)

A validator sits in front of the cache and blocks anything matching a
broad signature list covering common injection tags, event handlers,
and known exfiltration primitives (`fetch(`, `document.cookie`,
`XMLHttpRequest`, `sendBeacon`, `new Image(`, etc.), plus directory
traversal and a few other injection classes for good measure. This is
deliberately broad - checking only a handful of specific tags (`<img`,
`<script`) would let an attacker trivially swap to an untested
tag/handler combination (`<body onload=...>`) and skip the race
entirely. Sent alone, the crafted request from Stage 2 gets a `400`
regardless of which tag or exfil method is used.

The validator's bug is unrelated to the blocklist's contents - it's in
how the check is implemented:

```js
let sharedValidationTarget = null; // shared across ALL requests

async function isBlockedByWaf(rawUrl, decodedPath, cookieHeader) {
  const combined = `${rawUrl} ${decodedPath} ${cookieHeader || ''}`;
  sharedValidationTarget = combined;      // (1) stash
  await sleep(150);                        // (2) simulated slow lookup
  const target = sharedValidationTarget;  // (3) read back
  return matchesBlocklist(target);
}
```

The content being checked is held in a single variable shared by every
in-flight request instead of a value scoped to that request. If a second,
benign request arrives while the first is still "asleep" in step (2), it
overwrites the shared variable. When the first request wakes up and reads
it back in step (3), it reads the second request's clean content - and
gets validated against something it never sent. This is independent of
how strict or broad the blocklist itself is - broadening the blocklist
closes bypasses that don't need the race, but does nothing to fix the
race itself, since the bug is in the check's plumbing, not its rules.

Firing the malicious request and a benign one (e.g. `/certificate/2`)
concurrently, with the malicious one issued first, wins the race: the
malicious request's own check ends up reading the benign request's clean
content and passes.

## Stage 4 - handing it to the admin

Codemy has a "report a problem" form (`POST /report`) that queues a URL
for staff review. An admin bot polls this queue, logs in as admin
(establishing a real, non-`httpOnly` session cookie), then navigates to
whatever was reported. Since `/certificate/1` is now poisoned, the bot's
browser renders the injected `<img onerror=...>`, which fires inside the
bot's own authenticated session and exfiltrates `document.cookie` to the
attacker's collector.

In this build the admin's session cookie value **is** the flag, so
capturing it is equivalent to solving the challenge; in a real
application it would be a session token usable to directly hijack the
admin account.

## Full exploit sequence

```bash
# 0. sanity: solo malicious request is blocked
node race.js --solo            # -> 400

# 1. win the race, land the poisoned response in the cache
node race.js                   # retries until the WAF is bypassed

# 2. confirm the clean-looking URL now serves the payload
node attack.js --check         # -> x-cache: HIT, payload in body

# 3. report the poisoned (but ordinary-looking) URL to staff
node report.js "http://localhost:47002/certificate/1"

# 4. the bot (running separately, see README) visits it, executes the
#    payload, and the collector logs the stolen session/flag
```

### Automation

`solve.py` drives the four steps above in order, as a single command:

```bash
python3 solve.py [--target-url http://localhost:47002/certificate/1]
```

It just shells out to `node race.js --solo`, `node race.js`,
`node attack.js --check` and `node report.js <url>` in sequence and stops
on the first failure, so the whole chain above can be kicked off and
re-run without doing each step by hand.

## Root causes and fixes

| Stage | Root cause | Fix |
|---|---|---|
| 1 | User input reflected without HTML-encoding | Encode all reflected output; never build HTML by string interpolation |
| 2 | Cache computes its key from a different, more-normalized view of the path than the origin uses for routing | Cache and origin must agree on one canonical parsing of the path - ideally the cache rewrites the request line it forwards, not just its own bookkeeping key |
| 3 | Request-scoped state stored in a variable shared across concurrent requests | Never hold per-request data in module/global scope across an `await`; use a local variable or something explicitly keyed per-request |
| 4 | Session cookie not `httpOnly` | Set `httpOnly` on any cookie that doesn't need JS access - this alone would have stopped the exfiltration even with the XSS intact |

Any one of these fixes independently breaks the whole chain.
