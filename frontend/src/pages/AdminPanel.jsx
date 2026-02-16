import { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, Upload, Video, Copy, Check, CheckCircle, XCircle, Clock } from 'lucide-react';

const AdminPanel = () => {
    const [users, setUsers] = useState([]);
    const [cameras, setCameras] = useState([]);
    const [showUserModal, setShowUserModal] = useState(false);
    const [showCameraModal, setShowCameraModal] = useState(false);
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [showUrlModal, setShowUrlModal] = useState(false);
    const [streamUrl, setStreamUrl] = useState('');
    const [copied, setCopied] = useState(false);

    const [newUser, setNewUser] = useState({ name: '', email: '', password: '', role: 'police' });
    const [newCamera, setNewCamera] = useState({ name: '', location: '', url: '' });
    const [uploadFile, setUploadFile] = useState(null);

    const fetchData = async () => {
        try {
            const [usersRes, camerasRes] = await Promise.all([
                axios.get('http://localhost:8000/users/'),
                axios.get('http://localhost:8000/cameras/')
            ]);
            setUsers(usersRes.data);
            setCameras(camerasRes.data);
        } catch (error) {
            console.error("Error fetching admin data", error);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            await axios.post('http://localhost:8000/users/', newUser);
            setShowUserModal(false);
            fetchData();
            setNewUser({ name: '', email: '', password: '', role: 'police' });
        } catch (error) {
            alert("Error creating user");
        }
    };

    const handleCreateCamera = async (e) => {
        e.preventDefault();
        try {
            await axios.post('http://localhost:8000/cameras/', newCamera);
            setShowCameraModal(false);
            fetchData();
            setNewCamera({ name: '', location: '', url: '' });
        } catch (error) {
            alert("Error adding camera");
        }
    };

    const handleUploadVideo = async (e) => {
        e.preventDefault();
        if (!uploadFile) return;

        const formData = new FormData();
        formData.append('file', uploadFile);

        try {
            const response = await axios.post('http://localhost:8000/streams/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setShowUploadModal(false);
            const fullStreamUrl = `http://localhost:8000${response.data.stream_url}`;
            setStreamUrl(fullStreamUrl);
            setShowUrlModal(true);
        } catch (error) {
            alert("Error uploading video");
        }
    };

    const handleDeleteUser = async (id) => {
        if (!confirm("Are you sure?")) return;
        try {
            await axios.delete(`http://localhost:8000/users/${id}`);
            fetchData();
        } catch (error) {
            console.error(error);
        }
    };

    const handleDeleteCamera = async (id) => {
        if (!confirm("Are you sure?")) return;
        try {
            await axios.delete(`http://localhost:8000/cameras/${id}`);
            fetchData();
        } catch (error) {
            console.error(error);
        }
    };

    const handleUpdateApproval = async (userId, status) => {
        try {
            await axios.patch(`http://localhost:8000/users/${userId}/approval`, {
                approval_status: status
            });
            fetchData();
        } catch (error) {
            console.error("Error updating approval status", error);
            alert("Failed to update approval status");
        }
    };

    const getApprovalBadge = (status) => {
        switch (status) {
            case 'approved':
                return <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Approved
                </span>;
            case 'rejected':
                return <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    <XCircle className="h-3 w-3 mr-1" />
                    Rejected
                </span>;
            case 'pending':
            default:
                return <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <Clock className="h-3 w-3 mr-1" />
                    Pending
                </span>;
        }
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(streamUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="p-8">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-2xl font-bold text-gray-800">Admin Panel</h2>
                <button
                    onClick={() => setShowUploadModal(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
                >
                    <Upload className="h-4 w-4" />
                    <span>Upload Stream Video</span>
                </button>
            </div>


            <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-8 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-gray-800">User Management</h3>
                    <button
                        onClick={() => setShowUserModal(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md text-sm flex items-center space-x-1"
                    >
                        <Plus className="h-4 w-4" />
                        <span>Add User</span>
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 text-gray-600 font-medium text-sm">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">Email</th>
                                <th className="px-6 py-3">Role</th>
                                <th className="px-6 py-3">Status</th>
                                <th className="px-6 py-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {users.filter(u => u.email !== 'admin@example.com').map((u) => (
                                <tr key={u._id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 font-medium text-gray-800">{u.name}</td>
                                    <td className="px-6 py-4 text-gray-500">{u.email}</td>
                                    <td className="px-6 py-4"><span className="capitalize bg-gray-100 px-2 py-1 rounded text-xs font-medium text-gray-600">{u.role}</span></td>
                                    <td className="px-6 py-4">{getApprovalBadge(u.approval_status || 'pending')}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center space-x-2">
                                            {u.approval_status === 'pending' && (
                                                <>
                                                    <button
                                                        onClick={() => handleUpdateApproval(u._id, 'approved')}
                                                        className="text-green-600 hover:text-green-700 p-1 rounded hover:bg-green-50"
                                                        title="Approve"
                                                    >
                                                        <CheckCircle className="h-4 w-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleUpdateApproval(u._id, 'rejected')}
                                                        className="text-red-600 hover:text-red-700 p-1 rounded hover:bg-red-50"
                                                        title="Reject"
                                                    >
                                                        <XCircle className="h-4 w-4" />
                                                    </button>
                                                </>
                                            )}
                                            {u.approval_status === 'rejected' && (
                                                <button
                                                    onClick={() => handleUpdateApproval(u._id, 'approved')}
                                                    className="text-green-600 hover:text-green-700 p-1 rounded hover:bg-green-50"
                                                    title="Approve"
                                                >
                                                    <CheckCircle className="h-4 w-4" />
                                                </button>
                                            )}
                                            {u.approval_status === 'approved' && (
                                                <button
                                                    onClick={() => handleUpdateApproval(u._id, 'rejected')}
                                                    className="text-red-600 hover:text-red-700 p-1 rounded hover:bg-red-50"
                                                    title="Reject"
                                                >
                                                    <XCircle className="h-4 w-4" />
                                                </button>
                                            )}
                                            <button onClick={() => handleDeleteUser(u._id)} className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50">
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>


            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-gray-800">Camera Management</h3>
                    <button
                        onClick={() => setShowCameraModal(true)}
                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-md text-sm flex items-center space-x-1"
                    >
                        <Plus className="h-4 w-4" />
                        <span>Add Camera</span>
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 text-gray-600 font-medium text-sm">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">Location</th>
                                <th className="px-6 py-3">URL</th>
                                <th className="px-6 py-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {cameras.map((c) => (
                                <tr key={c._id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 font-medium text-gray-800">{c.name}</td>
                                    <td className="px-6 py-4 text-gray-500">{c.location}</td>
                                    <td className="px-6 py-4 text-blue-500 truncate max-w-xs">{c.url}</td>
                                    <td className="px-6 py-4">
                                        <button onClick={() => handleDeleteCamera(c._id)} className="text-red-500 hover:text-red-700">
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>


            {showUserModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-xl w-96">
                        <h3 className="text-lg font-bold mb-4">Add New User</h3>
                        <form onSubmit={handleCreateUser} className="space-y-4">
                            <input className="w-full border p-2 rounded" placeholder="Name" value={newUser.name} onChange={e => setNewUser({ ...newUser, name: e.target.value })} required />
                            <input className="w-full border p-2 rounded" type="email" placeholder="Email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} required />
                            <input className="w-full border p-2 rounded" type="password" placeholder="Password" value={newUser.password} onChange={e => setNewUser({ ...newUser, password: e.target.value })} required />
                            <select className="w-full border p-2 rounded" value={newUser.role} onChange={e => setNewUser({ ...newUser, role: e.target.value })}>
                                <option value="police">Police</option>
                                <option value="hospital">Hospital</option>
                                <option value="transport">Transport Authority</option>
                                <option value="road_safety">Road Safety</option>
                                <option value="admin">Admin</option>
                            </select>
                            <div className="flex justify-end space-x-2">
                                <button type="button" onClick={() => setShowUserModal(false)} className="px-4 py-2 text-gray-600">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Create</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showCameraModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-xl w-96">
                        <h3 className="text-lg font-bold mb-4">Add Camera Feed</h3>
                        <form onSubmit={handleCreateCamera} className="space-y-4">
                            <input className="w-full border p-2 rounded" placeholder="Name" value={newCamera.name} onChange={e => setNewCamera({ ...newCamera, name: e.target.value })} required />
                            <input className="w-full border p-2 rounded" placeholder="Location" value={newCamera.location} onChange={e => setNewCamera({ ...newCamera, location: e.target.value })} required />
                            <input className="w-full border p-2 rounded" placeholder="Stream URL" value={newCamera.url} onChange={e => setNewCamera({ ...newCamera, url: e.target.value })} required />
                            <div className="flex justify-end space-x-2">
                                <button type="button" onClick={() => setShowCameraModal(false)} className="px-4 py-2 text-gray-600">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded">Add</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showUploadModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-xl w-96">
                        <h3 className="text-lg font-bold mb-4">Upload Stream Video</h3>
                        <form onSubmit={handleUploadVideo} className="space-y-4">
                            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                                <input
                                    type="file"
                                    accept="video/*"
                                    onChange={e => setUploadFile(e.target.files[0])}
                                    className="hidden"
                                    id="video-upload"
                                />
                                <label htmlFor="video-upload" className="cursor-pointer flex flex-col items-center">
                                    <Video className="h-8 w-8 text-gray-400 mb-2" />
                                    <span className="text-sm text-gray-500">{uploadFile ? uploadFile.name : "Click to select video"}</span>
                                </label>
                            </div>
                            <div className="flex justify-end space-x-2">
                                <button type="button" onClick={() => setShowUploadModal(false)} className="px-4 py-2 text-gray-600">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-purple-600 text-white rounded" disabled={!uploadFile}>Upload & Stream</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showUrlModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-xl w-[500px]">
                        <h3 className="text-lg font-bold mb-4 text-green-600">✓ Stream Created Successfully!</h3>
                        <p className="text-sm text-gray-600 mb-4">Your video has been uploaded and is now streaming. An alert will be automatically generated after 2 minutes.</p>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Stream URL:</label>
                            <div className="flex items-center space-x-2">
                                <input
                                    type="text"
                                    value={streamUrl}
                                    readOnly
                                    className="flex-1 border border-gray-300 p-2 rounded text-sm font-mono bg-gray-50"
                                />
                                <button
                                    onClick={copyToClipboard}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center space-x-2 transition-colors"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="h-4 w-4" />
                                            <span>Copied!</span>
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="h-4 w-4" />
                                            <span>Copy</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        <div className="flex justify-end">
                            <button
                                onClick={() => setShowUrlModal(false)}
                                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminPanel;
