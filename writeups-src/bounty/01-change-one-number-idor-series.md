# Change One Number, Own Someone Else's Data: My IDOR Series

**By 0xsila** · *One bug class, four different spots, one habit: change the ID and see what happens.*

---

![Start of the night: me, my PC, and a long proxy history](https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/s4mD4r31YBusOmwRCe/200.gif)

<div style="width:100%;height:0;padding-bottom:75%;position:relative;"><iframe src="https://giphy.com/embed/qvzhHvXY6HxoG9jkp2" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>
<p><em>Me, staring at a response field that definitely shouldn't be public.</em></p>

It was one of those late nights where the coffee is cold and the proxy history is long. I was deep in my favorite private program, the one I keep coming back to because every new feature feels like a fresh playground.

I didn't have a grand plan. I just had one question I ask on every target:

> "When I click a button, which request fires, and what ID is in it?"

That question gave me four bugs. Let me walk you through them.

---

## First, what is an IDOR?

**IDOR = Insecure Direct Object Reference.** Fancy name, simple idea: the app identifies a thing (a profile, a plan, a comment) by an ID you can see and change, and it never asks *"does this thing belong to you?"*

In code, the bug looks like this:

```js
// vulnerable: checks you're logged in, but not that the plan is yours
app.delete("/plans/:id", requireLogin, (req, res) => {
  db.plans.delete(req.params.id);
});
```

The safe version adds one condition:

```js
db.plans.delete({ id: req.params.id, owner: currentUser.id });
```

That tiny `owner` check is the whole difference between secure and "anyone can delete anything".

**The hotel analogy:** your key card opens room 214 because the door reads the number on it. An IDOR is a hotel where you can type *any* room number and the door opens, because the lock asks "is this a valid room?" and not "is this *your* room?"

I ask two questions every time:
1. **Can I find other people's IDs?** (public profiles, lists, share links, error messages)
2. **Does the server check ownership when I use one?**

Both answers "yes / no"? That's an IDOR.

---

## Episode 1: "I'd like to edit someone else's profile, please"

The account page lets you edit your name, bio, company, job title, address, website, even your language and email preferences. Each save sends a request with an `id` in the body.

```json
{"input": {"id": "<user_id>", "name": "New Name"}}
```

The ID looked random, so I almost moved on. Then I asked the better question: **where else does this ID show up?**

I opened a random user's public forum profile with my proxy on. And there it was, the same ID, sitting in a response field. Public to everyone.

So the chain was:
1. Grab a victim's ID from their public profile.
2. Swap it into my own "save name" request.
3. The server says "sure!" and renames them.

It checked that I was logged in. It never checked that the ID was *mine*.

> **Why random IDs don't save you:** this is the difference between *sequential* IDs (`1001, 1002, ...`, trivial to guess) and *unpredictable* ones (long random strings). Unpredictable IDs make step 1 harder. They don't fix step 2. If the ID leaks anywhere, the bug is back.

**My mistake:** I submitted each field as its own report. Nine fields, one root cause. If you find this pattern, send **one** report ("any user's profile can be edited") and list the fields inside. Triagers love root causes.

---

## Episode 2: The planning tool with numbered plans

Next stop: a small planning/assessment tool in the same program. Here the IDs weren't hidden at all. Plans were numbered `21653`, `21654`, `21655`... like tickets at a deli counter.

```json
{"operationName": "DeletePlan", "variables": {"id": "21653"}}
```

I created a plan, deleted it from the UI, caught the request, and subtracted one from the number. Somebody else's plan vanished.

Then I got greedy (in a good way). Every button on the plan card is another request with the same shape: edit, rename, archive, unarchive, share, edit notes, cancel a transfer. All of them took an ID, none checked the owner. One even leaked the **email address** a plan was being transferred to.

**How I thought differently:** I stopped testing "delete" and asked *"what are all the verbs on this object?"* Clicking every button with my proxy on handed me the whole attack surface.

---

## Episode 3: Deleting other people's comments

Back in the collaboration hub. Files can have comments. The comment list returns every comment ID, and the delete request puts the comment ID in the URL.

```
DELETE /api/files/<file_id>/comments/<comment_id>
```

1. As the attacker, open a file in a shared project and read the comment IDs.
2. Delete one of my own comments and capture the request.
3. Swap in the victim's comment ID.
4. Gone.

**Mindset:** if the app *shows* me an ID in one request, I immediately try to *use* it in another. **List → action** is the most reliable IDOR pattern there is.

> 🏆 **Report resolved · Bounty awarded (Sep 2025)**

<div style="width:100%;height:0;padding-bottom:75%;position:relative;"><iframe src="https://giphy.com/embed/67ThRZlYBvibtdF9JH" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>

![Bounty incoming](https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/xmNLriacxN1AMzhFnn/giphy.gif)


---

## Episode 4: The empty `hubId` trick

This is my favorite, because it felt like a magic trick.

A GraphQL mutation creates a new version of a file with a description. The request had a `hubId` field, "which workspace is this in?", which the server used to check my access. With my own hub ID against someone else's file, the server correctly said no.

Then I tried something silly: **keep the field, delete the value.**

```json
{"hubId": "", "targetId": "<victim_file>", "description": "changed by me"}
```

The check was probably written as "if a hub ID is present, verify it". An empty string skipped the check and the write went through.

> 🏆 **Report resolved · Bounty awarded (Nov 2025)**


> **The lesson:** when a check blocks you, don't only try different values. Try the *absence* of the value: empty string, `null`, a missing key, an array instead of a string. Validators are written for the happy path.

---

## Impact

- Strangers could edit other users' profiles, delete or alter their plans, and delete their comments.
- Private data (a transfer email) leaked through the same pattern.

## Fix

- Check ownership on the server for **every** object access: `WHERE id = ? AND owner = ?`.
- Treat empty and missing values as *invalid*, never as "skip the check".

## What I took from it

- Find the ID, then find where it leaks.
- Test **every action** on an object, not just the first one.
- When a check blocks you, try blank, null, or missing.
- One root cause, one report.

---

*Written by 0xsila.*  
**Find me on HackerOne:** [https://hackerone.com/0xsila](https://hackerone.com/0xsila)
