import { fetchWithAuth } from "../utils/fetchWithAuth";

import { API_BASE_URL } from '../config/api';
import logger from '../utils/logger.js';

const ManageUsers = ({ getAuthHeaders }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    const fetchUsers = async () => {
      try {
        // ✅ Using fetchWithAuth for automatic token handling
        const response = await fetchWithAuth(`${API_BASE_URL}/admin/users`);
        
        if (!response.ok) {
          if (response.status === 403) {
            throw new Error("Admin access required");
          }
          throw new Error("Failed to fetch users");
        }
        
        const data = await response.json();
        setUsers(Array.isArray(data) ? data : []);
      } catch (err) {
        logger.error("Error fetching users:", err);
        setError(err.message || "Failed to load users");
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (loading) return <div className="p-6 text-center text-gray-500">Loading users...</div>;
  if (error) return <div className="p-6 text-center text-red-600">{error}</div>;

  return (
    <div className="bg-white p-6 rounded shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Manage Users</h2>
      
      {users.length === 0 ? (
        <p className="text-gray-500">No users found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-2 border text-left">Email</th>
                <th className="p-2 border text-left">Role</th>
                <th className="p-2 border text-left">Created</th>
                <th className="p-2 border text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="border p-2">{user.email}</td>
                  <td className="border p-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      user.role === 'admin' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="border p-2">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="border p-2">
                    <button className="text-blue-600 hover:underline text-xs">
                      Edit Role
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ManageUsers;
