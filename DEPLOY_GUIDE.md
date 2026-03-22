# Suhey Academy Deployment

## Deploy Route: Netlify GitHub App (NO GitHub Actions needed)

### One-time setup:
1. Go to app.netlify.com
2. Click "Add new site" -> "Import from Git"
3. Click GitHub -> authorize -> select "suhey-academy"
4. Build settings: leave blank (static HTML)
5. Click Deploy

### After first deploy:
- Every push to main auto-deploys in ~30 seconds
- Netlify handles everything — no GitHub secrets needed
- Copy the Netlify URL -> paste into Stripe as business website

### The 8 placeholders to fill in index.html:
- YOUR_TRIAL_LINK        -> Stripe payment link $50
- YOUR_MONTHLY_LINK      -> Stripe payment link $97/mo
- YOUR_COURSE_LINK       -> Stripe payment link $197
- YOUR_VIP_LINK          -> Stripe payment link $197/mo
- YOUR_SERVICE_ID        -> EmailJS service ID
- YOUR_TEMPLATE_ID       -> EmailJS template ID
- YOUR_WHATSAPP          -> WhatsApp number with country code
- YOUR_GOOGLE_CAL        -> Google Calendar booking URL

After filling: commit + push -> Netlify auto-deploys -> live in 30 seconds.
