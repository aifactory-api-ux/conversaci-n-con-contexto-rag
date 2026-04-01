class DocumentService:
    def __init__(self, db):
        self.db = db

    async def upload_document(self, filename, content_type, file_content, user_id):
        # Minimal stub for upload_document
        class DummyDoc:
            def __init__(self):
                import uuid
                self.id = uuid.uuid4()
                self.status = "pending"
        return DummyDoc()

    async def list_documents(self, user_id):
        # Minimal stub for list_documents
        class DummyDoc:
            def __init__(self):
                import uuid
                self.id = uuid.uuid4()
                self.status = "pending"
                self.filename = "dummy.pdf"
                self.chunks_count = 0
        return [DummyDoc()]

    async def get_document(self, document_id):
        # Minimal stub for get_document
        class DummyDoc:
            def __init__(self):
                import uuid
                self.id = uuid.UUID(document_id) if document_id else uuid.uuid4()
                self.status = "pending"
                self.chunks_count = 0
                self.error_message = None
                self.user_id = "current_user_id"
        return DummyDoc()

    async def delete_document(self, document_id, user_id):
        # Minimal stub for delete_document
        return True
