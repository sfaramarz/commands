# Claude Commands

Shared Claude Code slash commands for the team.

---

## Commands

### `/plc-docs-generator` — PLC Document Creator

Automatically populates a Confluence PLC (Product Life Cycle) template with real content gathered from Jira, Confluence, Obsidian, meeting notes, and web search — then publishes it as a new Confluence page.

**Supported document types:**

| Type | Description |
|------|-------------|
| SPP  | Software Project Plan |
| SRD  | Software Requirements Document |
| SADD | Software Architecture & Design Document |

**Example usage inside Claude Code:**

```
/plc-docs-generator
> Create an SPP titled "Widget v2 Software Project Plan" in space LS. Use Jira project WIDGET for context.
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/claude-commands.git
cd claude-commands
```

### 2. Set up your Confluence credentials

Create a `.env` file at the path referenced inside the command (or adjust the path in `.claude/commands/plc-docs-generator.md` to point to your own `.env`):

```env
CONFLUENCE_BASE_URL=https://your-org.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@your-org.com
CONFLUENCE_API_TOKEN=your_api_token_here
```

To generate an API token: [id.atlassian.com](https://id.atlassian.com) → Security → API tokens

### 3. Update the template IDs

Open `.claude/commands/plc-docs-generator.md` and replace the template IDs and URLs in the **Fixed Templates** table with the correct ones for your Confluence space. Ask your team lead for the right IDs if you don't have them.

### 4. Open Claude Code from this directory

```bash
cd claude-commands
claude
```

The `/plc-docs-generator` command will be available automatically. Claude Code loads commands from `.claude/commands/` in the current working directory.

---

## Adding New Commands

To add a new shared slash command:

1. Create a `.md` file in `.claude/commands/`
2. Write the instructions for Claude inside it
3. Commit and push — teammates get it on next `git pull`

---

## Requirements

- [Claude Code](https://github.com/anthropics/claude-code) installed
- Confluence API access
- Python with `requests` and `python-dotenv` installed (`pip install requests python-dotenv`)
