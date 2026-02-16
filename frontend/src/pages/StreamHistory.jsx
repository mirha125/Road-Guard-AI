import { useState, useEffect } from 'react';
import axios from 'axios';
import { Trash2, PlayCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const StreamHistory = () => {
    const { user } = useAuth();
    const [streams, setStreams] = useState([]);

    const fetchStreams = async () => {
        try {
            const response = await axios.get('http://localhost:8000/streams/');
            setStreams(response.data);
        } catch (error) {
            console.error("Error fetching streams", error);
        }
    };

    useEffect(() => {
        fetchStreams();
    }, []);

    const handleDelete = async (id) => {
        if (!confirm("Are you sure you want to delete this stream?")) return;
        try {
            await axios.delete(`http://localhost:8000/streams/${id}`);
            fetchStreams();
        } catch (error) {
            console.error(error);
        }
    };

    const handleStopStream = async (id) => {
        if (!confirm("Are you sure you want to stop this stream?")) return;
        try {
            await axios.patch(`http://localhost:8000/streams/${id}/stop`);
            fetchStreams();
        } catch (error) {
            console.error(error);
        }
    };

    const handleDeleteAll = async () => {
        if (!confirm("Are you sure you want to PERMANENTLY DELETE ALL STREAMS? This action cannot be undone.")) return;
        try {
            await axios.delete('http://localhost:8000/streams/all/delete');
            fetchStreams();
        } catch (error) {
            console.error("Error deleting all streams", error);
            alert("Failed to delete all streams");
        }
    };

    return (
        <div className="p-8">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Stream History</h2>
                {user?.role === 'admin' && streams.length > 0 && (
                    <button
                        onClick={handleDeleteAll}
                        className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors text-sm font-medium shadow-sm"
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete All Streams
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {streams.map((stream) => (
                    <div key={stream._id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden group">
                        <div className="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 relative flex items-center justify-center">

                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <PlayCircle className="h-16 w-16 text-white opacity-50 mb-2" />
                                <p className="text-white text-sm opacity-75">Video Stream</p>
                            </div>
                            <div className="absolute top-2 right-2">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${stream.is_active ? 'bg-red-600 text-white animate-pulse' : 'bg-gray-600 text-white'}`}>
                                    {stream.is_active ? 'LIVE' : 'STOPPED'}
                                </span>
                            </div>
                        </div>
                        <div className="p-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="font-medium text-gray-800 truncate" title={stream.video_path.split('/').pop()}>
                                        {stream.video_path.split('/').pop()}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Created: {new Date(stream.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                            <div className="mt-4 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${stream.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                                        {stream.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                    <a
                                        href={`http://localhost:8000${stream.stream_url}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                                    >
                                        View Feed
                                    </a>
                                </div>
                                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                                    <p className="text-xs text-gray-600 font-mono break-all">
                                        {`http://localhost:8000${stream.stream_url}`}
                                    </p>
                                </div>
                                <div className="grid grid-cols-2 gap-2 pt-2">
                                    {stream.is_active ? (
                                        <button
                                            onClick={() => handleStopStream(stream._id)}
                                            className="bg-amber-500 hover:bg-amber-600 text-white py-2 rounded text-sm font-medium transition-colors flex items-center justify-center"
                                        >
                                            Stop
                                        </button>
                                    ) : (
                                        <div className="bg-gray-100 text-gray-400 py-2 rounded text-sm font-medium text-center flex items-center justify-center cursor-not-allowed">
                                            Inactive
                                        </div>
                                    )}
                                    <button
                                        onClick={() => handleDelete(stream._id)}
                                        className="bg-red-500 hover:bg-red-600 text-white py-2 rounded text-sm font-medium transition-colors flex items-center justify-center space-x-1"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                        <span>Delete</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {streams.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
                        <p className="text-gray-500">No streams found.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StreamHistory;
