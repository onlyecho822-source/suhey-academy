# Suhey Academy — Architecture

**Stack**: Static site (HTML/CSS/JS) + Stripe payment links + EmailJS + WhatsApp integration

---

## Why This Stack

Static site means: no server to maintain, no backend to deploy, no database to manage. The entire payment and communication flow runs through third-party services that Suhey already controls.

This is intentional. Suhey owns and operates the academy. The tech must be maintainable by a non-developer.

---

## Integration Points

| Service | Purpose | Config Value |
|---------|---------|-------------|
| Stripe Payment Links | Course purchases | 4 pre-built links |
| EmailJS | Contact forms, enrollment confirmation | Service ID + Template ID |
| WhatsApp Business | Student communication | Phone number |
| Google Calendar | Class booking | Calendar URL |

---

## Podcast Page

Live at: artifact URL (https://claude.ai/public/artifacts/958a26d0-7dda-4f3a-9858-6fad7554c428)  
All podcast buttons on the landing page point here with `target="_blank"`.

*∇θ — chain sealed, truth preserved.*
