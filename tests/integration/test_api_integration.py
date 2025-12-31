"""
Backend API Integration Tests
Tests integration between frontend and backend APIs
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock


class TestAPIIntegration:
    """API integration tests for backend endpoints"""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app"""
        from src.backend.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        with patch("src.backend.db.session.get_db") as mock_session:
            yield mock_session

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service"""
        with patch("src.backend.services.ai_service.AIService") as mock:
            yield mock

    # ==================== Health API Tests ====================

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    # ==================== Chat API Tests (AC: 2) ====================

    def test_chat_diagnose_endpoint(self, client, mock_ai_service):
        """Test chat diagnosis endpoint integration"""
        # Mock AI service response
        mock_ai_instance = Mock()
        mock_ai_instance.diagnose.return_value = {
            "answer": "Based on analysis, this is a power supply issue.",
            "fault_code": "PWR-001",
            "component": "Power Supply Module",
            "summary": "Voltage fluctuation detected.",
            "resolution_steps": [
                "Measure voltage output levels",
                "Check for loose connections",
                "Replace faulty capacitors",
            ],
            "sources": [],
        }
        mock_ai_service.return_value = mock_ai_instance

        response = client.post(
            "/api/chat/diagnose", json={"query": "Equipment not powering on"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "answer" in data["data"]
        assert "power supply" in data["data"]["answer"].lower()

    def test_chat_diagnose_with_empty_query(self, client):
        """Test chat diagnosis with empty query"""
        response = client.post("/api/chat/diagnose", json={"query": ""})

        assert response.status_code == 422  # Validation error

    def test_chat_diagnose_with_long_query(self, client):
        """Test chat diagnosis with long query"""
        long_query = "x" * 1000
        response = client.post("/api/chat/diagnose", json={"query": long_query})

        # Should handle or reject based on validation
        assert response.status_code in [200, 422]

    # ==================== Search API Tests (AC: 2) ====================

    def test_search_similar_cases(self, client, mock_db_session):
        """Test search for similar cases endpoint"""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("WO-2024-001", "2024-12-15", "Similar power supply issue"),
            ("WO-2024-002", "2024-12-20", "Power supply module replaced"),
        ]

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        response = client.get("/api/search/similar", params={"query": "power supply"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_search_with_empty_query(self, client):
        """Test search with empty query"""
        response = client.get("/api/search/similar", params={"query": ""})

        # Should return empty results or validation error
        assert response.status_code in [200, 422]

    def test_search_with_no_results(self, client, mock_db_session):
        """Test search with no matching results"""
        # Mock empty database query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        response = client.get(
            "/api/search/similar", params={"query": "unique nonexistent query"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0

    # ==================== Analytics API Tests (AC: 2) ====================

    def test_analytics_summary(self, client, mock_db_session):
        """Test analytics summary endpoint"""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (150, 48.5, 72.5)

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        response = client.get(
            "/api/analytics/summary",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_work_orders" in data["data"]

    def test_analytics_with_invalid_date_range(self, client):
        """Test analytics with invalid date range"""
        response = client.get(
            "/api/analytics/summary",
            params={
                "start_date": "2024-12-31",
                "end_date": "2024-01-01",  # End before start
            },
        )

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_analytics_mtbf(self, client, mock_db_session):
        """Test MTBF analytics endpoint"""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("2024-01", 70.5),
            ("2024-02", 72.3),
            ("2024-03", 74.8),
        ]

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        response = client.get(
            "/api/analytics/mtbf",
            params={"start_date": "2024-01-01", "end_date": "2024-03-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    def test_analytics_pareto(self, client, mock_db_session):
        """Test Pareto analytics endpoint"""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("Power Supply", 45),
            ("Display Module", 32),
            ("Control Board", 28),
        ]

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        response = client.get(
            "/api/analytics/pareto",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    def test_analytics_fault_distribution(self, client, mock_db_session):
        """Test fault distribution analytics endpoint"""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("Critical", 15),
            ("Major", 45),
            ("Minor", 90),
        ]

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        response = client.get(
            "/api/analytics/fault-distribution",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    # ==================== Error Handling Tests (AC: 3) ====================

    def test_database_connection_error(self, client):
        """Test handling of database connection errors"""
        with patch("src.backend.db.session.get_db") as mock_session:
            mock_session.side_effect = Exception("Database connection failed")

            response = client.get(
                "/api/analytics/summary",
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
            )

            # Should return 500 error with appropriate message
            assert response.status_code == 500

    def test_ai_service_unavailable(self, client, mock_ai_service):
        """Test handling of AI service being unavailable"""
        # Mock AI service to raise error
        mock_ai_instance = Mock()
        mock_ai_instance.diagnose.side_effect = Exception("AI service unavailable")
        mock_ai_service.return_value = mock_ai_instance

        response = client.post("/api/chat/diagnose", json={"query": "Test fault"})

        # Should return 500 error
        assert response.status_code in [500, 503]

    def test_malformed_request_body(self, client):
        """Test handling of malformed request body"""
        response = client.post("/api/chat/diagnose", json={"invalid_key": "value"})

        # Should return 422 validation error
        assert response.status_code == 422

    def test_missing_required_parameters(self, client):
        """Test handling of missing required parameters"""
        response = client.get("/api/analytics/summary")

        # Should return 422 validation error
        assert response.status_code == 422

    # ==================== Performance Tests (AC: 4) ====================

    def test_api_response_time(self, client, mock_db_session):
        """Test API response time meets performance requirements"""
        import time

        # Mock fast database query
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (100, 24.5, 72.5)

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        start_time = time.time()

        response = client.get(
            "/api/analytics/summary",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )

        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        # API should respond within reasonable time (e.g., 1 second)
        assert response_time_ms < 1000

    def test_concurrent_requests(self, client, mock_db_session):
        """Test handling of concurrent requests"""
        import threading

        # Mock database query
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (100, 24.5, 72.5)

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        results = []
        errors = []

        def make_request():
            try:
                response = client.get(
                    "/api/analytics/summary",
                    params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create 10 concurrent threads
        threads = [threading.Thread(target=make_request) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(errors) == 0
        assert all(status == 200 for status in results)
        assert len(results) == 10

    # ==================== Integration Workflow Tests ====================

    def test_complete_diagnostic_workflow(
        self, client, mock_ai_service, mock_db_session
    ):
        """Test complete diagnostic workflow: search + diagnose"""
        # Mock search result
        search_result = MagicMock()
        search_result.fetchall.return_value = [
            ("WO-2024-001", "2024-12-15", "Similar case"),
        ]

        # Mock AI diagnosis
        mock_ai_instance = Mock()
        mock_ai_instance.diagnose.return_value = {
            "answer": "Diagnosis result",
            "fault_code": "TEST-001",
            "component": "Test Component",
            "resolution_steps": ["Step 1", "Step 2"],
            "sources": [],
        }
        mock_ai_service.return_value = mock_ai_instance

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = search_result
        mock_db_session.return_value = mock_conn

        # Step 1: Search for similar cases
        search_response = client.get(
            "/api/search/similar", params={"query": "power supply issue"}
        )
        assert search_response.status_code == 200

        # Step 2: Get diagnosis
        diagnosis_response = client.post(
            "/api/chat/diagnose", json={"query": "power supply issue"}
        )
        assert diagnosis_response.status_code == 200

        data = diagnosis_response.json()
        assert data["success"] is True
        assert "answer" in data["data"]

    def test_complete_analytics_workflow(self, client, mock_db_session):
        """Test complete analytics dashboard workflow"""
        # Mock all analytics queries
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (150, 48.5, 72.5)
        mock_result.fetchall.return_value = [
            ("2024-01", 70.5),
            ("2024-02", 72.3),
        ]

        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_result
        mock_db_session.return_value = mock_conn

        # Step 1: Get summary
        summary_response = client.get(
            "/api/analytics/summary",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert summary_response.status_code == 200

        # Step 2: Get MTBF
        mtbf_response = client.get(
            "/api/analytics/mtbf",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert mtbf_response.status_code == 200

        # Step 3: Get Pareto
        pareto_response = client.get(
            "/api/analytics/pareto",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert pareto_response.status_code == 200

        # Step 4: Get fault distribution
        fault_dist_response = client.get(
            "/api/analytics/fault-distribution",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )
        assert fault_dist_response.status_code == 200
