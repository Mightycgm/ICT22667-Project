# 🏢 ระบบจัดการอพาร์ทเม้นต์

> ระบบจัดการอพาร์ทเม้นต์ครบวงจร พัฒนาด้วย Django + MySQL  
> รองรับการจัดการห้องพัก ผู้เช่า สัญญา ใบแจ้งหนี้ และการจดมิเตอร์ออนไลน์

---

## 📋 Tech Stack

| ส่วน | เทคโนโลยี |
|---|---|
| Backend | Django 4.2 (Python) |
| Database | MySQL ผ่าน XAMPP |
| Frontend | Django Templates + Bootstrap 5 |
| DB Connector | mysqlclient |

---

## ⚙️ การติดตั้ง (Setup Guide)

### ✅ สิ่งที่ต้องมีก่อน

- [Python 3.10+](https://www.python.org/downloads/)
- [XAMPP](https://www.apachefriends.org/) (สำหรับ MySQL)
- Git

---

### 📥 ขั้นตอนที่ 1 — Clone โปรเจค

```bash
git clone https://github.com/Mightycgm/ICT22667-Project.git
cd Apartment Management Project
```

---

### 📦 ขั้นตอนที่ 2 — ติดตั้ง Packages

```bash
pip install django==4.2.29 mysqlclient python-dotenv
```

---

### 🗄️ ขั้นตอนที่ 3 — สร้าง Database

1. เปิด **XAMPP Control Panel** → กด **Start** ที่ MySQL
2. เปิดเบราว์เซอร์ไปที่ `http://localhost/phpmyadmin`
3. คลิก **New** แล้วตั้งค่าดังนี้

| ค่า | รายละเอียด |
|---|---|
| Database name | `apartment_db` |
| Collation | `utf8mb4_unicode_ci` |

4. กด **Create**

---

### 🔐 ขั้นตอนที่ 4 — ตั้งค่าไฟล์ .env

```bash
cp .env.example .env
```

เปิดไฟล์ `.env` แล้วแก้ค่าต่อไปนี้

```env
SECRET_KEY='django-insecure-ใส่ค่าสุ่มอะไรก็ได้ยาวๆ'
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
```

### วิธีหาค่าแต่ละตัว

**`SECRET_KEY`**
> copy มาจาก `settings.py` บรรทัดที่ขึ้นต้นด้วย `SECRET_KEY = '...'`  
> หรือสร้างใหม่ได้ด้วยคำสั่ง:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

**`EMAIL_HOST_USER`**
> ใส่ Gmail ที่จะใช้ส่งใบแจ้งหนี้ เช่น `myapartment@gmail.com`

**`EMAIL_HOST_PASSWORD`**
> ไม่ใช่รหัสผ่าน Gmail ปกติ แต่เป็น **Google App Password** (16 หลัก)  
> สร้างได้ดังนี้:
> 1. เข้า [myaccount.google.com](https://myaccount.google.com) → **Security**
> 2. เปิด **2-Step Verification** ก่อน (ถ้ายังไม่ได้เปิด)
> 3. ค้นหา **App passwords** → กด Create
> 4. เลือก **Mail** + **Windows Computer** → Copy password 16 หลักมาใส่

---

### 🔧 ขั้นตอนที่ 5 — Migrate สร้างตาราง

```bash
python manage.py migrate
```

---

### 🚀 ขั้นตอนที่ 6 — รัน Setup Files ตามลำดับ

```bash
# 1. สร้าง superuser (admin หลักของระบบ)
python manage.py createsuperuser

# 2. สร้าง Group และกำหนด Permission แต่ละ Role
python setup_groups.py

# 3. สร้าง User สำหรับแต่ละ Role
python create_users.py

# 4. Seed ข้อมูลห้องและข้อมูลตัวอย่าง
python seed_rooms.py
```

---

### ▶️ ขั้นตอนที่ 7 — รันระบบ

```bash
python manage.py runserver
```

เปิดเบราว์เซอร์ไปที่ 👉 `http://127.0.0.1:8000`

---

## 👤 Account สำหรับ Login

| Username | Password | Role | สิทธิ์ |
|---|---|---|---|
| *(ตั้งใน createsuperuser)* | *(ตั้งเอง)* | ADMIN | ทุกอย่าง |
| `manager01` | `pass1234` | MANAGER | จัดการสัญญา/ใบแจ้งหนี้ |
| `staff01` | `pass1234` | STAFF | จอง/แจ้งซ่อม/จดมิเตอร์ |
| `readonly01` | `pass1234` | READONLY | ดูข้อมูลอย่างเดียว |
| `meter01` | `pass1234` | METER | จดมิเตอร์ (หน้ามือถือ) |

---

## 🗂️ โครงสร้างไฟล์สำคัญ

```
apartment_project/
├── manage.py
├── .env                 ← สร้างเองจาก .env.example (ห้าม push ขึ้น GitHub)
├── .env.example         ← template สำหรับตั้งค่า
├── setup_groups.py      ← สร้าง Role และ Permission
├── create_users.py      ← สร้าง User ตัวอย่าง
├── seed_rooms.py        ← Seed ข้อมูลห้องและผู้เช่าตัวอย่าง
├── apartment_project/
│   ├── settings.py
│   └── urls.py
└── apartment/
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    ├── decorators.py
    ├── middleware.py
    ├── context_processors.py
    └── templates/
```

---

## ✨ Features หลัก

- 🏠 **Dashboard** — แสดงสถานะห้องทุกห้องแบบ Grid พร้อม Color Badge
- 👤 **จัดการผู้เช่า** — CRUD + ค้นหา
- 📋 **สัญญาเช่า** — สร้าง/แก้ไข/พิมพ์สัญญา
- 📌 **ระบบจอง** — จองห้อง → ยืนยันสัญญา
- ⚡ **จดมิเตอร์** — หน้า Desktop (นิติ) + หน้ามือถือ (แม่บ้าน)
- 📄 **ใบแจ้งหนี้** — Auto-generate วันที่ 25 + ส่งอีเมล์
- 🔧 **แจ้งซ่อม** — บันทึก/อัปเดตสถานะ
- 📊 **รายงานสรุป** — สรุปยอดรายเดือน
- 🖨️ **พิมพ์** — ใบแจ้งหนี้ + สัญญา พร้อม QR Code PromptPay
- 🔐 **Role System** — 5 ระดับสิทธิ์ (ADMIN/MANAGER/STAFF/READONLY/METER)

---

## 📅 Business Rules

| กิจกรรม | วันที่ |
|---|---|
| จดมิเตอร์ | 22-23 ของทุกเดือน |
| ออกใบแจ้งหนี้ (Auto) | 25 ของทุกเดือน |
| ครบกำหนดชำระ | 5 ของเดือนถัดไป |
| เกินกำหนด → อัปเดตอัตโนมัติ | ทุกครั้งที่เปิด Dashboard |

---

## ⚠️ หมายเหตุ

- ไฟล์ `.env` **ห้าม** push ขึ้น GitHub เด็ดขาด
- รัน `setup_groups.py` **ก่อน** `create_users.py` เสมอ
- รัน `seed_rooms.py` ใหม่ทุกครั้งที่ต้องการรีเซ็ตข้อมูล (จะลบข้อมูลเดิมทั้งหมด)

---

## 👥 ทีมพัฒนา

> โปรเจคนี้เป็นส่วนหนึ่งของวิชา ICT22667 — งานกลุ่มระดับมหาวิทยาลัย
