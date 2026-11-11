# The Free Trial That Never Ended: Business Logic Bugs That Print Money

**By 0xsila** · *Nothing is "hacked". The app just forgets its own rules, and the rules are where the money lives.*

---

![Delivery of bugs, coming right up](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/6pxAvNS8QwlyLYDvs1/giphy.gif)

<div style="width:100%;height:0;padding-bottom:100%;position:relative;"><iframe src="https://giphy.com/embed/8qpz12HY0GXHaKPxTn" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>
<p><em>Session start: let's see what this trial "limit" is really made of.</em></p>

My favorite private program sells paid features on top of a free trial. Which means somewhere in that product there's a very long list of rules:

- "This module is for paying customers only."
- "This plan allows 15 users."
- "One account, one workspace."

Every one of those is a promise. My favorite game is finding which promises are only *painted on the front door*.

---

## What is a business logic bug?

Most bugs are about *code* doing something it shouldn't (injecting a script, reading a file). A **business logic bug** is about the *rules of the product* not being enforced. The code works exactly as written, but the rule was only ever written in the front end, or never written at all.

**Where a rule can live:**

| Layer | Can I bypass it? |
|---|---|
| Hidden or greyed-out button | Yes, I never have to click it. |
| JavaScript check in the page | Yes, I can send the request myself. |
| API / server check | No. This is where the rule has to be. |

**The restaurant analogy:** the menu says "no dessert with the kids' meal", but the kitchen will cook one if you shout the order through the pass. The menu is the UI. The kitchen is the API.

**How I hunt:** keep two accounts, one that's *allowed* and one that *isn't* (expired trial, low role, free plan). Capture a request from the allowed account and replay it with the other account's token. If it works, the rule never lived on the server.

---

## Episode 1: The trial that doesn't end

The platform has several modules: quantity estimation, issue tracking, documents, collaboration, spec tools, and more. Each is unlocked by a license or a 30-day trial.

When my trial ended, the modules went dark in the UI. Great. But the page is only a client. The real work happens in API calls.

So I tried this:
1. Using a **fresh account** (trial still active), I used a module and captured a request, say "create a report":

   ```
   POST /api/projects/<project_id>/reports
   Authorization: Bearer <fresh_account_jwt>

   {"title": "Issue detail", "format": "pdf"}
   ```

2. I went to the **expired account**, took its auth token and its project ID, and dropped them into the same request.
3. `201 Created`.

The restriction lived only in the front end. The backend never asked, "does this account still have a license?"

I repeated it module by module: same bug, different feature. That's the joy of business logic bugs: once you find the pattern, you sweep the product. Later I found the same weakness on a GraphQL API where premium operations didn't check the entitlement at all.

> 🏆 **GraphQL variant: report triaged · Bounty awarded (Nov 2025)**

![Bounty incoming](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/PkdghjCPWrbsCBrHh7/giphy.gif)


**How I thought about it:** I didn't test "can I do X?" I tested **"is the gate in the UI or on the server?"** Replaying a valid request with an invalid account answers that cleanly.

## Episode 2: The toggle that said "not on your plan"

A hub admin screen had a setting for a premium calculation feature. For non-paying hubs, the toggle was disabled with a message saying it needs a paid plan.

But settings are saved through a request that carries the *whole preferences object*. I changed something unrelated (a file-sharing option), intercepted the save, and saw this in the body:

```json
{"shareFileAllowed": true, "premiumFeatureEnabled": "false"}
```

I changed `false` to `true` and sent it. The feature turned on. The UI had hidden the toggle, but the endpoint never checked the plan.

> 🏆 **Report triaged · Bounty awarded (Nov 2026)**


**Lesson:** a disabled form control isn't a security control. Read the **whole** body of a save request. Fields the UI doesn't let you change are often still accepted.

## Episode 3: The member cap that didn't hold

A free-tier hub has a member cap. The rule existed in the code, but it didn't survive when I tested it with several requests at the same moment. A rule that exists isn't the same as a rule that holds up.

> 🏆 **Report resolved · Bounty awarded (Sep 2025)**


## Episode 4: One account, many workspaces

Each account was supposed to own one hub. Sending several "create hub" requests at the same time left one account with several. Odd detail: they didn't show up right away. They became accessible about two hours later.

I couldn't explain why, but it happened twice. I said so in the report instead of pretending I understood. Honest reports beat confident wrong ones.

---

## My business-logic routine

1. **List the rules:** limits, roles, plans, one-per-account, expiry dates.
2. **For each rule, ask where it's enforced.** UI only? API? Database?
3. **Break it three ways:** skip it (call the API directly), repeat it (send it twice), or send it at the same time.
4. **Use two accounts.** One valid, one expired or limited. Replay between them.
5. **Write the impact as money or trust.** "Paid feature for free" is something any business understands.

## Impact

- Paid features available forever, for free.
- Plan limits that mean nothing, so the licensing model breaks.

## Fix

- Check entitlements on **every** API call, on the server.
- Don't rely on hidden buttons.
- Make limit checks safe against simultaneous requests.

## What I took from it

- The UI is a polite suggestion. The API is the rule.
- Replay a request from a good account with a bad account's token.
- If it works on one module, test them all.
- Say "I don't know why" when you don't.

<div style="width:100%;height:0;padding-bottom:56%;position:relative;"><iframe src="https://giphy.com/embed/xT5LMRgWdqopR1Ar04" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>

---

*Written by 0xsila.*  
**Find me on HackerOne:** [https://hackerone.com/0xsila](https://hackerone.com/0xsila)
