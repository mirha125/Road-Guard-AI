import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { AlertTriangle, Video, MapPin, Trash2, Camera, FileText, X, Mail, Globe, Activity, Bell, CheckCircle, XCircle, Clock, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../context/AuthContext';

const AUTO_DISPATCH_SECONDS = 15;
const OVERLAY_DISPLAY_SECONDS = 15;

const CountdownTimer = ({ createdAt }) => {
    const [secondsLeft, setSecondsLeft] = useState(() => {
        const elapsed = (Date.now() - new Date(createdAt).getTime()) / 1000;
        return Math.max(0, Math.ceil(AUTO_DISPATCH_SECONDS - elapsed));
    });

    useEffect(() => {
        if (secondsLeft <= 0) return;
        const timer = setInterval(() => {
            const elapsed = (Date.now() - new Date(createdAt).getTime()) / 1000;
            const remaining = Math.max(0, Math.ceil(AUTO_DISPATCH_SECONDS - elapsed));
            setSecondsLeft(remaining);
            if (remaining <= 0) clearInterval(timer);
        }, 500);
        return () => clearInterval(timer);
    }, [createdAt]);

    if (secondsLeft <= 0) return <span className="text-xs text-gray-400">Auto-dispatching...</span>;

    const urgency = secondsLeft <= 5 ? 'text-red-600 font-bold' : secondsLeft <= 10 ? 'text-orange-500 font-semibold' : 'text-yellow-600';

    return (
        <span className={`text-xs ${urgency} flex items-center`}>
            <Clock className="h-3 w-3 mr-1" />
            {secondsLeft}s
        </span>
    );
};

const StatusBadge = ({ status }) => {
    const config = {
        PENDING_ADMIN_REVIEW: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200', label: 'Pending Review' },
        EMERGENCY_DISPATCHED: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200', label: 'Dispatched' },
        AUTO_DISPATCHED: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-200', label: 'Auto-Dispatched' },
        FALSE_ALARM: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-200', label: 'False Alarm' },
    };
    const c = config[status] || config.PENDING_ADMIN_REVIEW;
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text} border ${c.border}`}>
            {c.label}
        </span>
    );
};

const AlertReviewOverlay = ({ alert, queueSize, onConfirm, onReject, onDismiss }) => {
    const [secondsLeft, setSecondsLeft] = useState(OVERLAY_DISPLAY_SECONDS);
    const [acting, setActing] = useState(false);
    const mountTimeRef = useRef(null);
    const videoRef = useRef(null);

    // Reset timer each time a NEW alert is shown
    useEffect(() => {
        if (!alert) return;
        mountTimeRef.current = Date.now();
        setActing(false);
        setSecondsLeft(OVERLAY_DISPLAY_SECONDS);
    }, [alert?._id]);

    // Countdown based on when overlay appeared (not alert.time)
    useEffect(() => {
        if (!alert || !mountTimeRef.current) return;
        const timer = setInterval(() => {
            const elapsed = (Date.now() - mountTimeRef.current) / 1000;
            const remaining = Math.max(0, Math.ceil(OVERLAY_DISPLAY_SECONDS - elapsed));
            setSecondsLeft(remaining);
            if (remaining <= 0) {
                clearInterval(timer);
                onDismiss(alert._id);
            }
        }, 500);
        return () => clearInterval(timer);
    }, [alert?._id]);

    if (!alert) return null;

    const progress = (secondsLeft / OVERLAY_DISPLAY_SECONDS) * 100;
    const snippetSrc = alert.snippet_url ? `http://localhost:8000${alert.snippet_url}` : null;

    const handleConfirm = async () => {
        if (acting) return;
        setActing(true);
        await onConfirm(alert._id);
    };

    const handleReject = async () => {
        if (acting) return;
        setActing(true);
        await onReject(alert._id);
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-4 px-4">
            {/* Backdrop */}
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />

            {/* Alert Card */}
            <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden border-2 border-red-500">
                {/* Countdown progress bar */}
                <div className="h-1.5 bg-gray-200 w-full">
                    <div
                        className={`h-full transition-all duration-500 ease-linear ${secondsLeft <= 5 ? 'bg-red-500' : secondsLeft <= 10 ? 'bg-orange-400' : 'bg-yellow-400'}`}
                        style={{ width: `${progress}%` }}
                    />
                </div>

                {/* Header */}
                <div className="bg-red-600 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="bg-white/20 rounded-full p-2">
                            <AlertTriangle className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <h2 className="text-white font-bold text-lg">Accident Detected</h2>
                            <p className="text-red-100 text-sm">Review and take action</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        {queueSize > 1 && (
                            <div className="bg-white/20 rounded-full px-3 py-1 text-white text-xs font-bold">
                                +{queueSize - 1} more
                            </div>
                        )}
                        <div className={`text-white font-mono text-2xl font-bold ${secondsLeft <= 5 ? 'animate-pulse' : ''}`}>
                            {secondsLeft}s
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {/* Video Snippet */}
                        <div className="bg-gray-900 rounded-xl overflow-hidden aspect-video flex items-center justify-center">
                            {snippetSrc ? (
                                <video
                                    ref={videoRef}
                                    key={snippetSrc}
                                    src={snippetSrc}
                                    autoPlay
                                    loop
                                    muted
                                    playsInline
                                    controls
                                    onLoadedData={() => {
                                        // Force play in case autoplay is blocked
                                        videoRef.current?.play().catch(() => {});
                                    }}
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="text-center text-gray-400">
                                    <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                    <p className="text-sm">No clip available</p>
                                </div>
                            )}
                        </div>

                        {/* Details */}
                        <div className="flex flex-col justify-between">
                            <div className="space-y-3">
                                <div className="flex items-center text-sm text-gray-700">
                                    <MapPin className="h-4 w-4 mr-2 text-blue-500 flex-shrink-0" />
                                    <span className="font-semibold">{alert.location}</span>
                                </div>
                                <div className="flex items-center text-sm text-gray-700">
                                    <Camera className="h-4 w-4 mr-2 text-purple-500 flex-shrink-0" />
                                    <span>{alert.camera_name || 'Unknown Camera'}</span>
                                </div>
                                <div className="flex items-center text-sm text-gray-700">
                                    <Clock className="h-4 w-4 mr-2 text-gray-500 flex-shrink-0" />
                                    <span>{new Date(alert.time).toLocaleString()}</span>
                                </div>
                                {alert.confidence && (
                                    <div className="flex items-center text-sm text-gray-700">
                                        <Zap className="h-4 w-4 mr-2 text-orange-500 flex-shrink-0" />
                                        <span>Confidence: <span className="font-bold text-red-600">{(alert.confidence * 100).toFixed(1)}%</span></span>
                                    </div>
                                )}
                                <p className="text-xs text-gray-500 mt-2 leading-relaxed">{alert.details}</p>
                            </div>

                            <div className="text-xs text-gray-400 mt-3 bg-gray-50 rounded-lg p-2 text-center">
                                Auto-dispatch in <span className="font-bold text-gray-600">{secondsLeft}s</span> if no action taken
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4 mt-6">
                        <button
                            onClick={handleConfirm}
                            disabled={acting}
                            className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold py-3.5 px-6 rounded-xl transition-all text-sm shadow-lg shadow-red-200"
                        >
                            <CheckCircle className="h-5 w-5" />
                            Confirm & Dispatch Emergency
                        </button>
                        <button
                            onClick={handleReject}
                            disabled={acting}
                            className="flex-1 flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700 font-bold py-3.5 px-6 rounded-xl transition-all text-sm border border-gray-300"
                        >
                            <XCircle className="h-5 w-5" />
                            Reject (False Alarm)
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
        <div className={`p-3 rounded-lg ${color}`}>
            <Icon className="h-6 w-6 text-white" />
        </div>
        <div>
            <p className="text-sm text-gray-500 font-medium">{title}</p>
            <h3 className="text-2xl font-bold text-gray-800">{value}</h3>
        </div>
    </div>
);

const CameraCard = ({ camera }) => {
    const [isLive, setIsLive] = useState(false);
    const [hasError, setHasError] = useState(false);

    return (
        <div className="group relative bg-gray-900 rounded-lg overflow-hidden aspect-video shadow-md hover:shadow-xl transition-all duration-300">

            {camera.url ? (
                <div className="absolute inset-0">

                    <img
                        src={camera.url}
                        alt={camera.name}
                        className={`w-full h-full object-cover transition-opacity duration-500 ${isLive ? 'opacity-80 group-hover:opacity-100' : 'opacity-0'}`}
                        onLoad={() => { setIsLive(true); setHasError(false); }}
                        onError={(e) => {
                            setIsLive(false);
                            setHasError(true);
                        }}
                    />


                    {(!isLive || hasError) && (
                        <img
                            src='https://placehold.co/600x400/1f2937/ffffff?text=No+Signal'
                            alt="No Signal"
                            className="w-full h-full object-cover absolute inset-0"
                        />
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent"></div>
                </div>
            ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
                    <Camera className="h-10 w-10 text-gray-600" />
                </div>
            )}

            {/* AI Monitoring Badge */}
            {camera.detection_active && (
                <div className="absolute top-2 left-2 z-10">
                    <span className="px-1.5 py-0.5 bg-green-500 text-white text-[10px] font-bold rounded flex items-center shadow-sm animate-pulse">
                        <Activity className="h-3 w-3 mr-1" />
                        AI ON
                    </span>
                </div>
            )}

            <div className="absolute inset-0 p-3 flex flex-col justify-between z-10">
                <div className="flex justify-end">
                    {isLive && !hasError ? (
                        <span className="px-1.5 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded flex items-center animate-pulse">
                            <span className="w-1.5 h-1.5 bg-white rounded-full mr-1"></span>
                            LIVE
                        </span>
                    ) : (
                        <span className="px-1.5 py-0.5 bg-gray-700 text-gray-300 text-[10px] font-bold rounded flex items-center">
                            OFFLINE
                        </span>
                    )}
                </div>

                <div>
                    <p className="text-white text-sm font-medium truncate shadow-sm">
                        {camera.name}
                    </p>
                    <p className="text-gray-300 text-xs truncate flex items-center mt-0.5">
                        <MapPin className="h-3 w-3 mr-1" />
                        {camera.location}
                    </p>
                </div>
            </div>
        </div>
    );
};

const LogsPanel = ({ alert, onClose, isOpen }) => {
    if (!isOpen || !alert) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-25 z-40 transition-opacity"
                onClick={onClose}
            ></div>

            {/* Panel */}
            <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 border-l border-gray-200 flex flex-col">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center">
                        <FileText className="h-5 w-5 mr-2 text-blue-600" />
                        Alert Logs
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-200 transition-colors"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto flex-1">
                    <div className="mb-8">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Alert Details</h4>
                        <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                            <div className="flex items-start mb-2">
                                <AlertTriangle className="h-5 w-5 text-red-500 mr-2 mt-0.5" />
                                <span className="font-semibold text-red-700">Accident Detected</span>
                            </div>
                            <p className="text-gray-700 text-sm mb-3 ml-7">{alert.details}</p>
                            <div className="flex items-center text-xs text-gray-500 ml-7 space-x-4 flex-wrap gap-y-1">
                                <span className="flex items-center">
                                    <MapPin className="h-3 w-3 mr-1" />
                                    {alert.location}
                                </span>
                                <span className="flex items-center">
                                    <Globe className="h-3 w-3 mr-1" />
                                    {new Date(alert.time).toLocaleString()}
                                </span>
                                <StatusBadge status={alert.status} />
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                            <span>Email Recipients</span>
                            <span className="text-xs font-normal text-gray-400 normal-case bg-gray-100 px-2 py-0.5 rounded-full">
                                {alert.notified_hospitals?.length || 0} {alert.status === 'PENDING_ADMIN_REVIEW' ? 'pending' : alert.status === 'FALSE_ALARM' ? 'not sent' : 'sent'}
                            </span>
                        </h4>

                        {alert.notified_hospitals && alert.notified_hospitals.length > 0 ? (
                            <ul className="space-y-2">
                                {alert.notified_hospitals.map((email, index) => (
                                    <li key={index} className="flex items-center p-3 bg-white rounded-lg border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                                        <div className="bg-blue-50 p-2 rounded-full mr-3 border border-blue-100">
                                            <Mail className="h-4 w-4 text-blue-600" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-gray-900 truncate">{email}</p>
                                            <p className="text-xs text-gray-500">Hospital Notification</p>
                                        </div>
                                        <div className="ml-2">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                                Sent
                                            </span>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                                <Mail className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                                <p className="text-gray-500 text-sm font-medium">No emails sent for this alert.</p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-4 border-t border-gray-100 bg-gray-50 text-center text-xs text-gray-400">
                    Alert ID: {alert._id}
                </div>
            </div>
        </>
    );
};

const DashboardOverview = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState({
        alerts: 0,
        activeStreams: 0,
        cameras: 0,
        users: 0
    });
    const [allAlerts, setAllAlerts] = useState([]);
    const [cameras, setCameras] = useState([]);
    const [streams, setStreams] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [timeRange, setTimeRange] = useState('24h');

    // Logs Panel State
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [isLogsOpen, setIsLogsOpen] = useState(false);

    // Track previous alert count for notifications
    const [previousAlertCount, setPreviousAlertCount] = useState(0);
    const [notificationPermission, setNotificationPermission] = useState(false);
    const [toastNotifications, setToastNotifications] = useState([]);

    // Alert review queue (for multiple simultaneous alerts)
    const [reviewQueue, setReviewQueue] = useState([]);  // array of alert objects
    const seenAlertIdsRef = useRef(new Set());            // alerts already queued or handled

    // Request notification permission on mount
    useEffect(() => {
        if ('Notification' in window) {
            if (Notification.permission === 'granted') {
                setNotificationPermission(true);
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission().then(permission => {
                    setNotificationPermission(permission === 'granted');
                });
            }
        }
    }, []);

    // Show notification for new alerts
    const showNotification = (alert) => {
        // Show in-app toast notification
        const toastId = Date.now();
        setToastNotifications(prev => [...prev, { ...alert, toastId }]);

        // Auto-remove toast after 8 seconds
        setTimeout(() => {
            setToastNotifications(prev => prev.filter(n => n.toastId !== toastId));
        }, 8000);

        // Show browser notification if permitted
        if (notificationPermission && 'Notification' in window) {
            const notification = new Notification('🚨 New Alert Detected!', {
                body: `Location: ${alert.location}\n${alert.details}`,
                icon: '/alert-icon.png',
                badge: '/alert-badge.png',
                tag: alert._id,
                requireInteraction: true,
                vibrate: [200, 100, 200],
            });

            notification.onclick = () => {
                window.focus();
                setSelectedAlert(alert);
                setIsLogsOpen(true);
                notification.close();
            };

            setTimeout(() => notification.close(), 10000);
        }

        // Play alert sound
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTUHG2m98OScTgwNUrDn77RnHwU7k9n0yXgqBSB0yO/ekEMME1+35+mhUBMJSKHh8rtoHwU7k9n0yXgqBR91x+/gkEIOFF+36OehTxMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEQME1635+mhUBMJSKHh8rtoHwU7k9n0yXgqBR90x+/gkEMME1+36OehTxMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEMOFF+35+mhUBQJSKHh8rtoHwU7k9n0yXgqBR90x+/gkEQME1+35+mhUBQJSKHh8rtoHwU7k9n0yXgqBSB0x+/gkEQMFF+35+mhUBMJSKHh8rtoHwU7k9n0yXgqBR90x+/gkEQME1635+mhUBMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEQME1635+mhUBMKSaLh8rtoHwU7k9n0yXgqBR90x+/gkEQME1635+mhUBMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEQME1635+mhUBMKSaLh8g==');
            audio.play().catch(() => {});
        } catch (e) {
            // Ignore audio errors
        }
    };

    const processChartData = (alerts, range) => {
        const now = new Date();
        let buckets = [];
        let startTime;

        switch (range) {
            case '24h':
                buckets = [
                    { time: '00:00', count: 0 },
                    { time: '04:00', count: 0 },
                    { time: '08:00', count: 0 },
                    { time: '12:00', count: 0 },
                    { time: '16:00', count: 0 },
                    { time: '20:00', count: 0 }
                ];
                startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const hour = alertTime.getHours();
                        const bucketIndex = Math.floor(hour / 4);
                        if (buckets[bucketIndex]) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case '7d':
                for (let i = 6; i >= 0; i--) {
                    const date = new Date(now);
                    date.setDate(date.getDate() - i);
                    buckets.push({
                        time: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                        count: 0
                    });
                }
                startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const daysDiff = Math.floor((now - alertTime) / (24 * 60 * 60 * 1000));
                        const bucketIndex = 6 - daysDiff;
                        if (bucketIndex >= 0 && bucketIndex < 7) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case '30d':
                for (let i = 4; i >= 0; i--) {
                    buckets.push({
                        time: `Week ${5 - i}`,
                        count: 0
                    });
                }
                startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const weeksDiff = Math.floor((now - alertTime) / (7 * 24 * 60 * 60 * 1000));
                        const bucketIndex = 4 - weeksDiff;
                        if (bucketIndex >= 0 && bucketIndex < 5) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case '1y':
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                for (let i = 11; i >= 0; i--) {
                    const monthDate = new Date(now);
                    monthDate.setMonth(monthDate.getMonth() - i);
                    buckets.push({
                        time: months[monthDate.getMonth()],
                        count: 0
                    });
                }
                startTime = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    if (alertTime >= startTime) {
                        const monthsDiff = (now.getFullYear() - alertTime.getFullYear()) * 12 +
                            (now.getMonth() - alertTime.getMonth());
                        const bucketIndex = 11 - monthsDiff;
                        if (bucketIndex >= 0 && bucketIndex < 12) {
                            buckets[bucketIndex].count++;
                        }
                    }
                });
                break;

            case 'all':
                const alertsByMonth = {};
                alerts.forEach(alert => {
                    const alertTime = new Date(alert.time);
                    const monthKey = `${alertTime.getFullYear()}-${String(alertTime.getMonth() + 1).padStart(2, '0')}`;
                    alertsByMonth[monthKey] = (alertsByMonth[monthKey] || 0) + 1;
                });

                const sortedMonths = Object.keys(alertsByMonth).sort();
                buckets = sortedMonths.map(monthKey => {
                    const [year, month] = monthKey.split('-');
                    const date = new Date(year, month - 1);
                    return {
                        time: date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
                        count: alertsByMonth[monthKey]
                    };
                });
                break;
        }

        return buckets;
    };

    const fetchData = async () => {
        try {
            const [alertsRes, streamsRes, camerasRes, usersRes] = await Promise.all([
                axios.get('http://localhost:8000/alerts/'),
                axios.get('http://localhost:8000/streams/'),
                axios.get('http://localhost:8000/cameras/'),
                axios.get('http://localhost:8000/users/')
            ]);

            const newAlerts = alertsRes.data;

            // Queue new PENDING_ADMIN_REVIEW alerts for overlay (admin only)
            if (user?.role === 'admin') {
                const pendingAlerts = newAlerts.filter(a => a.status === 'PENDING_ADMIN_REVIEW');
                const newForQueue = pendingAlerts.filter(a => !seenAlertIdsRef.current.has(a._id));
                if (newForQueue.length > 0) {
                    newForQueue.forEach(a => seenAlertIdsRef.current.add(a._id));
                    setReviewQueue(prev => [...prev, ...newForQueue]);
                    // Play alert sound for new arrivals
                    try {
                        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTUHG2m98OScTgwNUrDn77RnHwU7k9n0yXgqBSB0yO/ekEMME1+35+mhUBMJSKHh8rtoHwU7k9n0yXgqBR91x+/gkEIOFF+36OehTxMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEQME1635+mhUBMJSKHh8rtoHwU7k9n0yXgqBR90x+/gkEMME1+36OehTxMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEMOFF+35+mhUBQJSKHh8rtoHwU7k9n0yXgqBR90x+/gkEQME1+35+mhUBQJSKHh8rtoHwU7k9n0yXgqBSB0x+/gkEQMFF+35+mhUBMJSKHh8rtoHwU7k9n0yXgqBR90x+/gkEQME1635+mhUBMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEQME1635+mhUBMKSaLh8rtoHwU7k9n0yXgqBR90x+/gkEQME1635+mhUBMKSaLh8rtoHwU7k9n0yXgqBSB0x+/gkEQME1635+mhUBMKSaLh8g==');
                        audio.play().catch(() => {});
                    } catch (e) {}
                }
                // Remove alerts from queue that are no longer pending (server auto-dispatched)
                const pendingIds = new Set(pendingAlerts.map(a => a._id));
                setReviewQueue(prev => prev.filter(a => pendingIds.has(a._id)));
            }

            // Check for new alerts and show notifications (non-admin / browser notifications)
            if (previousAlertCount > 0 && newAlerts.length > previousAlertCount) {
                const alertsToNotify = newAlerts.slice(0, newAlerts.length - previousAlertCount);
                alertsToNotify.forEach(a => {
                    showNotification(a);
                });
            }

            // Update previous count
            setPreviousAlertCount(newAlerts.length);

            setStats({
                alerts: newAlerts.length,
                activeStreams: streamsRes.data.filter(s => s.is_active).length,
                cameras: camerasRes.data.length,
                users: usersRes.data.length
            });
            setAllAlerts(newAlerts);
            setCameras(camerasRes.data);
            setStreams(streamsRes.data);
            setChartData(processChartData(newAlerts, timeRange));
        } catch (error) {
            console.error("Error fetching dashboard data", error);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 3000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (allAlerts.length > 0) {
            setChartData(processChartData(allAlerts, timeRange));
        }
    }, [timeRange, allAlerts]);

    const handleDeleteAlert = async (id) => {
        if (!confirm("Are you sure you want to delete this alert?")) return;
        try {
            await axios.delete(`http://localhost:8000/alerts/${id}`);
            fetchData();
        } catch (error) {
            console.error("Error deleting alert", error);
            alert("Failed to delete alert");
        }
    };

    const handleDeleteAllAlerts = async () => {
        if (!confirm("Are you sure you want to PERMANENTLY DELETE ALL ALERTS? This action cannot be undone.")) return;
        try {
            await axios.delete('http://localhost:8000/alerts/all/delete');
            fetchData();
        } catch (error) {
            console.error("Error deleting all alerts", error);
            alert("Failed to delete all alerts");
        }
    };

    // Remove an alert from the review queue (next one auto-shows)
    const removeFromQueue = useCallback((id) => {
        setReviewQueue(prev => prev.filter(a => a._id !== id));
    }, []);

    const handleConfirmAlert = async (id) => {
        try {
            await axios.post(`http://localhost:8000/alerts/${id}/confirm`);
            removeFromQueue(id);
            fetchData();
        } catch (error) {
            if (error.response?.status === 409) {
                removeFromQueue(id);
                fetchData();
            } else {
                console.error("Error confirming alert", error);
            }
        }
    };

    const handleRejectAlert = async (id) => {
        try {
            await axios.post(`http://localhost:8000/alerts/${id}/reject`);
            removeFromQueue(id);
            fetchData();
        } catch (error) {
            if (error.response?.status === 409) {
                removeFromQueue(id);
                fetchData();
            } else {
                console.error("Error rejecting alert", error);
            }
        }
    };

    // Called when overlay timer expires — dismiss this alert, next one will show
    const handleDismissReview = useCallback((id) => {
        removeFromQueue(id);
    }, [removeFromQueue]);

    const openLogs = (alert) => {
        setSelectedAlert(alert);
        setIsLogsOpen(true);
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                    <p className="text-sm font-medium text-gray-800">{payload[0].payload.time}</p>
                    <p className="text-sm text-red-600">
                        accidents: <span className="font-bold">{payload[0].value}</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    const getChartTitle = () => {
        switch (timeRange) {
            case '24h': return 'Accident Trends (24h)';
            case '7d': return 'Accident Trends (7 Days)';
            case '30d': return 'Accident Trends (30 Days)';
            case '1y': return 'Accident Trends (1 Year)';
            case 'all': return 'Accident Trends (All Time)';
            default: return 'Accident Trends';
        }
    };

    return (
        <div className="p-8 relative">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Overview</h2>

            {/* Alert Review Overlay - queue-based, shows one at a time */}
            {user?.role === 'admin' && reviewQueue.length > 0 && (
                <AlertReviewOverlay
                    alert={reviewQueue[0]}
                    queueSize={reviewQueue.length}
                    onConfirm={handleConfirmAlert}
                    onReject={handleRejectAlert}
                    onDismiss={handleDismissReview}
                />
            )}

            {/* Toast Notifications (for non-pending alerts / non-admin users) */}
            <div className="fixed top-4 right-4 z-50 space-y-3 max-w-md">
                {toastNotifications.map((notification) => (
                    <div
                        key={notification.toastId}
                        className="bg-red-600 text-white rounded-lg shadow-2xl p-4 border-l-4 border-red-800 animate-slide-in-right flex items-start space-x-3"
                        style={{
                            animation: 'slideInRight 0.3s ease-out'
                        }}
                    >
                        <div className="flex-shrink-0">
                            <Bell className="h-6 w-6 animate-bounce" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-bold text-sm mb-1">New Alert Detected!</p>
                            <p className="text-xs opacity-90 mb-1">
                                <MapPin className="h-3 w-3 inline mr-1" />
                                {notification.location}
                            </p>
                            <p className="text-xs opacity-80 line-clamp-2">{notification.details}</p>
                        </div>
                        <button
                            onClick={() => {
                                setToastNotifications(prev =>
                                    prev.filter(n => n.toastId !== notification.toastId)
                                );
                                setSelectedAlert(notification);
                                setIsLogsOpen(true);
                            }}
                            className="flex-shrink-0 text-white hover:text-red-200 transition-colors"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    </div>
                ))}
            </div>

            {/* Logs Panel */}
            <LogsPanel
                alert={selectedAlert}
                isOpen={isLogsOpen}
                onClose={() => setIsLogsOpen(false)}
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard title="Total Alerts" value={stats.alerts} icon={AlertTriangle} color="bg-red-500" />
                <StatCard title="Cameras" value={stats.cameras} icon={Video} color="bg-blue-500" />
                <StatCard title="Total Users" value={stats.users} icon={MapPin} color="bg-purple-500" />
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-8">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                    <h3 className="text-lg font-bold text-gray-800">{getChartTitle()}</h3>
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value)}
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="1y">Last 1 Year</option>
                        <option value="all">All Time</option>
                    </select>
                </div>
                <div className="p-6">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: '#e5e7eb' }} />
                            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={{ stroke: '#e5e7eb' }} />
                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(239, 68, 68, 0.1)' }} />
                            <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} maxBarSize={60} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-8">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                    <div>
                        <h3 className="text-lg font-bold text-gray-800">All Alerts History</h3>
                        <p className="text-sm text-gray-500">Complete log of all detected incidents</p>
                    </div>
                    <div className="flex items-center space-x-3">
                        <div className="bg-white px-3 py-1 rounded-full text-xs font-semibold text-gray-500 border border-gray-200">
                            {allAlerts.length} Total Records
                        </div>
                        {user?.role === 'admin' && allAlerts.length > 0 && (
                            <button
                                onClick={handleDeleteAllAlerts}
                                className="flex items-center px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors text-xs font-medium border border-red-100"
                            >
                                <Trash2 className="h-4 w-4 mr-1.5" />
                                Delete All
                            </button>
                        )}
                    </div>
                </div>
                <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                    <table className="w-full text-left">
                        <thead className="bg-white text-gray-600 font-bold text-xs uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                            <tr>
                                <th className="px-6 py-4 border-b">Location / Time</th>
                                <th className="px-6 py-4 border-b">Details</th>
                                <th className="px-6 py-4 border-b">Status</th>
                                {user?.role === 'admin' && <th className="px-6 py-4 border-b text-right">Actions</th>}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {allAlerts.map((alert) => (
                                <tr key={alert._id} className="hover:bg-gray-50 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="font-bold text-gray-800">{alert.location}</div>
                                        <div className="text-xs text-gray-500 mt-1 flex items-center">
                                            <Globe className="h-3 w-3 mr-1" />
                                            {new Date(alert.time).toLocaleString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <p className="text-sm text-gray-600 line-clamp-2">{alert.details}</p>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col gap-1">
                                            <StatusBadge status={alert.status} />
                                            {alert.status === 'PENDING_ADMIN_REVIEW' && (
                                                <CountdownTimer createdAt={alert.time} />
                                            )}
                                        </div>
                                    </td>
                                    {user?.role === 'admin' && (
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end space-x-2">
                                                {alert.status === 'PENDING_ADMIN_REVIEW' && (
                                                    <>
                                                        <button
                                                            onClick={() => handleConfirmAlert(alert._id)}
                                                            className="flex items-center text-white bg-green-600 hover:bg-green-700 px-3 py-1.5 rounded-md transition-colors text-xs font-medium shadow-sm"
                                                            title="Confirm & Dispatch"
                                                        >
                                                            <CheckCircle className="h-4 w-4 mr-1.5" />
                                                            Confirm
                                                        </button>
                                                        <button
                                                            onClick={() => handleRejectAlert(alert._id)}
                                                            className="flex items-center text-white bg-gray-500 hover:bg-gray-600 px-3 py-1.5 rounded-md transition-colors text-xs font-medium shadow-sm"
                                                            title="Reject as False Alarm"
                                                        >
                                                            <XCircle className="h-4 w-4 mr-1.5" />
                                                            Reject
                                                        </button>
                                                    </>
                                                )}
                                                <button
                                                    onClick={() => openLogs(alert)}
                                                    className="flex items-center text-blue-600 hover:text-blue-800 px-3 py-1.5 rounded-md hover:bg-blue-50 transition-colors text-xs font-medium border border-transparent hover:border-blue-200"
                                                    title="View Logs"
                                                >
                                                    <FileText className="h-4 w-4 mr-1.5" />
                                                    Logs
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteAlert(alert._id)}
                                                    className="flex items-center text-red-500 hover:text-red-700 px-3 py-1.5 rounded-md hover:bg-red-50 transition-colors text-xs font-medium border border-transparent hover:border-red-200"
                                                    title="Delete Alert"
                                                >
                                                    <Trash2 className="h-4 w-4 mr-1.5" />
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    )}
                                </tr>
                            ))}
                            {allAlerts.length === 0 && (
                                <tr>
                                    <td colSpan={user?.role === 'admin' ? "4" : "3"} className="px-6 py-12 text-center text-gray-500 bg-gray-50">
                                        <div className="flex flex-col items-center">
                                            <AlertTriangle className="h-10 w-10 text-gray-300 mb-3" />
                                            <p className="font-medium">No alerts generated yet</p>
                                            <p className="text-sm text-gray-400 mt-1">System is monitoring for accidents...</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>


            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center">
                        <Camera className="h-5 w-5 mr-2" />
                        All Cameras ({cameras.length})
                    </h3>
                </div>
                <div className="p-6">
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                        {cameras.map((camera) => (
                            <CameraCard key={camera._id} camera={camera} />
                        ))}

                        {cameras.length === 0 && (
                            <div className="col-span-full text-center py-12 text-gray-500">
                                <Camera className="h-12 w-12 mx-auto mb-3 opacity-30" />
                                <p>No cameras available</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardOverview;
