# NEXTRACE 2025: six web challenges, one writeup

**Author: 0xsila** (Money laundering co-written with dhia)

NEXTRACE was the entry-level round of the Nexus Security Club CTF. I wrote six web challenges for it, and none of them needs more than a browser, DevTools and Burp Suite. The goal was to teach one idea per challenge: **the client is not a security boundary**, and every `403` is a hint, not a wall.

| Challenge | Idea | Trick |
|---|---|---|
| Rendez-Vous | DevTools | Read the page source |
| Inspect V2 | DevTools | Remove an overlay, enable a disabled button |
| Passw0rd | Response manipulation | Flip `false` to `true` in the response |
| Headers | Broken access control | Change `X-Admin: false` to `true` |
| HPP | HTTP parameter pollution | `?id=2&id=1` |
| Money laundering | Web cache + method override | `X-HTTP-Method-Override: PURGE` |

---

## Rendez-Vous

> "la prochaine rendez-vous est la semaine prochaine. Cordialement"

**Solution.** Inspect the page and the flag is there. It is the shortest challenge on purpose: always look at the source before reaching for tools.

`nexus{4lwaYS_1n5p3Ct_surpr1s3_M3}`

---

## Inspect V2

> "Hey Agent, you solved the first version of Inspect quite easily. Can you handle this new and improved version?"

**Solution.**

1. Open DevTools and inspect the page.
2. Remove the big image (delete its `src`, or delete the whole tag) so it stops covering the page.
3. Behind it sits a **disabled** button. Remove the `disabled` attribute.
4. Click it and the flag appears.

`nexus{1n5p3ct_c4n_d000_4_l0t_0f_th1ng55555}`

---

## Passw0rd

> "oh, I forgot my password... let's see what we will get in the response... maybe changing something will let us break the logic."

**Solution.**

1. Enter any random password with Burp's proxy on.
2. Intercept the **response** of the request that checks the password.
3. Change `false` to `true`.
4. The frontend believes it and shows the flag.

**Lesson.** If the browser decides whether you are authenticated from a value in the response, you can decide it for the browser.

`nexus{R3sp0ns3_M4n1pul4Ti0n_is_P0werFull}`

---

## Headers

> "The language of servers is headers, do you know how to speak it? Can you be the admin?"

**Solution.**

1. Intercept the requests. One of them carries `X-Admin: false`.
2. Change it to `X-Admin: true`.
3. The UI still shows nothing, but the flag is in the **response**.

**Lesson.** Never trust a header the client can set, and check the raw response, not only what the page renders.

`nexus{1_h34d3r_m4k3_u_4n_4dm1111111111n}`

---

## HPP

> "Pollution is a big problem in the world... can it reach HTTP? Can you read the secret book and get the flag?"

**Solution.** HTTP Parameter Pollution is a good way around restrictions, especially on IDOR bugs.

```
GET /book?id=1       ->  403 Forbidden
GET /book?id=3       ->  200 OK
GET /book?id=2&id=1  ->  flag
```

The access check and the data lookup read the duplicated parameter differently, so the check sees an allowed id while the lookup returns book 1.

`nexus{HTTP_p4r4m3t3r_p0lut10n_b000000000000m}`

---

## Money laundering

> "I have a lot of cash, I need to clear it. Can you help me?"

**Solution.**

1. "Cash" is a pun on **cache**. The target sits behind a caching layer, like most CDNs. Responses are stored under a key so repeat requests are cheap.
2. The method used to clear a cache is `PURGE`, and it should be forbidden to normal users.
3. Try it: `403 Forbidden`.
4. Any `403` is worth trying to bypass. A bit of research turns up method-override headers, which many proxies and frameworks accept.
5. The proxy checks the method of the request, sees a harmless `GET` and lets it through. It forgets that a header can change the method again further down.

Final exploit: send a normal `GET /` with this header added.

```
X-HTTP-Method-Override: PURGE
```

**Lesson.** Apply access control after method overrides are resolved, or do not accept override headers at all.

`nexus{D0nt_l3tt_th3m_cl34n_ur_C4Ch3}`

---

Source code and Docker files for every challenge: [nexus-nextrace-2025-challenges](https://github.com/0xsila/nexus-nextrace-2025-challenges).
