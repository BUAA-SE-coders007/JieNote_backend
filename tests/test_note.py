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


# 创建后删除笔记
def test_note_case1():
    db = SessionLocal()
    db.begin() 
    try:
        global Headers
        # 确保headers已经设置
        if not Headers:
            setup_headers()


        # 创建笔记
        create_response = client.post("/notes", json={
            "article_id": 1,
            "content": "<p> 12 <p>",
            "title": "test"
        }, headers=Headers)
        assert create_response.status_code == 200
        note_id = create_response.json().get('note_id')
        if note_id is None:
            raise ValueError("Failed to get note_id from create note response")

        # 删除笔记
        delete_response = client.delete(f"/notes/{note_id}", headers=Headers)
        assert delete_response.status_code == 200

        # 再次删除不存在的笔记
        double_delete_response = client.delete(f"/notes/{note_id}", headers=Headers)
        assert double_delete_response.status_code != 200
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def test_note_case2():
    db = SessionLocal()
    db.begin() 
    try:
        global Headers
        if not Headers:
            setup_headers()

        # 创建笔记
        create_response = client.post("/notes", json={
            "article_id": 1,
            "content": "<p> 12 <p>",
            "title": "test"
        }, headers=Headers)
        assert create_response.status_code == 200
        note_id = create_response.json().get('note_id')
        if note_id is None:
            raise ValueError("Failed to get note_id from create note response")

        print(note_id)
        # 更新笔记
        update_response = client.put(f"/notes/{note_id}", params={
            "content": "<p> 123 <p>",
            "title": "test2"
        }, headers=Headers)
        print(update_response.json())
        assert update_response.status_code == 200

        

        # 获取笔记
        get_response = client.get(f"/notes",params={
            "id": note_id
        }, headers=Headers)
        assert get_response.status_code == 200
        assert get_response.json().get('notes')[0].get('id') == note_id
        assert get_response.json().get('notes')[0].get('content') == "<p> 123 <p>"
        

        #删除笔记
        delete_response = client.delete(f"/notes/{note_id}", headers=Headers)
        assert delete_response.status_code == 200
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
