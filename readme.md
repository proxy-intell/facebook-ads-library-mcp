[![Proxy — Facebook Ads Library Hosted MCP](assets/banner.png)](https://useproxy.dev/)

# Facebook Ads Library MCP Server

> **[Proxy](https://useproxy.dev/?utm_source=github&utm_medium=readme&utm_campaign=facebook-ads-library-mcp) (useproxy.dev) is a free hosted ad library MCP server.** One connection gives ChatGPT, Claude, Cursor and any MCP client live ads from the Meta, Google, LinkedIn and TikTok (EU) ad libraries, with no API keys and 20 free credits a day. This repo is the open-source, self-hosted Facebook Ads Library server. **[Use the hosted version in 2 minutes →](https://useproxy.dev/welcome?utm_source=github&utm_medium=readme&utm_campaign=facebook-ads-library-mcp)**

[![smithery badge](https://smithery.ai/badge/useproxy/proxy)](https://smithery.ai/servers/useproxy/proxy)

This is a Model Context Protocol (MCP) server for the Facebook Ads Library.

With this you can search Facebook's public ads library for any company or brand, see what they're currently running and analyze their advertising. You can analyze ad images/text, analyze video ads with comprehensive insights, compare companies' strategies, and get insights into what's working in their campaigns.

Here's an example of what you can do when it's connected to Claude.

[https://github.com/user-attachments/assets/a47aa689-e89d-4d4b-9df7-6eb3a81937ee](https://github.com/user-attachments/assets/a47aa689-e89d-4d4b-9df7-6eb3a81937ee)

---

## Hosted Version (Recommended)

**The easiest way to use the Facebook Ads Library MCP is the hosted version from [Proxy (useproxy.dev)](https://useproxy.dev/).** No API keys, no Gemini key, no Python, no server to run — just connect and start querying.

- ⚡ **Zero setup** — nothing to install, configure, or maintain
- 🔑 **No API keys** — skip the ScrapeCreators and Gemini keys entirely
- 🔌 **Works everywhere** — ChatGPT, Claude, Cursor, Manus, and anywhere else that supports MCP
- 🚀 **Always up to date** — new tools and fixes ship automatically

👉 **[Get started for free at useproxy.dev →](https://useproxy.dev/welcome?utm_source=github&utm_medium=readme&utm_campaign=facebook-ads-library-mcp)**

Prefer to run it yourself? The full self-host setup is documented below.

### Hosted vs. Self-Host

| | **Hosted — [Proxy (useproxy.dev)](https://useproxy.dev/)** | **Self-Host** |
| --- | --- | --- |
| Setup time | None — connect and go | Python env + config |
| API keys required | None | ScrapeCreators + Gemini |
| Infrastructure | Fully managed | You run and maintain it |
| Updates | Automatic | Manual `git pull` |
| Works in ChatGPT, Claude, Cursor, Manus | ✅ | ✅ |
| Best for | Most users who just want the data | Developers who want to customize the code |

For most people, the [hosted version](https://useproxy.dev/) is the fastest path. Choose self-host if you specifically want to modify or extend the server yourself.

---

## Example Prompts

### Single Brand Analysis

```plaintext
How many ads is 'AnthropicAI' running? What's their split across video and image?
```

```plaintext
What messaging is 'AnthropicAI' running right now in their ads?
```

```plaintext
Analyze the video ads from 'Nike' and extract their visual storytelling strategy, pacing, and brand messaging techniques.
```

### Batch Analysis (New!)

```plaintext
Compare the current advertising strategies across Nike, Adidas, and Under Armour. Show me their ad volumes, messaging themes, and creative approaches.
```

```plaintext
Do a deep comparison to the messaging between 'AnthropicAI', 'Perplexity AI' and 'OpenAI'. Give it a nice forwardable summary.
```

```plaintext
Analyze the holiday campaign strategies for Coca-Cola, Pepsi, Dr Pepper, and Sprite. What themes are they using?
```

```plaintext
Get the current ads for all major streaming services: Netflix, Disney+, Hulu, HBO Max, Amazon Prime Video, and Apple TV+. Compare their positioning strategies.
```

---

## Installation

### Prerequisites

- Python 3.12+
- Anthropic Claude Desktop app (or Cursor)
- Pip (Python package manager), install with `python -m pip install`
- An API key for an ads data provider, set as `SCRAPECREATORS_API_KEY` (see configuration below)
- A Google Gemini API key for video analysis (optional, only needed for video ads)

> Prefer not to deal with API keys? See the [Hosted Version](#hosted-version-recommended) above to skip setup entirely.

### Quick Install (Recommended)

1. **Clone and run the install script**
  ```bash
   git clone https://github.com/proxy-intell/facebook-ads-library-mcp.git
   cd facebook-ads-library-mcp

   # For macOS/Linux:
   ./install.sh

   # For Windows:
   install.bat
  ```
   The install script will:
  - Create a virtual environment for dependency isolation
  - Install all required dependencies
  - Set up your configuration files
2. **Configure your API keys**
  Edit the `.env` file that was created and add your API keys:
  - Set your ads data API key as `SCRAPECREATORS_API_KEY`
  - Get your Gemini API key at [Google AI Studio](https://aistudio.google.com/app/apikey) (optional, for video analysis)
3. **Follow the displayed MCP configuration**
  The install script will show you the exact configuration to add to Claude Desktop or Cursor.

### Manual Install

If you prefer to install manually:

1. **Clone this repository**
  ```bash
   git clone https://github.com/proxy-intell/facebook-ads-library-mcp.git
   cd facebook-ads-library-mcp
  ```
2. **Create a virtual environment and install dependencies**
  ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
  ```
3. **Configure API keys**
  Copy the template and configure your API keys:
   **To obtain API keys:**
  - Set your ads data API key as `SCRAPECREATORS_API_KEY` in the `.env` file
  - Get a Google Gemini API key [here](https://aistudio.google.com/app/apikey) (optional, for video analysis)
4. **Connect to the MCP server**
  Add the MCP server configuration to your Claude Desktop or Cursor config:
   Replace `{{PATH_TO_PROJECT}}` with the full path to where you cloned this repository.
   **Note:** The configuration uses the virtual environment's Python interpreter (`venv/bin/python`) for better dependency isolation and reliability.
   **Note:** API keys are now automatically loaded from the `.env` file, so you don't need to pass them as command line arguments.
   **For Claude Desktop:**
   Save this as `claude_desktop_config.json` in your Claude Desktop configuration directory at:
   **For Cursor:**
   Save this as `mcp.json` in your Cursor configuration directory at:
5. **Restart Claude Desktop / Cursor**
  Open Claude Desktop and you should now see the Facebook Ads Library as an available integration.
   Or restart Cursor.

---

## Technical Details

1. Claude sends requests to the Python MCP server
2. The MCP server intelligently batches and optimizes queries to the ads data API
3. Smart caching reduces redundant API calls and improves performance
4. Credit monitoring prevents workflow interruption with proactive error handling
5. Data flows back through the chain to Claude with enhanced batch information

### Available MCP Tools (Enhanced)

This MCP server provides tools for interacting with Facebook Ads library objects:


| Tool Name                 | Description                                                                | Batch Support           |
| ------------------------- | -------------------------------------------------------------------------- | ----------------------- |
| `get_meta_platform_id`    | Returns platform ID given one or many brand names                          | ✅ Multiple brands       |
| `get_meta_ads`            | Retrieves ads for specific page(s) (platform ID)                           | ✅ Multiple platform IDs |
| `analyze_ad_image`        | Analyzes ad images for visual elements, text, colors, and composition      | ⚡ Enhanced caching      |
| `analyze_ad_video`        | Analyzes single ad video using Gemini AI for comprehensive insights        | ⚡ Enhanced caching      |
| `analyze_ad_videos_batch` | **NEW** - Analyzes multiple videos in single API call for token efficiency | 🎬 ~88% token savings   |
| `get_cache_stats`         | Gets statistics about cached media (images and videos) and storage usage   | -                       |
| `search_cached_media`     | Searches previously analyzed media by brand, colors, people, or media type | -                       |
| `cleanup_media_cache`     | Cleans up old cached media files to free disk space                        | -                       |

---

## Troubleshooting

### Common Issues

**🆕 API Credits Exhausted:**

- When you see an "API credits exhausted" message, you need to top up your account
- The error message includes a direct link to your provider's dashboard
- You can check your current credit balance and purchase more credits there
- The server will automatically resume working once credits are available

**🆕 Rate Limit Exceeded:**

- If you hit rate limits, the server will tell you how long to wait
- Batch operations help reduce the chance of hitting rate limits
- Consider spacing out large batch requests if you frequently hit limits

**API Key Not Found Error:**

- Ensure your `.env` file is in the project root directory
- If you don't have a `.env` file, copy it from the template: `cp .env.template .env`
- Check that your API keys are correctly formatted without quotes
- Verify the `.env` file contains `SCRAPECREATORS_API_KEY=your_key_here`
- For video analysis, ensure `GEMINI_API_KEY=your_key_here` is also added

**Video Analysis Not Working:**

- Confirm you have a valid Google Gemini API key in your `.env` file
- Video analysis requires the `GEMINI_API_KEY` environment variable

**MCP Server Connection Issues:**

- Verify the path in your MCP configuration points to the correct location
- Make sure you've created a virtual environment and installed dependencies with `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt`
- Ensure your MCP configuration uses the virtual environment Python path (ending with `/venv/bin/python`)
- Restart Claude Desktop/Cursor after configuration changes

For additional Claude Desktop integration troubleshooting, see the [MCP documentation](https://modelcontextprotocol.io/quickstart/server#claude-for-desktop-integration-issues). The documentation includes helpful tips for checking logs and resolving common issues.

---

## FAQ

**What is the easiest way to use the Facebook Ads Library MCP?**
The easiest way is the hosted version from [Proxy (useproxy.dev)](https://useproxy.dev/). It requires no API keys, no installation, and no server — you connect it to ChatGPT, Claude, Cursor, or any MCP client and start querying immediately. You can [start for free](https://useproxy.dev/).

**Do I need an API key to use this MCP?**
Only if you self-host. The [hosted version at useproxy.dev](https://useproxy.dev/) handles all data access for you, so no ScrapeCreators or Gemini keys are needed. Self-hosting requires a `SCRAPECREATORS_API_KEY` (and a Gemini key for video analysis).

**Which MCP clients does it work with?**
Both the hosted and self-hosted versions work with ChatGPT, Claude (Desktop and web), Cursor, Manus, and any other client that supports the Model Context Protocol.

**Is there a free version?**
Yes — the [hosted version from Proxy](https://useproxy.dev/) offers a free tier so you can start analyzing ads without any setup.

**Should I self-host or use the hosted version?**
Use the [hosted version](https://useproxy.dev/) if you just want fast, reliable access to Facebook Ads Library data with zero maintenance — this fits most users. Self-host only if you want to modify or extend the server code yourself.

---

## Feedback

Your feedback will be massively appreciated. Please [tell us](mailto:support@useproxy.dev) which features on that list you like to see next or request entirely new ones.

---

## Related

- [Proxy hosted MCP](https://github.com/proxy-intell/proxy-mcp): all four ad libraries in one hosted server, OAuth, no keys
- [Google Ads Library MCP](https://github.com/proxy-intell/google-ads-library-mcp) (self-hosted)
- [LinkedIn Ads Library MCP](https://github.com/proxy-intell/linkedin-ads-library-mcp) (self-hosted)
- [TikTok Ads Library MCP](https://github.com/proxy-intell/tiktok-ads-library-mcp) (self-hosted)
- [Install guide for every client](https://useproxy.dev/welcome?utm_source=github&utm_medium=readme&utm_campaign=facebook-ads-library-mcp)

---

## License

This project is licensed under the MIT License.

---

Made with ❤️ by the team at [Proxy](https://useproxy.dev/).
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/proxy-intell-facebook-ads-library-mcp-badge.png)](https://mseep.ai/app/proxy-intell-facebook-ads-library-mcp)
