#!/bin/bash
# Suhey Academy — Configuration Helper
# Run this AFTER Suhey provides the 8 values
# Usage: ./configure.sh

echo "Suhey Academy Configuration"
echo "============================"
echo ""
echo "Enter the 8 configuration values."
echo "Press ENTER to skip any you do not have yet."
echo ""

read -p "1. Stripe Trial Link (\$50 one-time):         " TRIAL_LINK
read -p "2. Stripe Monthly Link (\$97/mo):             " MONTHLY_LINK
read -p "3. Stripe Course Link (\$197 one-time):       " COURSE_LINK
read -p "4. Stripe VIP Link (\$197/mo):                " VIP_LINK
read -p "5. EmailJS Service ID:                        " SERVICE_ID
read -p "6. EmailJS Template ID:                       " TEMPLATE_ID
read -p "7. WhatsApp number (with country code, e.g. 18095551234): " WHATSAPP
read -p "8. Google Calendar booking URL:               " GOOGLE_CAL

echo ""
echo "Applying configuration to index.html..."

# Backup
cp index.html index.html.backup

# Apply replacements
[ -n "$TRIAL_LINK" ]   && sed -i "s|YOUR_TRIAL_LINK|$TRIAL_LINK|g" index.html
[ -n "$MONTHLY_LINK" ] && sed -i "s|YOUR_MONTHLY_LINK|$MONTHLY_LINK|g" index.html
[ -n "$COURSE_LINK" ]  && sed -i "s|YOUR_COURSE_LINK|$COURSE_LINK|g" index.html
[ -n "$VIP_LINK" ]     && sed -i "s|YOUR_VIP_LINK|$VIP_LINK|g" index.html
[ -n "$SERVICE_ID" ]   && sed -i "s|YOUR_SERVICE_ID|$SERVICE_ID|g" index.html
[ -n "$TEMPLATE_ID" ]  && sed -i "s|YOUR_TEMPLATE_ID|$TEMPLATE_ID|g" index.html
[ -n "$WHATSAPP" ]     && sed -i "s|YOUR_WHATSAPP|$WHATSAPP|g" index.html
[ -n "$GOOGLE_CAL" ]   && sed -i "s|YOUR_GOOGLE_CAL|$GOOGLE_CAL|g" index.html

echo ""
echo "Done. Checking remaining placeholders..."
REMAINING=$(grep -c "YOUR_" index.html 2>/dev/null || echo "0")
echo "Remaining YOUR_ placeholders: $REMAINING"

if [ "$REMAINING" -eq "0" ]; then
  echo ""
  echo "✅ All values filled. Ready to deploy."
  echo ""
  echo "Next step: git add index.html && git commit -m 'config: fill all 8 values' && git push"
  echo "Netlify will auto-deploy in ~30 seconds."
else
  echo ""
  echo "⚠️  $REMAINING placeholder(s) still need values."
  echo "Run this script again when you have them."
fi
