from fastapi.testclient import TestClient
import sys
import os

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将项目根目录添加到sys.path
sys.path.insert(0, project_root)

print(sys.path)

from app.main import app

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



def test_article_case1():
    global Headers
    # 确保headers已经设置
    if not Headers:
        setup_headers()

    #创建文件夹
    create_folder_response = client.post("/article/selfCreateFolder", headers=Headers, json={
        "folder_name" : "测试文件夹1" 
    })
    assert create_folder_response.status_code == 200

    #获取文件夹列表
    get_folder_list_response = client.get("/article/getSelfFolders", headers=Headers)
    assert get_folder_list_response.status_code == 200
    folders = get_folder_list_response.json().get('result')
    folder_id = None
    for folder in folders:
        if folder.get('folder_name') == '测试文件夹1':
            folder_id = folder.get('folder_id')
            break

    assert folder_id is not None

    #获取该文件夹下的文件列表
    get_file_list_response = client.get(f"/article/getArticlesInFolder", headers=Headers,
                                          params={"folder_id": folder_id})
    assert get_file_list_response.status_code == 200
    files = get_file_list_response.json().get('result')
    if len(files) == 0:
        #向该文件夹下上传文件  

        upload_file_response = client.post("/article/uploadToSelfFolder", params={"folder_id": folder_id},headers=Headers, files={
        "article": os.path.join(project_root, "tests/in/test.pdf")})
        assert upload_file_response.status_code == 200

    
    
