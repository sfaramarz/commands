# nSpect Diagram Requirements & Tips

Guidelines for architecture/dataflow diagrams that work well with nSpect TAVA 3.0's AI analysis.

---

## Accepted Formats

| Format | Notes |
|--------|-------|
| `.jpg` / `.jpeg` | Preferred for simplicity |
| `.png` | Good for high-resolution diagrams |
| `.vsdx` | Visio — prefer squares/rectangles, or export as JPG/PNG |
| Lucidchart | Provide the Lucid document ID |

**Only one diagram** can be uploaded per TAVA run.

---

## What to Include

- All **real, deployable system components** (services, databases, caches, queues, storage)
- **External systems**, APIs, and services the project depends on
- **Arrows with annotations** showing protocols and security properties
- **Clear labels** on ALL component blocks — names must match the architecture document

## What to Avoid

- Overlapping arrows or cluttered layouts
- Excessive components (keep it focused on the TOE scope)
- Generic or unlabeled components
- Embedded graphics in supporting documents (only text is extracted from docs)

---

## Mermaid to PNG Rendering

tava-gen outputs Mermaid `.mmd` files. To render for nSpect upload:

### Option 1: mermaid-cli (local)

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i architecture.mmd -o architecture.png -w 2048 -H 1536
```

### Option 2: mermaid.live (web)

1. Open https://mermaid.live
2. Paste the `.mmd` content
3. Download as PNG/SVG

### Option 3: VS Code extension

Install the "Mermaid Preview" extension and export from the preview pane.

---

## Component Shape Convention (Mermaid)

| Type | Shape | Mermaid Syntax |
|------|-------|---------------|
| Service | Rectangle | `id[Name]` |
| Database | Cylinder | `id[(Name)]` |
| Queue | Subroutine | `id[[Name]]` |
| Cache | Cylinder | `id[(Name)]` |
| External API | Circle | `id((Name))` |
| Gateway | Hexagon | `id{{Name}}` |
| UI | Parallelogram | `id[/Name\]` |

---

## Matching Diagram ↔ Document

nSpect TAVA 3.0 works best when:
- Component names in the **diagram** exactly match names in the **document**
- Connection descriptions use the same protocol names in both
- The diagram covers the same scope as the document's TOE section
