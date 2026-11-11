# Challenge Write-Up: 1xbet

## Challenge Name
**1xbet**

## Challenge Description

this machine eat all my money and still didnt win , can u beat it ?

---

## Vulnerability Chain

**Mass Assignment → Content-Type Confusion → Inconsistent Backend Validation → Response Manipulation → Business Logic Abuse → Flag Access**

---

## Challenge Overview
## Challenge Overview

The goal of **1xbet** is to turn a normal bet into a **winning bet** without proper authorization.

Key characteristics of the application:

- Bets are normally submitted using a classic form-encoded request
- The backend also accepts JSON input
- Internal bet objects contain a hidden property: `isWinner`
- The frontend relies entirely on HTTP status codes to decide whether to continue the bet validation flow

Even when the backend rejects malformed requests with a `400 Bad Request`, part of the internal state is already modified.
---

## Steps :

- afetr signup and login , we see a casion machine that eating our money , and u will never win and get the flag if u playes stright .

- intercept the request of bet , and start analyse the request and response , and start thinkig how i will win .

- a normal bet always respond with : {"result":"loss","bet":{"isWinner":false,"payout":0}...}
- interesting right ? , how can i now changing false to true .
- the first thing trying a normal response manipulation , but nothing really change .
- another idea is mass assigment , trying that with json body : 

`"curl -X POST http://ctf.nexus-security.club:4999/api/bet -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"amount":100,"isWinner":true}'`"

- we see in the reponse that we got : "isWinner":true
- but it reponse with 400 bad request , and see my wining return nothing .
- the main idea was doing the same steps , but intercept the resposne and changing the status code from 400 bad request to 200 ok , a lot of websites take actions corresponding with the status code of teh response .

- another unintende solution was reading js files and get the endpoint of validation , and send it with the bet id , and wiiiiiiiiiin .

- check my winnings : `curl http://ctf.nexus-security.club:4999/api/winnings \-H "Authorization: Bearer $TOKEN"`

- and bom get the flag .
- **Flag** :
nexus{lkm4r_7r4m_kh4wty_d1d1c4s_ysf_hhhhhhhh}



