# 🤖 ZeroX AI Platform

<div align="center">

![ZeroX AI](https://img.shields.io/badge/ZeroX-AI-blue?style=for-the-badge&logo=openai)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react)

**منصة ذكاء اصطناعي متكاملة مبنية بنماذج مجانية مفتوحة المصدر**

[English](#english) | [العربية](#arabic)

</div>

---

<a name="english"></a>
## 🌟 Features

### 🆓 100% Free AI Models
- **Llama 3.1 70B** - Meta's most powerful open model
- **Mixtral 8x7B** - Mistral's mixture of experts
- **Gemma 2** - Google's efficient model
- Powered by **Groq** (ultra-fast inference)

### 🔐 Enterprise-Grade Security
- JWT authentication with refresh tokens
- Encrypted API key storage
- Rate limiting per user
- Role-based access control (User/Premium/Admin)

### 💬 Professional Chat Interface
- Real-time streaming responses
- Markdown & code syntax highlighting
- Conversation history
- Multiple AI models selection

### 👥 User Management
- User registration & login
- Profile customization
- Usage tracking & limits
- Admin dashboard

### 📊 Admin Dashboard
- Platform statistics
- User management
- Role assignment
- Activity monitoring

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free API key from [Groq](https://console.groq.com)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔑 Getting Free API Keys

### Groq (Recommended - Ultra Fast!)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for free
3. Create an API key
4. Add to `.env` as `GROQ_API_KEY`

### Hugging Face (Optional)
1. Go to [huggingface.co](https://huggingface.co/settings/tokens)
2. Create a free account
3. Generate an access token
4. Add to `.env` as `HUGGINGFACE_API_KEY`

---

## 📁 Project Structure

```
zerox-ai/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── models/          # Database models
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   └── utils/           # Utilities
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── context/         # React context
│   │   ├── utils/           # Utilities
│   │   └── styles/          # CSS styles
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🛠️ API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login user |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Get current user |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/send` | Send message (streaming) |
| GET | `/api/v1/chat/conversations` | Get conversations |
| GET | `/api/v1/chat/conversations/{id}` | Get conversation |
| DELETE | `/api/v1/chat/conversations/{id}` | Delete conversation |

### Models
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/models` | Get available models |
| GET | `/api/v1/models/free` | Get free models |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/stats` | Get platform stats |
| GET | `/api/v1/admin/users` | Get all users |
| PUT | `/api/v1/admin/users/{id}/role` | Update user role |

---

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Short-lived access + long-lived refresh
- **API Key Encryption**: Fernet symmetric encryption
- **Rate Limiting**: Per-user daily limits
- **CORS Protection**: Configurable origins
- **Input Validation**: Pydantic schemas

---

## 📈 Scaling for Production

### Database
Replace SQLite with PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/zerox_ai
```

### Caching
Add Redis for session management:
```env
REDIS_URL=redis://localhost:6379
```

### Deployment
- Use Docker for containerization
- Deploy on AWS/GCP/Azure
- Use Nginx as reverse proxy
- Enable HTTPS with Let's Encrypt

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

<a name="arabic"></a>
## 🌟 المميزات (العربية)

### 🆓 نماذج ذكاء اصطناعي مجانية 100%
- **Llama 3.1 70B** - أقوى نموذج مفتوح من Meta
- **Mixtral 8x7B** - نموذج Mistral المتقدم
- **Gemma 2** - نموذج Google الفعال
- مدعوم بـ **Groq** (استجابة فائقة السرعة)

### 🔐 أمان على مستوى المؤسسات
- مصادقة JWT مع رموز التحديث
- تخزين مشفر لمفاتيح API
- تحديد معدل الاستخدام لكل مستخدم
- التحكم في الوصول حسب الدور

### 💬 واجهة دردشة احترافية
- استجابات متدفقة في الوقت الفعلي
- تنسيق Markdown وتمييز الكود
- سجل المحادثات
- اختيار نماذج AI متعددة

---

## 🚀 البدء السريع

### المتطلبات
- Python 3.10+
- Node.js 18+
- مفتاح API مجاني من [Groq](https://console.groq.com)

### إعداد الخادم الخلفي

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# أضف GROQ_API_KEY في ملف .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### إعداد الواجهة الأمامية

```bash
cd frontend
npm install
npm run dev
```

---

<div align="center">

**صنع بـ ❤️ بواسطة ZeroX Team**

</div>
