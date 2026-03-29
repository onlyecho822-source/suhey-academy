#!/bin/bash
# Suhey Academy — Pre-flight check before going live
echo "=== SUHEY ACADEMY PRE-FLIGHT CHECK ==="
echo ""

PASS=0
FAIL=0

check() {
  if grep -q "$2" index.html 2>/dev/null; then
    echo "✓ $1 found"
    PASS=$((PASS+1))
  else
    echo "✗ $1 NOT FOUND — check index.html"
    FAIL=$((FAIL+1))
  fi
}

check_placeholder() {
  if grep -q "$1" index.html 2>/dev/null; then
    echo "⚠ PLACEHOLDER STILL IN FILE: $1"
    FAIL=$((FAIL+1))
  else
    echo "✓ $1 replaced"
    PASS=$((PASS+1))
  fi
}

echo "--- Checking Stripe links ---"
check_placeholder "YOUR_TRIAL_LINK"
check_placeholder "YOUR_MONTHLY_LINK"
check_placeholder "YOUR_COURSE_LINK"
check_placeholder "YOUR_VIP_LINK"

echo ""
echo "--- Checking EmailJS ---"
check_placeholder "YOUR_SERVICE_ID"
check_placeholder "YOUR_TEMPLATE_ID"

echo ""
echo "--- Checking contact info ---"
check_placeholder "YOUR_WHATSAPP"
check_placeholder "YOUR_GOOGLE_CAL"

echo ""
echo "--- Core files ---"
check "index.html" "Suhey"
check "netlify.toml" "publish"

echo ""
echo "==================================="
echo "PASS: $PASS | FAIL: $FAIL"
if [ $FAIL -eq 0 ]; then
  echo "✅ READY TO DEPLOY"
  echo "Run: git add -A && git commit -m 'config: all 8 values set — ready to deploy' && git push"
else
  echo "❌ Fix $FAIL items before deploying"
fi
