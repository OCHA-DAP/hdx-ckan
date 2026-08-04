# 052 — Signup Flow: v2 Migration

**Scope IN:** Tiers (value-proposition) page, user-info form (step 1), verify-email page (step 2), change-email page (step 2b), account-validated page (step 3) — all migrated to v2.
**Scope OUT:** Backend signup logic, authentication flow, newsletter/Mailchimp integration internals.

---

## Context

The HDX signup flow consists of a tier selection page (value proposition) followed by a 3-step multi-step form: user details, email verification, and account confirmation. All pages currently use v1 BEM components, Bootstrap classes, and the legacy `hdx-form-validator` CKAN module.

This task migrates all five signup pages to v2: replacing BEM components with v2 snippets (`c-search-input`, `c-checkbox`, `c-button`), introducing two new v2 components (`c-signup-tier`, `c-step-pager`), adopting `v2/form-validator.js`, and updating validation styling to v2 design tokens. No backend logic changes.

---

## 1. Existing Signup Audit

### 1.1 Templates

| Template | Role | Step |
|---|---|---|
| `templates/onboarding/signup/value-proposition.html` | Three tier cards — pre-step choice | Pre-step |
| `templates/onboarding/signup/user-info.html` | Form: name, email×2, username, password×2, checkboxes, reCAPTCHA | Step 1 |
| `templates/onboarding/signup/verify-email.html` | Email confirmation waiting page | Step 2 |
| `templates/onboarding/signup/change-email.html` | Re-enter email form on step 2 | Step 2b |
| `templates/onboarding/signup/account-validated.html` | Success page with analytics metadata | Step 3 |
| `templates/bem.blocks/stepper.html` | v1 step indicator (BEM, to be replaced) | All |
| `templates/bem.blocks/input_field.html` | v1 form input with password toggle | Step 1, Step 2b |
| `templates/bem.blocks/checkbox_field.html` | v1 checkbox | Step 1 |
| `templates/bem.blocks/form_button.html` | v1 buttons | All |

Constants (string copy, button labels, step names) are externalised in:
- `ckanext/hdx_theme/helpers/ui_constants/onboarding/value_proposition.py`
- `ckanext/hdx_theme/helpers/ui_constants/onboarding/user_info.py`
- `ckanext/hdx_theme/helpers/ui_constants/onboarding/verify_email.py`
- `ckanext/hdx_theme/helpers/ui_constants/onboarding/change_email.py`
- `ckanext/hdx_theme/helpers/ui_constants/onboarding/account_validated.py`

### 1.2 Step Flow (server-driven, session-based)

```
GET  /signup/                            → value-proposition.html
GET  /signup/user-info/                  → user-info.html (form display)
POST /signup/user-info/                  → onboarding.py: creates/activates user, sends email, redirects
GET  /signup/verify-email/<user_id>/     → verify-email.html
GET  /signup/change-email/               → change-email.html
POST /signup/change-email/               → updates email, re-sends verification
GET  /signup/validate-account/<token>/   → validates token, activates account, redirects
GET  /signup/validated-account/<user_id>/→ account-validated.html
```

- State stored in Flask session: `session['user_info_id']`, `session['user_info_email']`
- All step transitions are HTTP redirects — no client-side routing
- Shadow user activation path supported (invited users)
- View code: `ckanext-hdx_users/ckanext/hdx_users/views/onboarding.py`

### 1.3 Validation System

**v1 (current on signup):** `fanstatic/hdx-form-validator.js` — initialised as a CKAN module via `data-module="hdx-form-validator"` on the `<form>` element.

**v2 (available, must adopt):** `fanstatic/v2/form-validator.js` — vanilla JS, initialised via `initFormValidator(form)`. Validation rules are identical to v1.

Data attributes (shared between v1 and v2):
```html
data-validation="username|email|password|fullname|match|checkbox"
data-validation-match="field-id"      <!-- id of field to compare against -->
data-live-feedback="true"             <!-- enables real-time feedback list -->
data-validation-error="Error message" <!-- message shown on error -->
```

CSS differences:
- v1: adds `.is-invalid` to `<input>`, uses Bootstrap `.text-danger`/`.text-success`
- v2: adds `.c-search-input--error` to the `.c-search-input` wrapper; uses `.c-form-validator__live-feedback` list with `.--pass` / `.--fail` item modifiers

Submit button behaviour: starts disabled (rendered with `disabled` attr or `button_disabled=True`); enabled by the validator only when all rules pass. This must be preserved.

Python server-side schema: `ckanext-hdx_users/ckanext/hdx_users/logic/schema.py` — `onboarding_user_new_form_schema()`, `onboarding_user_change_email_form_schema()`.

### 1.4 Analytics Tracking

**Tier selection (value-proposition.html) — client-side:**
```html
<!-- Wraps each tier CTA -->
<div data-module="hdx_click_stopper"
     data-module-link_type="onboarding value proposition"
     data-module-label="no account"
     data-module-just_send_event="true"
     data-module-selector="#search-data-btn">
```
Label values per tier: `"no account"` | `"individual account"` | `"individual account with org"`.
Fires `hdxUtil.analytics.sendLinkClickEvent` — **must be preserved verbatim on v2 page**.

**Account activation — server-side:**
- `EmailValidationAnalyticsSender` in `ckanext-hdx_users/ckanext/hdx_users/helpers/analytics.py`
- Tracks: `validation_type`, `validation_status`, `email_hash`, `authenticated`

**Account type metadata (account-validated.html):**
```jinja2
{% block analytics_account_type %}{{ analytics_account_type }}{% endblock %}
```
Values: `'new'` | `'shadow'` | `'validation failed'` | `'already validated'`. Must be preserved in v2 block.

**Onboarding flow tracker:** `fanstatic/hdx-onboarding-flow.js`
Tracks `start_page_type`, `start_page_additional_params`, `value_proposition_page` via `hdxUtil.net.updateOnboardingFlowData()`. Loaded on the tiers page and must remain.

### 1.5 Password Toggle

**v1:** `fanstatic/onboarding/toggle-password-visibility.js` — on click, swaps `input.type` between `'password'` and `'text'`; toggles `.fa-eye` / `.fa-eye-slash` visibility via `.d-none`.

**v2:** `fanstatic/v2/components/input-field.js` handles password toggle automatically for any `.c-search-input` wrapper containing `<input type="password">`. The eye SVG is rendered by the `v2/components/search-input.html` snippet when `type='password'` is passed. No extra JS needed.

**Decision:** `toggle-password-visibility.js` must **not** be included in the v2 bundle — the `c-search-input` component covers it entirely.

### 1.6 Existing Pager / Stepper

**v1 (current):** `templates/bem.blocks/stepper.html`
```jinja2
{{ h.snippet('bem.blocks/stepper.html',
    steps=[CONST.STEPS_1, CONST.STEPS_2, CONST.STEPS_3],
    spacing_class="my-5",
    current_step=1) }}
```
BEM classes: `.stepper`, `.stepper__item`, `.stepper__item_state_completed`, `.stepper__item_state_active`, `.stepper__counter`, `.stepper__name`.
Uses legacy color variables (`@blue-color`, `@grey-color`). **Must not be reused in v2.**

**v2:** Does not exist. Must be created as `c-step-pager`.

### 1.7 Asset Bundles (webassets.yml)

Current bundles used by signup pages:
- `hdx-form-validator` → `hdx-form-validator.js`
- `hdx-onboarding-scripts` → `came-from-input.js`, `confirm-page-leave.js`, `toggle-password-visibility.js`
- `hdx-verify-email-scripts` → `verify-email.js`
- `bem-blocks-styles` → all BEM CSS
- `bem-blocks-scripts` → BEM JS

v2 pages will need a new bundle (see §8.3).

---

## 2. Figma Mapping

### 2.1 Tiers Page (`signup-tier-xl/md/sm.html`)

| Element | Figma value | v2 token |
|---|---|---|
| Page background | `#fafbfb` | `var(--hdx-neutral-01)` |
| Card 1 & 3 background | `#fafbfb` + `1px solid #ebeff0` | `var(--hdx-neutral-01)` + `1px solid var(--hdx-neutral-1)` |
| Card 2 background (primary) | `#1862d8` | `var(--hdx-primary-5)` |
| Card 2 text | `#ffffff` | `var(--hdx-neutral-0)` |
| Card padding XL | `32px` | `var(--hdx-space-8)` |
| Card padding MD/SM | `24px` | `var(--hdx-space-6)` |
| Card gap XL/MD | `20px` | `var(--hdx-space-5)` |
| Card gap SM | `16px` | `var(--hdx-space-4)` |
| Card border-radius | `2px` | `var(--hdx-br-1)` |
| Card shadow | `0 1px 4px rgba(0,0,0,0.04)` | `var(--hdx-shadow-drop)` |
| Feature item | checkmarks in Figma → **numbered per brief** | numbered badge circle + text |
| Card 1 & 3 CTA button | blue background | `c-button --primary --size-m` |
| Card 2 CTA button | white bg, blue border | `c-button --secondary --size-m` |
| Page title font | Merriweather bold, 28px XL / 24px MD / 20px SM | `.hdx-display-s()` or similar display mixin |

**Layout:**
- XL + MD: 3-column flex row, equal width
- SM: single-column stack

### 2.2 Form Page (`signup-form-xl/md/sm.html`)

| Element | Figma value | v2 component |
|---|---|---|
| Step pager | 32px circles, 2px border, horizontal connecting lines | `c-step-pager` (new) |
| Active step badge | white bg, `#0162dd` border, bold number | `.c-step-pager__badge--active` |
| Inactive step badge | `#ccc` bg + border | default state |
| Step labels | visible XL/MD, hidden SM | responsive CSS |
| Page title | Merriweather, 2rem / 1.75rem / 1.5rem | `.hdx-display-s()` |
| Mandatory note ("* indicates mandatory fields") | body-s | `.hdx-body-s()` |
| Text input | 37px height, 1px gainsboro border, 2px radius | `c-search-input --size-m` |
| Password field | same + eye-off SVG toggle | `c-search-input --size-m` with `type='password'` |
| Required asterisk | `#c44536` | `var(--hdx-error-5)` via snippet's `required` param |
| Checkbox | 20px × 20px | `c-checkbox` |
| Cancel button | white bg, border | `c-button --secondary --size-m` |
| Submit button | `#1862d8` bg, white text | `c-button --primary --size-m` |
| reCAPTCHA widget | 302px × 76px | preserved as-is |
| Form container max-width | 580px centered | custom wrapper LESS |
| Top padding XL | `6rem` | `var(--hdx-space-12)` (adjust to match) |
| Top padding MD/SM | `2rem` / `1.5rem` | `var(--hdx-space-8)` / `var(--hdx-space-6)` |

### 2.3 Gaps vs v1

| Gap | v1 | v2 required |
|---|---|---|
| Pager component | BEM `.stepper` | `c-step-pager` with v2 tokens |
| Tier card | inline HTML in template | `c-signup-tier` snippet |
| Feature list icons | Font Awesome checkmarks | numbered badge circle |
| Validation error styling | Bootstrap `.is-invalid`, red border | `.c-search-input--error`, `var(--hdx-error-5)` |
| Input component | `bem.blocks/input_field.html` | `v2/components/search-input.html` |
| Checkbox | `bem.blocks/checkbox_field.html` | `v2/components/checkbox.html` |
| Buttons | `bem.blocks/form_button.html` | `v2/components/button.html` |
| Password toggle JS | `toggle-password-visibility.js` + fa-eye | `v2/components/input-field.js` (automatic) |
| Form validator | `hdx-form-validator.js` (CKAN module) | `v2/form-validator.js` (vanilla JS) |

---

## 3. Component Strategy

### 3.1 NEW: `c-signup-tier`

**Template:** `templates/v2/components/signup-tier.html`
**LESS:** `hdx-styles/src/common/less/v2/components/signup-tier.less`

Purpose: Reusable tier card for the value-proposition page. Handles two visual variants (default gray, primary blue), renders a numbered feature list, and accepts analytics data attributes for the CTA wrapper.

**API:**

| Prop | Type | Default | Notes |
|---|---|---|---|
| `title` | string | required | Card heading (Merriweather) |
| `description` | string | required | Body subtext |
| `features` | list of `{number, text}` | required | Numbered feature list items |
| `button_label` | string | `''` | CTA button text; omit for footer-text-only card |
| `button_href` | string | `''` | CTA button URL |
| `button_style` | `'primary'` \| `'secondary'` | `'primary'` | Primary card uses `'secondary'` (inverted on blue) |
| `variant` | `'default'` \| `'primary'` | `'default'` | `'primary'` = blue background |
| `footer_text` | string | `''` | Explanatory text below button (tier 3 only) |
| `analytics_wrapper_attrs` | string | `''` | Raw HTML data attributes for `hdx_click_stopper` wrapper |

**Example usage (tier 1):**
```jinja2
{% set features = [
  {'number': 1, 'text': 'Access all public humanitarian datasets'},
  {'number': 2, 'text': 'Use data visualisation tools'},
  {'number': 3, 'text': 'No registration required'},
] %}
{{ h.snippet('v2/components/signup-tier.html',
    title='Search and download data',
    description='Explore and use thousands of datasets on HDX without an account',
    features=features,
    button_label='Search Data',
    button_href=h.url_for('dataset.search'),
    button_style='primary',
    variant='default',
    analytics_wrapper_attrs='data-module="hdx_click_stopper" data-module-link_type="onboarding value proposition" data-module-label="no account" data-module-just_send_event="true" data-module-selector="#search-data-btn"') }}
```

**CSS structure:**
```less
.c-signup-tier {
  // default: neutral-01 bg, neutral-1 border, shadow-drop
}
.c-signup-tier--primary {
  // blue bg (var(--hdx-primary-5)), white text
}
.c-signup-tier__title { .hdx-display-xs(); }
.c-signup-tier__description { .hdx-body-m(); }
.c-signup-tier__features { list-style: none; }
.c-signup-tier__feature { display: flex; align-items: flex-start; gap: var(--hdx-space-3); }
.c-signup-tier__feature-number {
  // Bespoke div — styled entirely in signup-tier.less; no c-label dependency
  // 24px circle, primary-5 bg, white text, font-weight bold
  // on --primary variant: white bg, primary-5 text
}
.c-signup-tier__feature-text { .hdx-body-m(); }
.c-signup-tier__footer { .hdx-body-s(); color: var(--hdx-neutral-6); }
```

### 3.2 NEW: `c-step-pager`

**Template:** `templates/v2/components/step-pager.html`
**LESS:** `hdx-styles/src/common/less/v2/components/step-pager.less`

Purpose: Horizontal 3-step progress indicator shown at the top of all signup form pages. Pure Jinja + CSS — no JavaScript.

**API:**

| Prop | Type | Default | Notes |
|---|---|---|---|
| `steps` | list of strings | required | Step label text (e.g. `['Personal details', 'Verify email', 'Account created']`) |
| `current_step` | integer (1-based) | required | Index of the currently active step |

**States** (derived in template from `loop.index` vs `current_step`):
- `loop.index < current_step` → completed: blue filled circle with checkmark icon, blue connecting line
- `loop.index == current_step` → active: white bg circle, 2px blue border, bold number
- `loop.index > current_step` → inactive: neutral-2 bg circle, neutral-2 border, normal number

**Jinja structure:**

A `<div class="c-step-pager__connector">` is inserted between each step. When `loop.index <= current_step` the connector also receives the `--filled` modifier. No inline style or CSS custom property is used.

```jinja2
<div class="c-step-pager">
  {% for step in steps %}
    {% if not loop.first %}
      <div class="c-step-pager__connector{% if loop.index <= current_step %} c-step-pager__connector--filled{% endif %}"></div>
    {% endif %}
    {% set state = 'completed' if loop.index < current_step else 'active' if loop.index == current_step else '' %}
    <div class="c-step-pager__step{% if state %} c-step-pager__step--{{ state }}{% endif %}">
      <div class="c-step-pager__badge">{{ loop.index }}</div>
      <div class="c-step-pager__label">{{ step }}</div>
    </div>
  {% endfor %}
</div>
```

**CSS structure:**

Connectors are real DOM elements that flex-grow between steps. The `--filled` modifier switches the background from neutral to primary.

```less
.c-step-pager {
    display:     flex;
    align-items: flex-start;
    width:       100%;

    &__connector {
        flex:       1;
        height:     2px;
        margin-top: calc(var(--hdx-space-8) / 2 - 1px);
        background: var(--hdx-neutral-2);
        min-width:  var(--hdx-space-4);

        &--filled {
            background: var(--hdx-primary-5);
        }
    }

    &__step {
        display:        flex;
        flex-direction: column;
        align-items:    center;
        gap:            var(--hdx-space-2);
        flex-shrink:    0;
    }

    &__badge {
        width:         var(--hdx-space-8);
        height:        var(--hdx-space-8);
        border-radius: 50%;
        border:        2px solid var(--hdx-neutral-2);
        background:    var(--hdx-neutral-2);
        color:         var(--hdx-neutral-4);
        display:       flex;
        align-items:   center;
        justify-content: center;
        box-sizing:    border-box;
        .hdx-body-m-semibold();

        .c-step-pager__step--active & {
            background:   var(--hdx-neutral-0);
            border-color: var(--hdx-primary-5);
            color:        var(--hdx-primary-5);
        }

        .c-step-pager__step--completed & {
            background:   var(--hdx-primary-5);
            border-color: var(--hdx-primary-5);
            color:        var(--hdx-neutral-0);
        }
    }

    &__label {
        .hdx-body-xs();
        color:       var(--hdx-neutral-4);
        text-align:  center;
        white-space: nowrap;
        display:     none;

        @media (min-width: @hdx-bp-md) { display: block; }

        .c-step-pager__step--active &    { color: var(--hdx-primary-5); }
        .c-step-pager__step--completed & { color: var(--hdx-neutral-6); }
    }
}
```

### 3.3 REUSED Components

| Component | Snippet | Notes |
|---|---|---|
| Button | `v2/components/button.html` | `--primary` (submit), `--secondary` (cancel), `--size-m` |
| Input | `v2/components/search-input.html` | `type='password'` auto-adds eye toggle |
| Checkbox | `v2/components/checkbox.html` | terms (required) + newsletter (optional) |
| Form validator | `fanstatic/v2/form-validator.js` | replaces v1 `hdx-form-validator.js` |
| Input field JS | `fanstatic/v2/components/input-field.js` | password toggle + clear |

---

## 4. Form Integration Strategy

The existing form `action` URL, CSRF token hidden input, all field `name` attributes, and the reCAPTCHA `div#g-recaptcha` are **unchanged**. Only the markup structure changes.

| v1 element | v2 replacement |
|---|---|
| `{% snippet 'bem.blocks/input_field.html', name=..., id=..., data_attributes=... %}` | `{% snippet 'v2/components/search-input.html', name=..., id=..., input_attrs=... %}` |
| `{% snippet 'bem.blocks/checkbox_field.html', name=..., id=... %}` | `{% snippet 'v2/components/checkbox.html', name=..., id=... %}` |
| `{% snippet 'bem.blocks/form_button.html', ... %}` | `{% snippet 'v2/components/button.html', ... %}` |
| `{% snippet 'bem.blocks/stepper.html', steps=..., current_step=... %}` | `{% snippet 'v2/components/step-pager.html', steps=..., current_step=... %}` |
| `data-module="hdx-form-validator"` on `<form>` | removed; `initFormValidator()` called in new v2 bundle |

The `data-validation`, `data-validation-match`, `data-live-feedback`, `data-validation-error` attributes are forwarded through the v2 snippet's `input_attrs` parameter.

**reCAPTCHA:** The `<div id="recaptcha-widget">` and reCAPTCHA script block must be reproduced verbatim inside the v2 form block. The existing reCAPTCHA token injection JS must still be able to find `#recaptcha-widget`.

---

## 5. Validation Styling Strategy

| v1 class / style | v2 replacement |
|---|---|
| `.is-invalid` on `<input>` | `.c-search-input--error` on `.c-search-input` wrapper (emitted by `v2/form-validator.js`) |
| `border-color: red` / Bootstrap danger | `border-color: var(--hdx-error-5)` (handled by `.c-search-input--error` LESS) |
| `.text-danger` error message | `.c-search-input__error` span, color `var(--hdx-error-6)` |
| `.text-success` live feedback item | `.c-form-validator__live-feedback-item--pass`, color `var(--hdx-success-6)` |
| `.text-danger` live feedback item | `.c-form-validator__live-feedback-item--fail`, color `var(--hdx-error-5)` |
| `.fa-check` / `.fa-minus` in live feedback | SVG icons resolved by `v2/form-validator.js` via `--pass` / `--fail` item class |

`v2/form-validator.js` emits all v2 class names. It was updated as part of this task: removed `.c-drawer-form__field-error` references (consolidated into `c-search-input__error`), added `c-checkbox--error` support, dropped dead `.input-field` selector from `scrollToError`.
The v1 `hdx-form-validator` bundle must **not** be included on v2 pages.

---

## 6. Rendering Strategy

All five signup templates extend `v2/page.html` directly — no v1 fallback, no `{% if v2 %}` gate. Layout variables are set at the top of each template (read by `v2/page.html` as Jinja2 variables, not blocks):

```jinja2
{% extends "v2/page.html" %}
{% set outer_row_class      = 'hdx-v2-signup-outer-row' %}
{% set breadcrumb_row_class = 'hdx-v2-breadcrumb-row--white' %}
{% set content_class        = 'hdx-v2-content-columns__content' %}
```

### 6.1 value-proposition.html

Replace the `.account-options` grid with a flex row of three `c-signup-tier` snippets.
The `data-module="hdx_click_stopper"` wrapper divs must surround each tier's CTA button, preserving all existing `data-module-*` attributes.

```jinja2
<div class="hdx-v2-signup-tiers-page">
  <h1 class="hdx-v2-signup-tiers-page__heading">{{ CONST.PAGE_TITLE }}</h1>
  <div class="hdx-v2-signup-tiers-page__tiers">
    {# Each c-signup-tier snippet receives attrs={} for hdx_click_stopper analytics #}
    {% snippet 'v2/components/signup-tier.html',
        title=CONST.COLUMN_NO_ACCOUNT_LABEL,
        features=[{'text': ...}, ...],
        button_label=CONST.COLUMN_NO_ACCOUNT_BUTTON,
        button_style='primary',
        button_tag='a',
        button_href=h.url_for('dataset.search'),
        attrs={'data-module': 'hdx_click_stopper', ...} %}
    {# Tier 2: Individual Account (primary) ... #}
    {# Tier 3: Share Data (with numbered steps) ... #}
  </div>
  <p class="hdx-v2-signup-tiers-page__login">...</p>
</div>
```

The `CONST.ACCOUNT_OPTIONS_*_FEATURES` lists must be updated in `value_proposition.py` to use `{number, text}` dicts instead of plain strings, since the v2 tier card renders numbered badges.

### 6.2 user-info.html (Step 1)

```jinja2
<div class="hdx-v2-signup-form-page">
  {% snippet 'v2/components/step-pager.html',
      steps=[CONST.STEPS_1, CONST.STEPS_2, CONST.STEPS_3],
      current_step=1 %}

  <form id="user-info-form"
        class="hdx-v2-signup-form-page__card"
        method="post"
        action="{{ h.url_for('hdx_user_onboarding.user-info') }}"
        novalidate
        data-hdx-v2-form-validator>
    {{ h.csrf_input() }}
    <input type="hidden" name="came_from" id="came-from-input" value="">

    <h1 class="hdx-v2-signup-form-page__heading">{{ CONST.PAGE_TITLE }}</h1>
    <p class="hdx-v2-signup-form-page__mandatory-note">{{ CONST.MANDATORY_HELP }}</p>

    <div class="hdx-v2-signup-form-page__fields">
      {# Each field wrapped in c-form-field for consistent label+input+error spacing #}
      <div class="c-form-field">
        {% snippet 'v2/components/search-input.html',
            type='text', label=CONST.INPUT_FULLNAME_LABEL, required=True,
            name='fullname', value=data.get('fullname', ''),
            show_icon=False, errors=errors.get('fullname'),
            input_attrs={'data-validation': 'fullname', 'data-validation-error': CONST.INPUT_FULLNAME_ERROR} %}
      </div>
      {# … remaining fields follow the same c-form-field wrapper pattern … #}
    </div>

    <div class="hdx-v2-signup-form-page__checkbox-group">
      <div class="hdx-v2-signup-form-page__checkbox-row">
        {% snippet 'v2/components/checkbox.html',
            id='user_info_accept_terms', name='user_info_accept_terms', required=True,
            label=CONST.CHECKBOX_TERMS_OF_SERVICE.format(…),
            attrs={'data-validation': 'checkbox', 'data-validation-error': CONST.CHECKBOX_TERMS_OF_SERVICE_ERROR} %}
      </div>
    </div>

    {% if g.recaptcha_publickey %}
      <div class="g-recaptcha" data-sitekey="{{ g.recaptcha_publickey }}"></div>
    {% endif %}

    <div class="hdx-v2-signup-form-page__actions">
      {% snippet 'v2/components/button.html', label=CONST.BUTTON_CANCEL, style='tertiary',
          size='l', tag='a', href=h.url_for('home.index'), id='user-info-cancel-button' %}
      {% snippet 'v2/components/button.html', label=CONST.BUTTON_SUBMIT, style='primary',
          size='l', state='disabled', button_type='submit', id='user-info-submit-button' %}
    </div>
  </form>
</div>
```

> **Note:** `id="user-info-form"` on the `<form>`, `id="user-info-cancel-button"` and `id="user-info-submit-button"` on the respective buttons are **required** — `onboarding/confirm-page-leave.js` targets these IDs.

### 6.3 verify-email.html (Step 2)

```jinja2
<div class="hdx-v2-signup-form-page">
  {% snippet 'v2/components/step-pager.html',
      steps=[CONST.STEPS_1, CONST.STEPS_2, CONST.STEPS_3],
      current_step=2 %}
  <div class="hdx-v2-signup-form-page__card">
    <h1 class="hdx-v2-signup-form-page__heading">{{ CONST.PAGE_TITLE }}</h1>
    <p class="hdx-v2-signup-form-page__body-text">{{ main_text }}</p>
    {# "change email" link rendered as __body-text paragraph if user_info_id is set #}
  </div>
</div>
```

JS preserved: `confirm-page-leave.js` (back-button prevention), `verify-email.js` (polling or state checks). These work by presence of DOM elements they target — no class changes needed.

### 6.4 change-email.html (Step 2b)

```jinja2
<div class="hdx-v2-signup-form-page">
  {% snippet 'v2/components/step-pager.html',
      steps=[CONST.STEPS_1, CONST.STEPS_2, CONST.STEPS_3],
      current_step=2 %}

  <form class="hdx-v2-signup-form-page__card"
        method="post"
        action="{{ h.url_for('hdx_user_onboarding.change_email') }}"
        novalidate
        data-hdx-v2-form-validator>
    {{ h.csrf_input() }}
    <h1 class="hdx-v2-signup-form-page__heading">{{ CONST.PAGE_TITLE }}</h1>
    <div class="hdx-v2-signup-form-page__fields">
      <div class="c-form-field">
        {% snippet 'v2/components/search-input.html',
            type='email', label=CONST.INPUT_EMAIL_LABEL, required=True,
            name='email', show_icon=False, errors=errors.get('email'),
            input_attrs={'data-validation': 'email', 'data-validation-error': CONST.INPUT_EMAIL_ERROR} %}
      </div>
      <div class="c-form-field">
        {% snippet 'v2/components/search-input.html',
            type='email', label=CONST.INPUT_EMAIL2_LABEL, required=True,
            name='email2', show_icon=False, errors=errors.get('email2'),
            input_attrs={'data-validation': 'email,match', 'data-validation-match': 'email', ...} %}
      </div>
    </div>
    <div class="hdx-v2-signup-form-page__actions">
      {% snippet 'v2/components/button.html', label=CONST.BUTTON_SUBMIT, style='primary',
          size='l', state='disabled', button_type='submit' %}
    </div>
  </form>
</div>
```

### 6.5 account-validated.html (Step 3)

```jinja2
{% if analytics %}
  {% block analytics_account_type %}{{ analytics.analytics_account_type }}{% endblock %}
{% endif %}
{# …styles/scripts blocks… #}
<div class="hdx-v2-signup-form-page">
  {% snippet 'v2/components/step-pager.html',
      steps=[CONST.STEPS_1, CONST.STEPS_2, CONST.STEPS_3],
      current_step=3 %}
  <div class="hdx-v2-signup-form-page__card">
    <h1 class="hdx-v2-signup-form-page__heading">{{ title }}</h1>
    <div class="hdx-v2-signup-form-page__actions">
      {% snippet 'v2/components/button.html', label=CONST.BUTTON_SUBMIT,
          style='primary', size='l', tag='a', href=h.url_for('hdx_signin.login') %}
    </div>
  </div>
</div>
```

The `{% block analytics_account_type %}` block must be reproduced inside the v2 block. This is read by server-side analytics middleware and must not be removed.

---

## 7. Responsive Strategy

| Breakpoint | Tiers layout | Form container | Pager labels |
|---|---|---|---|
| XL (≥ 1280px / `@hdx-bp-xl`) | 3-column flex row, `var(--hdx-space-8)` card padding | max-width 580px, centred, 6rem top pad | Visible |
| MD (768px–1280px / `@hdx-bp-md` to `@hdx-bp-xl`) | 3-column flex row, `var(--hdx-space-6)` card padding | max-width 580px, centred, 2rem top pad | Visible |
| SM (< 768px / `@hdx-bp-md`) | Single-column stack, `var(--hdx-space-6)` card padding | Full width, `var(--hdx-space-6)` top pad | Hidden (`display: none`) |

Tier card layout LESS (`hdx-styles/src/common/less/v2/signup-page.less`):
```less
.hdx-v2-signup-tiers-page__tiers {
  display: flex;
  gap: var(--hdx-space-4);

  @media (min-width: @hdx-bp-md) { flex-direction: row; align-items: stretch; }
  @media (min-width: @hdx-bp-xl) { gap: var(--hdx-space-5); }
}
.c-signup-tier { flex: 1; }  // c-signup-tier is a reusable component — c- prefix correct
```

Form container LESS:
```less
.hdx-v2-signup-form-page {
  // See hdx-styles/src/common/less/v2/signup-page.less for full responsive rules.
  // __card child handles the centred max-width column (50% at XL, 80% at MD, 100% at SM).
}
```

---

## 8. Files Affected

### 8.1 New Templates
- `ckanext/hdx_theme/templates/v2/components/step-pager.html`
- `ckanext/hdx_theme/templates/v2/components/signup-tier.html`

### 8.2 New LESS
- `hdx-styles/src/common/less/v2/components/step-pager.less`
- `hdx-styles/src/common/less/v2/components/signup-tier.less`

### 8.3 Modified LESS
- `hdx-styles/src/common/less/v2/components/index.less` — add imports:
  ```less
  @import 'step-pager';
  @import 'signup-tier';
  ```

### 8.4 Modified Templates (add `{% if v2 %}` blocks)
- `templates/onboarding/signup/value-proposition.html`
- `templates/onboarding/signup/user-info.html`
- `templates/onboarding/signup/verify-email.html`
- `templates/onboarding/signup/change-email.html`
- `templates/onboarding/signup/account-validated.html`

### 8.5 Modified Constants (update feature lists)
- `ckanext/hdx_theme/helpers/ui_constants/onboarding/value_proposition.py`
  Update `ACCOUNT_OPTIONS_*_FEATURES` from plain string lists to `[{'number': N, 'text': '...'}]` dicts.

### 8.6 Modified webassets.yml

New bundles added. `v2-form-validator-scripts` already existed — no changes to it needed.
`toggle-password-visibility.js` is dropped entirely (handled by `v2/components/input-field.js`).

```yaml
# All 5 signup pages
v2-signup-page-styles:
  output: v2-signup-page-styles.css
  contents:
    - v2/signup-page.css

# Step 1 (user-info) and Step 2b (change-email) form pages
v2-signup-scripts:
  output: v2-signup-scripts.js
  contents:
    - onboarding/came-from-input.js    # converted to vanilla JS in place
    - onboarding/confirm-page-leave.js # converted to vanilla JS in place

# Step 2 (verify-email) page uses the pre-existing hdx-verify-email-scripts bundle unchanged
```

`v2/components/input-field.js` is already in `v2-components-scripts` (loaded via the preload chain from `v2-page-scripts`).

### 8.7 Vanilla JS conversions (onboarding scripts)

Two existing scripts were rewritten in place (no `v2/onboarding/` subdirectory created). `verify-email.js` was not rewritten — the legacy `hdx-verify-email-scripts` bundle is used as-is.

| File | Action | Notes |
|---|---|---|
| `fanstatic/onboarding/came-from-input.js` | Converted in place to vanilla JS | Targets `#came-from-input`; calls `hdxUtil.net.getOnboardingFlowData()` |
| `fanstatic/onboarding/confirm-page-leave.js` | Converted in place to vanilla JS | Targets `#user-info-form`, `#user-info-cancel-button`, `#user-info-submit-button` |
| `fanstatic/onboarding/verify-email.js` | Not rewritten — legacy bundle used | `hdx-verify-email-scripts` loaded on verify-email page as-is |
| `fanstatic/onboarding/toggle-password-visibility.js` | Dropped from v2 bundles | Handled by `v2/components/input-field.js` via `.c-search-input` |

---

## 9. Edge Cases

1. **Server-rendered validation errors:** When the server returns field errors (e.g. "username already taken"), the v2 form must render them via the `errors` parameter of `v2/components/search-input.html`, which populates `.c-search-input__error`. Verify `error_dict` is forwarded correctly to the v2 block.

2. **Submit button disabled on error re-render:** When the form is re-rendered after a server error, the submit button should remain disabled (restart client-side validation). Confirm `v2/form-validator.js` re-initialises on page load.

3. **reCAPTCHA failure:** The reCAPTCHA response field and error display must remain addressable by existing reCAPTCHA JS. Keep `<div id="recaptcha-widget">` and surrounding structure identical to v1.

4. **Long error messages:** `.c-search-input__error` must wrap gracefully — do not constrain to single line. Test with maximum-length server error messages.

5. **Shadow user activation:** The `account-validated.html` v2 block must correctly branch on `analytics_account_type` value. The `{% block analytics_account_type %}` must be inside the v2 block, not outside.

6. **Back-button prevention on step 2:** `confirm-page-leave.js` uses `history.pushState` and the `popstate` event — it targets the verify-email page by URL pattern, not DOM class. No change required, but confirm it still fires on v2 page.

7. **Tier 3 no-button case:** The "Share data" tier has no CTA button — only a footer text paragraph. The `c-signup-tier` snippet must render cleanly when `button_label` is empty.

8. **Feature list length mismatch across tiers:** All three tiers should have the same number of feature items for visual alignment. Confirm with design if heights must be equal across cards.

---

## 10. Decisions Taken

**D1. `c-step-pager` connector layout** → **Connector `<div>` elements with `--filled` modifier.**
One `<div class="c-step-pager__connector">` is inserted between each step in the Jinja loop. When `loop.index <= current_step` the `--filled` modifier switches the background to `var(--hdx-primary-5)`. No pseudo-elements or `--pager-fill-ratio` custom property. See §3.2.

**D2. Feature number badge** → **Bespoke `div`, no `c-label`.**
Style `.c-signup-tier__feature-number` entirely within `signup-tier.less`. No dependency on the `c-label` component.

**D3. `came-from-input.js` in v2 bundle** → **Yes, include (converted in place).**
`came-from-input.js` and `confirm-page-leave.js` were converted to vanilla JS in place (no `v2/onboarding/` subdirectory created). `verify-email.js` was not rewritten — the existing `hdx-verify-email-scripts` bundle is used as-is on the verify-email page. `toggle-password-visibility.js` is dropped — `c-search-input` handles toggling. See §8.7.

**D4. `verify-email.js` behaviour on v2 page** → **No BEM classes targeted; reuse as-is.**
The script uses only `history.pushState`, `window.onpopstate`, and `hdxUtil.net.removeOnboardingFlowData()` — no BEM or jQuery DOM selectors. The `hdxUtil.net.*` call is preserved verbatim (it is not jQuery). Script is used only on the verify-email page.

