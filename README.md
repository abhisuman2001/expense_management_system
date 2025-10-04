# Expense Management System

A comprehensive expense management system built with Flask (Python) backend and React frontend.

## Features

### Core Features
- **Multi-role Authentication**: Admin, Manager, and Employee roles with different permissions
- **Company Management**: Auto-create company on first signup with currency support
- **User Management**: Create employees, assign managers, and manage relationships
- **Expense Submission**: Submit expenses with currency conversion support
- **Multi-level Approval Workflow**: Configurable approval rules and workflows
- **OCR Receipt Scanning**: Automatically extract expense details from receipt images
- **Real-time Currency Conversion**: Support for multiple currencies with live exchange rates
- **Dashboard & Analytics**: Role-based dashboards with expense insights

### Technical Features
- JWT-based authentication
- Role-based access control
- RESTful API design
- Responsive Material-UI interface
- PostgreSQL/SQLite database support
- File upload handling
- External API integrations

## Project Structure

```
expense_management_system/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   └── utils/           # Helper functions
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── components/      # Reusable React components
    │   ├── pages/           # Page components
    │   ├── services/        # API calls
    │   ├── context/         # React context
    │   └── utils/           # Helper functions
    ├── package.json
    └── public/
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL (optional, SQLite works for development)
- Tesseract OCR (for receipt scanning)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Copy and edit the .env file
cp .env.example .env
```

Edit `.env` with your configuration:
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///expense_management.db
TESSERACT_CMD_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

5. Initialize the database:
```bash
python run.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

### OCR Setup (Optional)

1. Download and install Tesseract OCR:
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt-get install tesseract-ocr`

2. Update the `TESSERACT_CMD_PATH` in your `.env` file

## Running the Application

1. Start the backend server:
```bash
cd backend
python run.py
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user and company
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/change-password` - Change password

### Users
- `GET /api/users/` - Get users (role-based)
- `POST /api/users/create` - Create new user (admin only)
- `PUT /api/users/{id}` - Update user
- `POST /api/users/{id}/deactivate` - Deactivate user

### Expenses
- `POST /api/expenses/submit` - Submit new expense
- `GET /api/expenses/` - Get expenses (with filtering)
- `GET /api/expenses/{id}` - Get expense details
- `GET /api/expenses/currencies` - Get supported currencies

### Approvals
- `GET /api/approvals/pending` - Get pending approvals
- `POST /api/approvals/{id}/approve` - Approve expense
- `POST /api/approvals/{id}/reject` - Reject expense
- `GET /api/approvals/history` - Get approval history

### OCR
- `POST /api/ocr/extract` - Extract data from receipt image

### Company
- `GET /api/company/info` - Get company information
- `GET /api/company/categories` - Get expense categories
- `POST /api/company/categories` - Create expense category

## User Roles & Permissions

### Admin
- Full system access
- Create and manage users
- Configure approval rules
- View all company expenses
- Override approvals

### Manager
- Approve/reject team expenses
- View team member expenses
- Escalate approvals per rules
- Submit own expenses

### Employee
- Submit expense claims
- View own expense history
- Check approval status
- Upload receipts with OCR

## Default Test Users

After running the application for the first time, create an admin account through registration. This will:
- Create a new company
- Set up default expense categories
- Make the first user an admin

## Technologies Used

### Backend
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **Flask-JWT-Extended**: Authentication
- **Flask-CORS**: Cross-origin requests
- **pytesseract**: OCR functionality
- **requests**: External API calls
- **bcrypt**: Password hashing

### Frontend
- **React**: UI framework
- **Material-UI**: Component library
- **React Router**: Navigation
- **Axios**: HTTP client
- **React Hook Form**: Form handling
- **React Toastify**: Notifications

### External APIs
- **REST Countries API**: Country and currency data
- **ExchangeRate API**: Currency conversion rates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please create an issue in the repository or contact the development team.