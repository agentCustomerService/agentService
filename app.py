from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent import app as agent_app

from models import (
    ChatRequest,
    ChatResponse
)

api = FastAPI()
api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/")
async def root():

    return {
        "status": "running"
    }


@api.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(request: ChatRequest):

    result = await agent_app.ainvoke({

        "message": request.message,

        "order_id": request.order_id,

        "actions": [],

        "executed_actions": [],

        "logs": [],

        "response": ""

    })

    return {

        "success": True,

        "actions": result.get(
            "executed_actions",
            []
        ),

        "logs": result.get(
            "logs",
            []
        ),

        "response": result.get(
            "response",
            ""
        )
    }