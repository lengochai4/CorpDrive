import sqlite3
import uuid
import random

conn = sqlite3.connect('corpdrive.db')
c = conn.cursor()

c.executescript('''
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS activity_logs;

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE,
    username TEXT UNIQUE,
    password TEXT,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    citizen_id TEXT,
    department TEXT,
    position TEXT,
    salary TEXT,
    bio TEXT,
    role TEXT
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE,
    owner_id INTEGER,
    filename TEXT,
    category TEXT,
    content TEXT
);

CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    username TEXT,
    action TEXT,
    target TEXT,
    status TEXT,
    note TEXT
);
''')

# Tạo User 1 (Hải - Hacker/Tester) & User 2 (Ân - Trưởng phòng/Mục tiêu)
users = [
    (str(uuid.uuid4()), 'hai', 'hai123', 'Nguyễn Văn Hải', 'hai.nv@corpdrive.vn', '0901112233', '079099001122', 'Kỹ thuật Hệ thống', 'Chuyên viên IT', '18,000,000 VND', 'Nhân viên mới phòng IT', 'staff'),
    (str(uuid.uuid4()), 'an', 'an123', 'Trần Minh Ân', 'an.tm@corpdrive.vn', '0988999888', '001085009988', 'Vận hành & Bảo mật', 'Trưởng phòng Vận hành', '55,000,000 VND', 'Mã PIN két sắt nội bộ: 8842 - Truy cập /network-check để kiểm tra server', 'manager')
]

first_names = ['Minh', 'Lan', 'Tuấn', 'Hương', 'Dũng', 'Thảo', 'Hoàng', 'Linh', 'Nam', 'Trang', 'Phúc', 'Ngọc', 'Khang', 'Vy']
last_names = ['Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ']
depts = ['Kinh doanh', 'Kế toán', 'Nhân sự', 'Marketing', 'Phát triển Phần mềm']

for i in range(3, 31):
    full_name = f"{random.choice(last_names)} Văn {random.choice(first_names)} {i}"
    uname = f"user{i:02d}"
    users.append((
        str(uuid.uuid4()), uname, '123456', full_name, f"{uname}@corpdrive.vn",
        f"09{random.randint(10000000, 99999999)}", f"0790{random.randint(10000000, 99999999)}",
        random.choice(depts), 'Nhân viên', f"{random.randint(12, 30)},000,000 VND",
        f"Ghi chú bảo mật cá nhân của {uname}", 'staff'
    ))

c.executemany('''
INSERT INTO employees (uuid, username, password, full_name, email, phone, citizen_id, department, position, salary, bio, role)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', users)

# Tạo 45 tài liệu (file_id 1, 2 của Hải; file_id 3, 4 của Ân; còn lại của user 3..30)
docs = [
    (str(uuid.uuid4()), 1, 'Bao_cao_tuan_Hai.txt', 'Cá nhân', 'Báo cáo tiến độ công việc tuần 1 của Nguyễn Văn Hải.'),
    (str(uuid.uuid4()), 1, 'Ghi_chu_ca_nhan_Hai.txt', 'Cá nhân', 'Danh sách công việc cần hoàn thành trong tháng.'),
    (str(uuid.uuid4()), 2, 'Bang_luong_Ban_Giam_Doc_2026.txt', 'Tài chính - Mật', 'MẬT: Tổng quỹ thưởng Q4 của Ban Giám Đốc là 2.5 tỷ VND. Gợi ý hệ thống: Công cụ Ping nội bộ nằm tại /network-check.'),
    (str(uuid.uuid4()), 2, 'Mat_khau_Server_Backup.txt', 'Nội bộ - Mật', 'Server Backup IP: 10.0.0.15 | User: root | Pass: Sup3rS3cr3t!2026')
]

for i in range(5, 46):
    owner = random.randint(3, 30)
    docs.append((
        str(uuid.uuid4()), owner, f"Tai_lieu_noi_bo_{i:02d}.txt",
        random.choice(['Nội bộ', 'Tài chính', 'Hợp đồng']),
        f"Nội dung tài liệu mật số {i} thuộc quyền sở hữu của nhân viên ID={owner}."
    ))

c.executemany('INSERT INTO documents (uuid, owner_id, filename, category, content) VALUES (?, ?, ?, ?, ?)', docs)

with open('system_info.txt', 'w', encoding='utf-8') as f:
    f.write("CORPDRIVE SERVER SECRET FLAG: FLAG{OS_C0mm4nd_Inj3ct10n_D3m0_2026}\nServer Admin: Tran Minh An\n")

conn.commit()
conn.close()
print("Khởi tạo database corpdrive.db và system_info.txt thành công!")