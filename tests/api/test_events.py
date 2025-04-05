import pytest
from datetime import datetime, timedelta
from app.core.security import create_access_token

def test_create_event(client, test_alumni):
    # Create a token for the test alumni
    token = create_access_token({
        "sub": test_alumni.email,
        "user_id": test_alumni.id,
        "user_type": "alumni"
    })
    
    # Event data
    event_data = {
        "title": "Test Event",
        "description": "This is a test event",
        "location": "Test Location",
        "datetime": (datetime.now() + timedelta(days=7)).isoformat(),
        "cost": 0,
        "is_online": True
    }
    
    # Make request with the token
    response = client.post(
        "/events/events",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data

def test_list_events(client, db, test_alumni):
    # Create a token for the test alumni
    token = create_access_token({
        "sub": test_alumni.email,
        "user_id": test_alumni.id,
        "user_type": "alumni"
    })
    
    # Create an event in the future
    future_date = datetime.now() + timedelta(days=7)
    
    # Make request to create an event
    event_data = {
        "title": "Future Event",
        "description": "This is a future event",
        "location": "Test Location",
        "datetime": future_date.isoformat(),
        "cost": 0,
        "is_online": True
    }
    
    client.post(
        "/events/events",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # List events
    response = client.get("/events/events")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Future Event" 