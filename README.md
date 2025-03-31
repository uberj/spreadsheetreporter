# 📊 Spreadsheet Processor Pro

Transform your Excel spreadsheets into beautiful, professional PDF reports with just a few clicks! 

## ✨ Features

- 📤 **Easy Upload**: Simply upload your Excel (.xlsx) files
- 📄 **Automated PDF Generation**: Each row becomes a beautifully formatted PDF report
- 📦 **Batch Processing**: Download all reports as a single ZIP file
- 🎨 **Professional Design**: Clean, modern PDF layouts with custom styling
- ⚡ **Lightning Fast**: Optimized processing for large spreadsheets
- 🔍 **Smart Validation**: Built-in file validation and error handling
- 🏥 **Health Monitoring**: Built-in health check endpoint for system monitoring

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Conda environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spreadsheetdemo.git
cd spreadsheetdemo
```

2. Create and activate the conda environment:
```bash
conda create -n spreadsheetdemo python=3.8
conda activate spreadsheetdemo
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application!

## 🛠️ Tech Stack

- **Backend**: Django 5.0.2
- **Data Processing**: Pandas 2.2.1
- **Excel Handling**: OpenPyXL 3.1.2
- **PDF Generation**: ReportLab 4.1.0
- **Template Engine**: Jinja2 3.1.3
- **Markdown Support**: Markdown 3.5.2
- **HTML Parsing**: BeautifulSoup4 4.13.0

## 🌟 Key Features in Detail

### PDF Report Generation
- Custom styled headers and content
- Responsive table layouts
- Professional color scheme
- Automatic text wrapping
- PST timezone timestamps

### File Management
- Secure file upload handling
- Excel file validation
- Efficient storage management
- Batch processing capabilities

### User Interface
- Clean, intuitive design
- Real-time feedback
- Error handling and notifications
- Progress tracking

## 🔒 Security Features

- CSRF protection
- File type validation
- Secure file handling
- Error logging and monitoring

## 🚀 Deployment

The application includes deployment scripts for cloud environments:

- `create_instance.sh`: Creates a new cloud instance
- `deploy_app.sh`: Deploys the application
- `check_health.sh`: Monitors application health
- `connect_instance.sh`: Connects to the instance
- `delete_instance.sh`: Cleanup script

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Made with ❤️ by Your Team Name 