# Expense & Inventory Management System (AI Enhanced)

A modern, responsive web application for tracking restaurant or business expenses, managing warehouse stocks, and recipe costing.

## Features
- **Expense Tracking**: Register invoices with AI-suggested categories.
- **Warehouse Management**: Track stock movements, branches, and locations.
- **Recipe Costing**: Calculate profit margins for recipes with automatic material deduction.
- **Multilingual Support**: Arabic, Chinese, and English UI.
- **Modern Dashboard**: Chart.js analytics for financial monitoring.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **Database**: SQLite (SQLAlchemy ORM)

## Local Installation
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start the server: `uvicorn backend.main:app --reload`.

## Deployment
This application is ready for deployment on **Render** or **Railway**.
- Continuous Deployment via GitHub integration.
- Auto-starts via `Procfile`.
