// src/utils/fetchWithAuth.js

export async function fetchWithAuth(url, options = {}) {
  let accessToken = localStorage.getItem("access_token");
  let refreshToken = localStorage.getItem("refresh_token");

  options.headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  };

  let response = await fetch(url, options);

  if (response.status === 401 && refreshToken) {
    const refreshResponse = await fetch("http://127.0.0.1:8000/auth/refresh-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const refreshData = await refreshResponse.json();

    if (refreshResponse.ok) {
      localStorage.setItem("access_token", refreshData.access_token);
      options.headers.Authorization = `Bearer ${refreshData.access_token}`;
      response = await fetch(url, options);
    } else {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
  }

  return response;
}
