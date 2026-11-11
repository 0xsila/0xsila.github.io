# Challenge Write-Up: Dz-Kitab

## Challenge Name
**Dz-Kitab**

## Challenge Description
i have an amazing team for my first semester project
one girl used cursor i think to help us
Tip : choose ur team carfully

This challenge demonstrates how IDOR can be exploited by chaining FAT GET with HTTP Parameter Pollution (HPP) to bypass access controls and retrieve unauthorized resources.

---

## Vulnerability Chain

**IDOR → FAT GET (GET with Body) → HTTP Parameter Pollution (HPP) → Authorization Bypass → Flag Access**

---

## Challenge Overview
The goal of Dz-Kitab is to access a restricted book resource that should only be available to authorized users.

The application uses a weak authorization check combined with inconsistent parameter handling:

Parameters are read from both the URL query string and the request body

When duplicated parameters exist, the backend applies unexpected precedence rules

By abusing FAT GET (sending a request body with a GET request) together with HPP, an attacker can confuse the backend and bypass the ID-based access control.
---

## Steps :

1. Initial Enumeration

The application exposes an endpoint similar to:

```
GET /book?id=2
```

Behavior observed:

id=1 → Forbidden (contains the flag)

id=2 → Allowed (public book)

This indicates a classic IDOR scenario protected by a simple ID check.

2. Discovering FAT GET Behavior

During testing with Burp, we notice something interesting:

The server accepts a request body on GET requests

Parameters sent in the body are parsed normally

Example:

```http
GET /book?id=2 HTTP/1.1
Content-Type: application/x-www-form-urlencoded

id=1
```

This is known as a FAT GET.

3. HTTP Parameter Pollution (HPP)

Now we have two id parameters:

id=2 in the URL

id=1 in the body

This creates HTTP Parameter Pollution.

The key vulnerability:

Authorization logic uses the URL parameter (id=2)

Data-fetching logic uses the body parameter (id=1)

So the server checks:

“User is allowed to access book 2 ✅”

But then returns:

“Here is the content of book 1 ❌”

4. Bypassing Access Control

By combining FAT GET + HPP, we fully bypass the restriction.

Final exploit request:

```bash
curl -X GET "http://ctf.nexus-security.club:3555/book?id=2" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "id=1"
```
5. Flag Retrieval

The server responds with Book #1, which contains the flag:

**Flag:** `nexus{f4t_g3t++http_p4r4m3t3r_p0lut10n}`

## some unintended solution : 

- Check the author note: the challenge doesn't require brute forcing => what you see (endpoints) is what you should attack
- Send a request to / and check X-Powered-By header => you know it's express
- Send a request to /book?id=2 => book arrives, use id=1 and book doesn't => you know you need to   access book with id 1
- Since you're dealing with express and query strings, you look up how query strings are handled there => find qs and think of how to bypass the assumed condition

Working payload

```
/book?id[0]=2&id[1][]=1
```

the unintended solution is from : hxuu , didicas
