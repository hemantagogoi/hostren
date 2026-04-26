# Question Paper Generator

A full-stack automated question paper generation system built with Flask, PostgreSQL, and modern UI/UX design.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

### Installation Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Database**
   - Create a PostgreSQL database named `question_paper_db`
   - Update database credentials in `.env` file if needed

3. **Initialize Database Tables**
   ```bash
   python init_college.py
   ```

4. **Start the Application**
   ```bash
   # Development mode
   python app.py
   
   # Production mode
   python app.py
   ```

5. **Access the Application**
   - Open your browser and go to: http://localhost:3000
   
   - **Admin Login**: http://localhost:3000/auth/admin/login
     - Email: `admin@qpg.com`
     - Password: `admin123`
   
   - **User Login**: http://localhost:3000/auth/login
     - Users must be created by admin (no public registration)

## 📋 Features

### 🔐 Authentication System
- Admin-only user creation (no public registration)
- Secure session-based authentication
- Role-based access control (Admin/User)
- bcrypt password hashing

### 👨‍💼 Admin Features
- Advanced dashboard with statistics and charts
- User management (CRUD operations)
- Academic management (courses, departments, classes, subjects)
- Question management with advanced filtering
- Activity logging and monitoring

### 👤 User Features
- Personalized dashboard with paper history
- Advanced paper generation with filtering options
- PDF generation and download
- Paper viewing and management

### 🎨 UI/UX Features
- Modern glass-morphism design
- Responsive layout for all devices
- Smooth animations and transitions
- Professional color schemes

## 🗄️ Database Setup

### PostgreSQL Configuration
1. Install PostgreSQL on your system
2. Create a database:
   ```sql
   CREATE DATABASE question_paper_db;
   ```
3. Create a user (optional):
   ```sql
   CREATE USER qpg_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE question_paper_db TO qpg_user;
   ```

### Environment Variables
Update the `.env` file with your database credentials:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=question_paper_db
DB_USER=postgres
DB_PASSWORD=your_password
```

## 📁 Project Structure

```
render-main/
├── package.json                 # Dependencies and scripts
├── .env                        # Environment variables
├── server.js                   # Main Express server
├── config/
│   └── database.js            # PostgreSQL connection
├── middleware/
│   └── auth.js                # Authentication middleware
├── routes/
│   ├── auth.js                # Authentication routes
│   ├── admin.js               # Admin management routes
│   ├── user.js                # User panel routes
│   ├── api.js                 # REST API endpoints
│   ├── academic.js            # Academic management routes
│   └── questions.js          # Question management routes
├── utils/
│   └── pdfGenerator.js        # PDF generation utility
├── views/                     # Handlebars templates
├── public/                    # Static files
└── scripts/
    └── initDatabase.js        # Database initialization
```

## 🔧 Development

### Available Scripts
```bash
# Start development server with auto-reload
npm run dev

# Start production server
npm start

# Initialize database
npm run init-db
```

### Environment Variables
```env
# Server Configuration
PORT=3000
NODE_ENV=development

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=question_paper_db
DB_USER=postgres
DB_PASSWORD=postgres

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRE=7d

# Session Configuration
SESSION_SECRET=your-super-secret-session-key
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/admin/login` - Admin login
- `GET /auth/logout` - Logout

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `POST /admin/users/add` - Add new user
- `GET /admin/courses` - Course management
- `GET /admin/departments` - Department management
- `GET /admin/classes` - Class management
- `GET /admin/subjects` - Subject management
- `GET /admin/questions` - Question management

### User Endpoints
- `GET /user/dashboard` - User dashboard
- `GET /user/generate-paper` - Paper generation page
- `POST /user/generate-paper` - Generate paper
- `GET /user/paper/:id` - View paper
- `GET /user/paper/:id/download` - Download paper

### API Endpoints
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/questions/filter` - Filter questions
- `GET /api/questions/search` - Search questions
- `GET /api/questions/stats` - Question statistics

## 🎯 Default Credentials

### Admin Account
- **Email**: admin@qpg.com
- **Password**: admin123

### User Accounts
- Users must be created by admin through the admin panel
- No public registration available

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env` file
   - Verify database exists

2. **Port Already in Use**
   - Change PORT in `.env` file
   - Kill process using the port: `netstat -ano | findstr :3000`

3. **Module Not Found**
   - Run `npm install` to install dependencies
   - Check Node.js version compatibility

4. **PDF Generation Issues**
   - Ensure Puppeteer dependencies are installed
   - On Windows, you may need additional Visual Studio build tools

### Logs
- Application logs are displayed in the console
- Database operations are logged
- Error messages include detailed information

## 🔒 Security Features

- bcrypt password hashing
- Session-based authentication
- Rate limiting
- Security headers (Helmet)
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 📱 Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support and questions, please create an issue in the repository.
