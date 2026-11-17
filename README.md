# ☕ Cafe Management System – Odoo 17

A custom Odoo ERP module designed to manage cafe operations, recipes, ingredients, Point of Sale integration, kitchen workflows, waste tracking, and profitability analysis.

![Odoo](https://img.shields.io/badge/Odoo-17.0-714B67?logo=odoo)
![Python](https://img.shields.io/badge/Python-Development-3776AB?logo=python)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?logo=javascript)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql)
![License](https://img.shields.io/badge/License-LGPL--3-blue)

---

## 📌 Project Overview

The Cafe Management System is a custom Odoo module that extends the standard Point of Sale functionality to support cafe-specific business operations.

It connects product recipes with inventory consumption, creates kitchen orders automatically after POS payments, tracks ingredient costs, and provides tools for waste and profitability management.

The goal is to connect daily cafe operations within one integrated ERP workflow.

## ✨ Key Features

### 1. Recipe & Ingredient Management
- Create and manage ingredients.
- Link ingredients to stockable products.
- Define recipes for POS products.
- Support product variants and different sizes.
- Calculate recipe costs.

### 2. Point of Sale Integration
- Automatically process ingredient consumption after payment.
- Support online and offline-synchronized POS orders.
- Prevent duplicate ingredient deductions.
- Check ingredient availability before payment when configured.
- Support configurable ingredient restocking on refunds.

### 3. Kitchen Management
- Automatically create kitchen orders from paid POS orders.
- Track kitchen order statuses.
- Provide a kitchen display using a custom Kanban interface.
- Notify the kitchen interface through the Odoo Bus.
- Generate kitchen ticket references.

### 4. Inventory Management
- Deduct ingredients through stock moves.
- Link stock moves to POS orders.
- Use the POS configuration's source location.
- Provide low-stock alerts.
- Support retrying failed ingredient consumption.

### 5. Waste Management
- Record wasted ingredients.
- Calculate waste costs.
- Confirm waste records.

### 6. Cost & Profit Analysis
- Calculate ingredient costs.
- Store cost information on POS order lines.
- Calculate gross profit.

### 7. Security & User Roles
- Custom access rights.
- Security groups for cafe operations.
- Separate operational roles, including cashier, barista, storekeeper, and manager.

---

## 🔄 Business Workflow

```text
Create Ingredients
        |
        v
Define Recipes
        |
        v
Link Recipes to POS Products
        |
        v
Customer Places an Order
        |
        v
POS Payment
        |
        v
Create Kitchen Order
        |
        v
Deduct Ingredients from Inventory
        |
        v
Calculate Cost and Profit
```

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Odoo 17 | ERP Framework |
| Python | Backend Business Logic |
| PostgreSQL | Database |
| XML | Views, Security and Reports |
| JavaScript | POS and Kitchen Interface |
| OWL / Odoo Web Assets | Frontend Integration |
| Git & GitHub | Version Control |

## 🏗️ Project Structure

```text
cafe_management/
│
├── data/
│   ├── cron.xml
│   ├── cafe_data.xml
│   └── sequence.xml
│
├── demo/
│   └── cafe_demo.xml
│
├── models/
│   ├── cafe_ingredient.py
│   ├── cafe_recipe.py
│   ├── cafe_recipe_line.py
│   ├── cafe_kitchen_order.py
│   ├── cafe_waste.py
│   ├── pos_order.py
│   ├── pos_session.py
│   └── stock_move.py
│
├── report/
│   └── cafe_receipt.xml
│
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
│
├── static/
│   └── src/
│       ├── backend/
│       └── pos/
│
├── tests/
│   └── test_consumption.py
│
├── views/
│
├── __init__.py
└── __manifest__.py
```

## ⚙️ Installation

### Requirements

- Odoo 17.0
- PostgreSQL
- Required Odoo modules:
  - point_of_sale
  - stock
  - account
  - mail
  - product
  - bus

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/Ahmed-Ibrahim023/odoo-cafe-management.git
```

2. Copy the `cafe_management` module into your Odoo custom addons directory.

3. Restart the Odoo server.

4. Update the Apps List.

5. Search for **Cafe Management**.

6. Install the module.

### Running Tests

Run the module tests using:

```bash
odoo -d DB -i cafe_management --test-tags /cafe_management --stop-after-init
```

Replace `DB` with your database name.

---

## 🧪 Testing

The project includes automated tests covering:

- Recipe cost calculation.
- Ingredient deduction with unit-of-measure conversion.
- Prevention of duplicate ingredient deductions.
- Ingredient availability checks.
- Kitchen ticket sequence consistency.

**Note:** Tests are included in the repository; execution and passing results should be verified in the target Odoo environment.

## 🔐 Important Design Considerations

- Idempotent ingredient consumption to avoid duplicate stock deductions.
- Failed consumption operations can be retried.
- POS sales are not blocked by server-side consumption errors.
- Ingredient restocking on refunds is configurable.
- Recipe selection supports product variants.
- Kitchen updates use Odoo Bus notifications.

## 📸 Screenshots

Screenshots of the application interface will be added here.

Planned screenshots:
- Cafe Dashboard
- Ingredients Management
- Recipe Management
- Point of Sale Integration
- Kitchen Display
- Waste Management
- Profit Analysis

## 👨‍💻 Project Information

**Project:** Cafe Management System

**Platform:** Odoo 17

**Repository:** [odoo-cafe-management](https://github.com/Ahmed-Ibrahim023/odoo-cafe-management)

**Developer:** Ahmed Mohamed Ibrahim

**Development Note:** This project was created with AI assistance using Claude. It is included in my developer portfolio as a practical project for learning, understanding, testing, and demonstrating Odoo customization and ERP integration.

## 📄 License

This module is distributed under the LGPL-3 license, as specified in its manifest.

---

⭐ If you find this project interesting, feel free to explore the repository.

**Always learning. Always building.**
