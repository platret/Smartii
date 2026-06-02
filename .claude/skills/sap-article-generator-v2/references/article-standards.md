# SAP Article Formatting Standards

This document provides detailed formatting and style guidelines for creating professional SAP technical articles.

## Document Structure Standards

### Title Page
- **Article Title**: Heading 1, 20pt, SAP blue (#0070AD), centered
- **Subtitle**: 14pt, gray, centered, describes article scope
- **Metadata**: Author, date, version (11pt, centered)
- **Spacing**: Add 2-3 blank lines between elements

### Table of Contents (if applicable)
- Include for articles with 5+ main sections
- Heading: "Table of Contents" (Heading 1)
- Automatically linked to sections
- Include page numbers (right-aligned)
- Show up to Heading 3 level

### Headings Hierarchy
**Heading 1** (Main Sections):
- Font: Calibri, 16pt, Bold
- Color: SAP Blue (#0070AD)
- Spacing: 12pt before, 6pt after
- Examples: Introduction, Configuration Steps, Best Practices

**Heading 2** (Subsections):
- Font: Calibri, 14pt, Bold
- Color: Dark Gray (#333333)
- Spacing: 10pt before, 4pt after
- Examples: Prerequisites, Step 1: Access Transaction

**Heading 3** (Sub-subsections):
- Font: Calibri, 12pt, Bold
- Color: Black
- Spacing: 8pt before, 3pt after
- Examples: Field Descriptions, Common Errors

## Text Formatting Standards

### Body Text
- Font: Calibri or Arial
- Size: 11pt
- Color: Black
- Line spacing: 1.15
- Paragraph spacing: 6pt after
- Alignment: Left-justified
- No indentation for first line

### Transaction Codes
Format transaction codes distinctly:
- Font: Courier New or Consolas (monospace)
- Size: 10pt
- Background: Light gray (#F0F0F0)
- Border: 1pt gray border
- Example: `SARA`, `VOV8`, `/IWFND/MAINT_SERVICE`

**In text:** Use inline code format
**Standalone:** Use code block format with light background

### Menu Paths
Format IMG and menu paths:
- Use → (right arrow) to separate levels
- Font: 10pt, italic
- Example: *SPRO → Sales and Distribution → Sales → Sales Documents → Sales Document Header → Define Sales Document Types*

### Technical Terms
- **First mention**: Bold the term, provide brief definition
- **Subsequent mentions**: Regular text
- **SAP-specific terms**: Always capitalize (ABAP, BAPI, IDoc)

### Abbreviations
- **First use**: Full term followed by abbreviation in parentheses
- **Example**: "Material Management (MM)"
- **After first use**: Use abbreviation only

## Visual Elements

### Images
**Placement:**
- Place images immediately after the referencing paragraph
- Center-align all images
- Maximum width: 600px (or 6 inches)
- Minimum width: 400px for screenshots

**Captions:**
- Position: Below image, centered
- Format: "Figure X: [Descriptive caption]"
- Font: 10pt, italic, gray
- Numbering: Sequential throughout document

**Image types:**
1. **Screenshots**: Actual SAP screens showing configuration
2. **Diagrams**: Process flows, architecture, data flows
3. **Examples**: Sample data, output examples

**Quality standards:**
- Resolution: Minimum 800x600px
- Clarity: Text must be readable
- Relevance: Directly supports surrounding content
- Professional: No personal information visible

### Tables
**Structure:**
- **Header row**: 
  - Background: SAP Blue (#0070AD)
  - Text: White, bold, 11pt
  - Alignment: Center
- **Body rows**: 
  - Background: Alternating white and light gray (#F8F8F8)
  - Text: Black, 10pt
  - Alignment: Left for text, right for numbers
- **Borders**: All cells, 0.5pt gray

**Common table types:**
1. **Field descriptions**: Field Name | Description | Values
2. **Transaction codes**: Transaction | Purpose | Module
3. **Comparison tables**: Feature | ECC | S/4HANA
4. **Settings**: Parameter | Value | Description

### Code Blocks
For ABAP code, SQL, or technical content:
- Font: Courier New, 9pt
- Background: Light gray (#F5F5F5)
- Border: 1pt solid gray
- Padding: 10pt all sides
- Line numbers: Optional, for longer blocks
- Syntax highlighting: Not required but helpful

## Content Standards

### Introduction Section
Every article should start with:
1. **Purpose statement**: What this article covers (2-3 sentences)
2. **Target audience**: Who should read this
3. **Prerequisites**: Required knowledge or system access
4. **Estimated time**: How long to complete (if procedural)

### Step-by-Step Instructions
For configuration or procedural content:
1. **Use numbered lists**: Clear sequential order
2. **One action per step**: Don't combine multiple actions
3. **Include transaction codes**: Always specify which transaction
4. **Screenshot each major step**: Show the actual screen
5. **Explain outcomes**: What happens after each step

**Example format:**
```
1. Access the transaction code `VOV8` (Sales Document Types).
   
   [Screenshot of VOV8 initial screen]
   Figure 1: VOV8 Transaction Initial Screen

2. Click "New Entries" to create a new sales order type.

3. Enter the following details:
   - Sales Document Type: `ZORD`
   - Description: `Custom Order Type`
   - Document Category: `C` (Order)
```

### Best Practices Section
Include practical advice:
- Bullet points for readability
- Based on real-world experience
- Include "Do's and Don'ts" subsections
- Reference SAP Notes where applicable

### Troubleshooting Section
Format common issues:
- **Problem/Symptom**: Bold, describes the issue
- **Cause**: Explains root cause
- **Solution**: Step-by-step resolution
- **Prevention**: How to avoid in future

### References Section
Format citations:
1. **Numbering**: Sequential [1], [2], [3]
2. **Format**: Title, Source, URL, Access Date
3. **Types**: 
   - SAP Help Portal documentation
   - SAP Community blog posts
   - SAP Notes (if publicly accessible)
   - Official SAP press releases
   - Third-party technical blogs (if reputable)

**Example:**
```
[1] SAP Help Portal - Sales Order Processing, 
    https://help.sap.com/..., Accessed: 2024-10-25

[2] SAP Community - Best Practices for Order Types,
    https://community.sap.com/..., Accessed: 2024-10-25
```

## Writing Style Guidelines

### Tone
- **Professional**: Technical but accessible
- **Clear**: No unnecessary jargon
- **Direct**: Use active voice
- **Helpful**: Anticipate reader questions

### Voice
- **Active voice preferred**: "Configure the system" not "The system is configured"
- **Second person**: Use "you" for instructions
- **Present tense**: For current actions and descriptions

### Sentence Structure
- **Keep it concise**: 15-20 words average
- **One idea per sentence**: Don't combine multiple concepts
- **Vary length**: Mix short and medium sentences
- **Avoid run-ons**: Use periods or semicolons appropriately

### Paragraph Structure
- **One topic per paragraph**: Stay focused
- **3-5 sentences**: Ideal paragraph length
- **Topic sentence**: First sentence introduces the main idea
- **Supporting details**: Following sentences elaborate
- **Transition**: Last sentence links to next paragraph

## SAP-Specific Conventions

### Module References
Always include module code:
- Sales and Distribution (SD)
- Materials Management (MM)
- Financial Accounting (FI)
- Controlling (CO)
- Production Planning (PP)

### Transaction Code References
- First mention: Full name and code
  - "Define Sales Document Types (`VOV8`)"
- Subsequent mentions: Code only
  - "In `VOV8`, click New Entries"

### Table References
When referencing SAP tables:
- Use monospace font
- Include brief description on first mention
- Example: "The `VBAK` table stores sales document header data"

### Version Specificity
Clearly indicate version relevance:
- "In SAP ECC 6.0..."
- "This feature is available in S/4HANA 2020 and later..."
- "For SAP R/3 systems..."

## Quality Checklist

Before finalizing any article, verify:

**Content Quality:**
- [ ] All information fact-checked through web sources
- [ ] Transaction codes verified as current
- [ ] Menu paths tested and accurate
- [ ] No assumptions stated as facts
- [ ] Alternative approaches mentioned where applicable

**Technical Accuracy:**
- [ ] Transaction codes spelled correctly
- [ ] Module abbreviations correct
- [ ] Technical terms used properly
- [ ] Version-specific information labeled

**Visual Quality:**
- [ ] Minimum 2-3 images included
- [ ] All images have captions
- [ ] Images are clear and relevant
- [ ] Screenshots show actual SAP screens
- [ ] Diagrams are professional

**Formatting Quality:**
- [ ] Headings follow hierarchy
- [ ] Transaction codes in monospace
- [ ] Tables properly formatted
- [ ] Consistent spacing throughout
- [ ] No formatting inconsistencies

**Completeness:**
- [ ] Introduction section present
- [ ] Prerequisites listed
- [ ] Step-by-step instructions clear
- [ ] Troubleshooting section included
- [ ] References section complete
- [ ] No TODO or placeholder text

## Document Metadata

Include at end of document (as footer or final section):
- **Document Version**: v1.0, v1.1, etc.
- **Last Updated**: YYYY-MM-DD
- **Author**: Name or "Generated by AI Assistant"
- **Review Status**: Draft, Reviewed, Final

This ensures traceability and version control.
