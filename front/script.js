// API Base URL - change this to match your backend URL
const API_BASE_URL = "http://localhost:8080";

// Store the JWT token
let authToken = localStorage.getItem("authToken") || "";
let isAdmin = localStorage.getItem("isAdmin") === "true";

// DOM Elements
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanes = document.querySelectorAll(".tab-pane");
const resultsDiv = document.getElementById("results");

// Authentication forms
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const verifyEmailForm = document.getElementById("verify-email-form");
const resendVerificationForm = document.getElementById(
  "resend-verification-form"
);
const requestManualVerificationForm = document.getElementById(
  "request-manual-verification-form"
);
const verifyGraduateForm = document.getElementById("verify-graduate-form");

// Profile elements
const getProfileBtn = document.getElementById("get-profile-btn");
const updateProfileForm = document.getElementById("update-profile-form");
const getAllProfilesBtn = document.getElementById("get-all-profiles-btn");
const getProfileByIdForm = document.getElementById("get-profile-by-id-form");

// Event elements
const createEventForm = document.getElementById("create-event-form");
const listEventsBtn = document.getElementById("list-events-btn");
const listOwnerEventsBtn = document.getElementById("list-owner-events-btn");
const listParticipantEventsBtn = document.getElementById(
  "list-participant-events-btn"
);
const updateEventForm = document.getElementById("update-event-form");
const deleteEventForm = document.getElementById("delete-event-form");
const joinEventForm = document.getElementById("join-event-form");
const leaveEventForm = document.getElementById("leave-event-form");
const listParticipantsForm = document.getElementById("list-participants-form");

// Admin elements
const uploadEmailsForm = document.getElementById("upload-emails-form");
const importAlumniForm = document.getElementById("import-alumni-form");
const addAdminForm = document.getElementById("add-admin-form");
const listUsersBtn = document.getElementById("list-users-btn");
const listBannedBtn = document.getElementById("list-banned-btn");
const adminVerifyForm = document.getElementById("admin-verify-form");
const adminUnverifyForm = document.getElementById("admin-unverify-form");
const banUserForm = document.getElementById("ban-user-form");
const unbanUserForm = document.getElementById("unban-user-form");
const adminListEventsBtn = document.getElementById("admin-list-events-btn");
const approveEventForm = document.getElementById("approve-event-form");
const declineEventForm = document.getElementById("decline-event-form");

// Tab Switching
tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    // Remove active class from all buttons and panes
    tabButtons.forEach((btn) => btn.classList.remove("active"));
    tabPanes.forEach((pane) => pane.classList.remove("active"));

    // Add active class to clicked button and corresponding pane
    button.classList.add("active");
    const tabId = button.getAttribute("data-tab");
    document.getElementById(tabId).classList.add("active");
  });
});

// Display results
function displayResult(data, isError = false) {
  resultsDiv.textContent =
    typeof data === "object" ? JSON.stringify(data, null, 2) : data;
  resultsDiv.className = "results " + (isError ? "error" : "success");
}

// Handle API errors
function handleApiError(error) {
  console.error("API Error:", error);
  if (error.response && error.response.data) {
    displayResult(error.response.data, true);
  } else {
    displayResult(`Error: ${error.message || "Unknown error"}`, true);
  }
}

// Make authenticated request
async function makeAuthenticatedRequest(url, options = {}) {
  if (!authToken) {
    throw new Error("No authentication token available. Please login first.");
  }

  const headers = {
    Authorization: `Bearer ${authToken}`,
    "Content-Type": "application/json",
    ...options.headers,
  };

  return fetch(url, { ...options, headers });
}

// Login Form Submission
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw { response: { data } };
    }

    // Store token
    authToken = data.access_token;
    localStorage.setItem("authToken", authToken);

    // Check if user is admin by decoding the JWT token
    try {
      // Decode JWT token (without verification - just to read the payload)
      const tokenParts = authToken.split(".");
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));
        isAdmin = payload.user_type === "admin";
        localStorage.setItem("isAdmin", isAdmin);
      }
    } catch (error) {
      console.error("Error checking user role:", error);
    }

    displayResult({
      message: "Login successful",
      token: authToken,
      isAdmin,
    });
  } catch (error) {
    handleApiError(error);
  }
});

// Register Form Submission
registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;
  const firstName = document.getElementById("register-first-name").value;
  const lastName = document.getElementById("register-last-name").value;
  const graduationYear = document.getElementById(
    "register-graduation-year"
  ).value;
  const telegramAlias = document.getElementById("register-telegram").value;
  const manualVerification = document.getElementById(
    "manual-verification"
  ).checked;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        graduation_year: graduationYear,
        telegram_alias: telegramAlias,
        manual_verification: manualVerification,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw { response: { data } };
    }

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Upload Allowed Emails Form Submission
uploadEmailsForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!authToken) {
    displayResult("You must be logged in as an admin to upload emails", true);
    return;
  }

  const fileInput = document.getElementById("excel-file");
  const file = fileInput.files[0];

  if (!file) {
    displayResult("Please select an Excel file", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(
      `${API_BASE_URL}/admin/upload-allowed-emails`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
        body: formData,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw { response: { data } };
    }

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// ===== AUTHENTICATION HANDLERS =====

// Verify Email Form
verifyEmailForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("verify-email").value;
  const verificationCode = document.getElementById("verification-code").value;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, verification_code: verificationCode }),
    });

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    // Store token if verification successful
    if (data.access_token) {
      authToken = data.access_token;
      localStorage.setItem("authToken", authToken);
    }

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Resend Verification Form
resendVerificationForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("resend-email").value;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Request Manual Verification Form
requestManualVerificationForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("manual-request-email").value;

  try {
    const response = await fetch(
      `${API_BASE_URL}/auth/request-manual-verification`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Verify Graduate Form
verifyGraduateForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("graduate-email").value;
  const password = document.getElementById("graduate-password").value;
  const graduationYear = document.getElementById("graduate-year").value;
  const firstName = document.getElementById("graduate-first-name").value;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/verify-graduate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        graduation_year: graduationYear,
        first_name: firstName,
      }),
    });

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    // Store token if verification successful
    if (data.access_token) {
      authToken = data.access_token;
      localStorage.setItem("authToken", authToken);
    }

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// ===== PROFILE HANDLERS =====

// Get Profile Button
getProfileBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/profile/me`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Update Profile Form
updateProfileForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const updateData = {};
  const fields = [
    "update-first-name",
    "update-last-name",
    "update-graduation-year",
    "update-location",
    "update-biography",
    "update-telegram",
    "update-avatar",
  ];

  fields.forEach((fieldId) => {
    const value = document.getElementById(fieldId).value;
    if (value) {
      const key = fieldId.replace("update-", "").replace("-", "_");
      updateData[key] = value;
    }
  });

  updateData.show_location = document.getElementById("show-location").checked;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/profile/me`,
      {
        method: "PUT",
        body: JSON.stringify(updateData),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Get All Profiles Button
getAllProfilesBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/profile/all`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Get Profile by ID Form
getProfileByIdForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const userId = document.getElementById("profile-user-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/profile/${userId}`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// ===== EVENT HANDLERS =====

// Create Event Form
createEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventData = {
    title: document.getElementById("event-title").value,
    description: document.getElementById("event-description").value,
    location: document.getElementById("event-location").value,
    datetime: new Date(
      document.getElementById("event-datetime").value
    ).toISOString(),
    cost: parseFloat(document.getElementById("event-cost").value),
    is_online: document.getElementById("event-is-online").checked,
    cover: document.getElementById("event-cover").value || null,
  };

  try {
    const response = await makeAuthenticatedRequest(`${API_BASE_URL}/events/`, {
      method: "POST",
      body: JSON.stringify(eventData),
    });

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// List Events Button
listEventsBtn.addEventListener("click", async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/events/`);
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// List Owner Events Button
listOwnerEventsBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/owner`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// List Participant Events Button
listParticipantEventsBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/participant`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Update Event Form
updateEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("update-event-id").value;
  const updateData = {};

  const fields = [
    { id: "update-event-title", key: "title" },
    { id: "update-event-description", key: "description" },
    { id: "update-event-location", key: "location" },
    { id: "update-event-cost", key: "cost", transform: parseFloat },
    { id: "update-event-cover", key: "cover" },
  ];

  fields.forEach((field) => {
    const value = document.getElementById(field.id).value;
    if (value) {
      updateData[field.key] = field.transform ? field.transform(value) : value;
    }
  });

  const datetime = document.getElementById("update-event-datetime").value;
  if (datetime) {
    updateData.datetime = new Date(datetime).toISOString();
  }

  updateData.is_online = document.getElementById(
    "update-event-is-online"
  ).checked;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/${eventId}`,
      {
        method: "PUT",
        body: JSON.stringify(updateData),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Delete Event Form
deleteEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("delete-event-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/${eventId}`,
      {
        method: "DELETE",
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Join Event Form
joinEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("join-event-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/${eventId}/participants`,
      {
        method: "POST",
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Leave Event Form
leaveEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("leave-event-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/${eventId}/participants`,
      {
        method: "DELETE",
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// List Participants Form
listParticipantsForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("participants-event-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/events/${eventId}/participants`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// ===== ADMIN HANDLERS =====

// Import Alumni Form
importAlumniForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById("alumni-file");
  const file = fileInput.files[0];

  if (!file) {
    displayResult("Please select an Excel file", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/auth/import-alumni`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}` },
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Add Admin Form
addAdminForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("admin-email").value;
  const password = document.getElementById("admin-password").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/auth/add-admin`,
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// List Users Button
listUsersBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/users`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// List Banned Button
listBannedBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/banned`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Admin Verify Form
adminVerifyForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("verify-user-email").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/verify`,
      {
        method: "POST",
        body: JSON.stringify({ email }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Admin Unverify Form
adminUnverifyForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("unverify-user-email").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/unverify`,
      {
        method: "POST",
        body: JSON.stringify({ email }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Ban User Form
banUserForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("ban-user-email").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/ban`,
      {
        method: "POST",
        body: JSON.stringify({ email }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Unban User Form
unbanUserForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("unban-user-email").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/unban`,
      {
        method: "POST",
        body: JSON.stringify({ email }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Admin List Events Button
adminListEventsBtn.addEventListener("click", async () => {
  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/events`
    );
    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Approve Event Form
approveEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("approve-event-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/approve-event`,
      {
        method: "POST",
        body: JSON.stringify({ event_id: eventId }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Decline Event Form
declineEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const eventId = document.getElementById("decline-event-id").value;

  try {
    const response = await makeAuthenticatedRequest(
      `${API_BASE_URL}/admin/decline-event`,
      {
        method: "POST",
        body: JSON.stringify({ event_id: eventId }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw { response: { data } };

    displayResult(data);
  } catch (error) {
    handleApiError(error);
  }
});

// Check if user is already logged in
if (authToken) {
  displayResult({
    message: "Already logged in",
    token: authToken,
    isAdmin,
  });
}
