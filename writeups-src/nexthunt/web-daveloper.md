# Challenge Write-Up: web daveloper

## Challenge Name
**web daveloper**

## Challenge Description
i am just a web daveloper, using copilot and chatgbt to create challenges :(
i dont know where is flag.txt , can u find it for me !!!
NOTE: brute forcing is not allowed, you'll be blocked immediatly.

This challenge demonstrates how **HTTP method confusion and overrides** can be abused to bypass access controls in WebDAV-enabled applications.

---

## Vulnerability Chain

**WebDAV Exposure → PROPFIND Enumeration → Method Restriction → Header Bypass (`X-Original-URL`) → Flag Access**

---

## Challenge Overview
The goal of **webdav** is to bypass HTTP method restrictions on a WebDAV-enabled endpoint by abusing the **`X-HTTP-Method-Override`** header, allowing the attacker to perform unauthorized actions such as using **PROPFIND** method , to list directories and find the path of the flag , try to get the flag , get a 403 forbidden , but believing that we r right in the previous steps , so we have to bypass that , small googling or vibe hacking give us some methods .
---

## Steps :

The application exposes a WebDAV endpoint, but it appears to be restricted.

Basic enumeration shows that:
- `GET` requests are allowed
- `OPTIONS` show us that only get is allowed , but we some headers that related to webdav .

This gives the illusion of a secure configuration.

search and search , asking ur favorite ai agent , and u will start be familiar with webdav .

being 100% that u should use **PROPFIND** method to list directories and get the flag , but bom the method is not allowed .

bypass bypass bypass , that what u should think about , i remember that i learned this idea from the legend ebrahim hegazy , a big kudos for him .

the idea is using the header : **`X-HTTP-Method-Override`** .

use the header , use the method , and what we get , just some random xml data about the server .

asking again ur ai agent frendo , he will tell u that u missed another header hhhh , this time a WebDAV header : **Depth: 1**

use all what we have , we can enumerate the path of the flag :

the flag is at /vault/flag.txt

being happy and try to get the flag , another forbidden hhhhhhhhh

trying harder , and harder , and finally find that we can bypass that using another header : `X-Original-URL`

mixing all that steps , will give u the flag :

final exploit :

```bash
curl -H "X-Original-URL: /vault/flag.txt" http://ctf.nexus-security.club:3555/blablabla
```


**Flag:** `nexus{w3bd4v_wchw3y4_h3d34rs_ezzzzzzzzz}`
