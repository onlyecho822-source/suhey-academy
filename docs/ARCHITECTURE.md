# Suhey Academy — Architecture

**Protocol**: ECS v1.1-hardened | **Authority**: echo-core

---

## Stack

- Frontend: HTML/CSS/JS (5,948kb)
- Payments: Stripe (4 payment links)
- Email: EmailJS
- Contact: WhatsApp integration
- Booking: Google Calendar
- Deploy: Netlify (CI 10/10 passing)

---

## Components

- Main site: index.html
- Podcast page: live at artifact URL
- Payment integration: Stripe links
- Contact: WhatsApp + EmailJS
- Booking: Google Calendar embed

---

## Data Flow

Student visits → Browses content → Selects plan → Stripe checkout → EmailJS confirmation → Google Calendar booking

---

## Dependencies

**Depends on**: Stripe, EmailJS, Google Calendar (all external)  
**Depended on by**: echo-echolibrary-site (product catalog)

---

## Deployment

See `README.md` for deploy instructions.


---

## Ecosystem Connection

**Part of**: Echo Universe (45-repository sovereign AI and evidence ecosystem)  
**Operator**: Nathan Poinsette (∇θ) | onlyecho822-source  
**Ecosystem White Paper**: [`art-of-proof/docs/WHITE_PAPER_v3.md`](https://github.com/onlyecho822-source/art-of-proof/blob/main/docs/WHITE_PAPER_v3.md)  
**Governance Protocol**: ECS v1.1-hardened (`echo-core`)  
**Canonical Authority**: [`echo-core`](https://github.com/onlyecho822-source/echo-core)

*∇θ — chain sealed, truth preserved.*
