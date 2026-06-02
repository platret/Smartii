# SAP Article Generator v2.0

**Self-contained Claude skill for generating professional SAP technical articles with embedded images.**

## 🚀 Quick Start

1. Upload this skill to Claude
2. Ask: `"Create an SAP article about sales order configuration"`
3. Get a professional Word document with embedded images!

## ✨ Features

- ✅ **Self-contained** - All image fetching built-in, no external dependencies
- ✅ **Automatic research** - Fact-checks via web search
- ✅ **Image downloading** - Fetches and embeds screenshots & diagrams
- ✅ **Professional formatting** - SAP blue headers, monospace codes
- ✅ **Complete articles** - 2000-4000 words with 2-3+ images
- ✅ **References** - Properly cited sources

## 📁 What's Included

```
sap-article-generator/
├── SKILL.md                    # Main skill instructions
├── INTEGRATION_GUIDE.md        # Setup and usage guide
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── scripts/
│   ├── fetch_image.py         # Download single images
│   └── fetch_images_batch.py  # Download multiple images
└── references/
    ├── article-standards.md   # Formatting guidelines
    └── sap-terminology.md     # SAP terms and codes
```

## 💡 Example Usage

```
User: "Create an article on SAP sales order type configuration"

Claude will:
1. Research the topic (3+ web searches)
2. Find relevant images (2+ web searches)
3. Download screenshots and diagrams
4. Create professional Word document
5. Embed images with captions
6. Format with SAP styling
7. Add references section
8. Deliver download link
```

## 📝 What You Get

- Professional Word document (.docx)
- SAP-specific formatting and colors
- Embedded screenshots and flow diagrams
- Step-by-step instructions
- Transaction codes and menu paths
- Best practices and troubleshooting
- Cited references

## 🎯 Perfect For

- SAP consultants creating client documentation
- Technical writers documenting SAP processes
- Training materials and guides
- Knowledge base articles
- Configuration handover documents

## 🔧 Technical Requirements

**Python Dependencies** (auto-installed):
- requests
- Pillow

**Claude Requirements**:
- Access to web_search tool
- Access to docx skill
- File system access

## 📦 Installation

**Option 1: Quick Upload**
1. Upload the .zip file to Claude
2. Skill is automatically available

**Option 2: Manual**
1. Extract to your Claude skills directory
2. Restart Claude

## 🎪 Supported SAP Topics

- **SD**: Sales, pricing, delivery, billing
- **MM**: Procurement, inventory, materials
- **FI**: Finance, accounting, assets
- **CO**: Controlling, cost centers
- **PP**: Production planning
- **WM**: Warehouse management
- **Technical**: ABAP, APIs, IDocs, BAPIs
- **Basis**: Archiving, transports, admin
- **S/4HANA**: Fiori, analytics, simplifications

## 🔍 Example Requests

**Configuration Guides:**
- "Create an SAP article on VOV8 sales order types"
- "Write a guide for material master configuration"

**Conceptual Articles:**
- "Explain SAP pricing procedure architecture"
- "Create an article on data archiving concepts"

**Troubleshooting:**
- "Create a troubleshooting guide for SAP IDocs"
- "Document common OData API issues"

## 📚 Documentation

- **SKILL.md** - Complete workflow and instructions
- **INTEGRATION_GUIDE.md** - Setup, usage, and troubleshooting
- **references/** - SAP terminology and formatting standards

## ⚡ Key Improvements in v2.0

Compared to v1.0:
- ✅ Self-contained (no external skill dependencies)
- ✅ Simpler workflow
- ✅ Better error handling
- ✅ Clearer documentation
- ✅ More reliable image embedding

## 🛠️ Troubleshooting

**Images not downloading?**
- Check network access
- Try alternative image sources
- Some sites block automated downloads

**Images not in document?**
- Verify /home/claude/temp_images/ has files
- Ensure docx skill is available

**Dependencies missing?**
```bash
pip install requests Pillow --break-system-packages
```

## 📄 License

MIT License - Free to use and modify

## 🤝 Credits

Created for SAP consultants and technical writers who need fast, professional documentation generation.

---

**Version**: 2.0  
**Last Updated**: October 2025  
**Author**: Created with Claude

**Ready to generate amazing SAP documentation!** 🎉
