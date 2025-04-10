from fastapi import FastAPI, HTTPException, Depends,Body
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# --- Database Setup ---
DATABASE_URL = "sqlite:///./employees.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# --- SQLAlchemy Model ---
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    department = Column(String)
    position = Column(String)

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class EmployeeCreate(BaseModel):
    name: str
    age: int
    department: str
    position: str

class EmployeeOut(EmployeeCreate):
    id: int
    class Config:
        orm_mode = True

# --- FastAPI App ---
app = FastAPI(title="Employee Management API")

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Create Employee ---
@app.post("/employees/bulk", response_model=List[EmployeeOut])
def create_multiple_employees(
    employees: List[EmployeeCreate] = Body(...),
    db: Session = Depends(get_db)
):
    db_employees = [Employee(**emp.dict()) for emp in employees]
    db.add_all(db_employees)
    db.commit()
    # Refresh each to return their IDs
    for emp in db_employees:
        db.refresh(emp)
    return db_employees

# --- Read All Employees ---
@app.get("/employees/", response_model=List[EmployeeOut])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

# --- Read Single Employee ---
@app.get("/employees/{emp_id}", response_model=EmployeeOut)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

# --- Update Employee ---
@app.put("/employees/{emp_id}", response_model=EmployeeOut)
def update_employee(emp_id: int, emp_data: EmployeeCreate, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.name = emp_data.name
    emp.age = emp_data.age
    emp.department = emp_data.department
    emp.position = emp_data.position
    db.commit()
    db.refresh(emp)
    return emp

# --- Delete Employee ---
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted"}
