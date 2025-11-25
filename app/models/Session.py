from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
from app.utils.query_process import determine_single_welding_intent

sessions = {}  # TODO:这里简单地定义sessions字典常量，以内存的方式存储。后期则放在数据库中永久存储

# Message, SessionData: 定义数据格式的对象
class Message(BaseModel):
    query: str
    response: Any

class SessionData(BaseModel):
    id: str
    shared_data: Dict[str, Any]
    messages: List[Message]
    rag_messages: List[Message]
    state: int

# Session: 面向业务的对象
class Session:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.shared_data = {}
        self.original_data = {}
        self.messages = []
        self.rag_messages = []
        self.state = 0
        self.messages_all_user=[]

    def to_model(self) -> SessionData:
        return SessionData(
            id=self.id,
            shared_data=self.shared_data,
            messages=[Message(query=m["query"], response=m["response"]) for m in self.messages],
            rag_messages=[Message(query=m["query"], response=m["response"]) for m in self.rag_messages],
            state = self.state
        )

    def add_and_update(self, slots, standard_slots):
        for item in standard_slots:
            key, value = item[0], item[1]
            self.shared_data[key] = value
        for item in slots:
            key, value = item[0], item[1]
            self.original_data[key] = value

        # 由当前的slots确定查询状态
        intent_str = determine_single_welding_intent(self.shared_data)
        self.state = intent_str[-1] if intent_str != 'OTHER' else 0

    def get_intent_and_slots(self):
        standard_slots = []
        original_slots = []
        for key, value in self.shared_data.items():
            standard_slots.append((key, value))
        for key, value in self.original_data.items():
            original_slots.append((key, value))
        intent_str = "QUERY_" + str(self.state) if self.state != 0 else "OTHER"
        return intent_str, original_slots, standard_slots
    
    def add_rag_messages(self, query, response):
        self.rag_messages.append(Message(query=query, response=response))
        
    def get_rag_messages(self):
        return self.rag_messages
    
    def add_user_messages(self, query_user):
        self.messages_all_user.append(query_user)
        
    def get_user_messages(self):
        return self.messages_all_user

sessions['test-id'] = Session()
for i in range(50):
    sessions[f'test-id-{i}'] = Session()