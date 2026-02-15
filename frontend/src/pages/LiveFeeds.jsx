import { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, AlertTriangle, Trash2, Video, Eye, EyeOff } from 'lucide-react';

import { useAuth } from '../context/AuthContext';

const CameraFeedCard = ({ cam, user, handleGenerateAlert, handleDeleteCamera, handleToggleDetection, detectionStatus }) => {
    const [isLive, setIsLive] = useState(false);
    const [hasError, setHasError] = useState(false);
    const isDetecting = detectionStatus[cam._id] || false;

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="aspect-video bg-gray-900 relative flex items-center justify-center overflow-hidden group">
                {/* Video Feed */}
                {cam.url && !hasError ? (
                    <img
                        src={cam.url}
                        alt={cam.name}
                        className={`w-full h-full object-cover transition-opacity duration-500 ${isLive ? 'opacity-100' : 'opacity-0'}`}
                        onLoad={() => { setIsLive(true); setHasError(false); }}
                        onError={() => { setIsLive(false); setHasError(true); }}
                    />
                ) : null}

                {/* Placeholder/Error State */}
                {(!isLive || hasError) && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
                        <Video className="h-16 w-16 text-white opacity-20 mb-2" />
                        <p className="text-white text-xs opacity-50">
                            {hasError ? 'No Signal' : 'Connecting...'}
                        </p>
                    </div>
                )}

                {/* Detection Overlay */}
                {isDetecting && (
                    <div className="absolute inset-0 border-4 border-green-500 pointer-events-none">
                        <div className="absolute top-2 left-2 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold animate-pulse flex items-center space-x-1">
                            <Eye className="h-3 w-3" />
                            <span>AI MONITORING</span>
                        </div>
                    </div>
                )}

                {/* Status Badge */}
                <div className="absolute top-2 right-2 z-10">
                    {isLive && !hasError ? (
                        <span className="px-2 py-1 bg-red-600 text-white text-xs font-bold rounded animate-pulse flex items-center shadow-sm">
                            <span className="w-2 h-2 bg-white rounded-full mr-1.5"></span>
                            LIVE
                        </span>
                    ) : (
                        <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs font-bold rounded flex items-center shadow-sm border border-gray-600">
                            OFFLINE
                        </span>
                    )}
                </div>
            </div>

            <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-gray-800">{cam.name}</h3>
                    {user?.role === 'admin' && (
                        <div className="flex space-x-2">
                            <button
                                onClick={() => handleToggleDetection(cam._id, isDetecting)}
                                className={`${isDetecting
                                    ? 'text-green-600 hover:text-green-700 bg-green-50'
                                    : 'text-blue-500 hover:text-blue-700 bg-blue-50'
                                    } p-1.5 rounded transition-colors`}
                                title={isDetecting ? "Stop Detection" : "Start Detection"}
                            >
                                {isDetecting ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                            </button>
                            <button
                                onClick={() => handleGenerateAlert(cam.location)}
                                className="text-orange-500 hover:text-orange-700 p-1 rounded hover:bg-orange-50 transition-colors"
                                title="Generate Alert"
                            >
                                <AlertTriangle className="h-5 w-5" />
                            </button>
                            <button
                                onClick={() => handleDeleteCamera(cam._id)}
                                className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                                title="Remove Camera"
                            >
                                <Trash2 className="h-5 w-5" />
                            </button>
                        </div>
                    )}
                </div>
                <div className="flex items-center text-gray-500 text-sm mb-2">
                    <MapPin className="h-4 w-4 mr-1" />
                    {cam.location}
                </div>
                {isDetecting && (
                    <div className="mb-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                        <p className="text-xs text-green-700 font-medium flex items-center">
                            <Eye className="h-3 w-3 mr-1" />
                            Accident detection is active - Alerts will be generated automatically
                        </p>
                    </div>
                )}
                <div className="bg-gray-50 p-2 rounded border border-gray-200">
                    <p className="text-xs text-gray-600 font-mono break-all truncate">
                        {cam.url || 'No URL configured'}
                    </p>
                </div>
            </div>
        </div>
    );
};

const Cameras = () => {
    const { user } = useAuth();
    const [cameras, setCameras] = useState([]);
    const [detectionStatus, setDetectionStatus] = useState({});

    const fetchCameras = async () => {
        try {
            const response = await axios.get('http://localhost:8000/cameras/');
            setCameras(response.data);

            // Update detection status for each camera
            const statusMap = {};
            response.data.forEach(cam => {
                statusMap[cam._id] = cam.detection_active || false;
            });
            setDetectionStatus(statusMap);
        } catch (error) {
            console.error("Error fetching cameras", error);
        }
    };

    useEffect(() => {
        fetchCameras();
    }, []);

    const handleGenerateAlert = async (location) => {
        const details = prompt("Enter alert details (e.g., Accident detected):");
        if (!details) return;

        try {
            await axios.post('http://localhost:8000/alerts/', {
                location,
                details
            });
            alert("Alert generated and emails sent!");
        } catch (error) {
            alert("Error generating alert");
        }
    };

    const handleDeleteCamera = async (id) => {
        if (!confirm("Are you sure you want to remove this camera?")) return;
        try {
            await axios.delete(`http://localhost:8000/cameras/${id}`);
            fetchCameras();
        } catch (error) {
            console.error("Error deleting camera", error);
        }
    };

    const handleToggleDetection = async (cameraId, isCurrentlyDetecting) => {
        try {
            if (isCurrentlyDetecting) {
                // Stop detection
                await axios.post(`http://localhost:8000/detection/stop/${cameraId}`);
                setDetectionStatus(prev => ({ ...prev, [cameraId]: false }));
                alert("Accident detection stopped for this camera");
            } else {
                // Start detection
                await axios.post(`http://localhost:8000/detection/start/${cameraId}`);
                setDetectionStatus(prev => ({ ...prev, [cameraId]: true }));
                alert("Accident detection started! Alerts will be automatically generated when accidents are detected.");
            }
        } catch (error) {
            console.error("Error toggling detection", error);
            alert(`Error ${isCurrentlyDetecting ? 'stopping' : 'starting'} detection: ${error.response?.data?.detail || error.message}`);
        }
    };

    return (
        <div className="p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Cameras</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {cameras.map((cam) => (
                    <CameraFeedCard
                        key={cam._id}
                        cam={cam}
                        user={user}
                        handleGenerateAlert={handleGenerateAlert}
                        handleDeleteCamera={handleDeleteCamera}
                        handleToggleDetection={handleToggleDetection}
                        detectionStatus={detectionStatus}
                    />
                ))}

                {cameras.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
                        <p className="text-gray-500">No cameras found. Add cameras from the Admin Panel.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Cameras;
