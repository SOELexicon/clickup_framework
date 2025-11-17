# Mermaid Diagram Gallery

A visual reference of all major Mermaid diagram types with complex examples.

---

## 1. Flowchart - Application User Flow

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

---

## 2. Sequence Diagram - Microservices Order Processing

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

---

## 3. Class Diagram - E-Commerce Domain Model

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
```

---

## 4. State Diagram - Application State Machine

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
```

---

## 5. Entity Relationship Diagram - E-Commerce Database Schema

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
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        string phone
        datetime created_at
        datetime last_login
        boolean is_active
    }

    ORDER {
        uuid id PK
        string order_number UK
        uuid customer_id FK
        decimal subtotal
        decimal tax_amount
        decimal total_amount
        datetime created_at
    }

    PRODUCT {
        uuid id PK
        string sku UK
        string name
        text description
        decimal price
        uuid category_id FK
        boolean is_active
    }
```

---

## 6. User Journey - Customer Purchase Experience

Complete customer journey mapping with emotional states and touchpoints.

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
      Loyalty points earned: 5: Customer, Loyalty System
```

---

## 7. Gantt Chart - Software Development Project

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

    section Backend Development
    API design              :api1, after des1, 5d
    User authentication     :crit, api2, after api1, 8d
    User management API     :api3, after api2, 6d
    Product catalog API     :api4, after api2, 7d
    Order management API    :crit, api5, after api3, 9d
    Payment integration     :crit, api6, after api5, 10d

    section Frontend Development
    UI/UX design           :crit, ui1, after des1, 12d
    Design system          :ui2, after ui1, 7d
    Component library      :ui3, after ui2, 8d
    Homepage              :fe1, after ui3, 5d
    Shopping cart         :crit, fe4, after fe1, 8d
    Checkout flow         :crit, fe5, after fe4, 10d

    section Testing
    Integration testing       :crit, test3, after api6, 8d
    Performance testing      :crit, test6, after test3, 7d
    User acceptance testing  :crit, uat, after test6, 10d

    section Deployment
    Production deployment    :milestone, m5, after uat, 1d
```

---

## 8. Pie Chart - Customer Acquisition Channels

Distribution visualization showing channel performance.

```mermaid
pie title Customer Acquisition Channels - Q4 2024
    "Organic Search (SEO)" : 32.5
    "Paid Advertising (PPC)" : 24.3
    "Social Media" : 18.7
    "Email Marketing" : 12.4
    "Referrals" : 8.2
    "Direct Traffic" : 3.9
```

---

## 9. Quadrant Chart - Feature Prioritization

Prioritization matrix for feature development planning.

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
    API rate limiting: [0.3, 0.9]
    Real-time analytics: [0.9, 0.95]
    Bulk operations: [0.5, 0.8]
    Automated backups: [0.4, 0.95]
    Multi-language support: [0.75, 0.7]
```

---

## 10. Requirement Diagram - System Requirements

Complex requirement relationships and traceability matrix.

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

    element auth_service {
        type: service
        docref: docs/auth_service.md
    }

    element database {
        type: database
        docref: docs/database_schema.md
    }

    user_auth - contains -> two_factor
    user_auth - contains -> password_policy
    user_auth - satisfies -> data_encryption
    user_auth - satisfies -> performance

    auth_service - satisfies -> user_auth
    database - satisfies -> data_encryption
```

---

## 11. GitGraph - Git Branching Strategy

Complex Git workflow with releases and hotfixes.

```mermaid
%%{init: { 'gitGraph': {'mainBranchName': 'main'}} }%%
gitGraph
    commit id: "Initial commit"
    commit id: "Add README"

    branch develop
    checkout develop
    commit id: "Setup project"

    branch feature/user-auth
    checkout feature/user-auth
    commit id: "Add login API"
    commit id: "Add registration"

    checkout develop
    branch feature/products
    checkout feature/products
    commit id: "Create product model"

    checkout feature/user-auth
    commit id: "Add auth tests"

    checkout develop
    merge feature/user-auth tag: "v0.1.0"

    checkout feature/products
    commit id: "Add product search"

    checkout develop
    merge feature/products

    branch release/1.0
    checkout release/1.0
    commit id: "Update version"

    checkout main
    merge release/1.0 tag: "v1.0.0"

    checkout develop
    merge release/1.0

    checkout main
    branch hotfix/security
    checkout hotfix/security
    commit id: "Fix vulnerability"

    checkout main
    merge hotfix/security tag: "v1.0.1"

    checkout develop
    merge hotfix/security
```

---

## 12. Mindmap - Software Architecture Overview

Hierarchical architecture knowledge mapping.

```mermaid
mindmap
  root((Software Architecture))
    Frontend
      Frameworks
        React
        Vue
        Angular
      State Management
        Redux
        MobX
        Zustand
      Styling
        Tailwind CSS
        Styled Components
    Backend
      Languages
        Python
          FastAPI
          Django
        Node.js
          Express
          NestJS
        Go
      Databases
        PostgreSQL
        MongoDB
        Redis
      APIs
        REST
        GraphQL
        gRPC
    Infrastructure
      Cloud
        AWS
        Azure
        GCP
      Containers
        Docker
        Kubernetes
      CI/CD
        GitHub Actions
        Jenkins
```

---

## 13. Timeline - Product Development History

Product development milestones and key events.

```mermaid
timeline
    title Product Development Timeline - 2024-2025

    section Q1 2024
        January 2024 : Project Inception
                     : Market Research
        February 2024 : Requirements Finalized
                      : Team Onboarding
        March 2024 : MVP Design
                   : Database Schema

    section Q2 2024
        April 2024 : Development Kickoff
                   : Core Features Built
        May 2024 : Integration Testing
                 : Security Audit
        June 2024 : Beta Release
                  : User Testing

    section Q3 2024
        July 2024 : v1.0 Launch
                  : First 1000 Users
        August 2024 : Feature Expansion
                    : 5000 Users Milestone
        September 2024 : v1.1 Release
                       : 10000 Users

    section Q4 2024
        October 2024 : Enterprise Features
                     : SSO Implementation
        November 2024 : v2.0 Beta
                      : AI Features
        December 2024 : v2.0 Launch
                      : 50000 Users
```

---

## 14. Sankey Diagram - Website Traffic Flow

Flow visualization showing traffic sources and conversion paths.

```mermaid
%%{init: {'theme':'base'}}%%
sankey-beta

Website Traffic,Organic Search,50000
Website Traffic,Paid Ads,30000
Website Traffic,Social Media,25000
Website Traffic,Direct,15000

Organic Search,Homepage,35000
Organic Search,Product Pages,12000

Paid Ads,Product Pages,22000
Paid Ads,Landing Pages,8000

Social Media,Homepage,15000
Social Media,Product Pages,7000

Direct,Homepage,10000

Homepage,Product Viewed,25000
Homepage,Bounce,25000

Product Pages,Add to Cart,25000
Product Pages,Bounce,15000

Product Viewed,Add to Cart,17000

Add to Cart,Checkout,30000
Add to Cart,Continue Shopping,12000

Checkout,Purchase Complete,22000
Checkout,Abandoned,8000
```

---

## 15. XY Chart - Revenue Metrics

Revenue and expense tracking over time.

```mermaid
xychart-beta
    title "Monthly Revenue vs. Expenses - 2024"
    x-axis [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
    y-axis "Amount ($1000s)" 0 --> 200
    bar [65, 72, 78, 85, 92, 98, 105, 112, 125, 135, 145, 160]
    line [45, 48, 52, 58, 62, 68, 72, 78, 82, 88, 92, 98]
```

---

## 16. Block Diagram - System Architecture

Microservices architecture with component relationships.

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
        NotificationService["Notification"]
    end

    block:data["Data Layer"]
        columns 3
        PostgreSQL[("PostgreSQL")]
        Redis[("Redis Cache")]
        S3[("S3 Storage")]
    end

    WebApp --> APIGateway
    MobileApp --> APIGateway
    AdminPanel --> APIGateway

    APIGateway --> LoadBalancer
    LoadBalancer --> AuthService
    LoadBalancer --> UserService
    LoadBalancer --> ProductService

    AuthService --> PostgreSQL
    UserService --> PostgreSQL
    ProductService --> Redis
```

---

## Summary

This document showcases 16 different Mermaid diagram types, each demonstrating:
- Advanced syntax and features
- Real-world use cases
- Complex relationships and hierarchies
- Professional styling and layout

These diagrams were automatically converted to images and uploaded to ClickUp using the framework's built-in Mermaid processing capabilities.
