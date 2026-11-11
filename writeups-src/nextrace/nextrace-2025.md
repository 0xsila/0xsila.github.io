# NEXTRACE 2025: all my challenges in one writeup

**Author** : 0xsila (Money laundering with dhia)

NEXTRACE was an easy CTF, so instead of six small writeups here is one. Six web challenges, each one is about a simple idea : the client is not a security boundary, and any 403 is just a start.

---

## Rendez-Vous

> la prochaine rendez-vous est la semaine prochaine
> Cordialement

**SOLUTION :**

- inspect the page , and get the flag .

**flag :** `nexus{4lwaYS_1n5p3Ct_surpr1s3_M3}`

---

## Inspect V2

> Hey Agent,
> you solved the first version of Inspect quite easily.
> can you handle this new and improved version ?

**SOLUTION :**

- inspect the page .
- remove the big image by removing src for the image tag , or just removing all the tag .
- we see a disabled button , enable it .
- click the button and get the flag .

**flag :** `nexus{1n5p3ct_c4n_d000_4_l0t_0f_th1ng55555}`

---

## Passw0rd

> oh , i forgot my password ......
> lets see what we will get in the response ....
> maybe changing something will let us break the logic .....

**SOLUTION :**

- enter any random password .
- click enter , with proxy open in burp .
- intercept the response of the request that checks the password .
- change `false` => `true` .
- and bom get the flag .

**flag :** `nexus{R3sp0ns3_M4n1pul4Ti0n_is_P0werFull}`

---

## Headers

> the language of servers is headers , do u know how to speak it ?
> can u be the admin ?

**SOLUTION :**

Intercept the requests => see a header that says admin false `X-Admin:false` => change it to true : `X-Admin:true` => u can not see the flag in the UI , but u can see it in the response .

**flag :** `nexus{1_h34d3r_m4k3_u_4n_4dm1111111111n}`

---

## HPP

> pollution is a big problem in the world ....
> can it reach the HTTP ?
> can u read the secret book and get the flag ?

**SOLUTION :**

HPP : HTTP Parameter Pollution , is a really good idea to bypass restrictions , specially in IDOR bugs .

```
?id=1       => 403 Forbidden
?id=3       => 200 OK
?id=2&id=1  => bom get the flag
```

**flag :** `nexus{HTTP_p4r4m3t3r_p0lut10n_b000000000000m}`

---

## Money laundering

> i have a lot of cash , i need to clear it
> can u help me ?

**SOLUTION :**

- the word cash was a hint about cache ( CDN cache ) , websites use caching servers to help their servers and make the UX better , by caching responses of requests based on a key , expecting that the user will request them a lot of times .
- `PURGE` is the method used to clear the cache , this method is supposed to be protected and forbidden to normal users .
- try using the method , and yes we get a 403 Forbidden .
- but thinking like a hacker , any 403 we will try to bypass it .
- after a small vibe hacking or googling , we find that there are a lot of methods to bypass that .
- one of them is using the header : `X-HTTP-Method-Override`
- this header is accepted by a lot of proxy servers , it overrides the request method and uses its value .
- so the proxy checks the request method , sees that it is a GET request , so it is ok , but forgets to check the headers .

final exploit : add the header

```
X-HTTP-Method-Override: PURGE
```

**flag :** `nexus{D0nt_l3tt_th3m_cl34n_ur_C4Ch3}`

---

Source of all the challenges : [nexus-nextrace-2025-challenges](https://github.com/0xsila/nexus-nextrace-2025-challenges)
