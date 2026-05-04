/**
 * backend_integration.js
 * ──────────────────────
 * Connects the existing Qatar Foundation Admin Portal frontend to the
 * Flask backend.  This file DOES NOT change any HTML structure, CSS,
 * or the original admin.js UI logic.  It simply:
 *   1. Overrides the form submit handlers defined in admin.js with real
 *      fetch() calls to the Flask API.
 *   2. Loads opportunities from the database on dashboard entry.
 *   3. Wires "Add Opportunity" form to POST /api/opportunities.
 *   4. Adds edit / delete controls per card (using data attributes).
 *   5. Persists login state across page reloads via /api/auth/me.
 *
 * Load order in admin.html:
 *   <script src="/static/js/admin.js"></script>          ← original
 *   <script src="/static/js/backend_integration.js"></script>  ← this file
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
//  Utility helpers
// ─────────────────────────────────────────────────────────────────────────────

let csrfToken = null;

async function fetchCsrfToken() {
    if (!csrfToken) {
        const res = await fetch("/api/auth/csrf-token");
        const data = await res.json();
        csrfToken = data.csrf_token;
    }
    return csrfToken;
}

/** POST / PUT / DELETE with JSON body; returns parsed JSON. */
async function apiRequest(url, method = "GET", body = null) {
    const options = {
        method,
        credentials: "same-origin",   // send session cookie
        headers: { "Content-Type": "application/json" },
    };

    // Inject CSRF token for mutating requests
    if (["POST", "PUT", "DELETE"].includes(method.toUpperCase())) {
        const token = await fetchCsrfToken();
        options.headers["X-CSRFToken"] = token;
    }

    if (body) options.body = JSON.stringify(body);
    const res  = await fetch(url, options);
    const json = await res.json();
    return { ok: res.ok, status: res.status, data: json };
}

/** Safely escape a string for innerHTML insertion. */
function esc(str) {
    return String(str ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

/** Show the page-level toast (reuses existing showToast from admin.js). */
function toast(msg) {
    if (typeof showToast === "function") showToast(msg);
    else console.info("[Toast]", msg);
}

// ─────────────────────────────────────────────────────────────────────────────
//  Session persistence — check if already logged in on page load
// ─────────────────────────────────────────────────────────────────────────────

async function checkExistingSession() {
    try {
        const { ok, data } = await apiRequest("/api/auth/me");
        if (ok && data.success) {
            // Admin is already authenticated — go straight to dashboard
            if (typeof showDashboard === "function") {
                showDashboard(data.admin.email, data.admin.full_name);
            }
            await loadOpportunities();
        }
    } catch (_) {
        // Not logged in — stay on auth page; no action needed
    }
}

// Override showDashboard to also accept full_name
const _originalShowDashboard = typeof showDashboard !== "undefined" ? showDashboard : null;
window.showDashboard = function (email, fullName) {
    if (_originalShowDashboard) _originalShowDashboard(email);

    // Update displayed name with full_name if available
    if (fullName) {
        const dashNameEl   = document.getElementById("dashName");
        const dashAvatarEl = document.getElementById("dashAvatar");
        if (dashNameEl)   dashNameEl.textContent   = fullName;
        if (dashAvatarEl) dashAvatarEl.textContent = fullName.substring(0, 2).toUpperCase();
    }
};

// ─────────────────────────────────────────────────────────────────────────────
//  LOGIN — replace mock handler
// ─────────────────────────────────────────────────────────────────────────────

(function wireLogin() {
    const form = document.getElementById("loginForm");
    if (!form) return;

    // Clone the element to strip existing listeners added by admin.js
    const fresh = form.cloneNode(true);
    form.parentNode.replaceChild(fresh, form);

    fresh.addEventListener("submit", async function (e) {
        e.preventDefault();

        const email    = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value.trim();

        // Client-side CAPTCHA validation is still handled by admin.js state,
        // but we replicate the check here so we can abort early.
        const captchaInput = document.getElementById("loginCaptchaInput").value.trim();
        if (!captchaInput) {
            if (typeof showError === "function") showError("loginCaptchaErr", "Please enter the captcha code.");
            return;
        }
        if (typeof captchas !== "undefined" && captchaInput !== captchas.login) {
            if (typeof showError    === "function") showError("loginCaptchaErr", "Captcha does not match.");
            if (typeof generateCaptcha === "function") generateCaptcha("login");
            return;
        }

        const { ok, data } = await apiRequest("/api/auth/login", "POST", {
            email,
            password,
            remember_me: document.getElementById("rememberMe")?.checked ?? false,
        });

        if (ok && data.success) {
            toast("Login successful! Redirecting...");
            if (typeof generateCaptcha === "function") generateCaptcha("login");
            setTimeout(async () => {
                showDashboard(data.admin.email, data.admin.full_name);
                await loadOpportunities();
            }, 1200);
        } else {
            const errEl = document.getElementById("loginPasswordErr");
            if (errEl) {
                errEl.querySelector("span").textContent = data.message || "Invalid credentials.";
                errEl.classList.add("show");
            }
            if (typeof shakeForm    === "function") shakeForm("loginForm");
            if (typeof generateCaptcha === "function") generateCaptcha("login");
        }
    });
})();

// ─────────────────────────────────────────────────────────────────────────────
//  SIGNUP — replace mock handler
// ─────────────────────────────────────────────────────────────────────────────

(function wireSignup() {
    const form = document.getElementById("signupForm");
    if (!form) return;

    const fresh = form.cloneNode(true);
    form.parentNode.replaceChild(fresh, form);

    fresh.addEventListener("submit", async function (e) {
        e.preventDefault();
        if (typeof clearAllErrors === "function") clearAllErrors("signupForm");

        const full_name        = document.getElementById("signupName").value.trim();
        const email            = document.getElementById("signupEmail").value.trim();
        const password         = document.getElementById("signupPassword").value.trim();
        const confirm_password = document.getElementById("signupConfirmPassword").value.trim();
        const captchaInput     = document.getElementById("signupCaptchaInput").value.trim();

        // CAPTCHA check
        if (!captchaInput) {
            if (typeof showError === "function") showError("signupCaptchaErr", "Please enter the captcha code.");
            return;
        }
        if (typeof captchas !== "undefined" && captchaInput !== captchas.signup) {
            if (typeof showError    === "function") showError("signupCaptchaErr", "Captcha does not match.");
            if (typeof generateCaptcha === "function") generateCaptcha("signup");
            return;
        }

        const { ok, data } = await apiRequest("/api/auth/signup", "POST", {
            full_name, email, password, confirm_password,
        });

        if (ok && data.success) {
            toast("Account created successfully!");
            if (typeof generateCaptcha === "function") generateCaptcha("signup");
            this.reset();
            if (typeof checkStrength === "function") checkStrength("");
            setTimeout(() => {
                if (typeof showPage === "function") showPage("loginPage");
            }, 1500);
        } else {
            toast(data.message || "Signup failed. Please try again.");
            if (typeof shakeForm === "function") shakeForm("signupForm");
        }
    });
})();

// ─────────────────────────────────────────────────────────────────────────────
//  FORGOT PASSWORD — replace mock handler
// ─────────────────────────────────────────────────────────────────────────────

(function wireForgot() {
    const form = document.getElementById("forgotForm");
    if (!form) return;

    const fresh = form.cloneNode(true);
    form.parentNode.replaceChild(fresh, form);

    fresh.addEventListener("submit", async function (e) {
        e.preventDefault();
        if (typeof clearAllErrors === "function") clearAllErrors("forgotForm");

        const email        = document.getElementById("forgotEmail").value.trim();
        const captchaInput = document.getElementById("forgotCaptchaInput").value.trim();

        if (!captchaInput) {
            if (typeof showError === "function") showError("forgotCaptchaErr", "Please enter the captcha code.");
            return;
        }
        if (typeof captchas !== "undefined" && captchaInput !== captchas.forgot) {
            if (typeof showError    === "function") showError("forgotCaptchaErr", "Captcha does not match.");
            if (typeof generateCaptcha === "function") generateCaptcha("forgot");
            return;
        }

        const { ok, data } = await apiRequest("/api/auth/forgot-password", "POST", { email });

        if (ok) {
            toast(data.message || "Reset link sent! Check your terminal (dev mode).");
        } else {
            toast(data.message || "Something went wrong. Please try again.");
        }

        if (typeof generateCaptcha === "function") generateCaptcha("forgot");
        this.reset();
    });
})();

// ─────────────────────────────────────────────────────────────────────────────
//  LOGOUT — replace mock handler
// ─────────────────────────────────────────────────────────────────────────────

(function wireLogout() {
    // The logout button calls handleLogout() directly in admin.js; we override it.
    window.handleLogout = async function () {
        await apiRequest("/api/auth/logout", "POST");
        // Restore auth screen (original admin.js logic)
        document.getElementById("dashboardWrapper")?.classList.remove("active");
        const authWrapper = document.getElementById("authWrapper");
        if (authWrapper) authWrapper.style.display = "flex";
        document.body.style.alignItems = "";
        toast("Signed out successfully.");
        if (typeof showPage === "function") showPage("loginPage");
    };
})();

// ─────────────────────────────────────────────────────────────────────────────
//  OPPORTUNITIES — load from database
// ─────────────────────────────────────────────────────────────────────────────

async function loadOpportunities() {
    const grid = document.querySelector(".opportunities-grid");
    if (!grid) return;

    // Remove any hardcoded demo cards (they have no data-opp-id attribute)
    grid.querySelectorAll(".opportunity-card:not([data-opp-id])").forEach(c => c.remove());

    const { ok, data } = await apiRequest("/api/opportunities");
    if (!ok) return;

    // Clear previously rendered DB cards before re-rendering
    grid.querySelectorAll(".opportunity-card[data-opp-id]").forEach(c => c.remove());

    data.opportunities.forEach(opp => renderOpportunityCard(opp, grid));
}

/** Build and inject a single opportunity card from a DB record. */
function renderOpportunityCard(opp, grid) {
    const skills = (opp.skills_to_gain || "")
        .split(",")
        .map(s => s.trim())
        .filter(Boolean);

    const skillTags = skills
        .map(s => `<span class="skill-tag">${esc(s)}</span>`)
        .join("");

    const applicantsText = opp.max_applicants
        ? `${opp.max_applicants} applicants`
        : "0 applicants";

    const card = document.createElement("div");
    card.className    = "opportunity-card";
    card.dataset.oppId = opp.id;

    card.innerHTML = `
        <div class="opportunity-card-header">
            <h5>${esc(opp.opportunity_name)}</h5>
            <div class="opportunity-meta">
                <span>
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    ${esc(opp.duration)}
                </span>
                <span>
                    <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    ${esc(opp.start_date)}
                </span>
            </div>
        </div>
        <p class="opportunity-description">${esc(opp.description)}</p>
        <div class="opportunity-skills">
            <div class="opportunity-skills-label">Skills You'll Gain</div>
            <div class="skills-tags">${skillTags}</div>
        </div>
        <div class="opportunity-footer">
            <span class="applicants-count">${esc(applicantsText)}</span>
            <div style="display:flex;gap:8px;">
                <button class="view-course-btn opp-view-btn" style="width:auto;padding:8px 16px;">
                    View Details
                </button>
                <button class="view-course-btn opp-edit-btn" style="width:auto;padding:8px 16px;background:var(--accent,#6366f1);"
                    data-opp-id="${opp.id}">
                    Edit
                </button>
                <button class="view-course-btn opp-delete-btn" style="width:auto;padding:8px 16px;background:#ef4444;"
                    data-opp-id="${opp.id}">
                    Delete
                </button>
            </div>
        </div>`;

    // ── View Details ──────────────────────────────────────────────────────────
    card.querySelector(".opp-view-btn").addEventListener("click", () => {
        if (typeof openOpportunityDetails === "function") {
            openOpportunityDetails(opp.opportunity_name, {
                duration: opp.duration,
                startDate: opp.start_date,
                description: opp.description,
                skills: skills,
                applicants: opp.max_applicants || 0,
                futureOpportunities: opp.future_opportunities,
                prerequisites: ''
            });
        }
    });

    // ── Delete ────────────────────────────────────────────────────────────────
    card.querySelector(".opp-delete-btn").addEventListener("click", async () => {
        if (!confirm(`Delete "${opp.opportunity_name}"?`)) return;
        const { ok, data: res } = await apiRequest(`/api/opportunities/${opp.id}`, "DELETE");
        if (ok) {
            card.remove();
            toast(res.message || "Opportunity deleted.");
        } else {
            toast(res.message || "Delete failed.");
        }
    });

    // ── Edit (prefill form) ───────────────────────────────────────────────────
    card.querySelector(".opp-edit-btn").addEventListener("click", () => {
        prefillEditForm(opp);
    });

    grid.appendChild(card);
}

// ─────────────────────────────────────────────────────────────────────────────
//  OPPORTUNITY FORM — Create & Edit
// ─────────────────────────────────────────────────────────────────────────────

let _editingOppId = null;   // null = creating new; number = editing existing

/** Populate the opportunity modal form for editing. */
function prefillEditForm(opp) {
    _editingOppId = opp.id;

    document.getElementById("oppName").value           = opp.opportunity_name || "";
    document.getElementById("oppDuration").value       = opp.duration         || "";
    document.getElementById("oppStartDate").value      = opp.start_date       || "";
    document.getElementById("oppDescription").value    = opp.description      || "";
    document.getElementById("oppSkills").value         = opp.skills_to_gain   || "";
    document.getElementById("oppCategory").value       = opp.category         || "";
    document.getElementById("oppFuture").value         = opp.future_opportunities || "";
    document.getElementById("oppMaxApplicants").value  = opp.max_applicants   || "";

    // Update modal heading if present
    const modalTitle = document.querySelector("#opportunityModal h3, #opportunityModal .modal-title");
    if (modalTitle) modalTitle.textContent = "Edit Opportunity";

    if (typeof openOpportunityModal === "function") openOpportunityModal();
}

(function wireOpportunityForm() {
    const form = document.getElementById("opportunityForm");
    if (!form) return;

    const fresh = form.cloneNode(true);
    form.parentNode.replaceChild(fresh, form);

    fresh.addEventListener("submit", async function (e) {
        e.preventDefault();

        const payload = {
            opportunity_name:     document.getElementById("oppName").value.trim(),
            duration:             document.getElementById("oppDuration").value.trim(),
            start_date:           document.getElementById("oppStartDate").value,
            description:          document.getElementById("oppDescription").value.trim(),
            skills_to_gain:       document.getElementById("oppSkills").value.trim(),
            category:             document.getElementById("oppCategory").value,
            future_opportunities: document.getElementById("oppFuture").value.trim(),
            max_applicants:       document.getElementById("oppMaxApplicants").value.trim() || null,
        };

        if (!payload.opportunity_name || !payload.duration || !payload.start_date ||
            !payload.description || !payload.skills_to_gain || !payload.category ||
            !payload.future_opportunities) {
            toast("Please fill all required fields.");
            return;
        }

        let result;
        if (_editingOppId) {
            // UPDATE
            result = await apiRequest(`/api/opportunities/${_editingOppId}`, "PUT", payload);
        } else {
            // CREATE
            result = await apiRequest("/api/opportunities", "POST", payload);
        }

        const { ok, data } = result;

        if (ok && data.success) {
            toast(data.message);
            if (typeof closeOpportunityModal === "function") closeOpportunityModal();
            this.reset();
            _editingOppId = null;

            // Reset modal title
            const modalTitle = document.querySelector("#opportunityModal h3, #opportunityModal .modal-title");
            if (modalTitle) modalTitle.textContent = "Add New Opportunity";

            // Reload from DB
            await loadOpportunities();
        } else {
            toast(data.message || "Operation failed. Please try again.");
        }
    });

    // Reset edit state when modal is closed
    const modal = document.getElementById("opportunityModal");
    if (modal) {
        modal.addEventListener("click", function (ev) {
            if (ev.target === this) {
                _editingOppId = null;
                const modalTitle = document.querySelector("#opportunityModal h3, #opportunityModal .modal-title");
                if (modalTitle) modalTitle.textContent = "Add New Opportunity";
            }
        });
    }
})();

// ─────────────────────────────────────────────────────────────────────────────
//  NAV — reload opportunities when "opportunity" section is activated
// ─────────────────────────────────────────────────────────────────────────────

document.querySelectorAll(".nav-item[data-page]").forEach(item => {
    item.addEventListener("click", async function () {
        if (this.getAttribute("data-page") === "opportunity") {
            await loadOpportunities();
        }
    });
});

// ─────────────────────────────────────────────────────────────────────────────
//  INIT — run session check on page load
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    checkExistingSession();
});
