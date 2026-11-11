# The Server Said No. I Said Yes. 4 Response Manipulation Bugs

**By 0xsila** · *The server says "no". I edit it to say "yes". The app believes me. Four times.*

---

![Money, meet me](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/115k6FZWfhCP4Y/giphy.gif)

<div style="width:100%;height:0;padding-bottom:56%;position:relative;"><iframe src="https://giphy.com/embed/YQitE4YNQNahy" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>
<p><em>Me, watching the response come back before I touch it.</em></p>

There's a moment in every session when I stop attacking the server and start attacking the *browser's trust* in the server.

I was in my favorite private program, poking at a file-sharing feature, when I caught myself thinking: "the server just told the page `failed`. What if it had said `success`?"

That one thought cost me a few hours of sleep and gave me four bugs.

---

## What is response manipulation?

Most web apps work like this:

1. The browser asks: "is this password / code / access right?"
2. The server answers: `failed` or `success`.
3. The **browser** decides what to show next.

If step 3 is the only place the decision is enforced, then the only thing between me and the content is a word in a JSON response. I run a proxy, pause the response, change one word, and forward it.

**The analogy:** a bouncer shouts "NOT ALLOWED!" to the door guard. I stand between them and swap it for "ALLOWED!". If the door guard believes whatever he hears, I'm in.

**The real bug isn't the edit.** It's that the **server never checks again** when the protected thing is actually requested. If the next step (show the file, save the email, unlock the page) works without the server remembering the check failed, the app trusted the client.

> A related idea is a **client-side only restriction**: a rule that lives only in the page, like a greyed-out button or a JavaScript check. Same root cause: the enforcement is in the wrong place.

---

## Episode 1: The password-protected share link

The collaboration hub lets you share a file by link and add a password, so even a leaked link isn't enough.

I opened the link, got the password screen, typed a wrong password, and caught the response:

```json
{"status": "failed"}
```

I changed `failed` to `success` and forwarded it. The app opened the file. I could view and download it.

No password. One word.

## Episode 2: Same wall, different door

The vendor fixed that path. Or so they thought. I went back and looked at what the page loads *before* it shows the password screen: a metadata request. Its response contained:

```json
{"passwordProtected": "true", "downloadEnabled": "false"}
```

The page asks that response whether to show the password box. I flipped `true` to `false`. Same result: password prompt gone, file open.

**Lesson:** when a fix lands, test the *neighbors*. If the first bug was "the client trusts a field", look for every other field the client trusts.

## Episode 3: "Is this feature unlocked?" (it said false)

The same hub has a manufacturing add-on that needs a separate license.

While refreshing the page I noticed a request asking "does this hub have access?":

```
POST /api/access/info
{"hubId": "<hub_id>"}
```

```json
HTTP/1.1 200 OK
{"hasAccess": false}
```

I changed `false` to `true` and forwarded it. The add-on opened with no license.

Nothing clever. Just reading every response and asking, "what happens if this boolean is the other value?"

> 🏆 **Report resolved · Bounty awarded (Oct 2025)**

![Bounty incoming](https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/y1VzYuXEAks9FJEyVQ/giphy.gif)


## Episode 4: OTP bypass (three flavors)

Verification codes are a perfect fit for this bug:

- **Change email:** I entered a victim's email, typed a random 6-digit code, and intercepted the check:

  ```
  POST /api/two-factor-auth/passcode-validate
  {"verificationCode": "111111", "contact": "<victim_email>"}
  ```

  The response said the code was wrong. I edited it to say it was right, forwarded it, and the email was accepted without me proving I owned it.
- **Phone verification during a trial signup:** I took a "verified" response from another of my accounts and pasted it over the failed one.
- **Signup on a kids' 3D-design platform:** here I didn't even need a proxy. The account worked fully without confirming the email. The check just wasn't enforced.

> 🏆 **Signup bypass: report triaged · Bounty awarded (Sep 2026)**


**Why it matters:** a verified email is a trust signal. Now someone can register with *your* address, or claim an account that isn't theirs.

---

## How I thought differently

- **Turn the proxy on and watch the yes/no requests.** Booleans, status words and flags are all candidates.
- **Ask: "if I flip this, what changes on screen?"** If the screen changes, the client was making the call.
- **Prove the server doesn't re-check.** Download the file, call the next endpoint, save the change.
- **After a fix, test sideways.** Same feature, different request.

## Impact

- Protected files viewed or downloaded without the password.
- Paid add-ons used without a license.
- Email and phone "verification" that verifies nothing.

## Fix

- Enforce the decision on the server every time the protected resource is requested.
- Don't let a flag in a response decide access.
- Tie verification to server-side state (a session that remembers "verified").

## What I took from it

- The browser is a hostile environment.
- A boolean in a response is an invitation.
- When a bug is fixed, look at the sibling request.

<div style="width:100%;height:0;padding-bottom:75%;position:relative;"><iframe src="https://giphy.com/embed/7FCFG6sYV5UxW" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>

---

*Written by 0xsila.*  
**Find me on HackerOne:** [https://hackerone.com/0xsila](https://hackerone.com/0xsila)
