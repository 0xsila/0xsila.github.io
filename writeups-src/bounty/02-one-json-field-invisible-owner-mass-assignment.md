# I Added One JSON Field and Became an Invisible Project Owner (Mass Assignment)

**By 0xsila** · *The server copied everything I sent onto its objects. So I told it who made a project (nobody), and when I wrote a comment (2001).*

---

![Me, working the proxy history again](https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/T2eBA4BaryWrLe7YfK/giphy.gif)

Every hunter has that one private program they love. Mine has a huge collaboration platform: workspaces, projects, files, comments, wiki pages. It also has an **activity feed**, the page admins check to see who did what. That's basically the audit trail.

And I have a rule: **if a feature exists to hold people accountable, I try to lie to it.**

That's how I found a bug class I now hunt on purpose: mass assignment.

---

## What is mass assignment?

**The short version:** the server takes the JSON you send and copies *every field* onto a database object, instead of only the fields it meant to accept.

**Why developers do it:** it's lazy and convenient. Instead of writing

```js
project.name = body.name;
project.avatar = body.avatar;
```

they write one line that says "copy everything the client sent":

```js
const project = new Project(body);   // vulnerable: trusts every key
project.save();
```

Frameworks make this easy (Rails `update(params)`, Mongoose `new Model(req.body)`, Spring and Laravel model binding). The dangerous version is *shorter* than the safe one, which is why it's so common.

**What goes wrong:** a Project isn't only "name" and "avatar". It also has fields the **server** is supposed to control:

| Field kind | Examples |
|---|---|
| Ownership | `owner`, `createdBy`, `userId` |
| Permissions | `role`, `isAdmin`, `canPublish` |
| Money / plan | `price`, `plan`, `premium` |
| Timestamps | `createdAt`, `published`, `modifiedTime` |
| System flags | `defaultProject`, `verified`, `deleted` |

The UI has no input for these, so developers forget they're reachable. But the server can't tell "a field the form sent" from "a field I typed myself in the proxy". It just copies.

**The analogy:** a form asks for your name and phone. You scribble "VIP: yes" in the margin. A careful clerk ignores the margin. A lazy clerk types the whole page in, margin note included.

**The fix** is an allow-list: copy *only* the named fields you expect, and set the rest on the server.

```js
project.name   = body.name;
project.avatar = body.avatar;
project.owner  = currentUser.id;   // always server-decided
```

### My hunting checklist

1. **Capture a create or update request.** Note which fields the UI sends.
2. **Read the response** (or a GET of the same object). Every field you *didn't* send is a candidate: `id`, `owner`, `created`, `published`, `role`, `defaultProject`...
3. **Add one candidate field** with a value you can recognize (a weird date, `true`, your own ID).
4. **Check the result.** Did the object change?
5. **Ask what that field controls.** The impact comes from what the field *means*.

Here's step 5 doing the work, three times.

---

## Bug #1: The invisible project creator

Normal flow: a hub member with permission clicks "New project". The project says **Created by: you**, and the activity feed logs it.

The request:

```json
{"projectName": "visible", "avatarType": "pre-defined"}
```

I noticed the app has a notion of a *default project* (the one the system makes for you). I wondered: does the server let *me* say a project is a default project? So I added one field:

```json
{"projectName": "hidden", "defaultProject": true, "avatarType": "pre-defined"}
```

The result:
- The project was created normally.
- The owner showed up like it was the **system**, not me.
- **No entry in the activity feed.**

I could rename it so it didn't look like a default project. Normal-looking, untraceable. Admins lose the ability to answer "who made this?"

## Bug #2: Time travel through comments

Comments on files are part of the design record: approvals, feedback, "yes, ship it". The timestamp matters.

The comment body had a few fields (actor, parent, text). A *saved* comment, though, came back with a `published` field I never sent. So I sent it:

```json
{"body": "hello", "published": "2001-12-10T19:19:19.410Z"}
```

The comment appeared dated 2001. Any date, past or future.

> 🏆 **Report resolved · Bounty awarded (Nov 2025)**

<div style="width:100%;height:0;padding-bottom:75%;position:relative;"><iframe src="https://giphy.com/embed/QJvwBSGaoc4eI" width="100%" height="100%" style="position:absolute" frameBorder="0" class="giphy-embed" allowFullScreen></iframe></div>

![Bounty incoming](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHNra3J6M2FoY3ljbzJ1bnY3bjl0cWFjYW1wNnJnOHpicGRjamQ1eSZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/KpuwW9A1aKNFgRYpUB/200.gif)


## Bug #3: Same trick on wiki pages

Wiki pages had the same weakness. Adding `creationTime`, `lastModified` and `modifiedTime` to the create request let me backdate or forward-date a page.

> 🏆 **Report resolved · Bounty awarded (Nov 2025)**


Three features, one root cause: **the server trusted the client's JSON.**

---

## How I thought differently

- **Read responses like a shopping list.** Extra fields in a response are things the server stores. Can I set them myself?
- **Think about the field's purpose.** Ownership, timestamps, roles and plans are things only the server should decide.
- **Add one field at a time.** Rejection tells you the allow-list; acceptance tells you the bug.
- **Go where trust lives.** Audit trails, approvals and ownership are high impact even when the technical change is tiny.

## Impact

- Admins can't trace who created a project.
- A member can create projects silently.
- Comments and wiki pages can be backdated, so "who approved what, when" can't be trusted.

## Fix

- Allow-list fields on every create and update.
- Set owner, timestamps and system flags on the server only.

## Bonus: a lesson in testing carefully

On a different app in the same program, the create request had no `id` field because the server picks the next number. When I added my own `id` with a huge value, it was accepted, and afterwards some older items couldn't be deleted because the counter had jumped.

Two lessons: client-chosen IDs are mass assignment too, and **don't repeat a destructive test on a shared system**. I stopped, wrote it up, and asked the team not to re-run my PoC.

## What I took from it

- If the response has fields you didn't send, try sending them.
- Audit-trail fields are worth forging in a report because the impact is about trust.
- Test carefully. A "harmless" extra field can break real data.

---

*Written by 0xsila.*  
**Find me on HackerOne:** [https://hackerone.com/0xsila](https://hackerone.com/0xsila)
