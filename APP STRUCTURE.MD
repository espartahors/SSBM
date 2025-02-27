# Project Structure Overview
SSBModel/           # Main Django project folder
├── manage.py
├── SSBModel/       # Project configuration
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── users/                 # User management app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── migrations/
│   ├── models.py
│   ├── templates/
│   │   └── users/
│   │       ├── login.html
│   │       ├── register.html
│   │       ├── profile.html
│   │       └── password_reset.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── parts/                 # Main parts management app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── migrations/
│   ├── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── csv_handler.py
│   │   └── document_handler.py
│   ├── templates/
│   │   └── parts/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── part_list.html
│   │       ├── part_detail.html
│   │       ├── part_form.html
│   │       ├── part_confirm_delete.html
│   │       ├── document_list.html
│   │       ├── document_detail.html
│   │       ├── document_form.html
│   │       └── import_csv.html
│   ├── static/
│   │   └── parts/
│   │       ├── css/
│   │       │   └── style.css
│   │       ├── js/
│   │       │   ├── tree.js
│   │       │   ├── marker.js
│   │       │   └── document_viewer.js
│   │       └── images/
│   │           └── icons/
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── requirements.txt
└── media/                 # For uploaded documents
    └── documents/