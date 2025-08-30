# NearTools Deployment Guide

## 🚀 Deploy to Streamlit Cloud

### 1. GitHub Repository Setup ✅
Your repository is already set up at: `https://github.com/mauryatalluru/neartools.git`

### 2. Streamlit Cloud Deployment

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
2. **Sign in with GitHub**
3. **Click "New app"**
4. **Fill in the details:**
   - **Repository**: `mauryatalluru/neartools`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Will be auto-generated

### 3. Environment Variables (Optional)
If you want to customize the cookie password:
- Go to your app settings in Streamlit Cloud
- Add environment variable: `COOKIE_PASSWORD` with your desired password

### 4. Deploy! 🎉
Click "Deploy" and wait for the build to complete.

---

## 🔧 Local Development

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Development Server
- **Local URL**: `http://localhost:8501`
- **Network URL**: `http://192.168.x.x:8501` (for testing on other devices)

---

## 📁 Project Structure
```
neartools/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── .streamlit/           # Streamlit configuration
│   ├── config.toml      # Theme and settings
│   └── secrets.toml     # Local secrets (not in git)
├── data/                 # SQLite database (local only)
├── images/               # Tool images (local only)
├── pages/                # Additional pages (if any)
└── logo.png             # App logo
```

---

## 🎨 Customization

### Logo
- Place your logo as `logo.png` in the project root
- Supported formats: PNG, JPG
- Recommended size: 200x200px or larger

### Theme Colors
Edit `.streamlit/config.toml` to customize:
- Primary color
- Background colors
- Text color
- Font

### Admin Access
Set your email in `app.py`:
```python
ADMIN_EMAIL = "your.email@example.com"
```

---

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all dependencies are in `requirements.txt`
   - Run `pip install -r requirements.txt`

2. **Database errors**
   - The app auto-creates the database on first run
   - Check file permissions for the `data/` directory

3. **Image upload issues**
   - Ensure the `images/` directory exists
   - Check file permissions

4. **Cookie errors**
   - Clear browser cookies
   - Check if `streamlit-cookies-manager` is installed

### Local vs Cloud Differences
- **Local**: Uses local SQLite database and file storage
- **Cloud**: Uses Streamlit Cloud's ephemeral storage (data resets on restart)

---

## 📊 Features

### Core Functionality
- ✅ User registration and login
- ✅ Tool listing and management
- ✅ Booking system
- ✅ Review system
- ✅ Search and filtering
- ✅ Responsive design

### Technical Features
- ✅ SQLite database
- ✅ Cookie-based authentication
- ✅ File upload handling
- ✅ Date validation
- ✅ Error handling

---

## 🔒 Security Notes

- Passwords are hashed using SHA-256
- SQL injection protection via parameterized queries
- User authentication required for sensitive operations
- Admin reset functionality (use responsibly)

---

## 📈 Performance Tips

1. **Database**: SQLite is lightweight and fast for small to medium apps
2. **Images**: Compress images before upload for faster loading
3. **Caching**: Streamlit automatically caches expensive operations
4. **Lazy Loading**: Images and data load only when needed

---

## 🆘 Support

If you encounter issues:
1. Check the Streamlit Cloud logs
2. Verify all dependencies are installed
3. Check file permissions
4. Review the error messages in the app

---

**Happy Deploying! 🚀**
