"""Tests for the FastAPI activities application"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Basketball Club" in data
        assert "Tennis Team" in data
        assert "Debate Club" in data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_basketball_club_has_initial_participant(self, client):
        """Test that Basketball Club has its initial participant"""
        response = client.get("/activities")
        data = response.json()
        
        basketball = data["Basketball Club"]
        assert "alex@mergington.edu" in basketball["participants"]
    
    def test_debate_club_has_multiple_participants(self, client):
        """Test that Debate Club has multiple participants"""
        response = client.get("/activities")
        data = response.json()
        
        debate = data["Debate Club"]
        assert len(debate["participants"]) == 2
        assert "isabella@mergington.edu" in debate["participants"]
        assert "lucas@mergington.edu" in debate["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully" in data["message"] or "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        email = "testuser@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_duplicate_signup(self, client):
        """Test that duplicate signups are rejected"""
        email = "alex@mergington.edu"  # Already signed up for Basketball Club
        
        response = client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_multiple_activities_signup(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multiactivity@mergington.edu"
        
        # Sign up for Basketball Club
        response1 = client.post(
            "/activities/Basketball%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for Tennis Team
        response2 = client.post(
            "/activities/Tennis%20Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Club"]["participants"]
        assert email in data["Tennis Team"]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successfully unregistering from an activity"""
        response = client.post(
            "/activities/Basketball%20Club/unregister",
            params={"email": "alex@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"] or "unregistered" in data["message"].lower()
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "alex@mergington.edu"
        
        # Unregister
        client.post(
            "/activities/Basketball%20Club/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Basketball Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_not_signed_up(self, client):
        """Test that unregistering someone not signed up fails"""
        response = client.post(
            "/activities/Basketball%20Club/unregister",
            params={"email": "notsignedup@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can sign up again after unregistering"""
        email = "test@mergington.edu"
        activity = "Basketball%20Club"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify the signup
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball Club"]["participants"]
    
    def test_unregister_from_activity_with_multiple_participants(self, client):
        """Test unregistering from an activity with multiple participants"""
        # Debate Club has two participants initially
        email_to_remove = "isabella@mergington.edu"
        
        response = client.post(
            "/activities/Debate%20Club/unregister",
            params={"email": email_to_remove}
        )
        
        assert response.status_code == 200
        
        # Verify only one participant was removed
        response = client.get("/activities")
        data = response.json()
        debate_participants = data["Debate Club"]["participants"]
        assert email_to_remove not in debate_participants
        assert "lucas@mergington.edu" in debate_participants
        assert len(debate_participants) == 1


class TestIntegration:
    """Integration tests covering multiple operations"""
    
    def test_full_workflow(self, client):
        """Test a complete workflow: signup, verify, unregister, verify"""
        email = "integration@mergington.edu"
        activity = "Chess%20Club"
        
        # Initial state - verify not signed up
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        assert len(response.json()["Chess Club"]["participants"]) == initial_count + 1
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        assert len(response.json()["Chess Club"]["participants"]) == initial_count
    
    def test_concurrent_signups(self, client):
        """Test multiple students signing up for the same activity"""
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        activity = "Art%20Studio"
        
        # All students sign up
        for student in students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Verify all are signed up
        response = client.get("/activities")
        data = response.json()
        participants = data["Art Studio"]["participants"]
        
        for student in students:
            assert student in participants
