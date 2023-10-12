from typing import Optional
import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Boolean
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = "postgresql+asyncpg://postgres:1488@localhost/todo_1"
engine = create_async_engine(DB_PATH, connect_args={"ssl": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


app = FastAPI()


class TaskCreate(BaseModel):
    title: str
    description: str
    completed: Optional[bool] = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = True


class Table(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    completed = Column(Boolean)


@app.post("/tasks/")
async def add_task(task: TaskCreate, db=Depends(get_db)):
    try:
        item = Table(title=task.title, description=task.description, completed=False)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        print("Done!")
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task/{task_id}/")
async def get_task(task_id: int, db=Depends(get_db)):
    item = await db.get(Table, task_id)
    try:
        print("You caught it!")
        return item
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/task/{task_id}/", response_model=TaskUpdate)
async def edit_task(task_id: int, new_data: Optional[TaskUpdate] = None, db=Depends(get_db)):
    item = await db.get(Table, task_id)
    try:
        if new_data is None:
            item.completed = True
        elif new_data.completed is not None and new_data.completed:
            item.completed = True
        await db.commit()
        await db.refresh(item)
        print("Updated successfully!")
        return item
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/task/{task_id}/", response_model=str)
async def delete_task(task_id: int, db=Depends(get_db)):
    item = await db.get(Table, task_id)
    try:
        db.delete(item)
        await db.commit()
        return "Deleted successfully!"
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host='127.0.0.1', port=5000, reload=True, workers=4)
