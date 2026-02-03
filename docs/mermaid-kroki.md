# Mermaid & Kroki Integration Guide

This document explains why we switched to **Kroki** for rendering diagrams and how to use it effectively in our Backstage TechDocs.

## The Problem: Client-Side Rendering Limits

By default, Backstage TechDocs relies on client-side JavaScript (specifically `backstage-plugin-techdocs-addon-mermaid`) to render Mermaid diagrams in the browser. While this works for simple flowcharts, it often fails for complex diagrams like **C4 Architecture** diagrams due to:

1.  **Library Conflicts**: The specific version of Mermaid required for C4 syntax v2 often conflicts with the built-in version in the TechDocs addon.
2.  **Silent Failures**: Diagrams often fail to render entirely, leaving blank spaces or unhelpful error messages, making debugging difficult.
3.  **Browser Load**: Complex diagrams require significant client-side processing power.

## The Solution: Server-Side Rendering with Kroki

We have implemented **Server-Side Rendering (SSR)** using [Kroki](https://kroki.io). 

Instead of asking the browser to render the diagram, our build process (MkDocs) sends the diagram code to the Kroki API. Kroki renders it into an excessively optimized **SVG image** and returns the URL. The browser simply displays this static image.

### Benefits
-   **Reliability**: C4 diagrams render perfectly every time.
-   **Performance**: The browser just loads an image; no heavy JS execution.
-   **Stability**: We use the public `https://kroki.io` instance, which is maintained and always up-to-date with the latest diagram support.

## Configuration

The integration is configured in `mkdocs.yml` using the `mkdocs-kroki-plugin`.

```yaml
plugins:
  - techdocs-core
  - kroki:
      server_url: https://kroki.io
      http_method: POST
```

*   **`server_url`**: Points to the public Kroki instance. (We essentially bypassed local Docker issues by using the reliable public service).
*   **`http_method: POST`**: Ensures that large diagram payloads (like full system architecture) are sent correctly without hitting URL length limits.

## How to Write Diagrams

To ensure your diagrams are processed by Kroki instead of the default TechDocs handler, you must use the **`kroki-mermaid`** language identifier.

### Example: C4 Context

    ```kroki-mermaid
    C4Context
      title System Context
      Person(user, "User", "A user of the system")
      System(system, "Our System", "Does amazing things")
      Rel(user, system, "Uses")
    ```

### Example: Standard Flowchart

    ```kroki-mermaid
    graph TD
      A[Start] --> B{success?}
      B -->|Yes| C[Celebrate]
      B -->|No| D[Debug]
    ```

## Starting Backstage Correctly

To see your changes, you need to ensure the documentation is built and the Backstage app is running.

1.  **Build Documentation**:
    Generates the static site and processes the diagrams.
    ```bash
    mkdocs build
    ```

2.  **Start Backstage**:
    Starts the frontend and backend services.
    ```bash
    yarn start
    ```
    *Note: In the `hr-nexus` directory.*

When running locally with `builder: 'local'`, Backstage will often trigger the `mkdocs` build automatically when you refresh the page, but running `mkdocs build` manually ensures you catch any syntax errors immediately.
