import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
sys.path.append('/app')

from services.ingest_service.app.main import app as ingest_app
from libs.common.database import get_db

class TestKnowledgeIngestion:
    """Integration tests for knowledge ingestion pipeline."""
    
    @pytest.fixture
    def ingest_client(self, override_get_db, mock_openai_client, mock_weaviate_client):
        """Create test client for ingest service."""
        ingest_app.dependency_overrides[get_db] = override_get_db
        return TestClient(ingest_app)
    
    def test_pdf_upload_and_processing(self, ingest_client, test_persona, auth_headers):
        """Test PDF file upload and processing."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Write some PDF content (simplified for testing)
            tmp_file.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
            tmp_file_path = tmp_file.name
        
        try:
            # Upload the file
            with open(tmp_file_path, 'rb') as f:
                files = {'file': ('test.pdf', f, 'application/pdf')}
                data = {
                    'persona_id': str(test_persona.persona_id),
                    'title': 'Test PDF Document'
                }
                
                response = ingest_client.post(
                    "/knowledge/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            result = response.json()
            
            assert "upload_id" in result
            assert result["status"] == "pending"
            assert "queued for processing" in result["message"]
            
            # Test status check
            upload_id = result["upload_id"]
            status_response = ingest_client.get(
                f"/knowledge/{upload_id}/status",
                headers=auth_headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["source_id"] == upload_id
            assert status_data["title"] == "Test PDF Document"
            assert status_data["type"] == "pdf"
            
        finally:
            # Clean up
            os.unlink(tmp_file_path)
    
    def test_text_file_upload(self, ingest_client, test_persona, auth_headers):
        """Test text file upload."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("This is a test document with some content for processing.")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {
                    'persona_id': str(test_persona.persona_id),
                    'title': 'Test Text Document'
                }
                
                response = ingest_client.post(
                    "/knowledge/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "pending"
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_unsupported_file_type(self, ingest_client, test_persona, auth_headers):
        """Test upload of unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_file.write(b'unsupported content')
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                files = {'file': ('test.xyz', f, 'application/unknown')}
                data = {
                    'persona_id': str(test_persona.persona_id),
                    'title': 'Unsupported File'
                }
                
                response = ingest_client.post(
                    "/knowledge/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
            
            assert response.status_code == 400
            assert "Unsupported file type" in response.json()["detail"]
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_knowledge_source_listing(self, ingest_client, test_persona, auth_headers):
        """Test listing knowledge sources."""
        response = ingest_client.get(
            "/knowledge/sources",
            params={"persona_id": str(test_persona.persona_id)},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        sources = response.json()
        assert isinstance(sources, list)
    
    def test_knowledge_source_deletion(self, ingest_client, test_persona, auth_headers, test_db_session):
        """Test knowledge source deletion."""
        # First create a knowledge source
        from libs.common.models import KnowledgeSource
        
        knowledge_source = KnowledgeSource(
            org_id=test_persona.org_id,
            persona_id=test_persona.persona_id,
            title="Test Source for Deletion",
            type="text",
            status="ready",
            storage_path="/tmp/test_file.txt"
        )
        
        test_db_session.add(knowledge_source)
        test_db_session.commit()
        test_db_session.refresh(knowledge_source)
        
        # Delete the knowledge source
        response = ingest_client.delete(
            f"/knowledge/{knowledge_source.source_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
    
    @patch('services.ingest_service.app.tasks.process_upload_task.delay')
    def test_celery_task_queuing(self, mock_celery_task, ingest_client, test_persona, auth_headers):
        """Test that Celery tasks are properly queued."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'Test content')
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {
                    'persona_id': str(test_persona.persona_id),
                    'title': 'Test for Celery'
                }
                
                response = ingest_client.post(
                    "/knowledge/upload",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            # Verify that Celery task was queued
            mock_celery_task.assert_called_once()
            
        finally:
            os.unlink(tmp_file_path)
    
    def test_unauthorized_access(self, ingest_client, test_persona):
        """Test that unauthorized requests are rejected."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp_file:
            tmp_file.write(b'Test content')
            tmp_file.seek(0)
            
            files = {'file': ('test.txt', tmp_file, 'text/plain')}
            data = {
                'persona_id': str(test_persona.persona_id),
                'title': 'Unauthorized Test'
            }
            
            response = ingest_client.post(
                "/knowledge/upload",
                files=files,
                data=data
                # No auth headers
            )
            
            assert response.status_code == 403  # Forbidden