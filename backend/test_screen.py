"""Quick end-to-end test for the /api/screen endpoint."""
import httpx, os, glob, json

BASE = "http://localhost:8000"

# Login
login = httpx.post(f"{BASE}/auth/login",
                   data={"username": "Emmad", "password": "S@lidworks2016"},
                   timeout=10)
print("Login:", login.status_code)
token = login.json()["access_token"]

# Find PDFs
pdfs = glob.glob("Sample_data/*.pdf")
print("PDFs:", pdfs)

jd, cv = pdfs[0], pdfs[1]
with open(jd, "rb") as jdf, open(cv, "rb") as cvf:
    r = httpx.post(
        f"{BASE}/api/screen",
        files=[
            ("job_description", (os.path.basename(jd), jdf, "application/pdf")),
            ("resumes",         (os.path.basename(cv), cvf, "application/pdf")),
        ],
        headers={"Authorization": f"Bearer {token}"},
        timeout=300,
    )

print("Screen status:", r.status_code)
if r.status_code == 200:
    d = r.json()
    print("total_resumes:", d["total_resumes"])
    for res in d["results"]:
        print(f"  {res['full_name']}  score={res['similarity_score']:.3f}")
else:
    print("ERROR:", r.text[:800])
