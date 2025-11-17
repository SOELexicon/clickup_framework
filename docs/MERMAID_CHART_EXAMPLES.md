# Mermaid Chart Examples - Comprehensive Reference

This document provides complex examples of all major Mermaid diagram types. Each example demonstrates advanced features and syntax to help you create sophisticated visualizations.

Reference: [Mermaid Documentation](https://mermaid.js.org/intro/)

---

## Table of Contents

1. [Flowcharts](#1-flowcharts)
2. [Sequence Diagrams](#2-sequence-diagrams)
3. [Class Diagrams](#3-class-diagrams)
4. [State Diagrams](#4-state-diagrams)
5. [Entity Relationship Diagrams](#5-entity-relationship-diagrams)
6. [User Journey](#6-user-journey)
7. [Gantt Charts](#7-gantt-charts)
8. [Pie Charts](#8-pie-charts)
9. [Quadrant Charts](#9-quadrant-charts)
10. [Requirement Diagrams](#10-requirement-diagrams)
11. [GitGraph](#11-gitgraph)
12. [Mindmaps](#12-mindmaps)
13. [Timeline](#13-timeline)
14. [Sankey Diagrams](#14-sankey-diagrams)
15. [XY Charts](#15-xy-charts)
16. [Block Diagrams](#16-block-diagrams)

---

## 1. Flowcharts

Complex flowchart demonstrating decision trees, subgraphs, styling, and multiple node shapes.

```mermaid
flowchart TD
    Start([Start Application]) --> Init[Initialize System]
    Init --> CheckAuth{User<br/>Authenticated?}

    CheckAuth -->|No| Login[/Login Form/]
    Login --> ValidateCreds{Valid<br/>Credentials?}
    ValidateCreds -->|No| LoginError[Display Error]
    LoginError --> Login
    ValidateCreds -->|Yes| CreateSession[Create Session]

    CheckAuth -->|Yes| LoadDash[Load Dashboard]
    CreateSession --> LoadDash

    LoadDash --> FetchData[(Fetch User Data)]
    FetchData --> ProcessData[Process & Cache Data]

    ProcessData --> RenderUI{UI<br/>Component<br/>Type?}

    subgraph UserInterface[User Interface Layer]
        RenderUI -->|Admin| AdminPanel[Admin Dashboard]
        RenderUI -->|Standard| UserPanel[User Dashboard]
        RenderUI -->|Guest| GuestPanel[Limited View]
    end

    AdminPanel --> CheckPerms{Has Admin<br/>Permissions?}
    CheckPerms -->|No| AccessDenied[/Access Denied/]
    CheckPerms -->|Yes| AdminTools[Load Admin Tools]

    UserPanel --> LoadWidgets[Load Widgets]
    GuestPanel --> LoadPublic[Load Public Content]

    subgraph DataSync[Background Sync]
        SyncTimer[Sync Timer] -.->|Every 5min| SyncData[Sync Data]
        SyncData --> UpdateCache[(Update Cache)]
        UpdateCache -.-> NotifyUI[Notify UI]
    end

    AdminTools --> Monitor[Monitor System]
    LoadWidgets --> Ready
    LoadPublic --> Ready
    AccessDenied --> Ready

    Ready[Application Ready] --> UserAction{User<br/>Action}
    UserAction -->|Logout| Cleanup[Cleanup Session]
    UserAction -->|Continue| Ready

    Cleanup --> End([End Session])

    %% Styling
    classDef errorStyle fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef successStyle fill:#51cf66,stroke:#2f9e44,color:#000
    classDef processStyle fill:#74c0fc,stroke:#1971c2,color:#000
    classDef dataStyle fill:#ffd43b,stroke:#fab005,color:#000

    class LoginError,AccessDenied errorStyle
    class CreateSession,Ready successStyle
    class ProcessData,LoadDash processStyle
    class FetchData,UpdateCache dataStyle
```

**Key Features:**
- Multiple node shapes: rounded `([])`, rectangle `[]`, decision `{}`, input/output `/\`, database `[([])]`
- Subgraphs for organizing related components
- Dotted lines for async operations `-.->`
- Custom styling with classDef
- Line breaks in labels with `<br/>`

---

## 2. Sequence Diagrams

Complex microservices interaction with loops, alternatives, and parallel execution.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant Order as Order Service
    participant Inventory as Inventory Service
    participant Payment as Payment Service
    participant Queue as Message Queue
    participant Email as Email Service

    User->>+Web: Place Order
    Web->>+API: POST /api/orders

    API->>+Auth: Validate Token
    Auth-->>-API: Token Valid ✓

    rect rgb(200, 220, 250)
        note right of API: Order Processing Flow
        API->>+Order: Create Order
        Order->>Order: Generate Order ID

        par Parallel Validation
            Order->>+Inventory: Check Stock
            Inventory-->>-Order: Stock Available
        and
            Order->>+Payment: Validate Payment Method
            Payment-->>-Order: Payment Method Valid
        end

        alt Stock Available
            Order->>+Inventory: Reserve Items
            Inventory->>Inventory: Lock Inventory
            Inventory-->>-Order: Items Reserved

            Order->>+Payment: Process Payment
            Payment->>Payment: Charge Customer

            alt Payment Successful
                Payment-->>Order: Payment Confirmed
                Order->>Order: Update Order Status: CONFIRMED

                Order->>+Queue: Publish OrderConfirmed Event
                Queue-->>-Order: Event Published

                Order-->>-API: Order Created Successfully
                API-->>-Web: 201 Created {orderId}
                Web-->>-User: Order Confirmation

                Queue->>+Email: OrderConfirmed Event
                Email->>Email: Generate Confirmation Email
                Email->>User: Send Confirmation Email
                deactivate Email

            else Payment Failed
                Payment-->>Order: Payment Failed ✗
                Order->>+Inventory: Release Reserved Items
                Inventory-->>-Order: Items Released
                Order-->>-API: 402 Payment Required
                API-->>-Web: Payment Error
                Web-->>-User: Payment Failed Message
            end

        else Out of Stock
            Inventory-->>Order: Insufficient Stock
            Order-->>-API: 409 Conflict
            API-->>-Web: Out of Stock Error
            Web-->>-User: Product Unavailable
        end
    end

    loop Every 5 minutes
        Order->>Queue: Check Pending Orders
        Queue-->>Order: Pending Order List
        Order->>Order: Process Timeouts
    end

    note over User,Email: All services use distributed tracing<br/>for request monitoring
```

**Key Features:**
- Auto-numbering with `autonumber`
- Actor vs Participant distinction
- Parallel execution with `par/and`
- Alternative paths with `alt/else`
- Loops for recurring actions
- Activation/deactivation boxes with `+/-`
- Rectangle highlights with `rect`
- Notes spanning multiple participants
- Emoji support in messages

---

## 3. Class Diagrams

Complex class hierarchy with multiple relationship types and annotations.

```mermaid
classDiagram
    %% Abstract classes and interfaces
    class IRepository~T~ {
        <<interface>>
        +FindById(id: string) T
        +FindAll() List~T~
        +Save(entity: T) T
        +Delete(id: string) bool
    }

    class BaseEntity {
        <<abstract>>
        #id: string
        #createdAt: DateTime
        #updatedAt: DateTime
        +GetId() string
        +UpdateTimestamp() void
    }

    class IAuditable {
        <<interface>>
        +createdBy: string
        +modifiedBy: string
        +GetAuditLog() AuditLog
    }

    %% Domain Models
    class User {
        -password: string
        +email: string
        +username: string
        +role: UserRole
        +isActive: bool
        +GetFullName() string
        +ChangePassword(old: string, new: string) bool
        +Authenticate(password: string) bool
        -HashPassword(password: string) string
    }

    class UserRole {
        <<enumeration>>
        ADMIN
        USER
        GUEST
        MODERATOR
    }

    class Order {
        +orderNumber: string
        +status: OrderStatus
        +totalAmount: decimal
        +customerId: string
        -discountApplied: decimal
        +AddItem(item: OrderItem) void
        +RemoveItem(itemId: string) void
        +CalculateTotal() decimal
        +ApplyDiscount(code: string) bool
        +CanBeCancelled() bool
    }

    class OrderItem {
        +productId: string
        +quantity: int
        +unitPrice: decimal
        +GetSubtotal() decimal
        +UpdateQuantity(qty: int) void
    }

    class Product {
        +name: string
        +sku: string
        +price: decimal
        +stockLevel: int
        +category: Category
        +IsInStock() bool
        +UpdateStock(quantity: int) void
        +GetPriceWithTax() decimal
    }

    class Category {
        +name: string
        +description: string
        +parentId: string
        +GetFullPath() string
    }

    class Payment {
        +amount: decimal
        +status: PaymentStatus
        +method: PaymentMethod
        +transactionId: string
        +ProcessPayment() bool
        +Refund(amount: decimal) bool
    }

    class PaymentStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        FAILED
        REFUNDED
    }

    class PaymentMethod {
        <<enumeration>>
        CREDIT_CARD
        DEBIT_CARD
        PAYPAL
        BANK_TRANSFER
    }

    class OrderStatus {
        <<enumeration>>
        DRAFT
        PENDING
        CONFIRMED
        SHIPPED
        DELIVERED
        CANCELLED
    }

    %% Repository Implementations
    class UserRepository {
        +FindByEmail(email: string) User
        +FindByUsername(username: string) User
    }

    class OrderRepository {
        +FindByCustomerId(customerId: string) List~Order~
        +FindByStatus(status: OrderStatus) List~Order~
    }

    %% Relationships
    BaseEntity <|-- User : extends
    BaseEntity <|-- Order : extends
    BaseEntity <|-- Product : extends
    BaseEntity <|-- Category : extends

    IAuditable <|.. User : implements
    IAuditable <|.. Order : implements

    IRepository~User~ <|.. UserRepository : implements
    IRepository~Order~ <|.. OrderRepository : implements

    User "1" --> "0..*" Order : places
    User ..> UserRole : uses

    Order "1" *-- "1..*" OrderItem : contains
    Order "1" --> "0..1" Payment : has
    Order ..> OrderStatus : uses

    OrderItem "1" --> "1" Product : references

    Product "0..*" --> "1" Category : belongs to
    Category "0..*" --> "0..1" Category : parent

    Payment ..> PaymentStatus : uses
    Payment ..> PaymentMethod : uses

    note for User "Users can have multiple roles\nand custom permissions"
    note for Order "Orders are immutable once confirmed\nUse event sourcing for state changes"
    note for IRepository "Generic repository pattern\nT must extend BaseEntity"
```

**Key Features:**
- Generic types with `~T~`
- Access modifiers: `+` public, `-` private, `#` protected
- Stereotypes: `<<interface>>`, `<<abstract>>`, `<<enumeration>>`
- Relationship types:
  - Inheritance: `<|--`
  - Implementation: `<|..`
  - Composition: `*--`
  - Aggregation: `o--`
  - Association: `-->`
  - Dependency: `..>`
- Cardinality: `"1"`, `"0..1"`, `"1..*"`, `"0..*"`
- Annotations with notes
- Method and property definitions

---

## 4. State Diagrams

Complex state machine with nested states, parallel states, and transitions.

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Initializing : Start

    Initializing --> Ready : Init Success
    Initializing --> Error : Init Failed

    state Ready {
        [*] --> Standby
        Standby --> Processing : Receive Request

        state Processing {
            [*] --> Validating
            Validating --> Executing : Valid
            Validating --> ValidationError : Invalid

            state Executing {
                direction LR
                [*] --> FetchData
                FetchData --> TransformData
                TransformData --> SaveData
                SaveData --> [*]
            }

            Executing --> Success
            ValidationError --> Failed
        }

        Processing --> Standby : Complete
    }

    state "Parallel Monitoring" as ParallelState {
        state fork_state <<fork>>
        [*] --> fork_state
        fork_state --> HealthCheck
        fork_state --> MetricsCollection
        fork_state --> LogAggregation

        state HealthCheck {
            [*] --> CheckingServices
            CheckingServices --> AllHealthy : All OK
            CheckingServices --> Degraded : Some Issues
            AllHealthy --> CheckingServices : Periodic Check
            Degraded --> CheckingServices : Retry
        }

        state MetricsCollection {
            [*] --> CollectingMetrics
            CollectingMetrics --> AnalyzingMetrics
            AnalyzingMetrics --> CollectingMetrics
        }

        state LogAggregation {
            [*] --> GatheringLogs
            GatheringLogs --> ProcessingLogs
            ProcessingLogs --> GatheringLogs
        }

        state join_state <<join>>
        HealthCheck --> join_state
        MetricsCollection --> join_state
        LogAggregation --> join_state
        join_state --> [*]
    }

    Ready --> ParallelState : Enable Monitoring
    ParallelState --> Ready : Monitoring Active

    Ready --> Maintenance : Admin Request

    state Maintenance {
        [*] --> PreMaintenance
        PreMaintenance --> DrainConnections
        DrainConnections --> PerformMaintenance
        PerformMaintenance --> ValidateSystem
        ValidateSystem --> PostMaintenance
        PostMaintenance --> [*] : Resume
    }

    Maintenance --> Ready : Maintenance Complete

    Ready --> Shutdown : Stop Signal
    Error --> Shutdown : Fatal Error

    state Shutdown {
        [*] --> SaveState
        SaveState --> CloseConnections
        CloseConnections --> Cleanup
        Cleanup --> [*]
    }

    Shutdown --> [*]

    %% Notes
    note right of Initializing
        Load configuration
        Connect to database
        Initialize services
    end note

    note left of ParallelState
        These states run
        concurrently in
        separate threads
    end note

    note right of Maintenance
        Zero-downtime deployment
        requires proper draining
    end note
```

**Key Features:**
- Nested states with composite states
- Parallel states using `<<fork>>` and `<<join>>`
- Directional hints with `direction LR`
- Transition labels
- Notes for documentation
- Entry and exit points `[*]`
- Complex state hierarchies

---

## 5. Entity Relationship Diagrams

Comprehensive database schema with multiple relationship types and attributes.

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER ||--o{ PAYMENT_METHOD : has
    CUSTOMER ||--o{ ADDRESS : "has shipping"
    CUSTOMER ||--o{ REVIEW : writes
    CUSTOMER }o--|| CUSTOMER_TIER : "belongs to"

    ORDER ||--|{ ORDER_ITEM : contains
    ORDER ||--|| PAYMENT : "paid with"
    ORDER ||--o| SHIPMENT : "shipped via"
    ORDER }o--|| ORDER_STATUS : has
    ORDER }o--|| ADDRESS : "ships to"

    ORDER_ITEM }o--|| PRODUCT : references
    ORDER_ITEM }o--o| PROMOTION : "has discount"

    PRODUCT ||--o{ PRODUCT_IMAGE : has
    PRODUCT ||--o{ REVIEW : receives
    PRODUCT }o--|| CATEGORY : "belongs to"
    PRODUCT }o--|| BRAND : "manufactured by"
    PRODUCT }o--o{ TAG : tagged
    PRODUCT ||--o{ INVENTORY : "stocked in"

    CATEGORY }o--o| CATEGORY : "parent category"

    INVENTORY }o--|| WAREHOUSE : "located in"

    SHIPMENT ||--o{ TRACKING_EVENT : has
    SHIPMENT }o--|| CARRIER : "handled by"

    PAYMENT }o--|| PAYMENT_METHOD : uses
    PAYMENT }o--|| PAYMENT_STATUS : has

    CUSTOMER {
        uuid id PK "Primary Key"
        string email UK "Unique email address"
        string password_hash "Bcrypt hash"
        string first_name
        string last_name
        string phone
        datetime created_at
        datetime last_login
        boolean is_active
        boolean email_verified
        uuid tier_id FK "Customer tier"
    }

    CUSTOMER_TIER {
        uuid id PK
        string name UK "Bronze, Silver, Gold, Platinum"
        decimal discount_percentage
        int free_shipping_threshold
        int points_multiplier
    }

    ORDER {
        uuid id PK
        string order_number UK "ORD-YYYYMMDD-XXXX"
        uuid customer_id FK
        uuid status_id FK
        decimal subtotal
        decimal tax_amount
        decimal shipping_cost
        decimal discount_amount
        decimal total_amount
        datetime created_at
        datetime updated_at
        uuid shipping_address_id FK
        text notes "Customer notes"
    }

    ORDER_STATUS {
        int id PK
        string name UK "PENDING, CONFIRMED, SHIPPED, etc"
        string description
        int sort_order
    }

    ORDER_ITEM {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal unit_price "Price at time of order"
        decimal discount_amount
        decimal tax_amount
        uuid promotion_id FK "Applied promotion"
    }

    PRODUCT {
        uuid id PK
        string sku UK "Stock Keeping Unit"
        string name
        text description
        decimal price
        decimal cost "Wholesale cost"
        uuid category_id FK
        uuid brand_id FK
        boolean is_active
        boolean is_featured
        int weight_grams
        datetime created_at
        datetime updated_at
        json specifications "Product specs as JSON"
    }

    PRODUCT_IMAGE {
        uuid id PK
        uuid product_id FK
        string url
        string alt_text
        int sort_order
        boolean is_primary
    }

    CATEGORY {
        uuid id PK
        string name
        string slug UK
        text description
        uuid parent_id FK "Self-reference"
        int level "Hierarchy level"
        string path "Materialized path"
    }

    BRAND {
        uuid id PK
        string name UK
        string slug
        text description
        string logo_url
        string website
    }

    TAG {
        uuid id PK
        string name UK
        string slug
        string color_hex
    }

    REVIEW {
        uuid id PK
        uuid product_id FK
        uuid customer_id FK
        int rating "1-5 stars"
        string title
        text comment
        datetime created_at
        int helpful_count
        boolean is_verified_purchase
    }

    INVENTORY {
        uuid id PK
        uuid product_id FK
        uuid warehouse_id FK
        int quantity_available
        int quantity_reserved
        int reorder_point
        int reorder_quantity
        datetime last_updated
    }

    WAREHOUSE {
        uuid id PK
        string code UK "WHxxx"
        string name
        string address
        string city
        string state
        string postal_code
        string country
        boolean is_active
    }

    ADDRESS {
        uuid id PK
        uuid customer_id FK
        string address_line1
        string address_line2
        string city
        string state
        string postal_code
        string country
        boolean is_default
        string address_type "shipping, billing, both"
    }

    PAYMENT {
        uuid id PK
        uuid order_id FK
        uuid payment_method_id FK
        uuid status_id FK
        decimal amount
        string transaction_id "External reference"
        datetime processed_at
        text notes
    }

    PAYMENT_METHOD {
        uuid id PK
        uuid customer_id FK
        string type "credit_card, paypal, bank_transfer"
        string last_four "Last 4 digits"
        string brand "Visa, Mastercard, etc"
        int expiry_month
        int expiry_year
        boolean is_default
        string token "Payment gateway token"
    }

    PAYMENT_STATUS {
        int id PK
        string name UK "PENDING, AUTHORIZED, CAPTURED, etc"
        string description
    }

    PROMOTION {
        uuid id PK
        string code UK
        string name
        string type "percentage, fixed_amount, free_shipping"
        decimal value
        decimal min_purchase_amount
        datetime valid_from
        datetime valid_to
        int usage_limit
        int used_count
        boolean is_active
    }

    SHIPMENT {
        uuid id PK
        uuid order_id FK
        uuid carrier_id FK
        string tracking_number
        decimal weight_grams
        decimal shipping_cost
        datetime estimated_delivery
        datetime actual_delivery
        string status
    }

    CARRIER {
        uuid id PK
        string name UK "UPS, FedEx, USPS"
        string code
        string api_endpoint
        boolean is_active
    }

    TRACKING_EVENT {
        uuid id PK
        uuid shipment_id FK
        datetime event_time
        string status
        string location
        text description
    }
```

**Key Features:**
- Comprehensive e-commerce database schema
- Relationship types:
  - `||--||` one-to-one
  - `||--o{` one-to-many
  - `}o--||` many-to-one
  - `}o--o{` many-to-many
- Detailed attributes with types and descriptions
- Foreign keys and primary keys marked
- Unique constraints `UK`
- Self-referencing relationships (Category parent)
- Business rules in comments

---

## 6. User Journey

Complex user journey mapping emotional states and touchpoints.

```mermaid
journey
    title E-Commerce Customer Purchase Journey
    section Discovery
      Search for product: 5: Customer
      Browse categories: 4: Customer
      Read reviews: 5: Customer
      Watch product video: 4: Customer, Content Team
      Compare prices: 3: Customer
      Add to wishlist: 4: Customer
    section Consideration
      Check shipping costs: 3: Customer
      Read return policy: 4: Customer
      Look for discount codes: 5: Customer
      Contact support: 3: Customer, Support Team
      Get product recommendations: 4: Customer, AI System
    section Purchase
      Add to cart: 5: Customer
      Apply coupon code: 5: Customer
      Review cart items: 4: Customer
      Enter shipping info: 3: Customer
      Select payment method: 3: Customer
      Confirm payment: 2: Customer, Payment Gateway
      Receive confirmation: 5: Customer, Email Service
    section Fulfillment
      Order processing: 4: Customer, Warehouse Team
      Inventory check: 3: Warehouse Team, Inventory System
      Package preparation: 4: Warehouse Team
      Quality check: 5: Warehouse Team
      Shipment dispatch: 5: Warehouse Team, Carrier
      Track shipment: 4: Customer, Carrier
    section Delivery
      Out for delivery: 4: Customer, Carrier
      Receive package: 5: Customer, Carrier
      Inspect product: 4: Customer
      Test product: 5: Customer
    section Post-Purchase
      Leave review: 5: Customer
      Share on social media: 4: Customer
      Contact support (if needed): 3: Customer, Support Team
      Request return: 2: Customer, Support Team
      Receive refund: 3: Customer, Finance Team
      Loyalty points earned: 5: Customer, Loyalty System
```

**Key Features:**
- Multiple sections representing journey phases
- Emotional scoring (1-5 scale)
- Multiple actors per step
- Cross-functional touchpoints
- End-to-end customer experience mapping

---

## 7. Gantt Charts

Complex project timeline with dependencies, milestones, and resource allocation.

```mermaid
gantt
    title Software Development Project - Q1 2025
    dateFormat YYYY-MM-DD

    section Planning
    Project kickoff           :milestone, m1, 2025-01-02, 0d
    Requirements gathering    :crit, active, req1, 2025-01-02, 10d
    System design            :crit, des1, after req1, 8d
    Architecture review      :milestone, m2, after des1, 0d

    section Infrastructure
    Setup dev environment    :infra1, 2025-01-06, 5d
    CI/CD pipeline          :infra2, after infra1, 7d
    Database setup          :crit, infra3, after des1, 5d
    Staging environment     :infra4, after infra3, 4d
    Production environment  :infra5, after infra4, 5d

    section Backend Development
    API design              :api1, after des1, 5d
    User authentication     :crit, api2, after api1, 8d
    User management API     :api3, after api2, 6d
    Product catalog API     :api4, after api2, 7d
    Order management API    :crit, api5, after api3, 9d
    Payment integration     :crit, api6, after api5, 10d
    Email notifications     :api7, after api6, 5d
    Backend code review     :milestone, m3, after api7, 0d

    section Frontend Development
    UI/UX design           :crit, ui1, after des1, 12d
    Design system          :ui2, after ui1, 7d
    Component library      :ui3, after ui2, 8d
    Homepage              :fe1, after ui3, 5d
    Product listing       :fe2, after fe1, 6d
    Product details       :fe3, after fe2, 5d
    Shopping cart         :crit, fe4, after fe3, 8d
    Checkout flow         :crit, fe5, after fe4, 10d
    User dashboard        :fe6, after fe5, 7d
    Responsive design     :fe7, after fe6, 5d
    Frontend code review  :milestone, m4, after fe7, 0d

    section Testing
    Unit tests - Backend      :test1, after api3, 15d
    Unit tests - Frontend     :test2, after fe3, 15d
    Integration testing       :crit, test3, after m3, 8d
    API testing              :test4, after test3, 5d
    UI testing               :test5, after m4, 6d
    Performance testing      :crit, test6, after test5, 7d
    Security audit           :crit, test7, after test6, 5d
    User acceptance testing  :crit, uat, after test7, 10d
    Bug fixes               :crit, bugs, after uat, 7d

    section Deployment
    Deploy to staging        :deploy1, after bugs, 2d
    Staging validation       :deploy2, after deploy1, 3d
    Production deployment    :milestone, m5, after deploy2, 1d
    Smoke testing           :crit, deploy3, after m5, 2d

    section Post-Launch
    Monitor metrics          :post1, after m5, 14d
    Gather feedback         :post2, after m5, 14d
    Iteration planning      :post3, after post2, 5d
    Project retrospective   :milestone, m6, after post3, 0d
```

**Key Features:**
- Multiple sections for different workstreams
- Task dependencies using `after` keyword
- Critical path marking with `crit`
- Active tasks with `active`
- Milestones with `milestone`
- Date formatting
- Overlapping parallel tasks
- Resource allocation visibility

---

## 8. Pie Charts

Pie chart showing distribution with detailed labels.

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#ff6b6b', 'primaryTextColor':'#fff', 'primaryBorderColor':'#c92a2a', 'secondaryColor':'#51cf66', 'tertiaryColor':'#74c0fc'}}}%%
pie title Customer Acquisition Channels - Q4 2024
    "Organic Search (SEO)" : 32.5
    "Paid Advertising (PPC)" : 24.3
    "Social Media" : 18.7
    "Email Marketing" : 12.4
    "Referrals" : 8.2
    "Direct Traffic" : 3.9
```

```mermaid
pie title Tech Stack Usage in Production
    "Python (Backend APIs)" : 35
    "TypeScript (Frontend)" : 28
    "Go (Microservices)" : 15
    "PostgreSQL (Database)" : 10
    "Redis (Cache)" : 7
    "Other" : 5
```

**Key Features:**
- Percentage-based distribution
- Custom theming with init directive
- Clear labeling
- Visual hierarchy

---

## 9. Quadrant Charts

Prioritization matrix for feature development.

```mermaid
quadrantChart
    title Feature Prioritization Matrix - Q1 2025
    x-axis Low Effort --> High Effort
    y-axis Low Impact --> High Impact
    quadrant-1 Quick Wins
    quadrant-2 Major Projects
    quadrant-3 Fill-Ins
    quadrant-4 Time Wasters

    Mobile app push notifications: [0.8, 0.9]
    Two-factor authentication: [0.6, 0.85]
    Dark mode UI: [0.3, 0.7]
    Advanced search filters: [0.7, 0.75]
    Social media integration: [0.5, 0.6]
    Export to PDF: [0.2, 0.5]
    Email templates: [0.4, 0.45]
    Custom dashboards: [0.85, 0.8]
    API rate limiting: [0.3, 0.9]
    Real-time analytics: [0.9, 0.95]
    Bulk operations: [0.5, 0.8]
    Keyboard shortcuts: [0.15, 0.4]
    Automated backups: [0.4, 0.95]
    Multi-language support: [0.75, 0.7]
    Custom branding: [0.6, 0.5]
```

**Key Features:**
- Four-quadrant matrix
- X and Y axis labels
- Quadrant naming
- Coordinate-based positioning [x, y]
- Strategic planning visualization

---

## 10. Requirement Diagrams

Complex requirement relationships and traceability.

```mermaid
requirementDiagram
    requirement user_auth {
        id: FR-001
        text: User Authentication System
        risk: high
        verifymethod: test
    }

    requirement two_factor {
        id: FR-002
        text: Two-Factor Authentication
        risk: medium
        verifymethod: test
    }

    requirement password_policy {
        id: FR-003
        text: Password Complexity Requirements
        risk: medium
        verifymethod: inspection
    }

    requirement session_mgmt {
        id: FR-004
        text: Session Management
        risk: high
        verifymethod: test
    }

    requirement data_encryption {
        id: NFR-001
        text: Data Encryption at Rest
        risk: high
        verifymethod: inspection
    }

    requirement performance {
        id: NFR-002
        text: Response Time < 200ms
        risk: medium
        verifymethod: test
    }

    requirement scalability {
        id: NFR-003
        text: Support 10,000 concurrent users
        risk: high
        verifymethod: test
    }

    functionalRequirement audit_log {
        id: FR-005
        text: Audit Logging
        risk: low
        verifymethod: demonstration
    }

    performanceRequirement api_performance {
        id: NFR-004
        text: API Throughput > 1000 req/s
        risk: medium
        verifymethod: test
    }

    interfaceRequirement rest_api {
        id: IF-001
        text: RESTful API Interface
        risk: low
        verifymethod: inspection
    }

    element auth_service {
        type: service
        docref: docs/auth_service.md
    }

    element database {
        type: database
        docref: docs/database_schema.md
    }

    element load_balancer {
        type: infrastructure
        docref: docs/infrastructure.md
    }

    user_auth - contains -> two_factor
    user_auth - contains -> password_policy
    user_auth - contains -> session_mgmt
    user_auth - contains -> audit_log

    user_auth - satisfies -> data_encryption
    user_auth - satisfies -> performance

    scalability - refines -> performance

    auth_service - satisfies -> user_auth
    auth_service - implements -> rest_api

    database - satisfies -> data_encryption
    load_balancer - satisfies -> scalability
    load_balancer - satisfies -> api_performance
```

**Key Features:**
- Multiple requirement types (functional, performance, interface)
- Risk levels
- Verification methods
- Traceability with relationships:
  - `contains` - decomposition
  - `satisfies` - implementation
  - `refines` - elaboration
  - `implements` - realization
- Element linking to system components

---

## 11. GitGraph

Complex Git branching strategy with releases and hotfixes.

```mermaid
%%{init: { 'gitGraph': {'mainBranchName': 'main'}} }%%
gitGraph
    commit id: "Initial commit"
    commit id: "Add README"

    branch develop
    checkout develop
    commit id: "Setup project structure"
    commit id: "Add configuration"

    branch feature/user-auth
    checkout feature/user-auth
    commit id: "Add login API"
    commit id: "Add registration"
    commit id: "Add password reset"

    checkout develop
    branch feature/product-catalog
    checkout feature/product-catalog
    commit id: "Create product model"
    commit id: "Add CRUD operations"

    checkout feature/user-auth
    commit id: "Add tests for auth"

    checkout develop
    merge feature/user-auth tag: "v0.1.0"

    checkout feature/product-catalog
    commit id: "Add product search"

    checkout develop
    merge feature/product-catalog

    branch release/1.0
    checkout release/1.0
    commit id: "Update version to 1.0.0"
    commit id: "Update changelog"

    checkout main
    merge release/1.0 tag: "v1.0.0"

    checkout develop
    merge release/1.0

    branch feature/shopping-cart
    checkout feature/shopping-cart
    commit id: "Add cart functionality"
    commit id: "Add cart persistence"

    checkout main
    branch hotfix/security-patch
    checkout hotfix/security-patch
    commit id: "Fix security vulnerability"

    checkout main
    merge hotfix/security-patch tag: "v1.0.1"

    checkout develop
    merge hotfix/security-patch

    checkout feature/shopping-cart
    commit id: "Add cart tests"

    checkout develop
    merge feature/shopping-cart

    branch feature/checkout
    checkout feature/checkout
    commit id: "Add checkout flow"
    commit id: "Integrate payment gateway"

    checkout develop
    merge feature/checkout

    branch release/1.1
    checkout release/1.1
    commit id: "Bump version 1.1.0"

    checkout main
    merge release/1.1 tag: "v1.1.0"

    checkout develop
    merge release/1.1
    commit id: "Start next iteration"
```

**Key Features:**
- Multiple branch types (feature, release, hotfix)
- Branch merging
- Tagging releases
- GitFlow workflow visualization
- Custom main branch name
- Complex branching patterns

---

## 12. Mindmaps

Hierarchical knowledge organization.

```mermaid
mindmap
  root((Software Architecture))
    Frontend
      Frameworks
        React
          Next.js
          Remix
          Gatsby
        Vue
          Nuxt
          Vite
        Angular
      State Management
        Redux
        MobX
        Zustand
        Recoil
      Styling
        CSS-in-JS
          Styled Components
          Emotion
        Tailwind CSS
        SCSS
    Backend
      Languages
        Python
          FastAPI
          Django
          Flask
        Node.js
          Express
          NestJS
          Fastify
        Go
          Gin
          Echo
        Java
          Spring Boot
      Databases
        Relational
          PostgreSQL
          MySQL
        NoSQL
          MongoDB
          Redis
          Cassandra
        Graph
          Neo4j
      APIs
        REST
        GraphQL
        gRPC
        WebSocket
    Infrastructure
      Cloud Providers
        AWS
          EC2
          Lambda
          S3
          RDS
        Azure
        GCP
      Container
        Docker
        Kubernetes
        ECS
      CI/CD
        GitHub Actions
        GitLab CI
        Jenkins
        CircleCI
    Architecture Patterns
      Microservices
        Service Mesh
        API Gateway
        Event Driven
      Monolithic
      Serverless
      Event Sourcing
      CQRS
```

**Key Features:**
- Root node as central concept
- Hierarchical structure
- Multiple levels of nesting
- Radial layout
- Knowledge mapping

---

## 13. Timeline

Historical events and milestones.

```mermaid
timeline
    title Product Development Timeline - 2024-2025

    section Q1 2024
        January 2024 : Project Inception
                     : Market Research
                     : Competitor Analysis
        February 2024 : Requirements Finalized
                      : Team Onboarding
                      : Tech Stack Selection
        March 2024 : MVP Design
                   : Database Schema
                   : API Specification

    section Q2 2024
        April 2024 : Development Kickoff
                   : Sprint 1-2 Complete
                   : Core Features Built
        May 2024 : Sprint 3-4 Complete
                 : Integration Testing
                 : Security Audit
        June 2024 : Beta Release
                  : User Testing
                  : Bug Fixes

    section Q3 2024
        July 2024 : v1.0 Launch
                  : Marketing Campaign
                  : First 1000 Users
        August 2024 : Feature Expansion
                    : Mobile App Development
                    : 5000 Users Milestone
        September 2024 : v1.1 Release
                       : New Integrations
                       : 10000 Users

    section Q4 2024
        October 2024 : Enterprise Features
                     : SSO Implementation
                     : Advanced Analytics
        November 2024 : v2.0 Beta
                      : AI Features
                      : Performance Optimization
        December 2024 : v2.0 Launch
                      : Year End Review
                      : 50000 Users

    section Q1 2025
        January 2025 : Scale Infrastructure
                     : Global Expansion
                     : New Markets
        February 2025 : v2.1 Planning
                      : Feature Requests Review
        March 2025 : Next Generation Planning
```

**Key Features:**
- Time-based sections
- Multiple events per period
- Chronological progression
- Milestone tracking
- Historical documentation

---

## 14. Sankey Diagrams

Flow visualization showing quantities and distributions.

```mermaid
%%{init: {'theme':'base'}}%%
sankey-beta

Website Traffic,Organic Search,50000
Website Traffic,Paid Ads,30000
Website Traffic,Social Media,25000
Website Traffic,Direct,15000
Website Traffic,Email,10000

Organic Search,Homepage,35000
Organic Search,Product Pages,12000
Organic Search,Blog,3000

Paid Ads,Product Pages,22000
Paid Ads,Landing Pages,8000

Social Media,Homepage,15000
Social Media,Product Pages,7000
Social Media,Blog,3000

Direct,Homepage,10000
Direct,Account,5000

Email,Product Pages,6000
Email,Account,4000

Homepage,Bounce,25000
Homepage,Product Viewed,25000
Homepage,Sign Up,10000

Product Pages,Bounce,15000
Product Pages,Add to Cart,25000
Product Pages,Wishlist,7000

Landing Pages,Bounce,3000
Landing Pages,Sign Up,5000

Blog,Bounce,4000
Blog,Subscribe,2000

Account,Dashboard,7000
Account,Logout,2000

Product Viewed,Bounce,8000
Product Viewed,Add to Cart,17000

Add to Cart,Checkout,30000
Add to Cart,Continue Shopping,12000

Checkout,Purchase Complete,22000
Checkout,Abandoned,8000
```

**Key Features:**
- Flow-based visualization
- Quantity representation
- Multi-level flows
- Path analysis
- Conversion funnel visualization

---

## 15. XY Charts

Data plotting with multiple series.

```mermaid
xychart-beta
    title "Monthly Revenue vs. Expenses - 2024"
    x-axis [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
    y-axis "Amount ($1000s)" 0 --> 200
    bar [65, 72, 78, 85, 92, 98, 105, 112, 125, 135, 145, 160]
    line [45, 48, 52, 58, 62, 68, 72, 78, 82, 88, 92, 98]
```

```mermaid
xychart-beta
    title "User Growth Metrics"
    x-axis "Months" [Q1, Q2, Q3, Q4]
    y-axis "Users" 0 --> 100000
    line [10000, 25000, 55000, 92000]
```

**Key Features:**
- Multiple chart types (bar, line)
- X and Y axis configuration
- Data series
- Quantitative analysis
- Trend visualization

---

## 16. Block Diagrams

System architecture and component relationships.

```mermaid
block-beta
    columns 3

    block:frontend["Frontend Layer"]
        WebApp["Web Application"]
        MobileApp["Mobile App"]
        AdminPanel["Admin Panel"]
    end

    space

    block:gateway["API Layer"]
        APIGateway["API Gateway"]
        LoadBalancer["Load Balancer"]
    end

    block:services["Microservices"]
        columns 2
        AuthService["Auth Service"]
        UserService["User Service"]
        ProductService["Product Service"]
        OrderService["Order Service"]
        PaymentService["Payment Service"]
        NotificationService["Notification Service"]
    end

    block:data["Data Layer"]
        columns 3
        PostgreSQL[("PostgreSQL")]
        Redis[("Redis Cache")]
        S3[("S3 Storage")]
    end

    block:external["External Services"]
        columns 2
        PaymentGateway["Payment Gateway"]
        EmailProvider["Email Provider"]
        SMSProvider["SMS Provider"]
    end

    WebApp --> APIGateway
    MobileApp --> APIGateway
    AdminPanel --> APIGateway

    APIGateway --> LoadBalancer
    LoadBalancer --> AuthService
    LoadBalancer --> UserService
    LoadBalancer --> ProductService
    LoadBalancer --> OrderService
    LoadBalancer --> PaymentService
    LoadBalancer --> NotificationService

    AuthService --> PostgreSQL
    UserService --> PostgreSQL
    ProductService --> PostgreSQL
    OrderService --> PostgreSQL

    AuthService --> Redis
    UserService --> Redis
    ProductService --> Redis

    ProductService --> S3

    PaymentService --> PaymentGateway
    NotificationService --> EmailProvider
    NotificationService --> SMSProvider
```

**Key Features:**
- Block-based architecture
- Column layout control
- Nested blocks
- Connection visualization
- System component organization

---

## Usage with ClickUp Framework

All these diagrams can be used with the ClickUp Framework commands:

```bash
# In task descriptions
cum tc "Architecture Docs" --description-file examples.md --upload-images

# In comments
cum ca task_id --comment-file diagram.md --upload-images

# In docs
cum dc "Technical Specs" --content-file specs.md --upload-images
```

For more information, see [MERMAID_DIAGRAMS.md](MERMAID_DIAGRAMS.md).

---

## Testing Your Diagrams

Test diagrams locally before uploading:

```bash
# Render to PNG
mmdc -i diagram.mmd -o output.png

# With dark theme
mmdc -i diagram.mmd -o output.png -t dark -b transparent

# Specify width
mmdc -i diagram.mmd -o output.png -w 1920
```

---

## Resources

- [Official Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)
- [ClickUp Markdown Reference](MARKDOWN_FORMATTING_GUIDE.md)

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0
