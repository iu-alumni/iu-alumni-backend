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
    
    event_data = {
        "title": "Test Event",
        "description": "This is a test event",
        "location": "Test Location",
        "datetime": (datetime.now() + timedelta(days=7)).isoformat(),
        "cost": 0,
        "is_online": True
    }
    
    response = client.post(
        "/events/events",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data

def test_list_events(client, db, test_alumni):
    token = create_access_token({
        "sub": test_alumni.email,
        "user_id": test_alumni.id,
        "user_type": "alumni"
    })
    
    future_date = datetime.now() + timedelta(days=7)
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
    
    response = client.get("/events/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Verify that at least one event matches the one we created
    assert any(event["title"] == "Future Event" for event in data)

def test_delete_event(client, test_alumni):
    token = create_access_token({
        "sub": test_alumni.email,
        "user_id": test_alumni.id,
        "user_type": "alumni"
    })
    
    # Create an event to later delete
    event_data = {
        "title": "Event to Delete",
        "description": "Event that will be deleted",
        "location": "Delete Location",
        "datetime": (datetime.now() + timedelta(days=5)).isoformat(),
        "cost": 10,
        "is_online": False
    }
    create_response = client.post(
        "/events/events",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    
    # Now, delete the event
    delete_response = client.delete(
        f"/events/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200

def test_update_event(client, test_alumni):
    token = create_access_token({
        "sub": test_alumni.email,
        "user_id": test_alumni.id,
        "user_type": "alumni"
    })
    
    # Create an event first
    event_data = {
        "title": "Event to Update",
        "description": "Original Description",
        "location": "Update Location",
        "datetime": (datetime.now() + timedelta(days=3)).isoformat(),
        "cost": 20,
        "is_online": False
    }
    create_response = client.post(
        "/events/events",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    
    # Update the event.
    # Note: We omit "datetime" because the UpdateEventRequest model only allows null values for it.
    update_data = {
        "title": "Updated Event Title",
        "description": "Updated Description",
        "location": "Updated Location",
        "cost": 30,
        "is_online": True,
        "cover": None
    }
    update_response = client.put(
        f"/events/events/{event_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    updated_event = update_response.json()
    assert updated_event["title"] == "Updated Event Title"
    assert updated_event["description"] == "Updated Description"

def test_list_owner_events(client, test_alumni):
    token = create_access_token({
        "sub": test_alumni.email,
        "user_id": test_alumni.id,
        "user_type": "alumni"
    })
    
    # Create an event as owner
    event_data = {
        "title": "Owner Event",
        "description": "Event owned by user",
        "location": "Owner Location",
        "datetime": (datetime.now() + timedelta(days=4)).isoformat(),
        "cost": 15,
        "is_online": False
    }
    create_response = client.post(
        "/events/events",
        json=event_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 200
    
    # Retrieve events owned by the current user
    owner_response = client.get(
        "/events/events/owner",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert owner_response.status_code == 200
    owner_events = owner_response.json()
    assert any(event["title"] == "Owner Event" for event in owner_events)
