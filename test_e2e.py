import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def run_tests():
    print("--- Starting Automated API Tests ---")
    
    # 1. Register User
    username = f"testuser_{int(time.time())}"
    password = "testpassword123"
    print(f"\n[1] Registering new user: {username}")
    res = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password})
    if res.status_code != 200:
        print("❌ Register failed:", res.text)
        sys.exit(1)
    print("✅ Register successful.")
    
    # 2. Login User
    print("\n[2] Logging in to get token...")
    res = requests.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    if res.status_code != 200:
        print("❌ Login failed:", res.text)
        sys.exit(1)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful, token acquired.")
    
    # 3. Upload Document
    print("\n[3] Uploading a test document...")
    files = {"file": ("secret.txt", b"The secret launch code for the rocket is 998877. The rocket color is bright neon green.", "text/plain")}
    res = requests.post(f"{BASE_URL}/documents/", headers=headers, files=files)
    if res.status_code != 200:
        print("❌ Document upload failed:", res.text)
        sys.exit(1)
    doc = res.json()
    print("✅ Document uploaded successfully. ID:", doc.get("id"))
    
    # 4. Fetch Documents
    print("\n[4] Fetching document list...")
    res = requests.get(f"{BASE_URL}/documents/", headers=headers)
    if res.status_code != 200:
        print("❌ Fetch documents failed:", res.text)
        sys.exit(1)
    docs = res.json()
    print(f"✅ Document list retrieved. Found {len(docs)} documents.")
    
    # 5. Chat via RAG (Gemini)
    print("\n[5] Testing Gemini AI Chat (RAG)...")
    chat_payload = {"message": "What is the secret launch code for the rocket and what color is it?"}
    res = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_payload)
    if res.status_code != 200:
        print("❌ Chat failed:", res.text)
        sys.exit(1)
    chat_resp = res.json()
    print("✅ AI Chat Responded!")
    print("  AI Answer:", chat_resp.get("response"))
    print("  Sources retrieved:", len(chat_resp.get("sources", [])))
    
    # 6. Delete Document
    print("\n[6] Deleting test document...")
    res = requests.delete(f"{BASE_URL}/documents/{doc['id']}", headers=headers)
    if res.status_code != 200:
        print("❌ Delete document failed:", res.text)
        sys.exit(1)
    print("✅ Document deleted successfully.")
    
    print("\n🚀 ALL CORE REQUIREMENTS TESTED AND PASSED SUCCESSFULLY! 🚀")

if __name__ == "__main__":
    run_tests()
