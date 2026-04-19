# Broken Access Control - View Another User's Basket - OWASP Juice Shop

**Target:** OWASP Juice Shop `http://192.168.178.80:3000`  
**Vulnerability:** Insecure Direct Object Reference (IDOR) / Broken Access Control (CWE-639)  
**Severity:** High  
**Date:** 2026-04-13  
**Author:** sebarino5

---

## Overview

OWASP Juice Shop exposes a REST endpoint to retrieve a user's shopping basket at `/rest/basket/:id`. The endpoint authenticates the caller via a JWT but does not verify that the requested basket actually belongs to the authenticated user. By changing the numeric basket ID in the URL, any logged-in user can read any other user's basket contents. This is a textbook Insecure Direct Object Reference (IDOR).

---

## Reconnaissance

After registering and logging in with a low-privilege account (`123@123.com`), the application issues a JWT and associates the user with a basket ID. Adding an item to the cart and inspecting the traffic in Burp Suite reveals that the basket is fetched via:

```
GET /rest/basket/<ID> HTTP/1.1
Authorization: Bearer <JWT>
```

The basket ID is a small incrementing integer visible directly in the URL path, with no hash, no UUID, and no server-side ownership check surfaced to the client. This pattern is the classic IDOR smell: client-supplied object references + no authorization check = broken access control.

---

## Vulnerability Analysis

The backend handler for `/rest/basket/:id` appears to perform the following logic:

```javascript
// Pseudocode of the vulnerable handler
app.get('/rest/basket/:id', authenticate, (req, res) => {
  const basket = db.Basket.findByPk(req.params.id);
  return res.json(basket);
});
```

The `authenticate` middleware only verifies that the JWT is valid, it does **not** compare `basket.userId` against `req.user.id`. As a result, the caller's identity is checked but their authorization to access *this specific basket* is not.

**Attack primitive:** decrement or increment the basket ID in the URL to read baskets belonging to other users.

---

## Exploitation

### Step 1: Authenticate as a normal user

Register a throwaway account (`123@123.com`) and log in. The JWT returned by the server is automatically attached to subsequent REST requests by the frontend.

---

### Step 2: Intercept the basket request

Browse to the shopping cart so the frontend calls `/rest/basket/<own-id>`. Intercept the request in Burp Suite and change the numeric ID in the path to the ID of another user's basket (e.g. `6`):

```http
GET /rest/basket/6 HTTP/1.1
Host: 192.168.178.80:3000
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOi...
Accept: application/json
```

![Burp Request - Basket IDOR](images/01_burp_basket_idor.png)

The server responds with the full basket contents for user 6 despite the request being authenticated as a completely different user.

---

### Step 3: Challenge solved

Forwarding the tampered request triggers the Juice Shop challenge *"View Basket - View another user's shopping basket."*:

![Challenge Solved Banner](images/02_challenge_solved.png)

The success banner confirms that the attacker account successfully accessed another user's basket with no additional credentials.

---

## Impact

| Risk | Description |
|------|-------------|
| Horizontal Privilege Escalation | Any authenticated user can read any other user's basket |
| Data Exposure | Product selections, quantities, and pricing of other customers leak |
| Predictable IDs | Sequential integer IDs make full-database enumeration trivial |
| Enumeration Primitive | Attacker can iterate IDs `1..N` to map every user's cart contents |
| Compound Risk | If write endpoints share the same flaw, baskets of other users could also be modified or emptied |

Because the object references are small integers, a single loop over `1..N` can dump every basket in the system, turning a single-request bug into a mass data disclosure.

---

## Mitigation

### 1. Server-Side Ownership Check (Primary Fix)

Verify that the requested object belongs to the caller before returning it:

```javascript
app.get('/rest/basket/:id', authenticate, async (req, res) => {
  const basket = await db.Basket.findByPk(req.params.id);
  if (!basket || basket.userId !== req.user.id) {
    return res.status(403).send('Forbidden');
  }
  return res.json(basket);
});
```

### 2. Derive the Object from the Session, Not the URL

The basket is a per-user resource, so the ID does not need to be in the URL at all:

```javascript
app.get('/rest/basket', authenticate, async (req, res) => {
  const basket = await db.Basket.findOne({ where: { userId: req.user.id } });
  return res.json(basket);
});
```

Removing the client-controlled identifier eliminates the IDOR entirely.

### 3. Use Unpredictable Identifiers

Where object IDs must be exposed, use UUIDs or signed tokens instead of sequential integers. This does not *fix* missing authorization, but it raises the cost of enumeration significantly.

### 4. Centralized Authorization Layer

Introduce a policy layer (e.g. CASL, OSO, or a custom middleware) that evaluates `can(user, action, resource)` for every request, rather than scattering ad-hoc ownership checks across handlers.

### 5. Test for IDOR in CI

Add automated tests that log in as user A, request user B's resources, and assert a 403 response. IDOR flaws are easy to miss in code review but trivial to catch with targeted integration tests.

---

## Conclusion

The Juice Shop `/rest/basket/:id` endpoint authenticates the caller but fails to authorize them against the requested object. A single tampered request allows any logged-in user to read any other user's basket. The fix is a one-line ownership check, or better, removing the client-controlled ID entirely and deriving the basket from the session. This vulnerability is a classic example of OWASP Top 10 **A01:2021 - Broken Access Control**.

---

*This write-up was created in a controlled lab environment using OWASP Juice Shop for educational purposes.*
