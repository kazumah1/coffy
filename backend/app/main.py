from fastapi import FastAPI

app = FastAPI(
    title="W2M But Better",
    description="Smart Event Scheduling API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to W2M app"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}