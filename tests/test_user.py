from fastapi.testclient import TestClient
import sys
import os

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将项目根目录添加到sys.path
sys.path.insert(0, project_root)

print(sys.path)

from app.main import app
from app.db.session import SessionLocal

client = TestClient(app)
# 初始化全局变量headers
Headers = {}


def setup_headers():
    global Headers
    # 模拟登录获取令牌
    login_response = client.post("/public/login", json={
        "email": "22371147@buaa.edu.cn",
        "password": "123456"
    })
    assert login_response.status_code == 200
    token = login_response.json().get('access_token')
    if token is None:
        raise ValueError("Failed to get access_token from login response")
    Headers = {"Authorization": f"Bearer {token}"}


def test_user_case1():
    db = SessionLocal()
    db.begin() 
    try:
        global Headers
        if not Headers:
            setup_headers()
        # 修改信息
        save_response = client.get("/user", headers=Headers)
        assert save_response.status_code == 200
        save_data = save_response.json()
        
        advise_response = client.put("/user", data={"username":"李国庆test",
                                                    "address": "北京市海淀区中关村",
                                                    "university": "北京大学",
        }, headers=Headers)
        assert advise_response.status_code == 200

        # 获取修改后的信息
        adviser_response = client.get("/user", headers=Headers)
        assert adviser_response.status_code == 200
        assert adviser_response.json().get('address') == "北京市海淀区中关村"
        assert adviser_response.json().get('university') == "北京大学"
        assert adviser_response.json().get('username') == "李国庆test"

        restore_response = client.put("/user", data={
            "username": save_data.get('username'),
            "address": save_data.get('address'),
            "university": save_data.get('university')
        }, headers=Headers)
        assert restore_response.status_code == 200
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def test_user_case2():
    db = SessionLocal()
    db.begin() 
    try:
        global Headers
        if not Headers:
            setup_headers()
        
        # 修改密码
        password_response = client.post("/user/password", json={
            "old_password": "123456",
            "new_password": "654321"
            }, headers=Headers)
        assert password_response.status_code == 200
        # 验证密码是否修改成功
        login_response = client.post("/public/login", json={
            "email": "22371147@buaa.edu.cn",
            "password": "123456"
        })
        assert login_response.status_code == 401
        login_response = client.post("/public/login", json={
            "email": "22371147@buaa.edu.cn",
            "password": "654321"
        })
        assert login_response.status_code == 200
        # 还原密码
        restore_response = client.post("/user/password", json={
            "old_password": "654321",
            "new_password": "123456"
            }, headers=Headers)
        assert restore_response.status_code == 200
        # 验证密码是否还原成功
        login_response = client.post("/public/login", json={
            "email": "22371147@buaa.edu.cn",
            "password": "123456"
        })
        assert login_response.status_code == 200
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


    
