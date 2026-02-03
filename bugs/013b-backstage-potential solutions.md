# Executive Summary: Mermaid Integration & Troubleshooting in Backstage TechDocs

## Primary Technical Constraints

The failure of Mermaid diagrams to render within Backstage typically stems from the platform's multi-layered security model and the specific sequence of the MkDocs build pipeline. Key friction points include:

* **HTML Sanitization (DOMPurify):** Backstage filters all documentation through `DOMPurify`. Standard Mermaid implementations rely on client-side script execution or specific CSS classes that are often stripped if not explicitly permitted.
* **Content Security Policy (CSP):** Mermaid's layout engines often require `script-src: 'unsafe-eval'` to calculate SVG coordinates. Most hardened Backstage environments block this by default.
* **Extension Precedence:** In the `mkdocs.yml` configuration, if `pymdownx.superfences` is initialized before `pymdownx.extra`, Mermaid code blocks are frequently misinterpreted as standard pre-formatted text rather than diagram hooks.


* **Environment Parity:** The `techdocs-cli` used for local previews does not bundle the necessary React addons found in the production portal, leading to "blank diagram" false negatives during development.



## Recommended Technical Approaches

### 1. The Addon-Centric Integration (Standard)

The official `backstage-plugin-techdocs-addon-mermaid` is the preferred solution as it operates within the TechDocs Addon framework to safely bypass frontend sanitization.

* **Prerequisites:** Ensure `mkdocs-techdocs-core >= 1.0.2` is installed in the generator environment.


* **MkDocs Configuration:** Define custom fences to ensure the generator outputs the correct `<pre class="mermaid">` tag.yaml
markdown_extensions:
* pymdownx.extra
* pymdownx.superfences:
custom_fences:
- name: mermaid
class: mermaid
format:!!python/name:pymdownx.superfences.fence_code_format


```

```


* **Frontend Registration (New Frontend System):**
```typescript
import { techDocsMermaidAddonModule } from 'backstage-plugin-techdocs-addon-mermaid';
//...
const app = createApp({
  features:,
});

```


* **Frontend Registration (Legacy System):** Register within `<TechDocsAddons>` in `App.tsx` or `EntityPage.tsx`.



### 2. The Kroki Architecture (Server-Side Alternative)

For environments where `'unsafe-eval'` is strictly prohibited for security compliance, Kroki provides a server-side rendering path.

* **Mechanism:** Kroki converts Mermaid text to static SVGs during the build phase or via a dedicated rendering service.


* **Trade-offs:**
* **Pros:** Minimal CSP impact; no client-side JS execution required.


* **Cons:** Significantly larger image footprint (the Mermaid-dedicated Kroki container is ~600MB due to Chromium/Puppeteer dependencies).




* **Implementation:** Requires `mkdocs-kroki-plugin` and a self-hosted Kroki instance for enterprise data privacy.

### 3. Security & Sanitizer Overrides

If diagrams remain invisible after addon installation, the `app-config.yaml` must be adjusted to accommodate the Mermaid renderer's requirements:

* **CSP Adjustments:**
```yaml
backend:
  csp:
    script-src: ["'self'", "'unsafe-inline'", "'unsafe-eval'"]

```


* **Sanitizer Exceptions:** If using custom diagram elements or attributes, whitelist them to prevent DOMPurify stripping.


```yaml
techdocs:
  sanitizer:
    allowedCustomElementTagNameRegExp: '^mermaid-'
    allowedCustomElementAttributeNameRegExp: '^data-'

```



## Performance & UX Optimization

* **Large Diagrams:** Enable the `enableZoom` prop in the Mermaid addon to allow users to navigate complex schemas via D3-powered pan/zoom controls.


* **Advanced Layouts:** For complex directed graphs, integrate the ELK (Eclipse Layout Kernel) by adding `@mermaid-js/layout-elk` to the frontend app, providing superior node spacing compared to the default engine.

