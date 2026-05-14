// Ravinarayan Tiffin — progressive enhancement layer.
//   - Mobile nav toggle
//   - Order form: live total with lunch+dinner multiplier, pickup toggle,
//     pin location (GPS or paste URL), smart submit validator.
(function () {
  "use strict";

  // ---- nav: mobile drawer + scroll shadow ------------------------------
  const navEl = document.querySelector("[data-nav]");
  const navToggle = document.querySelector("[data-nav-toggle]");
  const navClose = document.querySelector("[data-nav-close]");
  const navBackdrop = document.querySelector("[data-nav-backdrop]");
  const body = document.body;

  function setDrawer(open) {
    body.classList.toggle("nav-open", open);
    if (navToggle) navToggle.setAttribute("aria-expanded", open ? "true" : "false");
  }
  if (navToggle) navToggle.addEventListener("click", () => setDrawer(!body.classList.contains("nav-open")));
  if (navClose) navClose.addEventListener("click", () => setDrawer(false));
  if (navBackdrop) navBackdrop.addEventListener("click", () => setDrawer(false));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && body.classList.contains("nav-open")) setDrawer(false);
  });
  document.querySelectorAll("#primary-nav a").forEach((a) => {
    a.addEventListener("click", () => setDrawer(false));
  });

  // Subtle shadow when scrolled
  if (navEl) {
    const onScroll = () => {
      navEl.classList.toggle("is-scrolled", window.scrollY > 4);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // Reset drawer state if user resizes from mobile to desktop
  let lastNarrow = window.matchMedia("(max-width: 879px)").matches;
  window.addEventListener("resize", () => {
    const narrow = window.matchMedia("(max-width: 879px)").matches;
    if (lastNarrow && !narrow) setDrawer(false);
    lastNarrow = narrow;
  });

  // ---- order form -------------------------------------------------------
  const form = document.querySelector("[data-order-form]");
  if (!form) return;

  const $ = (s, root) => (root || form).querySelector(s);
  const $$ = (s, root) => Array.from((root || form).querySelectorAll(s));

  const planHidden = $('input[name="plan"]');
  const planPicks = $$(".plan-pick");
  const qtyInput = $("#id_quantity");
  const mealTimeSelect = $("#id_meal_time");
  const addonCards = $$(".addon-card");
  const submitBtn = $("[data-sum-submit]");
  const missingHint = $("#missing-hint");
  const missingCountEl = $("[data-missing-count]");
  const missingPluralEl = $("[data-missing-plural]");
  const formAlert = $("#form-alert");
  const multiplierHint = $("#multiplier-hint");
  const mealWindowHint = $("#meal-window-hint");
  const quantityHint = $("#quantity-hint");
  const mealTimeRow = $("[data-meal-time-row]");

  const sumMethodEl = $("[data-sum-method]");
  const sumPlanEl = $("[data-sum-plan]");
  const sumMealsRow = $(".sum-meals-row");
  const sumMealsEl = $("[data-sum-meals]");
  const sumPlanTotalEl = $("[data-sum-plan-total]");
  const sumAddonsListEl = $("[data-sum-addons]");
  const sumAddonsTotalEl = $("[data-sum-addons-total]");
  const sumDeliveryRow = $("[data-sum-delivery-row]");
  const sumDeliveryFeeEl = $("[data-sum-delivery-fee]");
  const sumTotalEl = $("[data-sum-total]");
  const sumTotalMobileEl = $("[data-sum-total-mobile]");
  const mobilePlanEl = $("[data-mobile-plan]");
  const deliveryFreeKm = Number(form.dataset.deliveryFreeKm) || 2;
  const deliveryFeeSlabKm = Number(form.dataset.deliveryFeeSlabKm) || 2;
  const deliveryFeePerSlab = Number(form.dataset.deliveryFeePerSlab) || 10;
  const maxDeliveryKm = Number(form.dataset.maxDeliveryKm) || 4;
  const currentDateIso = form.dataset.currentDate || "";
  const renderedCurrentMinutes = Number(form.dataset.currentMinutes) || 0;
  const renderedAtMs = Date.now();
  const lunchCutoffMinutes = Number(form.dataset.lunchCutoffMinutes) || (10 * 60 + 30);
  const dinnerCutoffMinutes = Number(form.dataset.dinnerCutoffMinutes) || (19 * 60 + 30);

  const fmt = (n) => "₹" + Math.max(0, Math.round(n)).toLocaleString("en-IN");

  // ---- helpers ---------------------------------------------------------
  function localDateIso(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function effectiveCurrentMinutes() {
    return renderedCurrentMinutes + Math.floor((Date.now() - renderedAtMs) / 60000);
  }

  function getMethod() {
    const r = $('input[name="delivery_method"]:checked');
    return r ? r.value : "delivery";
  }
  function isDelivery() { return getMethod() === "delivery"; }

  function getSelectedPlan() {
    const checked = $('input[name="plan_pick"]:checked');
    if (!checked) return null;
    const card = checked.closest(".plan-pick");
    return {
      id: checked.value,
      name: card.dataset.planName,
      price: Number(card.dataset.planPrice) || 0,
      priceOnRequest: card.dataset.planPriceOnRequest === "1",
      category: card.dataset.planCategory || "tiffin",
      minQuantity: Math.max(1, Number(card.dataset.planMinQuantity) || 1),
      singleMealPrice: Number(card.dataset.planSingleMealPrice) || 0,
      unit: card.dataset.planUnit || "",
    };
  }
  function isPerMealPlan(p) { return p && /per meal/i.test(p.unit); }
  function isTiffinPlan(p) { return !p || p.category === "tiffin"; }

  function unitPriceForPlan(plan) {
    if (!plan || plan.priceOnRequest) return 0;
    const mt = mealTimeSelect ? mealTimeSelect.value : "";
    if (plan.category === "tiffin" && /per month/i.test(plan.unit) && plan.singleMealPrice && mt !== "both") {
      return plan.singleMealPrice;
    }
    return plan.price;
  }

  function mealMultiplier() {
    const plan = getSelectedPlan();
    const mt = mealTimeSelect ? mealTimeSelect.value : "";
    return isPerMealPlan(plan) && mt === "both" ? 2 : 1;
  }

  function getAddons() {
    return addonCards.map((card) => {
      const input = card.querySelector(".qty-num");
      const qty = Math.max(0, Math.min(100, parseInt(input.value, 10) || 0));
      return {
        name: card.dataset.addonName,
        price: Number(card.dataset.addonPrice) || 0,
        qty, card, input,
      };
    });
  }

  // Required-field set is dynamic (depends on method)
  function buildRequired() {
    const list = [
      { key: "plan",          label: "plan",         input: planHidden,             scrollEl: $(".plan-picker") },
      { key: "full_name",     label: "your name",    input: $("#id_full_name") },
      { key: "phone",         label: "your phone",   input: $("#id_phone") },
      { key: "quantity",      label: "quantity",     input: $("#id_quantity") },
      { key: "meal_time",     label: "meal time",    input: $("#id_meal_time") },
      { key: "delivery_date", label: "delivery date",input: $("#id_delivery_date") },
    ];
    if (isDelivery() && hasKitchen) {
      list.push({ key: "location_url", label: "delivery location", input: $("#id_location_url"), scrollEl: $("[data-loc-open]") });
    }
    if (isDelivery()) {
      list.push({ key: "address", label: "delivery address", input: $("#id_address") });
      list.push({ key: "area",    label: "delivery area",    input: $("#id_area") });
    }
    return list;
  }

  function isFilled(input) {
    if (!input) return false;
    const v = (input.value || "").trim();
    if (!v) return false;
    if (input.id === "id_quantity" && parseInt(v, 10) < 1) return false;
    return true;
  }

  function deliveryFeeForDistance(distanceKm) {
    if (distanceKm == null || distanceKm <= deliveryFreeKm) return 0;
    return Math.ceil((distanceKm - deliveryFreeKm) / deliveryFeeSlabKm) * deliveryFeePerSlab;
  }

  function currentDeliveryDistanceKm() {
    if (!isDelivery() || !hasKitchen || !locationField || !locationField.value) return null;
    const coords = parseCoordsFromUrl(locationField.value);
    if (!coords) return null;
    return haversineKm(coords[0], coords[1], kLat, kLng);
  }

  function deliveryFeeSummary(distanceKm, fee) {
    if (!hasKitchen) return fmt(0);
    if (distanceKm == null) return "Set location";
    return `${fmt(fee)}${fee === 0 ? " (free)" : ""}`;
  }

  function deliveryDistanceSummary(distanceKm) {
    if (distanceKm == null) return "";
    const fee = deliveryFeeForDistance(distanceKm);
    return `${distanceKm.toFixed(1)} km · ${fee === 0 ? "Free delivery" : `${fmt(fee)} delivery charge`}`;
  }

  // ---- recompute summary + validation hint -----------------------------
  function recompute() {
    const method = getMethod();
    if (sumMethodEl) sumMethodEl.textContent = method === "pickup" ? "Pick up from counter" : "Home delivery";

    const plan = getSelectedPlan();
    const qty = Math.max(1, parseInt(qtyInput && qtyInput.value, 10) || 1);
    const mult = mealMultiplier();
    const unitPrice = unitPriceForPlan(plan);
    const planSubtotal = plan ? unitPrice * qty * mult : 0;
    const priceOnRequest = Boolean(plan && plan.priceOnRequest);

    if (sumPlanEl) {
      sumPlanEl.textContent = plan
        ? `${plan.name} × ${qty}${mult > 1 ? " (Lunch+Dinner)" : ""}`
        : "—";
    }
    if (sumMealsRow && sumMealsEl) {
      if (mult > 1) {
        sumMealsRow.hidden = false;
        sumMealsEl.textContent = `${qty * mult} meals (${qty} lunch + ${qty} dinner)`;
      } else {
        sumMealsRow.hidden = true;
      }
    }
    if (multiplierHint) {
      if (plan && plan.category === "tiffin" && /per month/i.test(plan.unit) && plan.singleMealPrice) {
        multiplierHint.hidden = false;
        multiplierHint.textContent = `Lunch or dinner only is ₹${plan.singleMealPrice.toLocaleString("en-IN")}/month. Lunch + Dinner is ₹${plan.price.toLocaleString("en-IN")}/month.`;
      } else {
        multiplierHint.hidden = !(plan && isPerMealPlan(plan));
        multiplierHint.textContent = "Lunch + Dinner doubles the meal count.";
      }
    }

    if (sumPlanTotalEl) sumPlanTotalEl.textContent = priceOnRequest ? "On request" : fmt(planSubtotal);

    let addonsTotal = 0;
    if (sumAddonsListEl) sumAddonsListEl.innerHTML = "";
    getAddons().forEach((a) => {
      a.card.classList.toggle("has-qty", a.qty > 0);
      if (a.qty > 0) {
        addonsTotal += a.price * a.qty;
        if (sumAddonsListEl) {
          const row = document.createElement("div");
          row.className = "sum-line";
          const left = document.createElement("span");
          left.className = "muted";
          left.textContent = `${a.name} × ${a.qty}`;
          const right = document.createElement("span");
          right.textContent = fmt(a.price * a.qty);
          row.appendChild(left);
          row.appendChild(right);
          sumAddonsListEl.appendChild(row);
        }
      }
    });
    if (sumAddonsTotalEl) sumAddonsTotalEl.textContent = fmt(addonsTotal);

    const deliveryDistance = currentDeliveryDistanceKm();
    const deliveryFee = isDelivery() ? deliveryFeeForDistance(deliveryDistance) : 0;
    if (sumDeliveryRow) sumDeliveryRow.hidden = !isDelivery();
    if (sumDeliveryFeeEl) sumDeliveryFeeEl.textContent = deliveryFeeSummary(deliveryDistance, deliveryFee);

    const grand = planSubtotal + addonsTotal + deliveryFee;
    const knownTotal = addonsTotal + deliveryFee;
    const totalLabel = priceOnRequest
      ? (knownTotal > 0 ? `${fmt(knownTotal)} + quote` : "Quote on WhatsApp")
      : fmt(grand);
    if (sumTotalEl) sumTotalEl.textContent = totalLabel;
    if (sumTotalMobileEl) sumTotalMobileEl.textContent = totalLabel;
    if (mobilePlanEl) {
      if (plan) {
        const mealNote = mult > 1 ? " · L+D" : "";
        mobilePlanEl.textContent = `${plan.name} × ${qty}${mealNote}`;
        mobilePlanEl.classList.remove("muted");
      } else {
        mobilePlanEl.textContent = "Pick a plan";
        mobilePlanEl.classList.add("muted");
      }
    }

    // Live missing-fields hint
    const missing = buildRequired().filter((r) => !isFilled(r.input));
    if (missing.length === 0) {
      submitBtn.classList.remove("is-incomplete");
      if (missingHint) missingHint.hidden = true;
    } else {
      submitBtn.classList.add("is-incomplete");
      if (missingHint) {
        missingHint.hidden = false;
        if (missingCountEl) missingCountEl.textContent = String(missing.length);
        if (missingPluralEl) missingPluralEl.textContent = missing.length === 1 ? "" : "s";
      }
    }
  }

  // ---- pickup vs delivery toggle ---------------------------------------
  const deliveryFields = $("#delivery-fields");
  const pickupInfo = $("#pickup-info");

  function applyPlanControls() {
    const plan = getSelectedPlan();
    const tiffin = isTiffinPlan(plan);
    if (mealTimeRow) mealTimeRow.hidden = !tiffin;
    if (mealTimeSelect && !tiffin) mealTimeSelect.value = "lunch";

    const minQty = plan ? plan.minQuantity : 1;
    if (qtyInput) {
      qtyInput.min = String(minQty);
      const current = Math.max(1, parseInt(qtyInput.value, 10) || 1);
      if (current < minQty) qtyInput.value = String(minQty);
    }
    if (quantityHint) {
      quantityHint.hidden = minQty <= 1;
      quantityHint.textContent = minQty > 1 ? `Minimum order ${minQty} pcs.` : "";
    }

    if (dateInput && plan && (plan.category === "rice_bowl" || plan.category === "snack")) {
      dateInput.value = currentDateIso || localDateIso(new Date());
      syncDateChips();
    }

    updateMealAvailability();
  }

  function setMealOptionsDisabled(disabledValues) {
    if (!mealTimeSelect) return;
    const disabled = new Set(disabledValues);
    Array.from(mealTimeSelect.options).forEach((option) => {
      option.disabled = disabled.has(option.value);
    });
  }

  function selectedMealWindowMessage() {
    const plan = getSelectedPlan();
    if (!isTiffinPlan(plan) || !dateInput || dateInput.value !== currentDateIso) return "";

    const minutes = effectiveCurrentMinutes();
    const meal = mealTimeSelect ? mealTimeSelect.value : "";
    if (minutes >= dinnerCutoffMinutes) {
      return "Tiffin ordering is closed for today. Please choose another date.";
    }
    if (minutes >= lunchCutoffMinutes && (meal === "lunch" || meal === "both")) {
      return "Lunch ordering is closed for today. Please choose Dinner or another date.";
    }
    return "";
  }

  function updateMealAvailability() {
    const plan = getSelectedPlan();
    if (!mealTimeSelect || !isTiffinPlan(plan)) {
      setMealOptionsDisabled([]);
      if (mealWindowHint) mealWindowHint.hidden = true;
      return;
    }

    const isToday = dateInput && dateInput.value === currentDateIso;
    const minutes = effectiveCurrentMinutes();
    let message = "";
    setMealOptionsDisabled([]);

    if (isToday && minutes >= dinnerCutoffMinutes) {
      setMealOptionsDisabled(["lunch", "dinner", "both"]);
      mealTimeSelect.selectedIndex = -1;
      message = "Tiffin ordering is closed for today. Choose tomorrow or a later date.";
    } else if (isToday && minutes >= lunchCutoffMinutes) {
      setMealOptionsDisabled(["lunch", "both"]);
      if (mealTimeSelect.value === "lunch" || mealTimeSelect.value === "both") {
        mealTimeSelect.value = "dinner";
      }
      message = "Lunch is closed for today. Dinner orders are open until 7:30 PM.";
    } else if (isToday) {
      message = "Lunch closes at 10:30 AM. Dinner closes at 7:30 PM.";
    }

    if (mealWindowHint) {
      mealWindowHint.hidden = !message;
      mealWindowHint.textContent = message;
    }
  }

  function applyMethodVisibility() {
    const pickup = !isDelivery();
    if (deliveryFields) deliveryFields.hidden = pickup;
    if (pickupInfo) pickupInfo.hidden = !pickup;
    $$(".req.delivery-only").forEach((el) => { el.style.display = pickup ? "none" : ""; });
  }
  $$('input[name="delivery_method"]').forEach((r) => {
    r.addEventListener("change", () => { applyMethodVisibility(); recompute(); });
  });

  // ---- plan picker ------------------------------------------------------
  let userHasPickedPlan = false;
  const isMobile = () => window.matchMedia("(max-width: 879px)").matches;

  planPicks.forEach((label) => {
    const input = label.querySelector("input");
    input.addEventListener("change", () => {
      if (planHidden) planHidden.value = input.value;
      applyPlanControls();
      recompute();
      // On mobile only: smooth-scroll to step 2 after the user actively picks
      // a plan. Don't auto-scroll for the pre-selected default — that would
      // jump the page on first load.
      if (userHasPickedPlan && isMobile()) {
        const next = form.querySelectorAll("fieldset.step-card")[1];
        if (next) setTimeout(() => next.scrollIntoView({ behavior: "smooth", block: "start" }), 220);
      }
      userHasPickedPlan = true;
    });
  });
  const preChecked = $('input[name="plan_pick"]:checked');
  if (preChecked && planHidden) planHidden.value = preChecked.value;

  // ---- date chips: Tomorrow / Day after / In 3 days --------------------
  const dateInput = $("#id_delivery_date");
  const dateChipsWrap = $("[data-date-chips]");
  function syncDateChips() {
    if (!dateInput || !dateChipsWrap) return;
    const today = currentDateIso ? new Date(`${currentDateIso}T00:00:00`) : new Date();
    today.setHours(0,0,0,0);
    const v = dateInput.value;
    dateChipsWrap.querySelectorAll(".date-chip").forEach((c) => {
      const offset = parseInt(c.dataset.dayOffset, 10);
      const d = new Date(today); d.setDate(d.getDate() + offset);
      const iso = localDateIso(d);
      c.classList.toggle("is-active", v === iso);
    });
  }
  if (dateChipsWrap) {
    dateChipsWrap.querySelectorAll(".date-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const today = currentDateIso ? new Date(`${currentDateIso}T00:00:00`) : new Date();
        today.setHours(0,0,0,0);
        const offset = parseInt(chip.dataset.dayOffset, 10);
        const d = new Date(today); d.setDate(d.getDate() + offset);
        if (dateInput) {
          dateInput.value = localDateIso(d);
          dateInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
        syncDateChips();
      });
    });
    if (dateInput) dateInput.addEventListener("input", () => {
      syncDateChips();
      applyPlanControls();
      recompute();
    });
    syncDateChips();
  }

  // Watch every required field so the live hint stays accurate
  ["#id_full_name","#id_phone","#id_location_url","#id_address","#id_area","#id_quantity",
   "#id_meal_time","#id_delivery_date"].forEach((sel) => {
    const el = $(sel);
    if (el) {
      el.addEventListener("input", recompute);
      el.addEventListener("change", recompute);
    }
  });

  // ---- addon +/- buttons -----------------------------------------------
  addonCards.forEach((card) => {
    const input = card.querySelector(".qty-num");
    card.querySelectorAll("[data-qty-step]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const step = parseInt(btn.dataset.qtyStep, 10) || 0;
        const next = Math.max(0, Math.min(100, (parseInt(input.value, 10) || 0) + step));
        input.value = next;
        recompute();
      });
    });
    input.addEventListener("input", () => {
      const v = Math.max(0, Math.min(100, parseInt(input.value, 10) || 0));
      if (String(v) !== input.value) input.value = v;
      recompute();
    });
  });

  // ---- submit validator: scroll to first missing ----------------------
  function showAlert(text) {
    if (!formAlert) return;
    formAlert.textContent = text;
    formAlert.hidden = false;
    formAlert.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  function clearFieldHighlights() {
    $$(".field-invalid").forEach((el) => el.classList.remove("field-invalid"));
  }
  form.addEventListener("submit", (e) => {
    clearFieldHighlights();
    updateMealAvailability();
    const windowMessage = selectedMealWindowMessage();
    if (windowMessage) {
      e.preventDefault();
      if (mealTimeSelect) {
        mealTimeSelect.classList.add("field-invalid");
        mealTimeSelect.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => mealTimeSelect.focus({ preventScroll: true }), 350);
      }
      showAlert(windowMessage);
      return;
    }
    const missing = buildRequired().filter((r) => !isFilled(r.input));
    if (missing.length === 0) return;
    e.preventDefault();
    const first = missing[0];
    const input = first.input;
    const target = first.scrollEl || input;
    if (target) target.scrollIntoView({ behavior: "smooth", block: "center" });
    if (input && input.id !== "id_plan") {
      input.classList.add("field-invalid");
      setTimeout(() => input.focus({ preventScroll: true }), 350);
    }
    missing.slice(1).forEach((r) => {
      if (r.input && r.input.id !== "id_plan") r.input.classList.add("field-invalid");
    });
    const labels = missing.map((r) => r.label).join(", ");
    showAlert(missing.length === 1
      ? `Please fill in your ${labels} before placing the order.`
      : `Please fill in: ${labels}.`);
  });
  ["#id_full_name","#id_phone","#id_location_url","#id_address","#id_area","#id_quantity",
   "#id_meal_time","#id_delivery_date"].forEach((sel) => {
    const el = $(sel);
    if (el) el.addEventListener("input", () => {
      el.classList.remove("field-invalid");
      if (formAlert && !formAlert.hidden) {
        const stillMissing = buildRequired().filter((r) => !isFilled(r.input)).length;
        if (stillMissing === 0) formAlert.hidden = true;
      }
    });
  });

  // ---- LOCATION PICKER (Leaflet + Nominatim, lazy-loaded) -------------
  const locationField = $("#id_location_url");
  const locTrigger = $("[data-loc-open]");
  const locModal = document.querySelector("[data-loc-modal]");
  const locEmpty = $("[data-loc-empty]");
  const locSet = $("[data-loc-set]");
  const locSummary = $("[data-loc-summary]");
  const locDistance = $("[data-loc-distance]");
  const addressField = $("#id_address");
  const areaField = $("#id_area");
  const areaAuto = $("[data-area-auto]");

  // Kitchen + radius from form data attributes (set in template)
  const kLat = parseFloat(form.dataset.kitchenLat);
  const kLng = parseFloat(form.dataset.kitchenLng);
  const kRadius = maxDeliveryKm;
  const hasKitchen = !isNaN(kLat) && !isNaN(kLng);
  const hasMaxDeliveryRadius = maxDeliveryKm > 0;

  function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371, toRad = (d) => d * Math.PI / 180;
    const dLat = toRad(lat2 - lat1), dLng = toRad(lng2 - lng1);
    const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng/2)**2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  // Parse coords from a Google Maps URL like ?q=lat,lng or @lat,lng
  function parseCoordsFromUrl(url) {
    if (!url) return null;
    const m = url.match(/[?&@](?:q=|ll=|center=)?(-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)/);
    if (!m) return null;
    const lat = parseFloat(m[1]), lng = parseFloat(m[2]);
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;
    return [lat, lng];
  }

  // Update the trigger card with current location state
  function updateTriggerUI(state) {
    if (!locTrigger) return;
    if (!state) {
      locTrigger.classList.remove("is-set");
      if (locEmpty) locEmpty.hidden = false;
      if (locSet) locSet.hidden = true;
      return;
    }
    locTrigger.classList.add("is-set");
    if (locEmpty) locEmpty.hidden = true;
    if (locSet) locSet.hidden = false;
    if (locSummary) locSummary.textContent = state.label || "Pinned location";
    if (locDistance) {
      if (state.dist != null) {
        const inZone = (!hasMaxDeliveryRadius || state.dist <= kRadius);
        const feeText = deliveryDistanceSummary(state.dist);
        locDistance.textContent = `${inZone ? "✓ We deliver here" : "✗ Outside zone"} · ${feeText}`;
        locDistance.style.color = inZone ? "var(--green-700)" : "#8a1a1a";
      } else {
        locDistance.textContent = "📍 Saved";
        locDistance.style.color = "";
      }
    }
  }

  // Restore previously-saved location on page load
  (function restoreLocation() {
    if (!locationField || !locationField.value) return;
    const coords = parseCoordsFromUrl(locationField.value);
    let dist = null;
    if (coords && hasKitchen) dist = haversineKm(coords[0], coords[1], kLat, kLng);
    updateTriggerUI({ label: "Saved location", dist });
  })();

  // ---- Lazy-loader for Leaflet ----------------------------------------
  let leafletLoadPromise = null;
  function loadLeaflet() {
    if (window.L) return Promise.resolve();
    if (leafletLoadPromise) return leafletLoadPromise;
    leafletLoadPromise = new Promise((resolve, reject) => {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      css.integrity = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=";
      css.crossOrigin = "";
      document.head.appendChild(css);
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.integrity = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=";
      script.crossOrigin = "";
      script.onload = () => resolve();
      script.onerror = () => { leafletLoadPromise = null; reject(new Error("Leaflet failed to load")); };
      document.head.appendChild(script);
    });
    return leafletLoadPromise;
  }

  // ---- Modal state ----------------------------------------------------
  let map = null, userMarker = null, kitchenMarker = null, zoneCircle = null;
  let pendingState = null; // { lat, lng, address, suburb, dist, inZone }
  let geocodeTimer = null, searchTimer = null;

  const modalSearch = $("[data-loc-search]", locModal);
  const modalSearchClear = $("[data-loc-search-clear]", locModal);
  const modalResults = $("[data-loc-results]", locModal);
  const modalGps = $("[data-loc-gps]", locModal);
  const modalStatus = $("[data-loc-status]", locModal);
  const modalAddress = $("[data-loc-address]", locModal);
  const modalConfirm = $("[data-loc-confirm]", locModal);

  function setStatus(text, kind /* 'in' | 'out' | 'loading' | '' */) {
    if (!modalStatus) return;
    modalStatus.textContent = text;
    modalStatus.classList.remove("is-in", "is-out", "is-loading");
    if (kind) modalStatus.classList.add(`is-${kind}`);
  }

  async function reverseGeocode(lat, lng) {
    try {
      const r = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
        { headers: { "Accept-Language": "en" } }
      );
      if (!r.ok) throw new Error("nominatim");
      return await r.json();
    } catch (e) {
      return null;
    }
  }

  async function searchPlaces(q) {
    try {
      const r = await fetch(
        `https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(q)}&limit=6&countrycodes=in&addressdetails=1`,
        { headers: { "Accept-Language": "en" } }
      );
      if (!r.ok) throw new Error("nominatim");
      return await r.json();
    } catch (e) {
      return [];
    }
  }

  function pickSuburb(addr) {
    if (!addr) return "";
    return addr.suburb || addr.neighbourhood || addr.city_district
        || addr.town || addr.village || addr.locality || "";
  }

  // Update pendingState + UI when pin moves
  async function onMarkerMoved() {
    if (!userMarker) return;
    const ll = userMarker.getLatLng();
    const dist = hasKitchen ? haversineKm(ll.lat, ll.lng, kLat, kLng) : null;
    const inZone = !hasKitchen || !hasMaxDeliveryRadius || (dist !== null && dist <= kRadius);

    pendingState = { lat: ll.lat, lng: ll.lng, dist, inZone };

    // Status pill
    if (dist !== null && hasMaxDeliveryRadius) {
      if (inZone) {
        setStatus(`✓ We deliver here · ${deliveryDistanceSummary(dist)}`, "in");
      } else {
        setStatus(`✗ Outside delivery zone · ${dist.toFixed(1)} km (we deliver up to ${kRadius} km)`, "out");
      }
    } else {
      setStatus(`📍 Pinned · ${dist !== null ? deliveryDistanceSummary(dist) : "set"}`, "in");
    }

    if (modalAddress) modalAddress.textContent = "Looking up address…";

    // Reverse-geocode (debounced)
    clearTimeout(geocodeTimer);
    geocodeTimer = setTimeout(async () => {
      const data = await reverseGeocode(ll.lat, ll.lng);
      const display = data?.display_name || `Pinned at ${ll.lat.toFixed(4)}, ${ll.lng.toFixed(4)}`;
      pendingState.address = display;
      pendingState.suburb = pickSuburb(data?.address || {});
      if (modalAddress) modalAddress.textContent = display;
    }, 450);

    if (modalConfirm) modalConfirm.disabled = !inZone;
  }

  function setMapPin(lat, lng, opts = {}) {
    if (!map || !userMarker) return;
    userMarker.setLatLng([lat, lng]);
    if (opts.fly) map.setView([lat, lng], Math.max(map.getZoom(), 15));
    onMarkerMoved();
  }

  async function initMap() {
    await loadLeaflet();
    if (map) return;

    const center = hasKitchen ? [kLat, kLng] : [20.5937, 78.9629]; // India
    const zoom = hasKitchen ? 13 : 5;

    map = L.map("loc-map", { zoomControl: true, attributionControl: true }).setView(center, zoom);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map);

    if (hasKitchen) {
      const kIcon = L.divIcon({
        html: '<div class="loc-pin loc-kitchen-pin" title="Kitchen">🏠</div>',
        className: "", iconSize: [36, 36], iconAnchor: [18, 18],
      });
      kitchenMarker = L.marker([kLat, kLng], { icon: kIcon, interactive: false }).addTo(map);

      if (hasMaxDeliveryRadius || deliveryFreeKm > 0) {
        zoneCircle = L.circle([kLat, kLng], {
          radius: (hasMaxDeliveryRadius ? kRadius : deliveryFreeKm) * 1000,
          color: "#1f7a3a", weight: 1.5, opacity: .8,
          fillColor: "#2e9d4d", fillOpacity: .07,
          interactive: false,
        }).addTo(map);
        map.fitBounds(zoneCircle.getBounds().pad(0.4));
      }
    }

    // User pin: start at saved location, or kitchen, or center
    let initLat = center[0], initLng = center[1];
    if (locationField?.value) {
      const c = parseCoordsFromUrl(locationField.value);
      if (c) { initLat = c[0]; initLng = c[1]; }
    }

    const userIcon = L.divIcon({
      html: '<div class="loc-pin">📍</div>',
      className: "", iconSize: [36, 36], iconAnchor: [18, 32],
    });
    userMarker = L.marker([initLat, initLng], { draggable: true, icon: userIcon, autoPan: true }).addTo(map);
    userMarker.on("dragend", onMarkerMoved);

    map.on("click", (e) => setMapPin(e.latlng.lat, e.latlng.lng));

    onMarkerMoved();

    // Map sometimes mis-sizes if hidden during init — force a refresh
    setTimeout(() => map.invalidateSize(), 100);
  }

  // ---- Search-as-you-type ---------------------------------------------
  function renderResults(items) {
    if (!modalResults) return;
    if (!items.length) {
      modalResults.innerHTML = '<div class="loc-search-empty">No results found</div>';
      modalResults.hidden = false;
      return;
    }
    modalResults.innerHTML = items.map((it, i) => {
      const parts = (it.display_name || "").split(",");
      const title = parts.shift().trim();
      const sub = parts.join(",").trim();
      return `<button type="button" class="loc-search-result" data-idx="${i}" role="option">
        <span class="loc-search-result-title">${title.replace(/[<>]/g, "")}</span>
        <span class="loc-search-result-sub">${sub.replace(/[<>]/g, "")}</span>
      </button>`;
    }).join("");
    modalResults.hidden = false;

    Array.from(modalResults.querySelectorAll(".loc-search-result")).forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.idx, 10);
        const it = items[idx];
        if (!it) return;
        setMapPin(parseFloat(it.lat), parseFloat(it.lon), { fly: true });
        modalSearch.value = it.display_name;
        modalResults.hidden = true;
        if (modalSearchClear) modalSearchClear.hidden = false;
      });
    });
  }

  if (modalSearch) {
    modalSearch.addEventListener("input", (e) => {
      const q = e.target.value.trim();
      if (modalSearchClear) modalSearchClear.hidden = !q;
      clearTimeout(searchTimer);
      if (q.length < 3) { if (modalResults) modalResults.hidden = true; return; }
      if (modalResults) {
        modalResults.innerHTML = '<div class="loc-search-loading">Searching…</div>';
        modalResults.hidden = false;
      }
      searchTimer = setTimeout(async () => {
        const items = await searchPlaces(q);
        renderResults(items);
      }, 350);
    });
    modalSearch.addEventListener("blur", () => {
      // Delay so click on a result registers first
      setTimeout(() => { if (modalResults) modalResults.hidden = true; }, 180);
    });
    modalSearch.addEventListener("focus", () => {
      if (modalResults && modalResults.children.length) modalResults.hidden = false;
    });
  }
  if (modalSearchClear) {
    modalSearchClear.addEventListener("click", () => {
      modalSearch.value = "";
      modalSearchClear.hidden = true;
      if (modalResults) modalResults.hidden = true;
      modalSearch.focus();
    });
  }

  // ---- GPS button (in modal) ------------------------------------------
  if (modalGps) {
    modalGps.addEventListener("click", () => {
      if (!("geolocation" in navigator)) {
        setStatus("Location not supported on this device.", "out");
        return;
      }
      modalGps.disabled = true;
      const orig = modalGps.textContent;
      modalGps.textContent = "📍 Locating…";
      setStatus("Getting your current location…", "loading");
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setMapPin(pos.coords.latitude, pos.coords.longitude, { fly: true });
          modalGps.disabled = false; modalGps.textContent = orig;
        },
        (err) => {
          modalGps.disabled = false; modalGps.textContent = orig;
          let msg = "Couldn't get your location.";
          if (err.code === 1) msg = "Permission denied. Search for an address or drag the pin.";
          else if (err.code === 2) msg = "Location unavailable. Search or drag the pin.";
          else if (err.code === 3) msg = "Location request timed out.";
          setStatus(msg, "out");
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
      );
    });
  }

  // ---- Open / close modal ---------------------------------------------
  function openLocModal() {
    locModal.hidden = false;
    body.classList.add("loc-modal-open");
    initMap().catch(() => setStatus("Couldn't load the map. Please check your connection.", "out"));
    setTimeout(() => modalSearch && modalSearch.focus({ preventScroll: true }), 200);
  }
  function closeLocModal() {
    locModal.hidden = true;
    body.classList.remove("loc-modal-open");
    if (modalResults) modalResults.hidden = true;
  }
  if (locTrigger) locTrigger.addEventListener("click", openLocModal);
  document.querySelectorAll("[data-loc-close]").forEach((el) =>
    el.addEventListener("click", closeLocModal));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && locModal && !locModal.hidden) closeLocModal();
  });

  // ---- Confirm ---------------------------------------------------------
  if (modalConfirm) {
    modalConfirm.addEventListener("click", () => {
      if (!pendingState || !pendingState.inZone) return;
      const { lat, lng, address, suburb, dist } = pendingState;
      const url = `https://maps.google.com/?q=${lat.toFixed(6)},${lng.toFixed(6)}`;
      if (locationField) locationField.value = url;

      // Auto-fill the address field if empty (don't overwrite user's typing)
      if (addressField && !addressField.value.trim() && address) {
        addressField.value = address;
      }

      // Auto-select area if suburb name matches one of the options
      if (areaField && suburb) {
        const target = suburb.toLowerCase();
        let matched = false;
        for (const opt of areaField.options) {
          const t = (opt.textContent || "").toLowerCase();
          if (t && (t === target || t.includes(target) || target.includes(t))) {
            areaField.value = opt.value;
            matched = true;
            break;
          }
        }
        if (areaAuto) areaAuto.hidden = !matched;
      }

      const label = (address || "").split(",").slice(0, 2).join(",").trim() || "Pinned location";
      updateTriggerUI({ label, dist });

      closeLocModal();
      recompute();
    });
  }

  // After server-side validation errors, scroll to first .field-error
  const firstServerError = document.querySelector(".field-error, .msg-error:not([hidden])");
  if (firstServerError) {
    setTimeout(() => firstServerError.scrollIntoView({ behavior: "smooth", block: "center" }), 80);
  }

  applyMethodVisibility();
  applyPlanControls();
  recompute();
})();
