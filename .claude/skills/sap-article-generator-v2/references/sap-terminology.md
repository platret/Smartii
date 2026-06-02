# SAP Terminology Reference

Quick reference for common SAP terms, abbreviations, transaction codes, and concepts.

## Core SAP Modules

| Module | Full Name | Key Areas |
|--------|-----------|-----------|
| **SD** | Sales and Distribution | Sales orders, delivery, billing, pricing |
| **MM** | Materials Management | Procurement, inventory, purchasing |
| **FI** | Financial Accounting | General ledger, AP/AR, asset accounting |
| **CO** | Controlling | Cost centers, profit centers, internal orders |
| **PP** | Production Planning | Manufacturing, work centers, BOMs |
| **QM** | Quality Management | Inspections, quality planning |
| **PM** | Plant Maintenance | Equipment, maintenance orders |
| **HR** | Human Resources | Personnel, payroll, organizational mgmt |
| **WM** | Warehouse Management | Storage, inventory movements |
| **PS** | Project System | Project planning and execution |

## Common Transaction Codes by Module

### Sales and Distribution (SD)
- `VA01` - Create Sales Order
- `VA02` - Change Sales Order
- `VA03` - Display Sales Order
- `VL01N` - Create Outbound Delivery
- `VL02N` - Change Outbound Delivery
- `VF01` - Create Billing Document
- `VOV8` - Define Sales Document Types
- `VOV7` - Define Item Categories
- `V/06` - Maintain Pricing Conditions

### Materials Management (MM)
- `MM01` - Create Material Master
- `MM02` - Change Material Master
- `MM03` - Display Material Master
- `ME21N` - Create Purchase Order
- `ME22N` - Change Purchase Order
- `MIGO` - Goods Receipt/Issue
- `MB51` - Material Document List
- `MB52` - Warehouse Stock List
- `OMB9` - Material Document Retention Periods

### Financial Accounting (FI)
- `FB01` - Post Document
- `FB03` - Display Document
- `FB60` - Enter Incoming Invoices
- `FB70` - Enter Customer Invoice
- `F-02` - General Posting
- `FBL1N` - Vendor Line Items
- `FBL3N` - G/L Account Line Items
- `FBL5N` - Customer Line Items
- `FS00` - Create/Change G/L Account

### Controlling (CO)
- `KS01` - Create Cost Center
- `KS02` - Change Cost Center
- `KB21N` - Enter Activity Allocation
- `KSH1` - Actual/Plan/Variance Report
- `KO04` - Display Internal Order

### Production Planning (PP)
- `CO01` - Create Production Order
- `CO02` - Change Production Order
- `CO11N` - Confirm Production Order
- `CS01` - Create BOM
- `CS02` - Change BOM
- `CR01` - Create Work Center

### Basis and Administration
- `SARA` - Archive Administration
- `SARI` - Archive Information System
- `SE38` - ABAP Editor
- `SE11` - ABAP Dictionary
- `SM37` - Background Job Overview
- `STMS` - Transport Management System
- `SU01` - User Maintenance
- `PFCG` - Role Maintenance
- `SICF` - HTTP Service Maintenance
- `DB02` - Database Performance Monitor

### Gateway and OData
- `/IWFND/MAINT_SERVICE` - OData Service Maintenance
- `/IWFND/GW_CLIENT` - Gateway Client (API testing)
- `/IWFND/ERROR_LOG` - Gateway Error Log
- `/IWBEP/ERROR_LOG` - Backend Error Log

## SAP System Versions

| Version | Description | Key Features |
|---------|-------------|--------------|
| **SAP R/3** | Client-server architecture | Traditional three-tier system |
| **SAP ECC** | ERP Central Component | Standard ERP system, EHP 4-8 |
| **SAP S/4HANA** | Next-gen ERP on HANA | In-memory database, Fiori UI |

### SAP NetWeaver Versions
- **7.31**: Minimum for OData services
- **7.40+**: Recommended for Gateway
- **7.50+**: Enhanced features, CDS views

## Technical Terms

### ABAP (Advanced Business Application Programming)
- SAP's proprietary programming language
- Used for customizations and enhancements
- Key concepts: Function modules, BAPIs, reports

### BAPIs (Business Application Programming Interfaces)
- Standardized interfaces for SAP business objects
- Used for integration and automation
- Examples: `BAPI_SALESORDER_CREATE`, `BAPI_MATERIAL_GET_DETAIL`

### IDocs (Intermediate Documents)
- Standard data format for electronic data interchange
- Used for system-to-system communication
- Examples: ORDERS, MATMAS, DEBMAS

### RFCs (Remote Function Calls)
- Protocol for communication between SAP systems
- Types: sRFC (synchronous), aRFC (asynchronous), tRFC (transactional)

### OData (Open Data Protocol)
- RESTful protocol for web services
- Used in SAP Gateway and Fiori apps
- URL format: `/sap/opu/odata/sap/SERVICE_NAME`

### CDS Views (Core Data Services)
- Data modeling infrastructure in S/4HANA
- Replaces traditional database views
- Annotation-based definition

## Common SAP Abbreviations

### Document Types
- **SO** - Sales Order
- **DO** - Delivery Order
- **PO** - Purchase Order
- **PR** - Purchase Requisition
- **GR** - Goods Receipt
- **GI** - Goods Issue
- **FI Doc** - Financial Document

### Master Data
- **BP** - Business Partner
- **Customer** - Sold-to, Ship-to, Bill-to, Payer
- **Vendor** - Supplier
- **Material** - Product/SKU

### Organizational Units
- **Company Code** - Legal entity
- **Plant** - Physical location
- **Storage Location** - Inventory subdivision
- **Sales Organization** - Sales entity
- **Distribution Channel** - Method of distribution
- **Division** - Product line

### Fields and Attributes
- **VBAK** - Sales Document Header
- **VBAP** - Sales Document Item
- **VBEP** - Sales Document Schedule Lines
- **VBUK** - Sales Document Header Status
- **VBUP** - Sales Document Item Status
- **MARA** - General Material Data
- **MARC** - Plant Data for Material

## Configuration Concepts

### IMG (Implementation Guide)
- Central configuration tool
- Access via transaction `SPRO`
- Contains all customizing settings
- Path format: Node → Node → Node

### Customizing vs. Development
- **Customizing**: Configuration without code (IMG settings)
- **Development**: Custom ABAP code (Z*/Y* programs)

### Client Concept
- Highest level in SAP hierarchy
- Independent business entity
- Separate data and configurations
- Standard clients: 000 (master), 066 (Early Watch), 001 (Production template)

### Transport System
- Moves changes between systems (Dev → QA → Prod)
- Types: Workbench (cross-client), Customizing (client-specific)
- Transaction: `SE10` (Transport Organizer)

## Data Archiving Concepts

### SARA Transaction
- Archive Administration main transaction
- Phases: Write, Delete, Store
- Archive Objects: Logical units of data to archive

### Common Archive Objects
- `FI_DOCUMNT` - Financial documents
- `MM_MATBEL` - Material documents
- `SD_VBAK` - Sales orders
- `PP_ORDER` - Production orders

### Retention Periods
- Minimum time data must remain in database
- Set via customizing (module-specific)
- Compliance and legal requirements

## Business Processes

### Order-to-Cash (SD)
1. Sales Order (`VA01`)
2. Delivery (`VL01N`)
3. Picking/Packing
4. Goods Issue (via `VL02N`)
5. Billing (`VF01`)
6. Payment (FI)

### Procure-to-Pay (MM)
1. Purchase Requisition (`ME51N`)
2. Purchase Order (`ME21N`)
3. Goods Receipt (`MIGO`)
4. Invoice Receipt (`MIRO`)
5. Payment (FI)

### Make-to-Stock (PP)
1. Production Order (`CO01`)
2. Material Availability Check
3. Production Confirmation (`CO11N`)
4. Goods Receipt to Warehouse

## Integration Points

### SD ↔ MM Integration
- Availability check
- Goods issue for delivery
- Consignment processing
- Stock determination

### SD ↔ FI Integration
- Revenue posting from billing
- Credit management
- Payment terms
- Tax calculation

### MM ↔ FI Integration
- GR/IR (Goods Receipt/Invoice Receipt) clearing
- Inventory valuation
- Purchase order commitments

## Fiori Apps (S/4HANA)

### App Types
- **Transactional**: Create, change documents
- **Analytical**: Reports and dashboards
- **Fact Sheets**: Quick information views

### Common Apps
- `F0001` - Manage Sales Orders
- `F0002` - Track Sales Orders
- `F1481` - Purchase Order Approvals
- `F0203` - Manage Purchase Orders

## Best Practices Terminology

### Clean Core
- S/4HANA concept for minimal modifications
- Use standard functionality where possible
- Extensions via side-by-side approach

### SAP Notes
- Official corrections and enhancements
- Format: SAP Note XXXXXXX
- Applied via SNOTE transaction

### OSS (Online Service System)
- Now called SAP Support Portal
- Incident reporting and tracking
- Access to SAP Notes

## Version-Specific Features

### ECC-Only Features
- Classic GUI transactions
- Table-based architecture
- Separate modules

### S/4HANA-Only Features
- Universal Journal (ACDOCA table)
- Embedded Analytics
- Simplified data model
- CDS views
- Fiori as standard UI

## Common Error Messages

### Runtime Errors
- **ABAP Dump** - Runtime error in ABAP program
- **Short Dump** - System error (view in `ST22`)
- **RFC Timeout** - Remote function call timeout

### Business Errors
- **No number range** - Number range not maintained
- **Material not extended** - Material not defined for plant
- **Credit limit exceeded** - Customer credit check failed
- **Item not relevant for billing** - Billing block or missing data

This terminology reference should be used when writing SAP articles to ensure consistent and accurate use of SAP-specific terms.
